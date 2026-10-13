from __future__ import annotations

import csv
import json
import os
import sqlite3
import time
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

from core import normalize, user_data_dir

DB_FILENAME = "knowledge_user.db"
DEFAULT_LIMIT_GB = 5
MIN_LIMIT_GB = 1
MAX_LIMIT_GB = 5


def db_path() -> Path:
    p = user_data_dir() / "database"
    p.mkdir(parents=True, exist_ok=True)
    return p / DB_FILENAME


def bytes_to_human(n: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(n)
    for unit in units:
        if value < 1024 or unit == units[-1]:
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{n} B"


class KnowledgeDatabase:
    """SQLite store for user-added dictionary entries.

    Built-in content remains read-only JSON inside the app package. Only user
    entries and imported extension packs live here, so app updates cannot erase
    personal data. The file grows dynamically and is guarded by a configurable
    1-5 GB soft quota rather than pre-allocating gigabytes of empty space.
    """

    def __init__(self, limit_gb: int = DEFAULT_LIMIT_GB) -> None:
        self.path = db_path()
        self.limit_gb = max(MIN_LIMIT_GB, min(MAX_LIMIT_GB, int(limit_gb)))
        self.conn = sqlite3.connect(str(self.path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self.conn.execute("PRAGMA foreign_keys=ON")
        self._create_schema()

    def _create_schema(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS user_terms (
                id TEXT PRIMARY KEY,
                name_ko TEXT NOT NULL,
                name_en TEXT NOT NULL DEFAULT '',
                subject TEXT NOT NULL DEFAULT '사용자',
                category TEXT NOT NULL DEFAULT '사용자 추가',
                level TEXT NOT NULL DEFAULT '사용자',
                summary TEXT NOT NULL DEFAULT '',
                detail TEXT NOT NULL DEFAULT '',
                formula TEXT NOT NULL DEFAULT '',
                unit TEXT NOT NULL DEFAULT '',
                example TEXT NOT NULL DEFAULT '',
                caution TEXT NOT NULL DEFAULT '',
                aliases_json TEXT NOT NULL DEFAULT '[]',
                related_json TEXT NOT NULL DEFAULT '[]',
                sources_json TEXT NOT NULL DEFAULT '[]',
                simulator TEXT NOT NULL DEFAULT '',
                search_text TEXT NOT NULL DEFAULT '',
                created_at INTEGER NOT NULL,
                updated_at INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_user_terms_name_ko ON user_terms(name_ko);
            CREATE INDEX IF NOT EXISTS idx_user_terms_name_en ON user_terms(name_en);
            CREATE INDEX IF NOT EXISTS idx_user_terms_subject ON user_terms(subject);
            CREATE INDEX IF NOT EXISTS idx_user_terms_category ON user_terms(category);
            CREATE INDEX IF NOT EXISTS idx_user_terms_level ON user_terms(level);

            CREATE TABLE IF NOT EXISTS meta (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );
            """
        )
        self.conn.commit()

    @property
    def quota_bytes(self) -> int:
        return self.limit_gb * 1024 ** 3

    def set_limit_gb(self, value: int) -> None:
        self.limit_gb = max(MIN_LIMIT_GB, min(MAX_LIMIT_GB, int(value)))

    def size_bytes(self) -> int:
        total = 0
        for suffix in ("", "-wal", "-shm"):
            p = Path(str(self.path) + suffix)
            try:
                total += p.stat().st_size
            except OSError:
                pass
        return total

    def usage_ratio(self) -> float:
        return min(1.0, self.size_bytes() / max(1, self.quota_bytes))

    def ensure_room(self, incoming_bytes: int = 0) -> None:
        projected = self.size_bytes() + max(0, int(incoming_bytes))
        if projected > self.quota_bytes:
            raise ValueError(
                f"사용자 데이터 한도({self.limit_gb} GB)를 넘습니다. "
                f"현재 {bytes_to_human(self.size_bytes())}, 추가 예정 {bytes_to_human(incoming_bytes)}"
            )

    @staticmethod
    def _term_from_row(row: sqlite3.Row) -> dict:
        def arr(key: str) -> list:
            try:
                v = json.loads(row[key] or "[]")
                return v if isinstance(v, list) else []
            except Exception:
                return []
        return {
            "id": row["id"],
            "name_ko": row["name_ko"],
            "name_en": row["name_en"],
            "subject": row["subject"],
            "category": row["category"],
            "level": row["level"],
            "summary": row["summary"],
            "detail": row["detail"],
            "formula": row["formula"],
            "unit": row["unit"],
            "example": row["example"],
            "caution": row["caution"],
            "aliases": arr("aliases_json"),
            "related": arr("related_json"),
            "sources": arr("sources_json"),
            "simulator": row["simulator"],
            "search_text": row["search_text"],
            "user_added": True,
        }

    def all_user_terms(self) -> List[dict]:
        rows = self.conn.execute("SELECT * FROM user_terms ORDER BY name_ko COLLATE NOCASE").fetchall()
        return [self._term_from_row(r) for r in rows]

    def count(self) -> int:
        return int(self.conn.execute("SELECT COUNT(*) FROM user_terms").fetchone()[0])

    def upsert_term(self, term: dict) -> str:
        payload = dict(term)
        name_ko = str(payload.get("name_ko", "")).strip()
        if not name_ko:
            raise ValueError("표제어(한국어 이름)는 비워둘 수 없습니다.")
        name_en = str(payload.get("name_en", "")).strip()
        term_id = str(payload.get("id", "")).strip()
        if not term_id:
            stamp = int(time.time() * 1000)
            term_id = f"user-{stamp}-{abs(hash((name_ko, name_en, stamp))) % 1000000:06d}"
        aliases = [str(x).strip() for x in payload.get("aliases", []) if str(x).strip()]
        related = [str(x).strip() for x in payload.get("related", []) if str(x).strip()]
        sources = [str(x).strip() for x in payload.get("sources", []) if str(x).strip()]
        search_text = " ".join(
            [name_ko, name_en, str(payload.get("subject", "")), str(payload.get("category", "")),
             str(payload.get("level", "")), str(payload.get("summary", "")), str(payload.get("detail", "")),
             str(payload.get("formula", ""))] + aliases + related
        )
        approx = len(json.dumps(payload, ensure_ascii=False).encode("utf-8")) + 8192
        self.ensure_room(approx)
        now = int(time.time())
        self.conn.execute(
            """
            INSERT INTO user_terms (
                id,name_ko,name_en,subject,category,level,summary,detail,formula,unit,example,caution,
                aliases_json,related_json,sources_json,simulator,search_text,created_at,updated_at
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
            ON CONFLICT(id) DO UPDATE SET
                name_ko=excluded.name_ko,name_en=excluded.name_en,subject=excluded.subject,
                category=excluded.category,level=excluded.level,summary=excluded.summary,detail=excluded.detail,
                formula=excluded.formula,unit=excluded.unit,example=excluded.example,caution=excluded.caution,
                aliases_json=excluded.aliases_json,related_json=excluded.related_json,sources_json=excluded.sources_json,
                simulator=excluded.simulator,search_text=excluded.search_text,updated_at=excluded.updated_at
            """,
            (
                term_id, name_ko, name_en, str(payload.get("subject", "사용자")),
                str(payload.get("category", "사용자 추가")), str(payload.get("level", "사용자")),
                str(payload.get("summary", "")), str(payload.get("detail", "")), str(payload.get("formula", "")),
                str(payload.get("unit", "")), str(payload.get("example", "")), str(payload.get("caution", "")),
                json.dumps(aliases, ensure_ascii=False), json.dumps(related, ensure_ascii=False),
                json.dumps(sources, ensure_ascii=False), str(payload.get("simulator", "")), search_text, now, now,
            ),
        )
        self.conn.commit()
        return term_id

    def delete_term(self, term_id: str) -> bool:
        cur = self.conn.execute("DELETE FROM user_terms WHERE id=?", (term_id,))
        self.conn.commit()
        return cur.rowcount > 0

    def import_json(self, path: Path) -> Tuple[int, int]:
        self.ensure_room(path.stat().st_size * 3)
        payload = json.loads(path.read_text(encoding="utf-8-sig"))
        if isinstance(payload, dict):
            rows = payload.get("terms", payload.get("entries", []))
        elif isinstance(payload, list):
            rows = payload
        else:
            raise ValueError("JSON은 배열 또는 terms/entries 배열을 가진 객체여야 합니다.")
        if not isinstance(rows, list):
            raise ValueError("가져올 항목 배열을 찾지 못했습니다.")
        ok = bad = 0
        for row in rows:
            if not isinstance(row, dict):
                bad += 1
                continue
            try:
                row = dict(row)
                row.pop("id", None)  # imported rows receive local IDs
                self.upsert_term(row)
                ok += 1
            except Exception:
                bad += 1
        return ok, bad

    def import_csv(self, path: Path) -> Tuple[int, int]:
        self.ensure_room(path.stat().st_size * 4)
        ok = bad = 0
        with path.open("r", encoding="utf-8-sig", newline="") as f:
            for row in csv.DictReader(f):
                try:
                    term = dict(row)
                    for key in ("aliases", "related", "sources"):
                        value = str(term.get(key, "")).strip()
                        term[key] = [x.strip() for x in value.replace(";", ",").split(",") if x.strip()]
                    term.pop("id", None)
                    self.upsert_term(term)
                    ok += 1
                except Exception:
                    bad += 1
        return ok, bad

    def export_json(self, path: Path) -> None:
        payload = {"format": "PhysicsMathPocket-user-terms-v1", "terms": self.all_user_terms()}
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    def export_csv(self, path: Path) -> None:
        fields = ["name_ko", "name_en", "subject", "category", "level", "summary", "detail", "formula", "unit", "example", "caution", "aliases", "related"]
        with path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=fields)
            w.writeheader()
            for t in self.all_user_terms():
                row = {k: t.get(k, "") for k in fields}
                for k in ("aliases", "related"):
                    row[k] = ", ".join(t.get(k, []))
                w.writerow(row)

    def optimize(self) -> None:
        self.conn.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        self.conn.execute("VACUUM")
        self.conn.commit()

    def close(self) -> None:
        try:
            self.conn.close()
        except Exception:
            pass
