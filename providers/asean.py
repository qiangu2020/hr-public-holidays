"""Official public holidays for Malaysia, Thailand, Indonesia and Vietnam.

The Malaysian and Indonesian calendars are published as PDFs whose state or
date tables are scanned images, and the Vietnamese schedule is published as
prose notices rather than a machine-readable calendar.  Those tables are
therefore checked in after manual verification against the official documents;
the original source URLs are retained in each region and every event points at
the document that establishes it.

Thailand's central bank publishes its financial-institution calendar as JSON.
It is fetched at runtime and parsed directly.  The provider never calculates
lunar or Islamic dates and never invents substitute holidays.
"""

from __future__ import annotations

import json
import re
from datetime import date, datetime
from urllib.error import HTTPError, URLError
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
# HTTP / shared helpers
# ---------------------------------------------------------------------------


def _get(url: str) -> bytes:
    request = Request(url, headers={"User-Agent": USER_AGENT, "Accept": "*/*"})
    try:
        with urlopen(request, timeout=TIMEOUT) as response:
            return response.read()
    except (HTTPError, URLError, TimeoutError, OSError) as exc:
        raise ProviderError(f"GET {url} failed: {exc}") from exc


def _get_json(url: str):
    try:
        text = _get(url).decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise ProviderError(f"GET {url}: cannot decode as UTF-8: {exc}") from exc
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
                f"{region_id}: event source not declared in sources: "
                f"{event['source_url']}"
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


def _add_days(
    by_year: dict[int, list[dict]],
    year: int,
    days: list[tuple[int, int, str, str, str | None]],
    scope: str,
    kind: str,
    source_url: str,
    note: str | None = None,
) -> None:
    for month, day, name, name_en, day_note in days:
        by_year[year].append(
            _event(
                date(year, month, day),
                name,
                name_en,
                scope,
                kind,
                source_url,
                day_note or note,
            )
        )


# ---------------------------------------------------------------------------
# Malaysia — official HKA 2026 and HKA 2027 PDF calendars
# ---------------------------------------------------------------------------

MY_2026_SOURCE = "https://www.kabinet.gov.my/storage/2025/08/HKA-2026.pdf"
MY_2027_SOURCE = "https://www.kabinet.gov.my/storage/2026/08/HKA_2027.pdf"

MY_SCOPE = "马来西亚公共假期（以联邦表为主，州属适用范围见事件 scope）"
MY_FEDERAL = "马来西亚联邦"
MY_EXCEPT_SARAWAK = "马来西亚联邦（砂拉越除外）"
MY_QURBAN_SECOND = "马来西亚（吉兰丹、登嘉楼、吉打、玻璃市）"
MY_KUL_SCOPE = "吉隆坡联邦直辖区（W.P. Kuala Lumpur）"

MY_2026_COMMON = [
    (2, 17, "农历新年（Tahun Baharu Cina）", "Chinese New Year", None),
    (3, 21, "开斋节（Hari Raya Puasa）", "Hari Raya Puasa (Eid al-Fitr)", None),
    (
        3,
        22,
        "开斋节第二天（Hari Raya Puasa Hari Kedua）",
        "Second Day of Hari Raya Puasa",
        None,
    ),
    (5, 1, "劳动节（Hari Pekerja）", "Labour Day", None),
    (5, 27, "宰牲节（Hari Raya Qurban）", "Hari Raya Qurban (Eid al-Adha)", None),
    (5, 31, "卫塞节（Hari Wesak）", "Wesak Day", None),
    (
        6,
        1,
        "国家元首诞辰（Hari Keputeraan Rasmi Yang di-Pertuan Agong）",
        "Birthday of the Yang di-Pertuan Agong",
        None,
    ),
    (
        6,
        17,
        "伊斯兰新年（Awal Muharam / Maal Hijrah）",
        "Awal Muharam (Islamic New Year)",
        None,
    ),
    (
        8,
        25,
        "先知穆罕默德诞辰（Maulidur Rasul）",
        "Maulidur Rasul (Birthday of the Prophet Muhammad)",
        None,
    ),
    (8, 31, "国庆日（Hari Kebangsaan）", "National Day", None),
    (9, 16, "马来西亚日（Hari Malaysia）", "Malaysia Day", None),
    (12, 25, "圣诞节（Hari Krismas）", "Christmas Day", None),
]

MY_2027_COMMON = [
    (2, 6, "农历新年（Tahun Baharu Cina）", "Chinese New Year", None),
    (
        2,
        7,
        "农历新年第二天（Tahun Baharu Cina Hari Kedua）",
        "Second Day of Chinese New Year",
        "联邦表列 14 州（吉兰丹、登嘉楼除外）；该两州由州表列为州假，合并后全国适用。",
    ),
    (3, 10, "开斋节（Hari Raya Puasa）", "Hari Raya Puasa (Eid al-Fitr)", None),
    (
        3,
        11,
        "开斋节第二天（Hari Raya Puasa Hari Kedua）",
        "Second Day of Hari Raya Puasa",
        None,
    ),
    (5, 1, "劳动节（Hari Pekerja）", "Labour Day", None),
    (5, 17, "宰牲节（Hari Raya Qurban）", "Hari Raya Qurban (Eid al-Adha)", None),
    (5, 20, "卫塞节（Hari Wesak）", "Wesak Day", None),
    (
        6,
        6,
        "伊斯兰新年（Awal Muharam / Maal Hijrah）",
        "Awal Muharam (Islamic New Year)",
        None,
    ),
    (
        6,
        7,
        "国家元首诞辰（Hari Keputeraan Rasmi Yang di-Pertuan Agong）",
        "Birthday of the Yang di-Pertuan Agong",
        None,
    ),
    (
        8,
        15,
        "先知穆罕默德诞辰（Maulidur Rasul）",
        "Maulidur Rasul (Birthday of the Prophet Muhammad)",
        None,
    ),
    (8, 31, "国庆日（Hari Kebangsaan）", "National Day", None),
    (9, 16, "马来西亚日（Hari Malaysia）", "Malaysia Day", None),
    (12, 25, "圣诞节（Hari Krismas）", "Christmas Day", None),
]

