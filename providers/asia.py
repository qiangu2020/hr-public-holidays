"""Official public holidays for Hong Kong, Taiwan, Singapore and South Korea.

Every date is taken from a government-published calendar.  The provider never
calculates lunar dates and never invents substitute holidays; when an official
source is unavailable or malformed the whole fetch fails instead of returning
a silently incomplete calendar.
"""

from __future__ import annotations

import csv
import io
import json
import re
from datetime import date, datetime, timedelta
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin
from urllib.request import Request, urlopen

TARGET_YEARS = (2026, 2027)
TIMEOUT = 40
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
)

ALLOWED_KINDS = {"public", "bank", "government", "optional"}


class ProviderError(RuntimeError):
    """Raised when an official source cannot be fetched or parsed."""


# ---------------------------------------------------------------------------
# HTTP / parsing helpers
# ---------------------------------------------------------------------------


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProviderError(f"GET {url} failed: {exc}") from exc


def _get_text(url: str, encoding: str = "utf-8-sig") -> str:
    try:
        return _get(url).decode(encoding)
    except UnicodeDecodeError as exc:
        raise ProviderError(f"GET {url}: cannot decode as {encoding}: {exc}") from exc


def _get_json(url: str):
    text = _get_text(url, "utf-8-sig")
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ProviderError(f"GET {url}: invalid JSON: {exc}") from exc


def _event(
    day: date,
    name: str,
    name_en: str | None,
    scope: str,
    kind: str,
    source_url: str,
    note: str | None = None,
) -> dict:
    event = {
        "date": day.isoformat(),
        "name": name,
        "scope": scope,
        "kind": kind,
        "source_url": source_url,
    }
    if name_en:
        event["name_en"] = name_en
    if note:
        event["note"] = note
    return event


def _empty_by_year() -> dict[int, list[dict]]:
    return {year: [] for year in TARGET_YEARS}


def _select_years(
    by_year: dict[int, list[dict]],
    available: set[int],
    minimums: dict[int, int],
) -> dict[int, list[dict]]:
    """Keep only years that the source actually covers and that are complete.

    A year with no records at all is treated as "not published yet" and omitted.
    A year with records below the expected minimum is a parse/coverage failure.
    """

    selected: dict[int, list[dict]] = {}
    for year in TARGET_YEARS:
        if year not in available:
            continue
        events = by_year.get(year, [])
        minimum = minimums[year]
        if len(events) < minimum:
            raise ProviderError(
                f"{year}: parsed {len(events)} holidays, expected at least {minimum}"
            )
        selected[year] = events
    if 2026 not in selected:
        raise ProviderError("2026 is required but no complete 2026 calendar was parsed")
    return selected


def _make_region(
    region_id: str,
    name: str,
    name_en: str,
    timezone: str,
    scope: str,
    sources: list[dict],
    selected: dict[int, list[dict]],
    notes: list[str],
) -> dict:
    years = sorted(selected)
    events = [event for year in years for event in selected[year]]
    source_urls = {source["url"] for source in sources}

    seen_dates: dict[str, str] = {}
    seen_keys: set[tuple[str, str, str]] = set()
    for event in events:
        for field in ("date", "name", "scope", "kind", "source_url"):
            if not event.get(field):
                raise ProviderError(f"{region_id}: event missing {field}: {event!r}")
        if event["kind"] not in ALLOWED_KINDS:
            raise ProviderError(f"{region_id}: bad kind: {event!r}")
        if event["source_url"] not in source_urls:
            raise ProviderError(
                f"{region_id}: event source not declared in sources: {event['source_url']}"
            )
        try:
            event_year = int(event["date"][:4])
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"{region_id}: bad event date: {event!r}") from exc
        if event_year not in years:
            raise ProviderError(f"{region_id}: event year not in years: {event!r}")
        if event["date"] in seen_dates:
            raise ProviderError(
                f"{region_id}: multiple holidays on {event['date']}: "
                f"{seen_dates[event['date']]} / {event['name']}"
            )
        seen_dates[event["date"]] = event["name"]
        key = (event["date"], event["name"], event["scope"])
        if key in seen_keys:
            raise ProviderError(f"{region_id}: duplicate event: {key!r}")
        seen_keys.add(key)

    events.sort(key=lambda event: (event["date"], event["name"]))
    return {
        "id": region_id,
        "name": name,
        "name_en": name_en,
        "timezone": timezone,
        "scope": scope,
        "years": years,
        "sources": sources,
        "events": events,
        "notes": notes,
    }


