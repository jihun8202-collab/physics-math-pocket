# -*- coding: utf-8 -*-
"""Create indexed SQLite question bank from reviewed JSONL, suitable for 350k items.

Never auto-generate fake questions. An editor must independently check question
content, answers, explanations, source terms and licensing. The CLI requires
explicit acknowledgement and refuses to overwrite an existing bank by default.
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core import normalize
from quiz_engine import SUBJECTS, PER_SUBJECT_TARGET, validate_question

SCHEMA = """
CREATE TABLE questions (
    id TEXT PRIMARY KEY,
    subject TEXT NOT NULL,
    concept_id TEXT NOT NULL,
    concept_norm TEXT NOT NULL,
    difficulty TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL
);
CREATE INDEX questions_concept_id ON questions(subject, concept_id);
CREATE INDEX questions_concept_name ON questions(subject, concept_norm);
CREATE INDEX questions_filters ON questions(subject, difficulty, kind);
"""


def build(input_file: Path, destination: Path, *, replace: bool = False) -> dict:
    if destination.exists() and not replace:
        raise FileExistsError("Existing bank must not be overwritten without --replace")
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_suffix(destination.suffix + ".building")
    if staging.exists():
        staging.unlink()
    con = sqlite3.connect(staging)
    counts = {subject: 0 for subject in SUBJECTS}
    try:
        con.executescript(SCHEMA)
        with input_file.open("r", encoding="utf-8-sig") as reader:
            for line_no, line in enumerate(reader, start=1):
                if not line.strip():
                    continue
                try:
                    q = validate_question(json.loads(line))
                except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
                    raise ValueError(f"Line {line_no}: {error}") from error
                counts[q["subject"]] += 1
                if counts[q["subject"]] > PER_SUBJECT_TARGET:
                    raise ValueError("Subject target exceeded; review question inventory")
                try:
                    con.execute(
                        "INSERT INTO questions VALUES (?, ?, ?, ?, ?, ?, ?)",
                        (q["id"], q["subject"], q["concept_id"],
                         normalize(q["concept_name"]), q["difficulty"], q["kind"],
                         json.dumps(q, ensure_ascii=False, separators=(",", ":")))
                    )
                except sqlite3.IntegrityError as error:
                    raise ValueError(f"Line {line_no}: duplicate question id") from error
        con.commit()
        status = con.execute("PRAGMA integrity_check").fetchone()[0]
        if status != "ok":
            raise ValueError("SQLite integrity failure: " + status)
    except BaseException:
        con.close()
        if staging.exists():
            staging.unlink()
        raise
    else:
        con.close()
    staging.replace(destination)
    return {"per_subject": counts, "actual": sum(counts.values()),
            "target": 350000, "remaining": 350000-sum(counts.values())}


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("jsonl", type=Path, help="Editor-reviewed question records, one JSON object per line")
    p.add_argument("--output", type=Path, default=ROOT/"data"/"quiz_bank_355.sqlite3")
    p.add_argument("--replace", action="store_true")
    p.add_argument("--acknowledge-reviewed", action="store_true",
                   help="Confirm factual accuracy, provenance, and permissions were independently checked")
    a = p.parse_args()
    if not a.acknowledge_reviewed:
        p.error("Editor review acknowledgment is required")
    result = build(a.jsonl, a.output, replace=a.replace)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
