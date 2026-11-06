"""Official public holidays for Turkey, Vanuatu, UAE, India, Australia, Cyprus.

The official schedules for these jurisdictions are published as PDF or HTML
notices, several of which block automated access and none of which expose a
stable machine-readable endpoint.  This provider therefore contains a checked-in
normalization of the official publications.  Every date is copied from the
cited government or central-bank source; no lunar or religious date is
calculated here.  When a jurisdiction publishes a new year, its snapshot must be
updated from the official notice and the region's ``years`` list expanded.

Only 2026 is required.  2027 is included where the official publication already
exists (Turkey, India, Australia, Cyprus).  Vanuatu and the UAE have not
published 2027 dates, so those regions contain 2026 only.
"""

from __future__ import annotations

from datetime import date

ALLOWED_KINDS = {"public", "bank", "government", "optional"}
SNAPSHOT_NOTE = (
    "最近人工核对日期：2026-11-06；非实时接口，后续修订需重新核对。"
)


class ProviderError(RuntimeError):
    """Raised when the normalized data is internally inconsistent."""


def _event(
    day: str,
    name: str,
    scope: str,
    kind: str,
    source_url: str,
    name_en: str | None = None,
    note: str | None = None,
) -> dict:
    event = {
        "date": day,
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


def _region(
    region_id: str,
    name: str,
    name_en: str,
    timezone: str,
    scope: str,
    years: list[int],
    sources: list[dict],
    events: list[dict],
    notes: list[str],
) -> dict:
    years = sorted(years)
    source_urls = {source["url"] for source in sources}
    seen: set[tuple[str, str, str]] = set()

    for event in events:
        for field in ("date", "name", "scope", "kind", "source_url"):
            if not event.get(field):
                raise ProviderError(f"{region_id}: event missing {field}: {event!r}")
        try:
            day = date.fromisoformat(event["date"])
        except (TypeError, ValueError) as exc:
            raise ProviderError(f"{region_id}: bad event date: {event!r}") from exc
        if day.year not in years:
            raise ProviderError(f"{region_id}: event year not declared: {event!r}")
        if event["kind"] not in ALLOWED_KINDS:
            raise ProviderError(f"{region_id}: bad kind: {event!r}")
        if event["source_url"] not in source_urls:
            raise ProviderError(
                f"{region_id}: event source not declared: {event['source_url']}"
            )
        key = (event["date"], event["name"], event["scope"])
        if key in seen:
            raise ProviderError(f"{region_id}: duplicate event: {key!r}")
        seen.add(key)

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
        "notes": [*notes, SNAPSHOT_NOTE],
    }


# ---------------------------------------------------------------------------
# Turkey — Law No. 2429 and Diyanet religious-day calendars
# ---------------------------------------------------------------------------

TR_LAW = "https://www.mevzuat.gov.tr/MevzuatMetin/1.5.2429.pdf"
TR_DIYANET_2026 = "https://vakithesaplama.diyanet.gov.tr/dinigunler.php?yil=2026"
TR_DIYANET_2027 = "https://vakithesaplama.diyanet.gov.tr/icerik.php?icerik=154"
TR_SCOPE = "Nationwide (Law No. 2429)"


