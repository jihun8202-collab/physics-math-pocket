"""Download real PubChem computed properties, with resumable batches and throttling.

Only numerical/structural fields from the PUG REST property endpoint are requested.
Contributor descriptions, safety advice, and third-party annotations are not copied.
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/"
PROPERTIES = "/property/MolecularFormula,MolecularWeight,IUPACName,InChIKey/JSON"
LAST_REQUEST = 0.0


def request_batch(ids: list[int]) -> list[dict]:
    global LAST_REQUEST
    url = BASE + ",".join(map(str, ids)) + PROPERTIES
    for attempt in range(6):
        time.sleep(max(0, 0.4 - (time.monotonic() - LAST_REQUEST)))
        LAST_REQUEST = time.monotonic()
        try:
            req = Request(url, headers={"User-Agent": "PhysicsMathPocket/3.5.5 educational-content-import"})
            with urlopen(req, timeout=90) as response:
                result = json.load(response)
            rows = result.get("PropertyTable", {}).get("Properties", [])
            if any(int(row["CID"]) not in ids for row in rows):
                raise ValueError("PubChem returned a CID outside the requested batch")
            return rows
        except HTTPError as error:
            if error.code in (400, 404) and len(ids) > 1:
                middle = len(ids) // 2
                return request_batch(ids[:middle]) + request_batch(ids[middle:])
            if error.code == 404:
                return []
            if error.code not in (429, 500, 502, 503, 504) or attempt == 5:
                raise
            time.sleep(min(20, 2 ** (attempt + 1)))
    raise RuntimeError("unreachable")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--count", type=int, default=20000)
    parser.add_argument("--batch-size", type=int, default=200)
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 500 or not 1 <= args.count <= 100000:
        parser.error("batch size must be 1..500 and count 1..100000")
    args.directory.mkdir(parents=True, exist_ok=True)
    records = {}
    start = 1
    while len(records) < args.count:
        end = start + args.batch_size - 1
        batch_path = args.directory / f"cid-{start:06d}-{end:06d}.json"
        if batch_path.exists():
            payload = json.loads(batch_path.read_text(encoding="utf-8"))
        else:
            rows = request_batch(list(range(start, end + 1)))
            payload = {
                "request_url": BASE + ",".join(map(str, range(start, end + 1))) + PROPERTIES,
                "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "Properties": rows,
            }
            temporary = batch_path.with_suffix(".tmp")
            temporary.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            temporary.replace(batch_path)
        for row in payload["Properties"]:
            records[row["CID"]] = row
        print(f"CID {start}..{end}: {len(records)} verified returned records", flush=True)
        start = end + 1
    result = {
        "source": "PubChem PUG REST computed properties",
        "source_url": "https://pubchem.ncbi.nlm.nih.gov/",
        "retrieved_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "requested_valid_count": args.count,
        "PropertyTable": {"Properties": [records[key] for key in sorted(records)[:args.count]]},
    }
    output = args.directory / "pubchem-properties.json"
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Saved {args.count} actual records to {output}", flush=True)


if __name__ == "__main__":
    main()