# ---------------------------------------------------------------------------
# Hong Kong — 1823 official iCal JSON
# ---------------------------------------------------------------------------

HK_SC_URL = "https://www.1823.gov.hk/common/ical/sc.json"
HK_EN_URL = "https://www.1823.gov.hk/common/ical/en.json"
HK_SCOPE = (
    "香港特別行政區公眾假期（《假期條例》一般假期；"
    "星期日為法定一般假期，未逐日列出）"
)


def _ical_date(value) -> date:
    if isinstance(value, (list, tuple)):
        if not value:
            raise ValueError("empty iCal date")
        value = value[0]
    if not isinstance(value, str):
        raise ValueError(f"unsupported iCal date: {value!r}")
    return datetime.strptime(value.strip(), "%Y%m%d").date()


def _ical_vevents(document: dict) -> list[dict]:
    calendars = document.get("vcalendar")
    if isinstance(calendars, list):
        if not calendars:
            raise ValueError("empty vcalendar")
        calendar = calendars[0]
    else:
        calendar = calendars
    if not isinstance(calendar, dict):
        raise ValueError("vcalendar is not an object")
    events = calendar.get("vevent")
    if not isinstance(events, list):
        raise ValueError("vevent is not a list")
    return events


def _hk_region() -> dict:
    sc_document = _get_json(HK_SC_URL)
    en_document = _get_json(HK_EN_URL)

    try:
        sc_events = _ical_vevents(sc_document)
        en_events = _ical_vevents(en_document)
    except (KeyError, TypeError, ValueError) as exc:
        raise ProviderError(f"HK: unexpected iCal JSON structure: {exc}") from exc

    english_by_start: dict[str, str] = {}
    for item in en_events:
        try:
            start = _ical_date(item["dtstart"])
        except (KeyError, TypeError, ValueError):
            continue
        summary = item.get("summary")
        if isinstance(summary, str) and summary.strip():
            english_by_start[start.strftime("%Y%m%d")] = summary.strip()

    by_year = _empty_by_year()
    for item in sc_events:
        try:
            start = _ical_date(item["dtstart"])
            end = (
                _ical_date(item["dtend"])
                if item.get("dtend")
                else start + timedelta(days=1)
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"HK: bad event date in {item!r}: {exc}") from exc
        if end <= start:
            end = start + timedelta(days=1)

        summary = item.get("summary")
        if not isinstance(summary, str) or not summary.strip():
            raise ProviderError(f"HK: event without a summary: {item!r}")
        name = summary.strip()
        name_en = english_by_start.get(start.strftime("%Y%m%d"))

        day = start
        while day < end:
            if day.year in TARGET_YEARS:
                by_year[day.year].append(
                    _event(day, name, name_en, "香港", "public", HK_SC_URL)
                )
            day += timedelta(days=1)

    available = {2026}
    if by_year[2027]:
        available.add(2027)
    selected = _select_years(by_year, available, {2026: 17, 2027: 17})

    notes = [
        f"1823 官方 iCal 於 2026 年列出 {len(by_year[2026])} 日"
        + (f"、2027 年列出 {len(by_year[2027])} 日" if 2027 in selected else "")
        + "一般假期。",
        "星期日同屬《假期條例》下的一般假期，但官方 iCal 不逐日列出，因此本資料不含每個星期日。",
        "本資料為一般假期（general holidays），有別於法定假期（statutory holidays，勞工假期）；兩者日數及適用範圍不同。",
    ]
    if 2027 in selected:
        notes.append(
            "2027 年日期來自同一官方 iCal；農曆日期為官方公布，非本程式推算，官方日曆仍可能更新。"
        )
    else:
        notes.append("2027 年官方 iCal 尚未提供完整資料，未納入 years。")

    return _make_region(
        "HK",
        "香港",
        "Hong Kong",
        "Asia/Hong_Kong",
        HK_SCOPE,
        [
            {
                "name": "1823 — 香港特別行政區政府公眾假期（簡體中文 iCal JSON）",
                "url": HK_SC_URL,
                "format": "JSON (iCalendar)",
            },
            {
                "name": "1823 — Hong Kong public holidays (English iCal JSON)",
                "url": HK_EN_URL,
                "format": "JSON (iCalendar)",
            },
        ],
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Singapore — data.gov.sg / Ministry of Manpower consolidated dataset
# ---------------------------------------------------------------------------

SG_API = (
    "https://data.gov.sg/api/action/datastore_search"
    "?resource_id=d_8ef23381f9417e4d4254ee8b4dcdb176"
)
SG_SOURCE_URL = f"{SG_API}&limit=1000"
SG_DATASET_URL = (
    "https://data.gov.sg/datasets/d_8ef23381f9417e4d4254ee8b4dcdb176/view"
)
SG_MOM_URL = "https://www.mom.gov.sg/employment-practices/public-holidays"
SG_SCOPE = (
    "Nationwide public holidays designated by the Ministry of Manpower (MOM), "
    "including official observed days"
)


def _sg_records() -> list[dict]:
    records: list[dict] = []
    offset = 0
    total: int | None = None
    while total is None or len(records) < total:
        url = f"{SG_API}&limit=1000&offset={offset}"
        document = _get_json(url)
        if not document.get("success"):
            raise ProviderError(f"SG: datastore API reported failure: {document!r}")
        result = document.get("result")
        if not isinstance(result, dict):
            raise ProviderError(f"SG: unexpected datastore response: {document!r}")
        batch = result.get("records")
        if not isinstance(batch, list):
            raise ProviderError(f"SG: records is not a list: {result!r}")
        records.extend(batch)
        try:
            total = int(result["total"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ProviderError(f"SG: missing datastore total: {result!r}") from exc
        if not batch and len(records) < total:
            raise ProviderError(
                f"SG: datastore returned an empty page at offset {offset}"
            )
        offset += len(batch)
    return records


def _sg_region() -> dict:
    records = _sg_records()
    by_year = _empty_by_year()
    for record in records:
        if not isinstance(record, dict):
            raise ProviderError(f"SG: unexpected record: {record!r}")
        raw_date = str(record.get("date", "")).strip()
        name = str(record.get("holiday", "")).strip()
        if not raw_date or not name:
            raise ProviderError(f"SG: record without date/holiday: {record!r}")
        try:
            day = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ProviderError(
                f"SG: bad date in record {record!r}: {exc}"
            ) from exc
        if day.year not in TARGET_YEARS:
            continue
        note = (
            "Official observed day published by MOM."
            if name.endswith("(Observed)")
            else None
        )
        by_year[day.year].append(
            _event(day, name, None, "Singapore", "public", SG_SOURCE_URL, note)
        )

    available = {2026}
    if by_year[2027]:
        available.add(2027)
    selected = _select_years(by_year, available, {2026: 14, 2027: 12})

    notes = [
        f"2026 年 {len(by_year[2026])} 日"
        + (f"、2027 年 {len(by_year[2027])} 日" if 2027 in selected else "")
        + "，取自 data.gov.sg 的 MOM 全國公共假期合併資料集。",
        "星期日適逢公眾假期時，翌日星期一為官方補假；星期六假期不補假。",
        "Hari Raya Puasa、Hari Raya Haji 及 Vesak Day 日期以 MOM 官方公布為準，非本程式推算"
        + ("；2027 年日期仍可能官方修訂。" if 2027 in selected else "。"),
    ]
    if 2027 not in selected:
        notes.append("2027 年官方資料尚未提供完整資料，未納入 years。")

    return _make_region(
        "SG",
        "新加坡",
        "Singapore",
        "Asia/Singapore",
        SG_SCOPE,
        [
            {
                "name": "data.gov.sg — MOM consolidated public holidays dataset",
                "url": SG_DATASET_URL,
                "format": "HTML",
            },
            {
                "name": "data.gov.sg datastore API — MOM public holidays",
                "url": SG_SOURCE_URL,
                "format": "JSON",
            },
            {
                "name": "Ministry of Manpower — Public holidays",
                "url": SG_MOM_URL,
                "format": "HTML",
            },
        ],
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Taiwan — DGPA government office calendar via data.gov.tw dataset 14718
# ---------------------------------------------------------------------------

TW_DATASET_API = "https://data.gov.tw/api/v2/rest/dataset/14718"
TW_DATASET_URL = "https://data.gov.tw/dataset/14718"
TW_SCOPE = (
    "Government administrative office calendar (central and local government "
    "employees); private-sector observance may differ"
)

_TW_EN = {
    "開國紀念日": "Founding Day of the Republic of China",
    "小年夜": "Little New Year's Eve",
    "農曆除夕": "Chinese New Year's Eve",
    "春節": "Spring Festival (Chinese New Year)",
    "補假": "Make-up holiday",
    "和平紀念日": "Peace Memorial Day",
    "兒童節": "Children's Day",
    "清明節": "Tomb Sweeping Day",
    "勞動節": "Labour Day",
    "端午節": "Dragon Boat Festival",
    "中秋節": "Mid-Autumn Festival",
    "孔子誕辰紀念日/教師節": "Confucius' Birthday / Teachers' Day",
    "國慶日": "National Day",
    "臺灣光復暨金門古寧頭大捷紀念日": (
        "Taiwan Retrocession Day and Kinmen Guningtou Victory Commemoration Day"
    ),
    "行憲紀念日": "Constitution Day",
}


def _tw_resource_rank(resource: dict) -> int:
    description = str(resource.get("resourceDescription", ""))
    match = re.search(r"\((\d{7})更新\)", description)
    return int(match.group(1)) if match else 0


def _tw_csv_encoding(resource: dict) -> str:
    encoding = str(resource.get("resourceCharacterEncoding", "UTF-8")).upper()
    return "big5" if "BIG5" in encoding else "utf-8-sig"


def _tw_parse_csv(text: str, year: int, source_url: str) -> tuple[list[dict], list[str]]:
    reader = csv.DictReader(io.StringIO(text))
    fields = set(reader.fieldnames or [])
    required = {"西元日期", "星期", "是否放假", "備註"}
    if not required.issubset(fields):
        raise ProviderError(
            f"TW {year}: CSV header mismatch: {sorted(fields)!r}"
        )

    events: list[dict] = []
    make_up_workdays: list[str] = []
    row_count = 0
    for row in reader:
        row_count += 1
        raw_date = str(row.get("西元日期") or "").strip()
        if not raw_date:
            continue
        try:
            if re.fullmatch(r"\d{8}", raw_date):
                day = datetime.strptime(raw_date, "%Y%m%d").date()
            else:
                day = datetime.strptime(raw_date, "%Y/%m/%d").date()
        except ValueError as exc:
            raise ProviderError(
                f"TW {year}: bad date {raw_date!r}: {exc}"
            ) from exc
        if day.year != year:
            raise ProviderError(
                f"TW {year}: resource contains a date outside the year: {raw_date}"
            )

        flag = str(row.get("是否放假") or "").strip()
        note = str(row.get("備註") or "").strip()
        if flag == "2" and note:
            event_note = None
            if note == "補假":
                event_note = (
                    "Official make-up holiday listed by the DGPA; the calendar "
                    "does not name the compensated holiday."
                )
            events.append(
                _event(
                    day,
                    note,
                    _TW_EN.get(note),
                    "Government offices",
                    "government",
                    source_url,
                    event_note,
                )
            )
        elif flag != "2" and note:
            make_up_workdays.append(f"{day.isoformat()} {note}")

    if row_count < 360:
        raise ProviderError(
            f"TW {year}: CSV has only {row_count} rows; expected a full-year calendar"
        )
    if len(events) < 15:
        raise ProviderError(
            f"TW {year}: parsed only {len(events)} named holidays; expected at least 15"
        )
    return events, make_up_workdays


def _tw_region() -> dict:
    metadata = _get_json(TW_DATASET_API)
    result = metadata.get("result")
    if not isinstance(result, dict):
        raise ProviderError(f"TW: unexpected dataset metadata: {metadata!r}")
    distributions = result.get("distribution")
    if not isinstance(distributions, list):
        raise ProviderError("TW: dataset metadata has no distribution list")

    by_year = _empty_by_year()
    available: set[int] = set()
    sources = [
        {
            "name": "data.gov.tw 資料集 14718 — 中華民國政府行政機關辦公日曆表（metadata API）",
            "url": TW_DATASET_API,
            "format": "JSON",
        },
        {
            "name": "data.gov.tw 資料集 14718 — 政府行政機關辦公日曆表",
            "url": TW_DATASET_URL,
            "format": "HTML",
        },
    ]
    make_up_notes: list[str] = []

    for year in TARGET_YEARS:
        roc_year = year - 1911
        prefix = f"{roc_year}年"
        candidates = []
        for resource in distributions:
            if not isinstance(resource, dict):
                continue
            description = str(resource.get("resourceDescription", ""))
            if (
                description.startswith(prefix)
                and "政府行政機關辦公日曆表" in description
                and "Google" not in description
                and str(resource.get("resourceFormat", "")).upper() == "CSV"
                and resource.get("resourceDownloadUrl")
            ):
                candidates.append(resource)

        if not candidates:
            if year == 2026:
                raise ProviderError(f"TW: no 2026 ({prefix}) CSV resource found")
            continue

        candidates.sort(key=_tw_resource_rank)
        resource = candidates[-1]
        source_url = urljoin("https://data.gov.tw/", resource["resourceDownloadUrl"])
        text = _get_text(source_url, _tw_csv_encoding(resource))
        events, make_up_workdays = _tw_parse_csv(text, year, source_url)
        by_year[year].extend(events)
        available.add(year)
        sources.append(
            {
                "name": f"{prefix}（{year}）政府行政機關辦公日曆表",
                "url": source_url,
                "format": "CSV",
            }
        )
        if make_up_workdays:
            make_up_notes.append(
                f"{year} 年官方表另有補班日（不列入假期）："
                + "、".join(make_up_workdays)
            )

    selected = _select_years(by_year, available, {2026: 22, 2027: 24})

    notes = [
        "2026（民國115年）"
        + ("與 2027（民國116年）" if 2027 in selected else "")
        + "取自 DGPA 官方「政府行政機關辦公日曆表」。",
        "僅收錄官方表中 `是否放假=2` 且 `備註` 有名稱的日期；一般週末不逐日列出。",
        "`補假` 為官方明列之補假；官方表未逐字標明所補節日，本程式不作推測。",
        "此為政府行政機關辦公日曆，民間企業放假未必相同。",
        "2026/2027 農曆日期為官方日曆公布，非本程式推算；官方日曆仍可能更新。",
    ]
    notes.extend(make_up_notes)
    if 2027 not in selected:
        notes.append("2027 年官方資源尚未提供完整資料，未納入 years。")

    return _make_region(
        "TW",
        "台湾",
        "Taiwan",
        "Asia/Taipei",
        TW_SCOPE,
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# South Korea — KASI calendar data + official 2026 amendment
# ---------------------------------------------------------------------------

KR_DISCOVERY_URL = (
    "https://astro.kasi.re.kr/kor/life/post/calendarData?search_year={year}"
)
KR_FILE_BASE = "https://astro.kasi.re.kr/"
KR_2026_ANNOUNCEMENT = (
    "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156738544"
)
KR_2026_AMENDMENT = (
    "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156758983"
)
KR_2027_ANNOUNCEMENT = (
    "https://www.korea.kr/briefing/pressReleaseView.do?newsId=156768474"
)
KR_SCOPE = (
    "National public holidays for government offices (관공서 공휴일), including "
    "official substitute holidays; private-sector observance may differ"
)

_KR_EN = {
    "1월 1일": "New Year's Day",
    "설날": "Seollal (Korean New Year)",
    "3.1절": "Independence Movement Day",
    "노동절": "Labour Day",
    "어린이날": "Children's Day",
    "부처님오신날": "Buddha's Birthday",
    "전국동시지방선거": "Nationwide Local Election Day",
    "현충일": "Memorial Day",
    "제헌절": "Constitution Day",
    "광복절": "Liberation Day",
    "추석": "Chuseok (Korean Thanksgiving)",
    "개천절": "National Foundation Day",
    "한글날": "Hangeul Day",
    "기독탄신일": "Christmas Day",
}

_KASI_LINE = re.compile(
    r"^(?P<name>.+?)\s{2,}"
    r"(?P<start>\d{1,2}월\s*\d{1,2}일)"
    r"(?:\s*~\s*(?P<end>\d{1,2}월\s*\d{1,2}일))?"
    r"\s+(?P<days>[월화수목금토일](?:,[월화수목금토일])*)\s*$"
)


def _kr_name_en(name: str) -> str | None:
    if name.startswith("대체공휴일(") and name.endswith(")"):
        inner = name[len("대체공휴일(") : -1]
        base = _KR_EN.get(inner)
        return f"Substitute Holiday for {base}" if base else f"Substitute Holiday ({inner})"
    return _KR_EN.get(name)


def _kasi_date(value: str, year: int) -> date:
    match = re.fullmatch(r"(\d{1,2})월\s*(\d{1,2})일", value.strip())
    if not match:
        raise ValueError(f"bad Korean holiday date: {value!r}")
    return date(year, int(match.group(1)), int(match.group(2)))


def _parse_kasi(text: str, year: int, source_url: str) -> list[dict]:
    in_section = False
    found_section = False
    events: list[dict] = []

    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not in_section:
            if line.strip() == "국경일과 공휴일":
                in_section = True
                found_section = True
            continue
        if line.startswith("==="):
            break
        match = _KASI_LINE.match(line)
        if not match:
            continue

        name = match.group("name").strip()
        marker = ""
        if name.endswith("**"):
            marker = "**"
            name = name[:-2].rstrip()
        elif name.endswith("*"):
            marker = "*"
            name = name[:-1].rstrip()
        if marker == "**":
            # KASI's footnote: national day but not a public holiday.
            continue
        if not name:
            raise ProviderError(f"KR {year}: empty holiday name in {line!r}")

        start = _kasi_date(match.group("start"), year)
        end = _kasi_date(match.group("end"), year) if match.group("end") else start
        if end < start:
            end = date(year + 1, end.month, end.day)
        weekday_count = len(match.group("days").split(","))
        day_count = (end - start).days + 1
        if weekday_count != day_count:
            raise ProviderError(
                f"KR {year}: weekday count {weekday_count} does not match "
                f"{day_count} day(s) in {line!r}"
            )

        day = start
        while day <= end:
            if day.year in TARGET_YEARS:
                events.append(
                    _event(
                        day,
                        name,
                        _kr_name_en(name),
                        "대한민국",
                        "public",
                        source_url,
                    )
                )
            day += timedelta(days=1)

    if not found_section:
        raise ProviderError(f"KR {year}: holiday section not found")
    if not events:
        raise ProviderError(f"KR {year}: no holidays parsed")
    return events


def _kr_region() -> dict:
    by_year = _empty_by_year()
    available: set[int] = set()
    file_urls: dict[int, str] = {}

    for year in TARGET_YEARS:
        page = _get_text(KR_DISCOVERY_URL.format(year=year), "utf-8")
        match = re.search(r"downLocation\('([^']+\.txt)'", page)
        if not match:
            match = re.search(r'href="([^"]+\.txt)"', page)
        if not match:
            if year == 2026:
                raise ProviderError(f"KR: no calendar data file found for {year}")
            continue
        file_ref = match.group(1)
        if file_ref.startswith(("http://", "https://")):
            file_url = file_ref
        elif file_ref.startswith("/"):
            file_url = urljoin(KR_FILE_BASE, file_ref)
        else:
            file_url = urljoin(KR_FILE_BASE, f"file/{file_ref}")
        text = _get_text(file_url, "utf-8")
        events = _parse_kasi(text, year, file_url)
        by_year[year].extend(events)
        available.add(year)
        file_urls[year] = file_url

    # The KASI 2026 file was generated in 2024 and predates the April 2026
    # amendment.  Overlay the two holidays that the official amendment added.
    if 2026 in available:
        existing_dates = {event["date"] for event in by_year[2026]}
        overlay = [
            (
                date(2026, 5, 1),
                "노동절",
                "Labour Day",
                "2026-04-30 公布、2026-05-01 施行之《관공서의 공휴일에 관한 규정》"
                "修正（대통령령 제36290호）新增 노동절為公休日；KASI 2026 檔"
                "（2024-07-25 生成）尚未反映。",
            ),
            (
                date(2026, 7, 17),
                "제헌절",
                "Constitution Day",
                "2026-04-30 公布、2026-05-01 施行之《관공서의 공휴일에 관한 규정》"
                "修正（대통령령 제36290호）指定 제헌절為公休日；KASI 2026 檔"
                "將制憲節標為國慶日但非公休日（**），本資料依官方修正補入。",
            ),
        ]
        for day, name, name_en, note in overlay:
            if day.isoformat() not in existing_dates:
                by_year[2026].append(
                    _event(
                        day,
                        name,
                        name_en,
                        "대한민국",
                        "public",
                        KR_2026_AMENDMENT,
                        note,
                    )
                )

    selected = _select_years(by_year, available, {2026: 22, 2027: 24})

    sources = []
    if 2026 in file_urls:
        sources.append(
            {
                "name": "KASI 2026 달력자료 (calendar data, generated 2024-07-25)",
                "url": file_urls[2026],
                "format": "TXT",
            }
        )
    if 2027 in file_urls:
        sources.append(
            {
                "name": "KASI 2027 달력자료 (calendar data, generated 2026-06-30)",
                "url": file_urls[2027],
                "format": "TXT",
            }
        )
    sources.extend(
        [
            {
                "name": "우주항공청 — 2026년 월력요항 발표 (2025-06-30)",
                "url": KR_2026_ANNOUNCEMENT,
                "format": "HTML",
            },
            {
                "name": "인사혁신처 — 노동절·제헌절 공휴일 지정 (2026-04-28 의결)",
                "url": KR_2026_AMENDMENT,
                "format": "HTML",
            },
            {
                "name": "우주항공청 — 2027년 월력요항 발표 (2026-06-29)",
                "url": KR_2027_ANNOUNCEMENT,
                "format": "HTML",
            },
        ]
    )

    notes = [
        "2026 年基本日曆取自 KASI 달력자료（2024-07-25 生成）。KASI 頁面標明該檔非官方發表資料；2026 年官方 월력요항 於 2025-06-30 公布。",
        "KASI 2026 檔所列 20 個公休日與 2025-06-30 官方 월력요항 一致；差異僅在 2026 年 4 月修正新增之 2 日。",
        "2026-04-30 公布、2026-05-01 施行之《관공서의 공휴일에 관한 규정》修正（대통령령 제36290호）新增 노동절（5/1），並將 제헌절（7/17）指定為公休日；本資料依 인사혁신처 說明補入，KASI 2026 檔尚未反映。",
        "관공서 공휴일（含 대체공휴일）為準；民間部門實際休假可能不同。",
        "官方發表可能日後修正。",
    ]
    if 2027 in selected:
        notes.append(
            "2027 年取自 KASI 달력자료（2026-06-30 生成）與 우주항공청 2027 年 월력요항 發表（2026-06-29）；農曆日期為官方發表值，非本程式計算。"
        )
    else:
        notes.append("2027 年 KASI 資料尚未提供完整資料，未納入 years。")

    return _make_region(
        "KR",
        "韩国",
        "South Korea",
        "Asia/Seoul",
        KR_SCOPE,
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def fetch() -> list[dict]:
    """Return the four Asia regions with official 2026 (and 2027) holidays."""

    return [
        _hk_region(),
        _tw_region(),
        _sg_region(),
        _kr_region(),
    ]


__all__ = ["ProviderError", "fetch"]