def _tr_region() -> dict:
    sources = [
        {
            "name": "Law No. 2429 on National Holidays and General Holidays (official text)",
            "url": TR_LAW,
            "format": "PDF",
        },
        {
            "name": "Diyanet İşleri Başkanlığı — 2026 religious days",
            "url": TR_DIYANET_2026,
            "format": "HTML",
        },
        {
            "name": "Diyanet İşleri Başkanlığı — 2027 religious days",
            "url": TR_DIYANET_2027,
            "format": "HTML",
        },
    ]

    events = [
        _event("2026-01-01", "Yılbaşı", "Türkiye", "public", TR_LAW, "New Year's Day"),
        _event(
            "2026-03-19",
            "Ramazan Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Ramadan Bayram Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2026-03-20",
            "Ramazan Bayramı 1. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Ramadan Bayram, Day 1",
        ),
        _event(
            "2026-03-21",
            "Ramazan Bayramı 2. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Ramadan Bayram, Day 2",
        ),
        _event(
            "2026-03-22",
            "Ramazan Bayramı 3. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Ramadan Bayram, Day 3",
        ),
        _event(
            "2026-04-23",
            "Ulusal Egemenlik ve Çocuk Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "National Sovereignty and Children's Day",
        ),
        _event(
            "2026-05-01",
            "Emek ve Dayanışma Günü",
            "Türkiye",
            "public",
            TR_LAW,
            "Labour and Solidarity Day",
        ),
        _event(
            "2026-05-19",
            "Atatürk'ü Anma, Gençlik ve Spor Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "Commemoration of Atatürk, Youth and Sports Day",
        ),
        _event(
            "2026-05-26",
            "Kurban Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Sacrifice Bayram Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2026-05-27",
            "Kurban Bayramı 1. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Sacrifice Bayram, Day 1",
        ),
        _event(
            "2026-05-28",
            "Kurban Bayramı 2. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Sacrifice Bayram, Day 2",
        ),
        _event(
            "2026-05-29",
            "Kurban Bayramı 3. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Sacrifice Bayram, Day 3",
        ),
        _event(
            "2026-05-30",
            "Kurban Bayramı 4. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2026,
            "Sacrifice Bayram, Day 4",
        ),
        _event(
            "2026-07-15",
            "Demokrasi ve Millî Birlik Günü",
            "Türkiye",
            "public",
            TR_LAW,
            "Democracy and National Unity Day",
        ),
        _event(
            "2026-08-30",
            "Zafer Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "Victory Day",
        ),
        _event(
            "2026-10-28",
            "Cumhuriyet Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_LAW,
            "Republic Day Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2026-10-29",
            "Cumhuriyet Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "Republic Day",
        ),
        _event("2027-01-01", "Yılbaşı", "Türkiye", "public", TR_LAW, "New Year's Day"),
        _event(
            "2027-03-08",
            "Ramazan Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Ramadan Bayram Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2027-03-09",
            "Ramazan Bayramı 1. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Ramadan Bayram, Day 1",
        ),
        _event(
            "2027-03-10",
            "Ramazan Bayramı 2. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Ramadan Bayram, Day 2",
        ),
        _event(
            "2027-03-11",
            "Ramazan Bayramı 3. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Ramadan Bayram, Day 3",
        ),
        _event(
            "2027-04-23",
            "Ulusal Egemenlik ve Çocuk Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "National Sovereignty and Children's Day",
        ),
        _event(
            "2027-05-01",
            "Emek ve Dayanışma Günü",
            "Türkiye",
            "public",
            TR_LAW,
            "Labour and Solidarity Day",
            "Falls on Saturday; no substitute holiday is granted.",
        ),
        _event(
            "2027-05-15",
            "Kurban Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Sacrifice Bayram Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2027-05-16",
            "Kurban Bayramı 1. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Sacrifice Bayram, Day 1",
        ),
        _event(
            "2027-05-17",
            "Kurban Bayramı 2. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Sacrifice Bayram, Day 2",
        ),
        _event(
            "2027-05-18",
            "Kurban Bayramı 3. Gün",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Sacrifice Bayram, Day 3",
        ),
        _event(
            "2027-05-19",
            "Kurban Bayramı 4. Gün / Atatürk'ü Anma, Gençlik ve Spor Bayramı",
            "Türkiye",
            "public",
            TR_DIYANET_2027,
            "Sacrifice Bayram Day 4 / Commemoration of Atatürk, Youth and Sports Day",
            "Both official holidays fall on 19 May 2027; Law No. 2429 provides no substitute holiday.",
        ),
        _event(
            "2027-07-15",
            "Demokrasi ve Millî Birlik Günü",
            "Türkiye",
            "public",
            TR_LAW,
            "Democracy and National Unity Day",
        ),
        _event(
            "2027-08-30",
            "Zafer Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "Victory Day",
        ),
        _event(
            "2027-10-28",
            "Cumhuriyet Bayramı Arifesi",
            "Türkiye",
            "public",
            TR_LAW,
            "Republic Day Eve",
            "Half-day holiday from 13:00 under Law No. 2429.",
        ),
        _event(
            "2027-10-29",
            "Cumhuriyet Bayramı",
            "Türkiye",
            "public",
            TR_LAW,
            "Republic Day",
        ),
    ]

    notes = [
        "Fixed-date holidays are taken from Law No. 2429; 2026 and 2027 Ramadan and Sacrifice Bayram dates are taken from the Presidency of Religious Affairs (Diyanet) official calendars.",
        "Ramazan Bayramı is three days and Kurban Bayramı is four days; their eves are half-day holidays from 13:00 under Law No. 2429.",
        "No substitute holiday is granted when a holiday falls on a weekend or on another holiday; this follows from the absence of a substitute-day rule in Law No. 2429.",
        "1 May 2027 falls on Saturday, and 19 May 2027 is both the fourth day of Kurban Bayramı and Atatürk'ü Anma, Gençlik ve Spor Bayramı; the latter is represented as one combined event.",
    ]

    return _region(
        "TR",
        "土耳其",
        "Türkiye",
        "Europe/Istanbul",
        TR_SCOPE,
        [2026, 2027],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# Vanuatu — Prime Minister's Office public-holiday notice
# ---------------------------------------------------------------------------

VU_2026 = (
    "https://pmo.gov.vu/images/Public_Holidays/Public%20Holidays%202026.pdf"
)
VU_SCOPE = "National (Public Holidays Act)"


def _vu_region() -> dict:
    sources = [
        {
            "name": "Prime Minister's Office — Public Holidays 2026 notice",
            "url": VU_2026,
            "format": "PDF",
        },
    ]

    holidays = [
        ("2026-01-01", "New Year's Day"),
        ("2026-02-21", "Father Lini Day"),
        ("2026-03-05", "Custom Chiefs' Day"),
        ("2026-04-03", "Good Friday"),
        ("2026-04-06", "Easter Monday"),
        ("2026-05-01", "Labour Day"),
        ("2026-05-14", "Ascension Day"),
        ("2026-07-24", "Children's Day"),
        ("2026-07-30", "Independence Day"),
        ("2026-08-15", "Assumption Day"),
        ("2026-10-05", "Constitution Day"),
        ("2026-11-29", "National Unity Day"),
        ("2026-12-25", "Christmas Day"),
        ("2026-12-26", "Family Day"),
    ]
    events = [
        _event(day, name, "Vanuatu", "public", VU_2026)
        for day, name in holidays
    ]

    notes = [
        "Only 2026 is represented: the Prime Minister's Office had not published an official 2027 public-holiday notice as of 6 November 2026.",
        "Dates are transcribed from the official PMO 2026 notice; no substitute holidays are inferred.",
        "The PMO notice is a scanned one-page PDF; its dates are transcribed directly.",
    ]

    return _region(
        "VU",
        "瓦努阿图",
        "Vanuatu",
        "Pacific/Efate",
        VU_SCOPE,
        [2026],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# United Arab Emirates — Cabinet Resolution No. 27/2024 and 2026 announcements
# ---------------------------------------------------------------------------

AE_UAE = (
    "https://u.ae/en/information-and-services/public-holidays-and-religious-affairs/"
    "public-holidays"
)
AE_FAHR_EID_FITR = (
    "https://www.fahr.gov.ae/en/news/"
    "eid-al-fitr-holiday-in-the-federal-government-from-19-to-22-march-2026/"
)
AE_FAHR_EID_ADHA = (
    "https://www.fahr.gov.ae/en/news/"
    "the-federal-authority-for-human-resources-announces-the-eid-al-adha-holiday-"
    "for-the-federal-government-from-may-25-29-2026/"
)
AE_FAHR_MAWLID = (
    "https://www.fahr.gov.ae/wp-content/uploads/2026/08/"
    "Circular-No.-11-of-2026-Regarding-The-Holiday-of-the-Prophet-Mohammads-"
    "Birthday-1448-AH.pdf"
)
AE_CMA_HIJRI = (
    "https://www.uaecma.gov.ae/en/media-center/news/12/6/2026/"
    "%D8%B9%D8%B7%D9%84%D8%A9-%D8%B1%D8%A3%D8%B3-%D8%A7%D9%84%D8%B3%D9%86%D8%A9-"
    "%D8%A7%D9%84%D9%87%D8%AC%D8%B1%D9%8A%D8%A9"
)
AE_SCOPE = (
    "Public and private sectors (Cabinet Resolution No. 27/2024; "
    "sector-specific 2026 announcements noted)"
)


def _ae_region() -> dict:
    sources = [
        {
            "name": "UAE Government Portal — Public holidays (Cabinet Resolution No. 27/2024)",
            "url": AE_UAE,
            "format": "HTML",
        },
        {
            "name": "FAHR — Eid Al Fitr holiday in the federal government, 19–22 March 2026",
            "url": AE_FAHR_EID_FITR,
            "format": "HTML",
        },
        {
            "name": "FAHR — Arafat Day and Eid Al Adha holiday in the federal government, 25–29 May 2026",
            "url": AE_FAHR_EID_ADHA,
            "format": "HTML",
        },
        {
            "name": "FAHR Circular No. 11 of 2026 — Prophet Mohammed's Birthday 1448 AH",
            "url": AE_FAHR_MAWLID,
            "format": "PDF",
        },
        {
            "name": "UAE Capital Market Authority — Hijri New Year 1448 market closure",
            "url": AE_CMA_HIJRI,
            "format": "HTML",
        },
    ]

    events = [
        _event(
            "2026-01-01",
            "Gregorian New Year",
            "UAE public and private sectors",
            "public",
            AE_UAE,
        ),
        _event(
            "2026-03-19",
            "Eid Al Fitr holiday — 30 Ramadan",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_FITR,
            note=(
                "The 30th day of Ramadan was an official holiday because Ramadan "
                "lasted 30 days; the private-sector conditional day was confirmed."
            ),
        ),
        _event(
            "2026-03-20",
            "Eid Al Fitr — 1 Shawwal",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_FITR,
        ),
        _event(
            "2026-03-21",
            "Eid Al Fitr — 2 Shawwal",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_FITR,
        ),
        _event(
            "2026-03-22",
            "Eid Al Fitr — 3 Shawwal",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_FITR,
        ),
        _event(
            "2026-05-25",
            "Eid Al Adha holiday — federal government",
            "UAE federal government",
            "government",
            AE_FAHR_EID_ADHA,
            note=(
                "Federal holiday window 25–29 May 2026; the private-sector "
                "holiday begins on 26 May."
            ),
        ),
        _event(
            "2026-05-26",
            "Arafah Day",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_ADHA,
            note="9 Dhul Hijjah; the private-sector holiday runs 26–29 May 2026.",
        ),
        _event(
            "2026-05-27",
            "Eid Al Adha — 10 Dhul Hijjah",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_ADHA,
        ),
        _event(
            "2026-05-28",
            "Eid Al Adha — 11 Dhul Hijjah",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_ADHA,
        ),
        _event(
            "2026-05-29",
            "Eid Al Adha — 12 Dhul Hijjah",
            "UAE public and private sectors",
            "public",
            AE_FAHR_EID_ADHA,
        ),
        _event(
            "2026-06-15",
            "Hijri New Year holiday (1448 AH)",
            "UAE public and private sectors",
            "public",
            AE_CMA_HIJRI,
            note=(
                "FAHR and MoHRE announced 15 June 2026 as the holiday for the "
                "federal government and private sector; the CMA closed financial "
                "markets that day. The UAE Fatwa Council separately declared "
                "1 Muharram on 16 June 2026, so the religious date and the "
                "public-holiday date differ in official announcements."
            ),
        ),
        _event(
            "2026-08-28",
            "Prophet Mohammed's Birthday — 12 Rabi' Awwal 1448",
            "UAE public and private sectors",
            "public",
            AE_FAHR_MAWLID,
        ),
        _event(
            "2026-12-02",
            "UAE National Day — Day 1",
            "UAE public and private sectors",
            "public",
            AE_UAE,
        ),
        _event(
            "2026-12-03",
            "UAE National Day — Day 2",
            "UAE public and private sectors",
            "public",
            AE_UAE,
        ),
    ]

    notes = [
        "Only 2026 is represented: no official 2027 holiday dates had been published as of 6 November 2026; the u.ae list gives categories, not Gregorian dates.",
        "Islamic holidays are subject to moon sighting. The dates shown are the officially announced 2026 dates; this provider does not calculate them.",
        "Eid Al Fitr: federal government 19–22 March 2026 (30 Ramadan and 1–3 Shawwal); private sector 19–21 March plus 22 March when Ramadan lasts 30 days, which occurred in 2026.",
        "Eid Al Adha: federal government 25–29 May 2026; private sector 26–29 May 2026.",
        "Hijri New Year: the federal and private-sector holiday was 15 June 2026; the UAE Fatwa Council separately declared 1 Muharram on 16 June 2026.",
        "Cabinet Resolution No. 27/2024 does not allow a public holiday to be moved when it coincides with a weekend or another public holiday.",
        "Commemoration Day (30 November) is not listed as a public holiday in Cabinet Resolution No. 27/2024 and is not included.",
    ]

    return _region(
        "AE",
        "阿联酋",
        "United Arab Emirates",
        "Asia/Dubai",
        AE_SCOPE,
        [2026],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# India — DoPT gazetted holiday lists
# ---------------------------------------------------------------------------

IN_2026 = (
    "https://rb.indianrailways.gov.in/uploads/directorate/establishment/2025/"
    "Letter_20250805_HolidaysList2026.pdf"
)
IN_2027 = (
    "https://rb.indianrailways.gov.in/uploads/directorate/establishment/E(LR)/"
    "Letter_20260723_HolidaysList2027.pdf"
)
IN_BAKRID_2026 = (
    "https://rb.indianrailways.gov.in/uploads/directorate/establishment/E(LR)/"
    "Letter_20260522%20to%20All%20IR%20-%20Change%20in%20the%20date%20of%20Id-ul-Zuha(Bakrid).pdf"
)
IN_AMBEDKAR_2026 = (
    "https://rb.indianrailways.gov.in/uploads/directorate/establishment/E(LR)/"
    "Letter_20260409%20to%20All%20IR%20-%20HL%20on%2020260414%20birthday%20of%20Dr_%20BR%20Ambedkar.pdf"
)
IN_SCOPE = (
    "Central government offices in Delhi/New Delhi (DoPT annual lists and subsequent "
    "orders; restricted and state/local holidays excluded)"
)


def _in_region() -> dict:
    sources = [
        {
            "name": (
                "DoPT OM No. 12/2/2023-JCA dated 03.07.2025 — Annexure-I "
                "(Railway Board official copy)"
            ),
            "url": IN_2026,
            "format": "PDF",
        },
        {
            "name": (
                "DoPT OM No. 12/2/2023-JCA dated 16.07.2026 — Annexure-I "
                "(Railway Board official copy)"
            ),
            "url": IN_2027,
            "format": "PDF",
        },
        {
            "name": "DoPT OM dated 22.05.2026 — revised Bakrid date (Railway Board official copy)",
            "url": IN_BAKRID_2026,
            "format": "PDF",
        },
        {
            "name": "DoPT OM dated 09.04.2026 — Dr. B. R. Ambedkar's birthday holiday (Railway Board official copy)",
            "url": IN_AMBEDKAR_2026,
            "format": "PDF",
        },
    ]

    muslim_note = (
        "Date subject to official moon-sighting change under DoPT OM paras 5.1/5.2."
    )
    events = [
        _event("2026-01-26", "Republic Day", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event("2026-03-04", "Holi", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event(
            "2026-03-21",
            "Id-ul-Fitr",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
            note=muslim_note,
        ),
        _event("2026-03-26", "Ram Navami", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event("2026-03-31", "Mahavir Jayanti", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event("2026-04-03", "Good Friday", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event(
            "2026-04-14",
            "Birthday of Dr. B. R. Ambedkar",
            "Central government offices throughout India (Delhi/New Delhi included)",
            "government",
            IN_AMBEDKAR_2026,
            note="Additional holiday declared by DoPT OM dated 09.04.2026.",
        ),
        _event("2026-05-01", "Buddha Purnima", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event(
            "2026-05-28",
            "Id-ul-Zuha (Bakrid)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_BAKRID_2026,
            note="DoPT OM dated 22.05.2026 moved the Delhi/New Delhi holiday from 27 May to 28 May 2026.",
        ),
        _event(
            "2026-06-26",
            "Muharram",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
            note=muslim_note,
        ),
        _event("2026-08-15", "Independence Day", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event(
            "2026-08-26",
            "Milad-un-Nabi (Id-e-Milad)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
            note=muslim_note,
        ),
        _event("2026-09-04", "Janmashtami", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event(
            "2026-10-02",
            "Mahatma Gandhi's Birthday",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
        ),
        _event(
            "2026-10-20",
            "Dussehra (Vijaya Dashmi)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
        ),
        _event(
            "2026-11-08",
            "Diwali (Deepavali)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
        ),
        _event(
            "2026-11-24",
            "Guru Nanak's Birthday",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2026,
        ),
        _event("2026-12-25", "Christmas Day", "Central government offices (Delhi/New Delhi)", "government", IN_2026),
        _event("2027-01-26", "Republic Day", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event(
            "2027-03-10",
            "Id-ul-Fitr",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
            note=muslim_note,
        ),
        _event("2027-03-23", "Holi", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event("2027-03-26", "Good Friday", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event("2027-04-15", "Ram Navami", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event("2027-04-19", "Mahavir Jayanti", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event(
            "2027-05-17",
            "Id-ul-Zuha (Bakrid)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
            note=muslim_note,
        ),
        _event("2027-05-20", "Buddha Purnima", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event(
            "2027-06-16",
            "Muharram",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
            note=muslim_note,
        ),
        _event(
            "2027-08-15",
            "Independence Day / Milad-un-Nabi (Id-e-Milad)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
            note=(
                "Both gazetted holidays fall on 15 August 2027; the DoPT OM lists "
                "both and provides no substitute holiday."
            ),
        ),
        _event("2027-08-25", "Janmashtami", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
        _event(
            "2027-10-02",
            "Mahatma Gandhi's Birthday",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
        ),
        _event(
            "2027-10-09",
            "Dussehra (Vijaya Dashmi)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
        ),
        _event(
            "2027-10-29",
            "Diwali (Deepavali)",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
            note="The DoPT OM para 6 confirms Diwali on Friday 29 October 2027 (Kartika 7).",
        ),
        _event(
            "2027-11-14",
            "Guru Nanak's Birthday",
            "Central government offices (Delhi/New Delhi)",
            "government",
            IN_2027,
        ),
        _event("2027-12-25", "Christmas Day", "Central government offices (Delhi/New Delhi)", "government", IN_2027),
    ]

    notes = [
        "2026 and 2027 Annexure-I each list 17 gazetted holidays for Central Government offices at Delhi/New Delhi; the 2027 OM is dated 16.07.2026.",
        "Outside Delhi/New Delhi, 14 holidays are compulsory and three further holidays are chosen from 12 optional holidays by the Central Government Employees Welfare Coordination Committee in each State capital; state governments and private employers publish separate lists.",
        "Includes Annexure-I gazetted holidays and subsequent DoPT orders; Annexure-II restricted holidays are optional and excluded.",
        "Islamic holiday dates (Id-ul-Fitr, Id-ul-Zuha, Muharram and Milad-un-Nabi) may be changed by official moon-sighting announcements under OM paras 5.1/5.2.",
        "No substitute holiday is allowed when a holiday falls on a weekend or another holiday (OM para 3.2).",
        "In 2027, Independence Day and Milad-un-Nabi both fall on 15 August; the OM lists both and allows no substitute.",
        "The DoPT website copies were unavailable at the time of checking; all cited PDFs are official Railway Board copies of the DoPT Office Memoranda.",
        "The 22.05.2026 DoPT order supersedes the annual 2026 Bakrid date with 28 May; the 09.04.2026 order adds 14 April for Dr. B. R. Ambedkar's birthday.",
    ]

    return _region(
        "IN",
        "印度",
        "India",
        "Asia/Kolkata",
        IN_SCOPE,
        [2026, 2027],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# Australia — national-common subset of official state/territory calendars
# ---------------------------------------------------------------------------

AU_2026 = (
    "https://www.fairwork.gov.au/employment-conditions/public-holidays/"
    "2026-public-holidays"
)
AU_2027 = (
    "https://www.fairwork.gov.au/employment-conditions/public-holidays/"
    "2027-public-holidays"
)
AU_NSW = "https://www.nsw.gov.au/about-nsw/public-holidays"
AU_ACT_2027 = (
    "https://www.act.gov.au/__data/assets/pdf_file/0018/2327004/"
    "ACT-Public-Holidays-2027.pdf"
)
AU_WA = (
    "https://www.wa.gov.au/service/employment/workplace-arrangements/"
    "public-holidays-western-australia"
)
AU_VIC_2027 = (
    "https://business.vic.gov.au/business-information/public-holidays/"
    "victorian-public-holidays-2027"
)
AU_QLD = "https://www.qld.gov.au/recreation/travel/holidays/public"
AU_SA = "https://www.safework.sa.gov.au/resources/public-holidays"
AU_NT = "https://nt.gov.au/nt-public-holidays"
AU_TAS_ACT = (
    "https://www.legislation.tas.gov.au/view/html/authorised/"
    "2026-10-09%202026-10-14/act-2000-096"
)
AU_SCOPE = (
    "National common holidays plus explicitly scoped state exceptions; other "
    "state/territory holidays excluded"
)


def _au_region() -> dict:
    sources = [
        {
            "name": "Fair Work Ombudsman — 2026 public holidays",
            "url": AU_2026,
            "format": "HTML",
        },
        {
            "name": "Fair Work Ombudsman — 2027 public holidays",
            "url": AU_2027,
            "format": "HTML",
        },
        {
            "name": "NSW Government — Public holidays",
            "url": AU_NSW,
            "format": "HTML",
        },
        {
            "name": "ACT Government — Public Holidays 2027",
            "url": AU_ACT_2027,
            "format": "PDF",
        },
        {
            "name": "Western Australia — Public holidays",
            "url": AU_WA,
            "format": "HTML",
        },
        {
            "name": "Business Victoria — Victorian public holidays 2027",
            "url": AU_VIC_2027,
            "format": "HTML",
        },
        {
            "name": "Queensland Government — Public holidays",
            "url": AU_QLD,
            "format": "HTML",
        },
        {
            "name": "SafeWork SA — Public holidays",
            "url": AU_SA,
            "format": "HTML",
        },
        {
            "name": "Northern Territory Government — Public and regional holidays",
            "url": AU_NT,
            "format": "HTML",
        },
        {
            "name": "Tasmania — Statutory Holidays Act 2000 (current authorised version)",
            "url": AU_TAS_ACT,
            "format": "HTML",
        },
    ]

    events = [
        _event("2026-01-01", "New Year's Day", "All states and territories", "public", AU_2026),
        _event("2026-01-26", "Australia Day", "All states and territories", "public", AU_2026),
        _event("2026-04-03", "Good Friday", "All states and territories", "public", AU_2026),
        _event("2026-04-06", "Easter Monday", "All states and territories", "public", AU_2026),
        _event(
            "2026-04-25",
            "Anzac Day",
            "All states and territories",
            "public",
            AU_2026,
            note=(
                "Falls on Saturday. NSW, ACT and WA observe Monday 27 April "
                "as an additional public holiday; see the separate state-scoped "
                "event."
            ),
        ),
        _event(
            "2026-04-27",
            "Anzac Day (observed)",
            "NSW, ACT and WA",
            "public",
            AU_2026,
            note=(
                "State-specific additional holiday for Anzac Day falling on "
                "Saturday. Not observed in QLD, VIC, SA, TAS or NT."
            ),
        ),
        _event("2026-12-25", "Christmas Day", "All states and territories", "public", AU_2026),
        _event(
            "2026-12-26",
            "Boxing Day",
            "All states and territories except Tasmania",
            "public",
            AU_2026,
            note=(
                "South Australia calls 26 December Proclamation Day. Tasmania "
                "observes the Boxing Day holiday on Monday 28 December instead "
                "when 26 December falls on a Saturday."
            ),
        ),
        _event(
            "2026-12-28",
            "Additional public holiday",
            "All states and territories",
            "public",
            AU_2026,
            note="Additional day for Boxing Day in most states and territories; Tasmania observes its Boxing Day holiday on this date.",
        ),
        _event("2027-01-01", "New Year's Day", "All states and territories", "public", AU_2027),
        _event("2027-01-26", "Australia Day", "All states and territories", "public", AU_2027),
        _event("2027-03-26", "Good Friday", "All states and territories", "public", AU_2027),
        _event("2027-03-29", "Easter Monday", "All states and territories", "public", AU_2027),
        _event(
            "2027-04-25",
            "Anzac Day",
            "NSW, VIC, WA, SA, TAS and ACT",
            "public",
            AU_2027,
            note=(
                "Falls on Sunday. QLD and NT observe Monday 26 April only; "
                "NSW, ACT and WA observe both dates; VIC, SA and TAS observe "
                "25 April only."
            ),
        ),
        _event(
            "2027-04-26",
            "Anzac Day (observed)",
            "NSW, ACT, WA, QLD and NT",
            "public",
            AU_2027,
            note=(
                "State-specific substitute for Anzac Day falling on Sunday. "
                "Not a public holiday in Victoria, South Australia or Tasmania."
            ),
        ),
        _event("2027-12-25", "Christmas Day", "All states and territories", "public", AU_2027),
        _event(
            "2027-12-26",
            "Boxing Day",
            "All states and territories except Tasmania",
            "public",
            AU_2027,
            note=(
                "South Australia calls 26 December Proclamation Day. Tasmania "
                "observes the Boxing Day holiday on Tuesday 28 December instead "
                "when 26 December falls on a Sunday."
            ),
        ),
        _event(
            "2027-12-27",
            "Additional public holiday",
            "All states and territories",
            "public",
            AU_2027,
            note="Additional day for Christmas Day, which falls on Saturday.",
        ),
        _event(
            "2027-12-28",
            "Additional public holiday",
            "All states and territories",
            "public",
            AU_2027,
            note="Additional day for Boxing Day in most states and territories; Tasmania observes its Boxing Day holiday on this date.",
        ),
    ]

    notes = [
        "Australia has no single nationwide public-holiday statute; dates are set by state and territory. This region contains the common base plus explicitly state-scoped Anzac Day substitutes.",
        "King's Birthday, Labour Day, Easter Saturday/Sunday, show days, bank holidays and part-day Christmas Eve are state/territory-specific and excluded.",
        "The Fair Work Ombudsman pages were not reachable from the build environment; dates were cross-checked against official state/territory tables for NSW, ACT, WA, VIC, QLD, SA, NT and TAS.",
        "Some official state/territory pages block automated requests (HTTP 403); their published tables were transcribed and cross-checked against accessible official pages.",
        "Additional public holidays are included for 28 December 2026 and 27–28 December 2027, when Christmas Day and Boxing Day fall on weekends.",
        "Tasmania's Statutory Holidays Act 2000 moves Boxing Day to the following Monday or Tuesday when 26 December falls on a weekend, so 26 December is not a Tasmanian public holiday in 2026 or 2027; the 28 December event covers Tasmania's Boxing Day holiday.",
        "Anzac Day is national, but weekend substitutes vary. The 27 April 2026 substitute is included with scope limited to NSW, ACT and WA. The 26 April 2027 substitute is included with scope limited to NSW, ACT, WA, QLD and NT because QLD and NT observe it instead of 25 April; other state-specific substitutes are noted only.",
    ]

    return _region(
        "AU",
        "澳大利亚",
        "Australia",
        "Australia/Sydney",
        AU_SCOPE,
        [2026, 2027],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# Cyprus — Central Bank of Cyprus bank-holiday schedule
# ---------------------------------------------------------------------------

CY_PAGE = "https://www.centralbank.cy/en/the-bank/working-hours-bank-holidays"
CY_2026 = (
    "https://www.centralbank.cy/images/media/pdf/Bank-Holidays-%202026-ENG.pdf"
)
CY_2027 = (
    "https://www.centralbank.cy/images/media/pdf/Bank-Holidays-2027-English.pdf"
)
CY_SCOPE = (
    "Public sector and banks (Central Bank of Cyprus bank-holiday schedule); "
    "private-sector observance may differ"
)


def _cy_region() -> dict:
    sources = [
        {
            "name": "Central Bank of Cyprus — Working hours and bank holidays",
            "url": CY_PAGE,
            "format": "HTML",
        },
        {
            "name": "Central Bank of Cyprus — Bank holidays 2026",
            "url": CY_2026,
            "format": "PDF",
        },
        {
            "name": "Central Bank of Cyprus — Bank holidays 2027",
            "url": CY_2027,
            "format": "PDF",
        },
    ]

    events = [
        _event("2026-01-01", "New Year's Day", "Public sector and banks", "public", CY_2026),
        _event("2026-01-06", "Epiphany", "Public sector and banks", "public", CY_2026),
        _event("2026-02-23", "Green Monday", "Public sector and banks", "public", CY_2026),
        _event(
            "2026-03-25",
            "Greek Independence Day",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event(
            "2026-04-01",
            "Cyprus National Day",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event(
            "2026-04-10",
            "Good Friday (Orthodox)",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event(
            "2026-04-13",
            "Easter Monday",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event(
            "2026-04-14",
            "Easter Tuesday (bank holiday)",
            "Banks",
            "bank",
            CY_2026,
        ),
        _event("2026-05-01", "Labour Day", "Public sector and banks", "public", CY_2026),
        _event(
            "2026-06-01",
            "Pentecost (bank holiday)",
            "Banks",
            "bank",
            CY_2026,
        ),
        _event(
            "2026-08-15",
            "Assumption Day",
            "Public sector and banks",
            "public",
            CY_2026,
            note="Falls on Saturday; the CBC schedule notes it as a public holiday.",
        ),
        _event(
            "2026-10-01",
            "Cyprus Independence Day",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event(
            "2026-10-28",
            "Greek National Day (Ochi Day)",
            "Public sector and banks",
            "public",
            CY_2026,
        ),
        _event("2026-12-25", "Christmas Day", "Public sector and banks", "public", CY_2026),
        _event(
            "2026-12-26",
            "Boxing Day",
            "Public sector and banks",
            "public",
            CY_2026,
            note="Falls on Saturday; the CBC schedule notes it as a public holiday.",
        ),
        _event("2027-01-01", "New Year's Day", "Public sector and banks", "public", CY_2027),
        _event("2027-01-06", "Epiphany", "Public sector and banks", "public", CY_2027),
        _event("2027-03-15", "Green Monday", "Public sector and banks", "public", CY_2027),
        _event(
            "2027-03-25",
            "Greek Independence Day",
            "Public sector and banks",
            "public",
            CY_2027,
        ),
        _event(
            "2027-04-01",
            "Cyprus National Day",
            "Public sector and banks",
            "public",
            CY_2027,
        ),
        _event(
            "2027-04-30",
            "Good Friday (Orthodox)",
            "Public sector and banks",
            "public",
            CY_2027,
        ),
        _event("2027-05-01", "Labour Day", "Public sector and banks", "public", CY_2027,
               note="Falls on Saturday; no substitute holiday is added."),
        _event("2027-05-03", "Easter Monday", "Public sector and banks", "public", CY_2027),
        _event(
            "2027-05-04",
            "Easter Tuesday (bank holiday)",
            "Banks",
            "bank",
            CY_2027,
        ),
        _event(
            "2027-06-21",
            "Pentecost (bank holiday)",
            "Banks",
            "bank",
            CY_2027,
        ),
        _event(
            "2027-08-15",
            "Assumption Day",
            "Public sector and banks",
            "public",
            CY_2027,
            note="Falls on Sunday; the CBC schedule notes it as a public holiday.",
        ),
        _event(
            "2027-10-01",
            "Cyprus Independence Day",
            "Public sector and banks",
            "public",
            CY_2027,
        ),
        _event(
            "2027-10-28",
            "Greek National Day (Ochi Day)",
            "Public sector and banks",
            "public",
            CY_2027,
        ),
        _event(
            "2027-12-25",
            "Christmas Day",
            "Public sector and banks",
            "public",
            CY_2027,
            note="Falls on Saturday; no substitute holiday is added.",
        ),
        _event(
            "2027-12-26",
            "Boxing Day",
            "Public sector and banks",
            "public",
            CY_2027,
            note="Falls on Sunday; no substitute holiday is added.",
        ),
    ]

    notes = [
        "The Central Bank of Cyprus schedule covers banks; public-sector offices observe the same statutory holidays. Private-sector observance may differ.",
        "Easter Tuesday and Pentecost are bank holidays, not statutory public holidays; they are marked kind='bank'.",
        "Assumption Day, Boxing Day and, in 2027, Labour Day and Christmas Day are included from the CBC notes even when they fall on weekends (15 August and 26 December 2026; 1 May, 15 August, 25 and 26 December 2027).",
        "No substitute holidays are added.",
        "Green Monday is the Orthodox Lent start date published by the Central Bank of Cyprus.",
    ]

    return _region(
        "CY",
        "塞浦路斯",
        "Cyprus",
        "Asia/Nicosia",
        CY_SCOPE,
        [2026, 2027],
        sources,
        events,
        notes,
    )


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def fetch() -> list[dict]:
    """Return the six regions with official 2026 and available 2027 holidays."""

    return [
        _tr_region(),
        _vu_region(),
        _ae_region(),
        _in_region(),
        _au_region(),
        _cy_region(),
    ]