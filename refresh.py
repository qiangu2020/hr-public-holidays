"""Refresh the public, provenance-bearing holiday dataset; never publish partial data."""
from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone
import importlib
import json
from pathlib import Path
import sys
from urllib.parse import urlsplit

PROVIDERS = ("asia", "asean", "global_regions")
REGIONS = ("MY", "MY-KUL", "HK", "TW", "SG", "KR", "TH", "ID", "VN", "TR", "VU", "AE", "IN", "AU", "CY")
ROOT = Path(__file__).resolve().parent

# Exact hosts reviewed against the issuing public bodies; never trust a suffix match.
# KASI, u.ae and the Central Bank of Cyprus use official non-.gov domains.
OFFICIAL_HOSTS = frozenset({
    "www.kabinet.gov.my", "www.1823.gov.hk", "data.gov.tw", "www.dgpa.gov.tw",
    "data.gov.sg", "www.mom.gov.sg", "astro.kasi.re.kr", "www.korea.kr",
    "www.bot.or.th", "www.kemenkopmk.go.id", "en.baochinhphu.vn",
    "xaydungchinhsach.chinhphu.vn", "hatinh.gov.vn", "baochinhphu.vn",
    "www.mevzuat.gov.tr", "vakithesaplama.diyanet.gov.tr", "pmo.gov.vu",
    "u.ae", "www.fahr.gov.ae", "www.uaecma.gov.ae", "rb.indianrailways.gov.in",
    "www.fairwork.gov.au", "www.nsw.gov.au", "www.act.gov.au", "www.wa.gov.au",
    "business.vic.gov.au", "www.qld.gov.au", "www.safework.sa.gov.au",
    "nt.gov.au", "www.legislation.tas.gov.au", "www.centralbank.cy",
})


def validate(regions: list[dict]) -> None:
    ids = [region["id"] for region in regions]
    if len(ids) != len(set(ids)) or set(ids) != set(REGIONS):
        raise ValueError(f"Region coverage mismatch: {ids}")
    for region in regions:
        if 2026 not in region["years"]:
            raise ValueError(f"Missing official 2026 coverage: {region['id']}")
        if not region["sources"] or not region["scope"]:
            raise ValueError(f"Missing official provenance/scope: {region['id']}")
        sources = {source["url"] for source in region["sources"]}
        for url in sources:
            parsed = urlsplit(url)
            if (
                parsed.scheme != "https" or parsed.hostname not in OFFICIAL_HOSTS
                or parsed.username is not None or parsed.password is not None
            ):
                raise ValueError(f"Unapproved official source: {region['id']} {url}")
        seen = set()
        for event in region["events"]:
            day = date.fromisoformat(event["date"])
            if day.year not in region["years"]:
                raise ValueError(f"Undeclared year: {region['id']} {day}")
            if event["source_url"] not in sources:
                raise ValueError(f"Unknown source: {region['id']} {day}")
            if event["kind"] not in {"public", "bank", "government", "optional"}:
                raise ValueError(f"Unknown holiday category: {event}")
            key = (event["date"], event["name"], event["scope"])
            if key in seen or not event["name"] or not event["scope"]:
                raise ValueError(f"Duplicate or incomplete holiday: {region['id']} {key}")
            seen.add(key)
        region["events"].sort(key=lambda event: (event["date"], event["name"]))


def refresh(destination: Path) -> dict:
    def fetch(name: str) -> list[dict]:
        return importlib.import_module(f"providers.{name}").fetch()

    regions = []
    with ThreadPoolExecutor(max_workers=len(PROVIDERS)) as pool:
        for name, result in zip(PROVIDERS, pool.map(fetch, PROVIDERS)):
            regions.extend(result)
            print(f"{name}: {len(result)} regions", file=sys.stderr)
    validate(regions)
    regions.sort(key=lambda region: REGIONS.index(region["id"]))
    dataset = {
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "regions": regions,
        "errors": [],
    }
    destination.parent.mkdir(parents=True, exist_ok=True)
    temporary = destination.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(destination)
    print(f"Published {len(regions)} regions, {sum(len(r['events']) for r in regions)} dated holidays")
    return dataset


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "static/data/holidays.json")
    args = parser.parse_args()
    refresh(args.output)


if __name__ == "__main__":
    main()