MY_2026_KUL = [
    (1, 1, "元旦（Tahun Baharu）", "New Year's Day", None),
    (
        2,
        1,
        "联邦直辖区日暨大宝森节（Hari Wilayah Persekutuan / Hari Thaipusam）",
        "Federal Territory Day and Thaipusam",
        "两个假日同日；官方表在吉隆坡栏均予勾选。",
    ),
    (2, 17, "农历新年（Tahun Baharu Cina）", "Chinese New Year", None),
    (
        2,
        18,
        "农历新年第二天（Tahun Baharu Cina Hari Kedua）",
        "Second Day of Chinese New Year",
        None,
    ),
    (
        3,
        7,
        "古兰经降示日（Hari Nuzul Al-Quran）",
        "Nuzul Al-Quran Day",
        None,
    ),
    (3, 21, "开斋节（Hari Raya Puasa）", "Hari Raya Puasa (Eid al-Fitr)", None),
    (
        3,
        22,
        "开斋节第二天（Hari Raya Puasa Hari Kedua）",
        "Second Day of Hari Raya Puasa",
        None,
    ),
    (5, 1, "劳动节（Hari Pekerja）", "Labour Day", None),
    (5, 27, "宰牲节（Hari Raya Qurban）", "Hari Raya Qurban (Eid al-Adha)", None),
    (5, 31, "卫塞节（Hari Wesak）", "Wesak Day", None),
    (
        6,
        1,
        "国家元首诞辰（Hari Keputeraan Rasmi Yang di-Pertuan Agong）",
        "Birthday of the Yang di-Pertuan Agong",
        None,
    ),
    (
        6,
        17,
        "伊斯兰新年（Awal Muharam / Maal Hijrah）",
        "Awal Muharam (Islamic New Year)",
        None,
    ),
    (
        8,
        25,
        "先知穆罕默德诞辰（Maulidur Rasul）",
        "Maulidur Rasul (Birthday of the Prophet Muhammad)",
        None,
    ),
    (8, 31, "国庆日（Hari Kebangsaan）", "National Day", None),
    (9, 16, "马来西亚日（Hari Malaysia）", "Malaysia Day", None),
    (11, 8, "屠妖节（Hari Deepavali）", "Deepavali", None),
    (12, 25, "圣诞节（Hari Krismas）", "Christmas Day", None),
]

MY_2027_KUL = [
    (1, 1, "元旦（Tahun Baharu）", "New Year's Day", None),
    (1, 22, "大宝森节（Hari Thaipusam）", "Thaipusam", None),
    (
        2,
        1,
        "联邦直辖区日（Hari Wilayah Persekutuan）",
        "Federal Territory Day",
        None,
    ),
    (2, 6, "农历新年（Tahun Baharu Cina）", "Chinese New Year", None),
    (
        2,
        7,
        "农历新年第二天（Tahun Baharu Cina Hari Kedua）",
        "Second Day of Chinese New Year",
        None,
    ),
    (
        2,
        24,
        "古兰经降示日（Hari Nuzul Al-Quran）",
        "Nuzul Al-Quran Day",
        None,
    ),
    (3, 10, "开斋节（Hari Raya Puasa）", "Hari Raya Puasa (Eid al-Fitr)", None),
    (
        3,
        11,
        "开斋节第二天（Hari Raya Puasa Hari Kedua）",
        "Second Day of Hari Raya Puasa",
        None,
    ),
    (5, 1, "劳动节（Hari Pekerja）", "Labour Day", None),
    (5, 17, "宰牲节（Hari Raya Qurban）", "Hari Raya Qurban (Eid al-Adha)", None),
    (5, 20, "卫塞节（Hari Wesak）", "Wesak Day", None),
    (
        6,
        6,
        "伊斯兰新年（Awal Muharam / Maal Hijrah）",
        "Awal Muharam (Islamic New Year)",
        None,
    ),
    (
        6,
        7,
        "国家元首诞辰（Hari Keputeraan Rasmi Yang di-Pertuan Agong）",
        "Birthday of the Yang di-Pertuan Agong",
        None,
    ),
    (
        8,
        15,
        "先知穆罕默德诞辰（Maulidur Rasul）",
        "Maulidur Rasul (Birthday of the Prophet Muhammad)",
        None,
    ),
    (8, 31, "国庆日（Hari Kebangsaan）", "National Day", None),
    (9, 16, "马来西亚日（Hari Malaysia）", "Malaysia Day", None),
    (10, 28, "屠妖节（Hari Deepavali）", "Deepavali", None),
    (12, 25, "圣诞节（Hari Krismas）", "Christmas Day", None),
]


