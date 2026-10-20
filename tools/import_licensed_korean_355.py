"""Import explicitly licensed Korean dictionary CSV without altering the 50k baseline.

CSV columns: entry_id, headword, meaning, pos, category, source_url.
The operator must obtain and review the dataset license separately; the tool
does not scrape websites, infer rights, or download unlicensed definitions.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "korean_import_355.json"
ALLOWED_CATEGORIES = {
    "어휘", "문법", "문학", "읽기", "쓰기", "듣기·말하기", "매체",
    "관용구", "속담", "사자성어", "맞춤법", "방언", "고어", "기타"
}
SOURCE_NAME = "국립국어원 개방형 사전(우리말샘)"
SOURCE_URL = "https://www.data.go.kr/data/15019347/openapi.do"
ATTRIBUTION = "자료 출처: 문화체육관광부 국립국어원, 개방형 사전(우리말샘), 공공누리 제1유형(출처표시)"
FIELDS = ("entry_id", "headword", "meaning", "pos", "category", "source_url")


def convert(rows):
    """Validate one externally supplied, documented dictionary export."""
    entries = []
    seen = set()
    for number, row in enumerate(rows, 2):
        if not isinstance(row, dict):
            raise ValueError(f"Row {number}: not a dictionary")
        entry_id = str(row.get("entry_id", "")).strip()
        headword = str(row.get("headword", "")).strip()
        meaning = str(row.get("meaning", "")).strip()
        pos = str(row.get("pos", "")).strip()
        category = str(row.get("category", "어휘")).strip() or "어휘"
        url = str(row.get("source_url", "")).strip() or SOURCE_URL
        if not re.fullmatch(r"[A-Za-z0-9_.:-]{1,80}", entry_id):
            raise ValueError(f"Row {number}: invalid official entry_id")
        if not headword or not meaning or not pos:
            raise ValueError(f"Row {number}: missing headword, meaning or pos")
        if len(headword) > 120 or len(meaning) > 15000:
            raise ValueError(f"Row {number}: invalid length")
        if category not in ALLOWED_CATEGORIES:
            raise ValueError(f"Row {number}: unsupported category {category!r}")
        parsed = urlparse(url)
        if parsed.scheme != "https" or not (parsed.hostname in
              ("opendict.korean.go.kr", "www.data.go.kr", "data.go.kr")):
            raise ValueError(f"Row {number}: source URL must be an official HTTPS location")
        unique_id = "woorimalsam-" + entry_id
        if unique_id in seen:
            raise ValueError(f"Row {number}: duplicate entry id")
        seen.add(unique_id)
        entries.append({
            "id": unique_id,
            "subject": "국어",
            "category": "국어 · " + category,
            "name_ko": headword,
            "name_en": "",
            "level": "사전",
            "summary": meaning,
            "detail": meaning,
            "example": "",
            "caution": "우리말샘은 참여형 사전입니다. 규범 여부와 용례는 원문에서 확인하세요.",
            "formula": "",
            "aliases": [],
            "related": [],
            "search_text": f"{headword} {meaning} {pos} {category}",
            "pos": pos,
            "sources": [url],
            "source_entry_id": entry_id,
            "source_license": "KOGL-1",
            "curation_version": "3.5.5",
            "tier": "사전 원문"
        })
    return entries


def import_csv(path: Path, *, write=False, output=OUTPUT):
    with path.open("r", encoding="utf-8-sig", newline="") as stream:
        reader = csv.DictReader(stream)
        if not set(FIELDS).issubset(reader.fieldnames or []):
            raise ValueError("CSV must contain: " + ", ".join(FIELDS))
        entries = convert(reader)
    if len(entries) > 50000:
        raise ValueError("This import batch exceeds the Korean target of 50,000")
    payload = {
        "schema_version": 1,
        "source_name": SOURCE_NAME,
        "source_url": SOURCE_URL,
        "attribution": ATTRIBUTION,
        "license": "KOGL-1",
        "imported_count": len(entries),
        "terms": entries
    }
    if write:
        output.parent.mkdir(parents=True, exist_ok=True)
        temp = output.with_suffix(output.suffix + ".tmp")
        temp.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        temp.replace(output)
    return payload


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("csv", type=Path, help="Already licensed and exported CSV")
    parser.add_argument("--write", action="store_true", help="Write app data; otherwise preview only")
    parser.add_argument("--acknowledge-license", action="store_true",
                        help="Confirm you verified the dataset's use and redistribution terms")
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    if args.write and not args.acknowledge_license:
        parser.error("--write requires --acknowledge-license")
    payload = import_csv(args.csv, write=args.write, output=args.output)
    print(json.dumps({"validated": payload["imported_count"],
                      "written": bool(args.write),
                      "attribution": ATTRIBUTION}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