def _my_region() -> dict:
    by_year = _empty_by_year()

    # Federal table entries that apply nationwide.
    _add_days(by_year, 2026, MY_2026_COMMON, MY_FEDERAL, "public", MY_2026_SOURCE)
    _add_days(by_year, 2027, MY_2027_COMMON, MY_FEDERAL, "public", MY_2027_SOURCE)

    # Federal table entries whose applicability is restricted by state.
    by_year[2026].append(
        _event(
            date(2026, 2, 18),
            "农历新年第二天（Tahun Baharu Cina Hari Kedua）",
            "Second Day of Chinese New Year",
            "马来西亚（全国；吉兰丹、登嘉楼依州表）",
            "public",
            MY_2026_SOURCE,
            "联邦表列 14 州（吉兰丹、登嘉楼除外）；该两州由州表列为州假，合并后全国适用。",
        )
    )
    by_year[2026].append(
        _event(
            date(2026, 5, 28),
            "宰牲节第二天（Hari Raya Qurban Hari Kedua）",
            "Second Day of Hari Raya Qurban",
            MY_QURBAN_SECOND,
            "public",
            MY_2026_SOURCE,
            "联邦表列吉兰丹、登嘉楼；州表列吉打、玻璃市。",
        )
    )
    by_year[2026].append(
        _event(
            date(2026, 11, 8),
            "屠妖节（Hari Deepavali）",
            "Deepavali",
            MY_EXCEPT_SARAWAK,
            "public",
            MY_2026_SOURCE,
            "官方表列明砂拉越不适用。",
        )
    )
    by_year[2027].append(
        _event(
            date(2027, 5, 18),
            "宰牲节第二天（Hari Raya Qurban Hari Kedua）",
            "Second Day of Hari Raya Qurban",
            MY_QURBAN_SECOND,
            "public",
            MY_2027_SOURCE,
            "联邦表列吉兰丹、登嘉楼；州表列吉打、玻璃市。",
        )
    )
    by_year[2027].append(
        _event(
            date(2027, 10, 28),
            "屠妖节（Hari Deepavali）",
            "Deepavali",
            MY_EXCEPT_SARAWAK,
            "public",
            MY_2027_SOURCE,
            "官方表列明砂拉越不适用。",
        )
    )

    selected = _select_years(by_year, {2026, 2027}, {2026: 15, 2027: 15})
    sources = [
        {
            "name": "马来西亚首相署（BKPP）— HKA 2026 联邦及州公共假期表",
            "url": MY_2026_SOURCE,
            "format": "PDF",
        },
        {
            "name": "马来西亚首相署（BKPP）— HKA 2027 联邦及州公共假期表",
            "url": MY_2027_SOURCE,
            "format": "PDF",
        },
    ]
    notes = [
        "日期取自马来西亚首相署（Bahagian Kabinet, Perundangan dan Perhubungan Antara Institusi）公布的 HKA 2026 与 HKA 2027 官方 PDF；不是第三方整理资料。",
        "官方 PDF 的规范化快照，最近人工核对日期：2026-11-06。HKA 州属适用栏为图形勾选，后续修订需重新核对，不是实时接口；原始 PDF 链接保留供查核。",
        "MY 以 HKA 联邦表为主；同一日期由联邦表与州表合并适用的条目（如吉兰丹、登嘉楼、吉打、玻璃市）以事件 scope 标注。其他州属未单独设区；吉隆坡适用假日见 MY-KUL。",
        "官方表未列出的补假不自行推算；例如 2026 年 11 月 8 日屠妖节适逢星期日，HKA 未列翌日补假。",
        "伊斯兰历及农历日期以官方表为准；官方以 * 标注者可能调整，若官方修订应更新本表。",
    ]
    return _make_region(
        "MY",
        "马来西亚",
        "Malaysia",
        "Asia/Kuala_Lumpur",
        MY_SCOPE,
        sources,
        selected,
        notes,
    )


def _my_kul_region() -> dict:
    by_year = _empty_by_year()
    _add_days(
        by_year,
        2026,
        MY_2026_KUL,
        MY_KUL_SCOPE,
        "public",
        MY_2026_SOURCE,
    )
    _add_days(
        by_year,
        2027,
        MY_2027_KUL,
        MY_KUL_SCOPE,
        "public",
        MY_2027_SOURCE,
    )

    selected = _select_years(by_year, {2026, 2027}, {2026: 17, 2027: 18})
    sources = [
        {
            "name": "马来西亚首相署（BKPP）— HKA 2026 联邦及州公共假期表（W.P. Kuala Lumpur 栏）",
            "url": MY_2026_SOURCE,
            "format": "PDF",
        },
        {
            "name": "马来西亚首相署（BKPP）— HKA 2027 联邦及州公共假期表（W.P. Kuala Lumpur 栏）",
            "url": MY_2027_SOURCE,
            "format": "PDF",
        },
    ]
    notes = [
        "只列 HKA 2026 / HKA 2027 中 W.P. KUALA LUMPUR（吉隆坡联邦直辖区）栏勾选的假日；不适用于吉隆坡的联邦或州假日已剔除。",
        "2026 年 2 月 1 日同时为联邦直辖区日与大宝森节，合并为一笔事件。",
        "官方 PDF 的规范化快照，最近人工核对日期：2026-11-06。HKA 州属适用栏为图形勾选，后续修订需重新核对，不是实时接口；原始 PDF 链接保留。",
        "官方表未列出的补假不自行推算。",
        "伊斯兰历及农历日期以官方表为准；官方以 * 标注者可能调整。",
    ]
    return _make_region(
        "MY-KUL",
        "吉隆坡",
        "Kuala Lumpur",
        "Asia/Kuala_Lumpur",
        "吉隆坡联邦直辖区公共假期",
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Thailand — Bank of Thailand financial-institution holiday JSON
# ---------------------------------------------------------------------------

TH_PAGE = "https://www.bot.or.th/en/financial-institutions-holiday.html"
TH_MODEL = (
    "https://www.bot.or.th/content/bot/en/financial-institutions-holiday/"
    "jcr:content/root/container/holidaycalendar.model.{year}.json"
)
TH_SCOPE = "泰国金融机构/银行假日（泰国银行 BOT 公布；非公务员统一假期）"


def _th_chinese_name(description: str) -> str:
    normalized = " ".join(description.split()).replace("’", "'")
    if normalized.startswith("Substitution for "):
        base = normalized[len("Substitution for ") :]
        base = re.sub(r"\s*\([^)]*\)\s*$", "", base).strip()
        return f"{_th_chinese_name(base)}补假"
    if normalized == "New Year's Day":
        return "元旦"
    if normalized == "New Year's Eve":
        return "除夕"
    if normalized == "Additional special holiday in Bangkok":
        return "曼谷额外特别假日"
    if normalized == "Additional special holiday":
        return "额外特别假日"
    if normalized == "Makha Bucha Day":
        return "万佛节"
    if normalized == "Chakri Memorial Day":
        return "却克里王朝纪念日"
    if normalized == "Songkran Festival":
        return "宋干节"
    if normalized == "National Labor Day":
        return "国家劳动节"
    if normalized == "Coronation Day":
        return "国王加冕纪念日"
    if normalized == "Visakha Bucha Day":
        return "卫塞节"
    if "Queen Suthida" in normalized:
        return "素提达王后诞辰"
    if "King Maha Vajiralongkorn" in normalized:
        return "国王玛哈·哇集拉隆功诞辰"
    if normalized == "Asarnha Bucha Day":
        return "三宝佛节"
    if "Queen Sirikit" in normalized:
        return "诗丽吉王太后诞辰暨母亲节"
    if normalized == "H.M. King Bhumibol Adulyadej the Great Memorial Day":
        return "普密蓬国王逝世纪念日"
    if normalized == "H.M. King Chulalongkorn the Great Memorial Day":
        return "朱拉隆功国王纪念日"
    if (
        "King Bhumibol Adulyadej the Great's Birthday" in normalized
        and "National Day" in normalized
    ):
        return "普密蓬国王诞辰、国庆日暨父亲节"
    if normalized == "Constitution Day":
        return "宪法日"
    return normalized


def _th_region() -> dict:
    by_year = _empty_by_year()
    sources = [
        {
            "name": "泰国银行（BOT）— Financial Institutions Holiday 说明页",
            "url": TH_PAGE,
            "format": "HTML",
        }
    ]

    for year in TARGET_YEARS:
        source_url = TH_MODEL.format(year=year)
        document = _get_json(source_url)
        rows = document.get("holidayCalendarLists") if isinstance(document, dict) else None
        if not isinstance(rows, list) or not rows:
            raise ProviderError(f"TH {year}: holidayCalendarLists missing or empty")
        for row in rows:
            if not isinstance(row, dict):
                raise ProviderError(f"TH {year}: unexpected holiday row: {row!r}")
            raw_description = row.get("holidayDescription")
            raw_date = row.get("date")
            raw_month = row.get("month")
            raw_year = row.get("year")
            if not all(
                isinstance(value, str) and value.strip()
                for value in (raw_description, raw_date, raw_month, raw_year)
            ):
                raise ProviderError(f"TH {year}: incomplete holiday row: {row!r}")
            if raw_year.strip() != str(year):
                raise ProviderError(
                    f"TH {year}: row has unexpected year: {row!r}"
                )
            description = " ".join(raw_description.split())
            match = re.fullmatch(
                r"([A-Za-z]+)\s+(\d{1,2})",
                " ".join(raw_date.split()),
            )
            if not match:
                raise ProviderError(f"TH {year}: bad date field: {raw_date!r}")
            weekday, day_text = match.groups()
            month_text = " ".join(raw_month.split())
            year_text = raw_year.strip()
            try:
                day = datetime.strptime(
                    f"{day_text} {month_text} {year_text}", "%d %B %Y"
                ).date()
            except ValueError as exc:
                raise ProviderError(f"TH {year}: bad holiday date: {row!r}") from exc
            if day.strftime("%A") != weekday:
                raise ProviderError(
                    f"TH {year}: weekday does not match date: {row!r}"
                )
            if day.year != year:
                raise ProviderError(f"TH {year}: row outside year: {row!r}")

            scope = "泰国（曼谷金融机构）" if "in Bangkok" in description else "泰国（金融机构）"
            note = None
            if description.startswith("Substitution for "):
                original = re.search(r"\(([^)]+)\)", description)
                note = (
                    f"BOT 列为补假；原假日：{original.group(1)}"
                    if original
                    else "BOT 列为补假。"
                )
            elif description == "Additional special holiday in Bangkok":
                note = "BOT 公布之额外特别假日，仅适用于曼谷地区金融机构。"
            elif description == "Additional special holiday":
                note = "BOT 公布之金融机构额外特别假日。"
            by_year[year].append(
                _event(
                    day,
                    _th_chinese_name(description),
                    description,
                    scope,
                    "bank",
                    source_url,
                    note,
                )
            )
        sources.append(
            {
                "name": f"泰国银行（BOT）— {year} 年金融机构假日（JSON）",
                "url": source_url,
                "format": "JSON",
            }
        )

    selected = _select_years(by_year, {2026, 2027}, {2026: 20, 2027: 18})
    notes = [
        "BOT 公布的是金融机构及专门金融机构（银行）假日，不等同于泰国公务员/政府机关或所有私营企业的统一假期。",
        "5 月 1 日国家劳动节属劳动假日，BOT 亦将其列入金融机构休假日；其法律性质与一般银行假日不同。2027 年 5 月 1 日为星期六，BOT 列 5 月 3 日为补假。",
        "2026 年 1 月 2 日为金融机构额外特别假日；2026 年 10 月 16 日额外特别假日仅适用于曼谷。",
        "BOT 日历说明：伊斯兰银行及南部边境府（那拉提瓦、北大年、也拉、沙敦、宋卡）可能另有开斋节、宰牲节及农历新年假日；未列入本表。",
        "补假及特别假日均以 BOT 公布的年度 JSON 为准，本程序不自行推算。",
        "2027 年资料已由 BOT 同日历端点提供，故一并纳入。",
    ]
    return _make_region(
        "TH",
        "泰国",
        "Thailand",
        "Asia/Bangkok",
        TH_SCOPE,
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Indonesia — official SKB 3 Menteri 2026 and 2027 (scanned PDFs)
# ---------------------------------------------------------------------------

ID_2026_SOURCE = (
    "https://www.kemenkopmk.go.id/sites/default/files/pengumuman/2025-09/"
    "SKB%20Libur%20Nasional%20dan%20Cuti%20Bersama%20Tahun%202026.pdf"
)
ID_2027_SOURCE = (
    "https://www.kemenkopmk.go.id/sites/default/files/pengumuman/2026-09/"
    "SKB%20Libur%20Nasional%20dan%20Cuti%20Bersama%20Tahun%202027.pdf"
)
ID_SCOPE = "印度尼西亚全国公共假日及政府机关共同休假（SKB 3 Menteri）"
ID_PUBLIC = "印度尼西亚（全国）"
ID_GOVERNMENT = "印度尼西亚（政府机关）"

ID_2026_PUBLIC = [
    (1, 1, "元旦（Tahun Baru 2026 Masehi）", "New Year's Day 2026", None),
    (
        1,
        16,
        "先知登霄日（Isra Mikraj Nabi Muhammad SAW）",
        "Isra Mikraj (Ascension of the Prophet)",
        None,
    ),
    (
        2,
        17,
        "农历新年（Tahun Baru Imlek 2577 Kongzili）",
        "Chinese New Year 2577",
        None,
    ),
    (
        3,
        19,
        "静居日（Hari Suci Nyepi，Saka 1948）",
        "Nyepi (Balinese Day of Silence)",
        None,
    ),
    (
        3,
        21,
        "开斋节第 1 天（Hari Raya Idul Fitri 1447 Hijriah）",
        "Eid al-Fitr 1447 AH (Day 1)",
        None,
    ),
    (
        3,
        22,
        "开斋节第 2 天（Hari Raya Idul Fitri 1447 Hijriah）",
        "Eid al-Fitr 1447 AH (Day 2)",
        None,
    ),
    (
        4,
        3,
        "耶稣受难日（Wafat Isa Al Masih）",
        "Good Friday (Death of Jesus Christ)",
        None,
    ),
    (4, 5, "复活节（Paskah）", "Easter Sunday", None),
    (
        5,
        1,
        "国际劳动节（Hari Buruh Internasional）",
        "International Labour Day",
        None,
    ),
    (
        5,
        14,
        "耶稣升天节（Kenaikan Isa Al Masih）",
        "Ascension Day of Jesus Christ",
        None,
    ),
    (
        5,
        27,
        "宰牲节（Hari Raya Idul Adha 1447 Hijriah）",
        "Eid al-Adha 1447 AH",
        None,
    ),
    (
        5,
        31,
        "卫塞节（Hari Raya Waisak 2570 BE）",
        "Vesak Day 2570 BE",
        None,
    ),
    (6, 1, "建国五原则日（Hari Lahir Pancasila）", "Pancasila Day", None),
    (
        6,
        16,
        "伊斯兰新年（Tahun Baru Islam 1448 Hijriah）",
        "Islamic New Year 1448 AH",
        None,
    ),
    (
        8,
        17,
        "印度尼西亚独立日（Hari Kemerdekaan Republik Indonesia）",
        "Independence Day of Indonesia",
        None,
    ),
    (
        8,
        25,
        "先知穆罕默德诞辰（Maulid Nabi Muhammad SAW）",
        "Birthday of the Prophet Muhammad",
        None,
    ),
    (12, 25, "圣诞节（Hari Raya Natal）", "Christmas Day", None),
]

ID_2026_JOINT = [
    (
        2,
        16,
        "农历新年共同休假（Cuti Bersama Tahun Baru Imlek）",
        "Joint Leave for Chinese New Year",
        None,
    ),
    (
        3,
        18,
        "静居日共同休假（Cuti Bersama Hari Suci Nyepi）",
        "Joint Leave for Nyepi",
        None,
    ),
    (
        3,
        20,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        3,
        23,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        3,
        24,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        5,
        15,
        "耶稣升天节共同休假（Cuti Bersama Kenaikan Isa Al Masih）",
        "Joint Leave for Ascension Day",
        None,
    ),
    (
        5,
        28,
        "宰牲节共同休假（Cuti Bersama Idul Adha）",
        "Joint Leave for Eid al-Adha",
        None,
    ),
    (
        12,
        24,
        "圣诞节共同休假（Cuti Bersama Hari Raya Natal）",
        "Joint Leave for Christmas",
        None,
    ),
]

ID_2027_PUBLIC = [
    (1, 1, "元旦（Tahun Baru 2027 Masehi）", "New Year's Day 2027", None),
    (
        1,
        5,
        "先知登霄日（Isra Mikraj Nabi Muhammad SAW 1448 Hijriah）",
        "Isra Mikraj 1448 AH",
        None,
    ),
    (
        2,
        6,
        "农历新年（Tahun Baru Imlek 2578 Kongzili）",
        "Chinese New Year 2578",
        None,
    ),
    (
        3,
        8,
        "静居日（Hari Suci Nyepi，Saka 1949）",
        "Nyepi (Balinese Day of Silence)",
        None,
    ),
    (
        3,
        10,
        "开斋节第 1 天（Hari Raya Idul Fitri 1448 Hijriah）",
        "Eid al-Fitr 1448 AH (Day 1)",
        None,
    ),
    (
        3,
        11,
        "开斋节第 2 天（Hari Raya Idul Fitri 1448 Hijriah）",
        "Eid al-Fitr 1448 AH (Day 2)",
        None,
    ),
    (
        3,
        26,
        "耶稣受难日（Wafat Isa Al Masih）",
        "Good Friday (Death of Jesus Christ)",
        None,
    ),
    (3, 28, "复活节（Paskah）", "Easter Sunday", None),
    (
        5,
        1,
        "国际劳动节（Hari Buruh Internasional）",
        "International Labour Day",
        None,
    ),
    (
        5,
        6,
        "耶稣升天节（Kenaikan Isa Al Masih）",
        "Ascension Day of Jesus Christ",
        None,
    ),
    (
        5,
        17,
        "宰牲节（Hari Raya Idul Adha 1448 Hijriah）",
        "Eid al-Adha 1448 AH",
        None,
    ),
    (
        5,
        20,
        "卫塞节（Hari Raya Waisak 2571 BE）",
        "Vesak Day 2571 BE",
        None,
    ),
    (6, 1, "建国五原则日（Hari Lahir Pancasila）", "Pancasila Day", None),
    (
        6,
        6,
        "伊斯兰新年（Tahun Baru Islam 1449 Hijriah）",
        "Islamic New Year 1449 AH",
        None,
    ),
    (
        8,
        15,
        "先知穆罕默德诞辰（Maulid Nabi Muhammad SAW）",
        "Birthday of the Prophet Muhammad",
        None,
    ),
    (
        8,
        17,
        "印度尼西亚独立日（Hari Kemerdekaan Republik Indonesia）",
        "Independence Day of Indonesia",
        None,
    ),
    (12, 25, "圣诞节（Hari Raya Natal）", "Christmas Day", None),
    (
        12,
        26,
        "先知登霄日（Isra Mikraj Nabi Muhammad SAW 1449 Hijriah）",
        "Isra Mikraj 1449 AH",
        None,
    ),
]

ID_2027_JOINT = [
    (
        2,
        5,
        "农历新年共同休假（Cuti Bersama Tahun Baru Imlek）",
        "Joint Leave for Chinese New Year",
        None,
    ),
    (
        3,
        9,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        3,
        12,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        3,
        15,
        "开斋节共同休假（Cuti Bersama Idul Fitri）",
        "Joint Leave for Eid al-Fitr",
        None,
    ),
    (
        3,
        25,
        "耶稣受难日共同休假（Cuti Bersama Wafat Isa Al Masih）",
        "Joint Leave for Good Friday",
        None,
    ),
    (
        5,
        18,
        "宰牲节共同休假（Cuti Bersama Idul Adha）",
        "Joint Leave for Eid al-Adha",
        None,
    ),
    (
        5,
        19,
        "卫塞节共同休假（Cuti Bersama Waisak）",
        "Joint Leave for Vesak",
        None,
    ),
    (
        12,
        24,
        "圣诞节共同休假（Cuti Bersama Hari Raya Natal）",
        "Joint Leave for Christmas",
        None,
    ),
]


def _id_region() -> dict:
    by_year = _empty_by_year()
    _add_days(
        by_year,
        2026,
        ID_2026_PUBLIC,
        ID_PUBLIC,
        "public",
        ID_2026_SOURCE,
        "SKB 2026 全国公共假日（libur nasional）。",
    )
    _add_days(
        by_year,
        2026,
        ID_2026_JOINT,
        ID_GOVERNMENT,
        "government",
        ID_2026_SOURCE,
        "SKB 2026 共同休假（cuti bersama）；适用于政府机关，私营部门可选择执行。",
    )
    _add_days(
        by_year,
        2027,
        ID_2027_PUBLIC,
        ID_PUBLIC,
        "public",
        ID_2027_SOURCE,
        "SKB 2027 全国公共假日（libur nasional）。",
    )
    _add_days(
        by_year,
        2027,
        ID_2027_JOINT,
        ID_GOVERNMENT,
        "government",
        ID_2027_SOURCE,
        "SKB 2027 共同休假（cuti bersama）；适用于政府机关，私营部门可选择执行。",
    )

    selected = _select_years(by_year, {2026, 2027}, {2026: 25, 2027: 26})
    sources = [
        {
            "name": "印度尼西亚人类发展与文化统筹部 — SKB Libur Nasional dan Cuti Bersama Tahun 2026（SKB 1497/2025、2/2025、5/2025）",
            "url": ID_2026_SOURCE,
            "format": "PDF（扫描件）",
        },
        {
            "name": "印度尼西亚人类发展与文化统筹部 — SKB Libur Nasional dan Cuti Bersama Tahun 2027（SKB 1205/2026、3/2026、2/2026）",
            "url": ID_2027_SOURCE,
            "format": "PDF（扫描件）",
        },
    ]
    notes = [
        "日期取自印度尼西亚人类发展与文化统筹部官网公布的 SKB 3 Menteri：2026 年 SKB 编号 1497/2025、2/2025、5/2025；2027 年 SKB 编号 1205/2026、3/2026、2/2026（2026-09-15 签署）。",
        "官方扫描 PDF 的规范化快照，最近人工核对日期：2026-11-06。后续修订需重新核对，不是实时接口；原始 PDF 链接保留供查核。",
        "libur nasional（kind=public）适用于全国；SKB 未列地方性假日。",
        "cuti bersama（kind=government）为政府机关共同休假，私营部门可依 SKB 建议执行，故单独标注。",
        "宗教节日日期以 SKB 公布为准；若宗教部 itsbat 结果导致调整，应由政府发布新 SKB，本程序不自行推算。",
    ]
    return _make_region(
        "ID",
        "印度尼西亚",
        "Indonesia",
        "Asia/Jakarta",
        ID_SCOPE,
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Vietnam — official Government/Office of Government holiday notices
# ---------------------------------------------------------------------------

VN_2026_SCHEDULE = (
    "https://en.baochinhphu.vn/"
    "ministry-of-home-affairs-announces-2026-holiday-schedule-"
    "111251017163421877.htm"
)
VN_2026_NEW_YEAR = (
    "https://en.baochinhphu.vn/govt-approves-4-day-break-for-2026-new-year-"
    "holiday-111251225145321864.htm"
)
VN_2026_NEW_YEAR_SWAP = (
    "https://xaydungchinhsach.chinhphu.vn/"
    "cong-chuc-vien-chuc-nghi-tet-duong-lich-2026-lien-tuc-4-ngay-"
    "119251225092146478.htm"
)
VN_2026_TET_DETAIL = (
    "https://hatinh.gov.vn/vi/bai-viet/"
    "lich-nghi-tet-nguyen-dan-binh-ngo-2026-va-cac-chi-dao-to-chuc-"
    "vui-xuan-don-tet-072633939"
)
VN_2026_NATIONAL_DAY = (
    "https://en.baochinhphu.vn/"
    "public-employees-to-enjoy-five-day-break-for-national-day-holiday-"
    "111260728204115825.htm"
)
VN_2026_HUNG_KINGS = (
    "https://baochinhphu.vn/"
    "chinh-thuc-bo-noi-vu-ra-thong-bao-lich-nghi-gio-to-hung-vuong-"
    "le-30-4-1-5-102260410213402453.htm"
)
VN_2026_CULTURE_DAY = (
    "https://en.baochinhphu.vn/"
    "november-24-recognized-as-viet-nams-public-holiday-"
    "111260424130923489.htm"
)
VN_2027_SCHEDULE = (
    "https://en.baochinhphu.vn/"
    "viet-nam-announces-2027-public-holiday-schedule-"
    "111261012155048477.htm"
)
VN_2027_POLICY = (
    "https://xaydungchinhsach.chinhphu.vn/"
    "de-xuat-2-phuong-an-nghi-tet-nguyen-dan-2027-tet-dinh-mui-"
    "11926080513033257.htm"
)

VN_SCOPE = "越南全国法定公共假日；政府机关调休日另列"
VN_PUBLIC = "越南（全国法定假日）"
VN_GOVERNMENT = "越南（政府机关调休）"

VN_2026_PUBLIC = [
    (
        1,
        1,
        "元旦（Tết Dương lịch）",
        "New Year's Day",
        "法定 1 天；政府机关连休 1/1–1/4（1/2 为调休，补班 1/10）。",
    ),
    (
        2,
        16,
        "春节（Tết Nguyên đán，除夕）",
        "Tet Nguyen Dan (Lunar New Year's Eve)",
        "法定春节 5 天（2/16–2/20）的第 1 天；政府机关连休 2/14–2/22。",
    ),
    (
        2,
        17,
        "春节（Tết Nguyên đán，正月初一）",
        "Tet Nguyen Dan (Lunar New Year, Day 1)",
        "法定春节 5 天的第 2 天。",
    ),
    (
        2,
        18,
        "春节（Tết Nguyên đán，正月初二）",
        "Tet Nguyen Dan (Lunar New Year, Day 2)",
        "法定春节 5 天的第 3 天。",
    ),
    (
        2,
        19,
        "春节（Tết Nguyên đán，正月初三）",
        "Tet Nguyen Dan (Lunar New Year, Day 3)",
        "法定春节 5 天的第 4 天。",
    ),
    (
        2,
        20,
        "春节（Tết Nguyên đán，正月初四）",
        "Tet Nguyen Dan (Lunar New Year, Day 4)",
        "法定春节 5 天的第 5 天。",
    ),
    (
        4,
        26,
        "雄王纪念日（Giỗ Tổ Hùng Vương）",
        "Hung Kings Commemoration Day",
        "农历三月初十，适逢星期日；政府通知未另列补假日，依《劳动法》2019 员工享有补偿休假权利。",
    ),
    (
        4,
        30,
        "南方解放日（Ngày Giải phóng miền Nam）",
        "Reunification Day",
        None,
    ),
    (
        5,
        1,
        "国际劳动节（Ngày Quốc tế Lao động）",
        "International Labour Day",
        None,
    ),
    (
        9,
        1,
        "国庆日第 1 天（Quốc khánh）",
        "National Day (Day 1)",
        "法定国庆 2 天（9/1–9/2）；政府机关连休 8/29–9/2。",
    ),
    (
        9,
        2,
        "国庆日第 2 天（Quốc khánh）",
        "National Day (Day 2)",
        "法定国庆 2 天的第 2 天。",
    ),
    (
        11,
        24,
        "越南文化日（Ngày Văn hóa Việt Nam）",
        "Vietnam Culture Day",
        "依国会第 28/2026/QH16 号决议列为带薪公共假日；2026 年为星期二，法定 1 天。",
    ),
]

VN_2026_GOVERNMENT = [
    (
        1,
        2,
        "元旦调休（政府机关）",
        "New Year holiday swap day (public employees)",
        "政府机关 1/1–1/4 连休中的调休日；补班 1/10（星期六）。私营部门仅 1/1 为法定假日。",
    ),
    (
        8,
        31,
        "国庆调休（政府机关）",
        "National Day swap day (public employees)",
        "政府机关 8/29–9/2 连休中的调休日；补班 8/22（星期六）。",
    ),
]

VN_2027_PUBLIC = [
    (
        1,
        1,
        "元旦（Tết Dương lịch）",
        "New Year's Day",
        "政府机关连休 1/1–1/3（1/2–1/3 为周末）。",
    ),
    (
        2,
        4,
        "春节（Tết Nguyên đán，春节前第 2 天）",
        "Tet Nguyen Dan (2 days before Tet)",
        "2027 年法定春节 5 天（2/4–2/8）的第 1 天；政府机关连休 2/4–2/10。",
    ),
    (
        2,
        5,
        "春节（Tết Nguyên đán，春节前第 1 天）",
        "Tet Nguyen Dan (1 day before Tet)",
        "法定春节 5 天的第 2 天。",
    ),
    (
        2,
        6,
        "春节（Tết Nguyên đán，正月初一）",
        "Tet Nguyen Dan (Lunar New Year, Day 1)",
        "法定春节 5 天的第 3 天。",
    ),
    (
        2,
        7,
        "春节（Tết Nguyên đán，正月初二）",
        "Tet Nguyen Dan (Lunar New Year, Day 2)",
        "法定春节 5 天的第 4 天。",
    ),
    (
        2,
        8,
        "春节（Tết Nguyên đán，正月初三）",
        "Tet Nguyen Dan (Lunar New Year, Day 3)",
        "法定春节 5 天的第 5 天。",
    ),
    (
        4,
        16,
        "雄王纪念日（Giỗ Tổ Hùng Vương）",
        "Hung Kings Commemoration Day",
        "农历三月初十；政府机关连休 4/16–4/18。",
    ),
    (
        4,
        30,
        "南方解放日（Ngày Giải phóng miền Nam）",
        "Reunification Day",
        None,
    ),
    (
        5,
        1,
        "国际劳动节（Ngày Quốc tế Lao động）",
        "International Labour Day",
        None,
    ),
    (
        9,
        2,
        "国庆日第 1 天（Quốc khánh）",
        "National Day (Day 1)",
        "法定国庆 2 天（9/2–9/3）；政府机关连休 9/2–9/5。",
    ),
    (
        9,
        3,
        "国庆日第 2 天（Quốc khánh）",
        "National Day (Day 2)",
        "2027 年法定国庆第 2 天；私营部门可选择 9/1 或 9/3。",
    ),
    (
        11,
        24,
        "越南文化日（Ngày Văn hóa Việt Nam）",
        "Vietnam Culture Day",
        "法定带薪公共假日 1 天。",
    ),
]

VN_2027_GOVERNMENT = [
    (
        2,
        9,
        "春节补偿假（政府机关）",
        "Tet compensatory day (public employees)",
        "因 2/6–2/7 周休与春节重叠，政府机关按官方安排于 2/9–2/10 补休。",
    ),
    (
        2,
        10,
        "春节补偿假（政府机关）",
        "Tet compensatory day (public employees)",
        "官方 2/4–2/10 连休中的第 2 个补偿日。",
    ),
    (
        5,
        3,
        "劳动节补偿假（政府机关）",
        "Labour Day compensatory day (public employees)",
        "因 5/1 适逢星期六，政府机关按官方安排于 5/3 补休。",
    ),
]


def _vn_region() -> dict:
    by_year = _empty_by_year()
    for year, days, source_url in (
        (2026, VN_2026_PUBLIC, VN_2026_SCHEDULE),
        (2027, VN_2027_PUBLIC, VN_2027_SCHEDULE),
    ):
        _add_days(by_year, year, days, VN_PUBLIC, "public", source_url)

    # Point the 2026 events at the notice that establishes each date.
    source_by_date_2026 = {
        "2026-01-01": VN_2026_NEW_YEAR,
        "2026-02-16": VN_2026_TET_DETAIL,
        "2026-02-17": VN_2026_TET_DETAIL,
        "2026-02-18": VN_2026_TET_DETAIL,
        "2026-02-19": VN_2026_TET_DETAIL,
        "2026-02-20": VN_2026_TET_DETAIL,
        "2026-04-26": VN_2026_HUNG_KINGS,
        "2026-04-30": VN_2026_HUNG_KINGS,
        "2026-05-01": VN_2026_HUNG_KINGS,
        "2026-09-01": VN_2026_NATIONAL_DAY,
        "2026-09-02": VN_2026_NATIONAL_DAY,
        "2026-11-24": VN_2026_CULTURE_DAY,
    }
    for event in by_year[2026]:
        event["source_url"] = source_by_date_2026.get(
            event["date"], event["source_url"]
        )
    _add_days(
        by_year,
        2026,
        VN_2026_GOVERNMENT,
        VN_GOVERNMENT,
        "government",
        VN_2026_NEW_YEAR,
    )
    for event in by_year[2026]:
        if event["date"] == "2026-01-02":
            event["source_url"] = VN_2026_NEW_YEAR_SWAP
        elif event["date"] == "2026-08-31":
            event["source_url"] = VN_2026_NATIONAL_DAY

    # The 2027 statutory dates come from the Ministry of Home Affairs notice;
    # the 2027 schedule article establishes Hung Kings and Culture Day.
    source_by_date_2027 = {
        "2027-02-04": VN_2027_POLICY,
        "2027-02-05": VN_2027_POLICY,
        "2027-02-06": VN_2027_POLICY,
        "2027-02-07": VN_2027_POLICY,
        "2027-02-08": VN_2027_POLICY,
        "2027-09-02": VN_2027_POLICY,
        "2027-09-03": VN_2027_POLICY,
    }
    for event in by_year[2027]:
        event["source_url"] = source_by_date_2027.get(
            event["date"], event["source_url"]
        )
    _add_days(
        by_year,
        2027,
        VN_2027_GOVERNMENT,
        VN_GOVERNMENT,
        "government",
        VN_2027_POLICY,
    )
    for event in by_year[2027]:
        if event["date"] == "2027-05-03":
            event["source_url"] = VN_2027_SCHEDULE

    selected = _select_years(by_year, {2026, 2027}, {2026: 14, 2027: 15})
    sources = [
        {
            "name": "越南政府门户 — 内务部公布 2026 年公共假期安排（2025-10-17）",
            "url": VN_2026_SCHEDULE,
            "format": "HTML",
        },
        {
            "name": "越南政府门户 — 政府批准 2026 年元旦连休 4 天（2025-12-25）",
            "url": VN_2026_NEW_YEAR,
            "format": "HTML",
        },
        {
            "name": "越南政府政策门户 — 2026 年元旦调休安排（2025-12-25）",
            "url": VN_2026_NEW_YEAR_SWAP,
            "format": "HTML",
        },
        {
            "name": "河静省政府门户 — 2026 年丙午春节及全年假期通知",
            "url": VN_2026_TET_DETAIL,
            "format": "HTML",
        },
        {
            "name": "越南政府门户 — 2026 年国庆连休 5 天（2026-07-28）",
            "url": VN_2026_NATIONAL_DAY,
            "format": "HTML",
        },
        {
            "name": "越南政府门户 — 雄王纪念日及 4/30–5/1 假期通知（2026-04-10）",
            "url": VN_2026_HUNG_KINGS,
            "format": "HTML",
        },
        {
            "name": "越南政府门户 — 国会将 11 月 24 日列为公共假日（2026-04-24）",
            "url": VN_2026_CULTURE_DAY,
            "format": "HTML",
        },
        {
            "name": "越南政府门户 — 2027 年公共假期安排（2026-10-12）",
            "url": VN_2027_SCHEDULE,
            "format": "HTML",
        },
        {
            "name": "越南政府政策门户 — 内务部第 11483/TB-BNV 号通知的 2027 年春节及国庆方案报道（2026-11-05）",
            "url": VN_2027_POLICY,
            "format": "HTML",
        },
    ]
    notes = [
        "越南法定公共假日适用于所有雇主；kind=government 的调休/补偿日是全国政府机关及公立单位的统一安排，私营部门可自行协商，但须至少提前 30 天通知员工。",
        "2026 年春节：政府机关连休 2/14–2/22（含周末），法定 5 天为 2/16–2/20（春节前 1 天、春节后 4 天）。",
        "2027 年春节：政府机关连休 2/4–2/10，法定 5 天为 2/4–2/8（春节前 2 天、春节后 3 天），2/9–2/10 为周休重叠产生的补偿日。",
        "2026 年国庆：政府机关连休 8/29–9/2，法定 2 天为 9/1–9/2；8/31 为调休，补班 8/22。2027 年国庆：政府机关连休 9/2–9/5，法定 2 天为 9/2–9/3。",
        "2026 年元旦：政府机关连休 1/1–1/4，1/2 为调休，补班 1/10；2027 年元旦政府机关连休 1/1–1/3，其中 1/2–1/3 为周末。",
        "2026 年雄王纪念日为 4/26（星期日）；官方通知未另列补假日，本表不自行推算；依《劳动法》2019，员工享有补偿休假的法定权利。",
        "越南文化日 11/24 依国会第 28/2026/QH16 号决议成为带薪公共假日；2026 年为星期二，法定 1 天。",
        "官方公告的规范化快照，最近人工核对日期：2026-11-06。后续修订需重新核对，不是实时接口；越南政府及官方政策门户的原始链接保留供查核。",
    ]
    return _make_region(
        "VN",
        "越南",
        "Vietnam",
        "Asia/Ho_Chi_Minh",
        VN_SCOPE,
        sources,
        selected,
        notes,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def fetch() -> list[dict]:
    """Return the five ASEAN regions with official 2026 and 2027 holidays."""

    return [
        _my_region(),
        _my_kul_region(),
        _th_region(),
        _id_region(),
        _vn_region(),
    ]


__all__ = ["ProviderError", "fetch"]