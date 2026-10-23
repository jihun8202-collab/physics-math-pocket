from __future__ import annotations

import json
import math
import os
import re
import sys
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

APP_NAME = "PhysicsMathPocket"
APP_VERSION = "3.5.10"
APP_BUILD = 35100
APP_CHANNEL = "beta"
APP_COPYRIGHT = "Copyright © 2026 Physics + Math Pocket Project"


def resource_path(relative: str) -> Path:
    """Return a path that works in source and PyInstaller builds."""
    base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return base / relative


def user_data_dir() -> Path:
    # Development/test override. This keeps build-time tests away from the
    # user's real LOCALAPPDATA database and settings on Windows.
    override = os.environ.get("PHYSICSMATHPOCKET_DATA_DIR", "").strip()
    if override:
        path = Path(override).expanduser()
        path.mkdir(parents=True, exist_ok=True)
        return path

    if sys.platform == "win32":
        root = Path(os.environ.get("LOCALAPPDATA", os.environ.get("APPDATA", Path.home())))
    elif sys.platform == "darwin":
        root = Path.home() / "Library" / "Application Support"
    else:
        root = Path(os.environ.get("XDG_CONFIG_HOME", Path.home() / ".config"))
    path = root / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text or "").casefold()
    text = "".join(
        _CHOSEONG[ord(ch) - 0x1100] if 0x1100 <= ord(ch) <= 0x1112 else ch
        for ch in text
    )
    return re.sub(r"[^0-9a-z가-힣ㄱ-ㅎα-ω]+", "", text)


_CHOSEONG = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"


def hangul_initials(text: str) -> str:
    """Return Korean initial consonants while preserving non-Hangul characters.

    Examples: '전자기 유도' -> 'ㅈㅈㄱㅇㄷ', 'F=ma' -> 'fma'.
    """
    result: List[str] = []
    for ch in unicodedata.normalize("NFKC", text or "").casefold():
        code = ord(ch)
        if 0xAC00 <= code <= 0xD7A3:
            result.append(_CHOSEONG[(code - 0xAC00) // 588])
        elif ch.isalnum() or ch in _CHOSEONG:
            result.append(ch)
    return "".join(result)


def is_initial_query(text: str) -> bool:
    cleaned = normalize(text)
    return bool(cleaned) and all(ch in _CHOSEONG or ch.isdigit() for ch in cleaned)


def load_json(relative: str) -> dict:
    path = resource_path(relative)
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _prepare_term_for_search(term: dict) -> dict:
    """Cache normalized fields so a 50k-card corpus stays responsive."""
    term["_ko_norm"] = normalize(term.get("name_ko", ""))
    term["_en_norm"] = normalize(term.get("name_en", ""))
    term["_aliases_norm"] = [normalize(x) for x in term.get("aliases", [])]
    term["_related_norm"] = [normalize(x) for x in term.get("related", [])]
    term["_formula_norm"] = normalize(term.get("formula", ""))
    term["_summary_norm"] = normalize(term.get("summary", ""))
    term["_detail_norm"] = normalize(term.get("detail", ""))
    term["_search_blob"] = normalize(term.get("search_text", "") or " ".join([
        term.get("name_ko", ""), term.get("name_en", ""), term.get("summary", ""),
        term.get("detail", ""), term.get("formula", ""), " ".join(term.get("aliases", [])),
        " ".join(term.get("related", [])), term.get("category", ""), term.get("subject", "")
    ]))
    term["_initials_ko"] = hangul_initials(term.get("name_ko", ""))
    term["_initials_aliases"] = [hangul_initials(x) for x in term.get("aliases", [])]
    return term

def load_terms() -> List[dict]:
    payload = load_json("data/terms.json")
    terms = list(payload.get("terms", []))
    if not isinstance(terms, list) or not terms:
        raise ValueError("수학·과학 개념 데이터가 비어 있습니다.")
    # Officially sourced supplements are shipped separately so the original
    # 50,000-card corpus remains byte-for-byte reproducible.  Merge by stable
    # id and keep the base record when a collision is encountered.
    supplement_path = resource_path("data/imports/science_terms_355.json")
    if supplement_path.exists():
        try:
            supplement = json.loads(supplement_path.read_text(encoding="utf-8"))
            seen = {str(item.get("id")) for item in terms if isinstance(item, dict)}
            for item in supplement.get("terms", []):
                if not isinstance(item, dict):
                    continue
                item_id = str(item.get("id", ""))
                if item_id and item_id not in seen:
                    terms.append(item)
                    seen.add(item_id)
        except (OSError, ValueError, TypeError):
            # A damaged optional supplement must not prevent the base app from
            # opening; release verification reports the missing supplement.
            pass
    return [_prepare_term_for_search(t) for t in terms]

def load_sources() -> List[dict]:
    sources = list(load_json("data/sources.json").get("sources", []))
    supplement_path = resource_path("data/imports/science_terms_355.json")
    if supplement_path.exists():
        try:
            payload = json.loads(supplement_path.read_text(encoding="utf-8"))
            seen = {str(item.get("id")) for item in sources if isinstance(item, dict)}
            for item in payload.get("sources", []):
                if isinstance(item, dict) and str(item.get("id", "")) not in seen:
                    sources.append(item)
                    seen.add(str(item.get("id")))
        except (OSError, ValueError, TypeError):
            pass
    return sources


def load_constants() -> List[dict]:
    return load_json("data/constants.json").get("constants", [])


def score_term(term: dict, query: str) -> float:
    q = normalize(query)
    if not q:
        return 1.0

    ko = term.get("_ko_norm") or normalize(term.get("name_ko", ""))
    en = term.get("_en_norm") or normalize(term.get("name_en", ""))
    aliases = term.get("_aliases_norm") or [normalize(x) for x in term.get("aliases", [])]
    related = term.get("_related_norm") or [normalize(x) for x in term.get("related", [])]
    formula = term.get("_formula_norm") or normalize(term.get("formula", ""))
    summary = term.get("_summary_norm") or normalize(term.get("summary", ""))
    detail = term.get("_detail_norm") or normalize(term.get("detail", ""))
    blob = term.get("_search_blob") or normalize(term.get("search_text", ""))
    initials_ko = term.get("_initials_ko") or hangul_initials(term.get("name_ko", ""))
    initials_aliases = term.get("_initials_aliases") or [hangul_initials(x) for x in term.get("aliases", [])]

    score = 0.0
    initial_query = is_initial_query(query)
    if initial_query:
        if q == initials_ko or q in initials_aliases: score += 138
        if initials_ko.startswith(q): score += 94
        if q in initials_ko: score += 68
        if any(a.startswith(q) for a in initials_aliases): score += 72
    if q == ko or q == en or q in aliases: score += 520
    if ko.startswith(q) or en.startswith(q): score += 95
    if any(a.startswith(q) for a in aliases): score += 82
    if q in ko: score += 72
    if q in en: score += 62
    if any(q in a for a in aliases): score += 55
    if any(q in r for r in related): score += 30
    if q in formula: score += 28
    if q in summary: score += 22
    if q in detail: score += 14
    if q in blob: score += 10

    # Fuzzy matching across 50k cards is expensive. Only attempt it for
    # plausible title candidates; exact/sub-string matches above remain unchanged.
    if score == 0 and len(q) >= 3:
        candidates = [ko, en] + aliases
        plausible = [c for c in candidates if c and (c[:1] == q[:1] or q[:2] in c or c[:2] in q)]
        if plausible:
            fuzzy = max((SequenceMatcher(None, q, c).ratio() for c in plausible), default=0.0)
            if fuzzy >= 0.64:
                score += fuzzy * 38
    # Detailed core dictionary entries should rank above 50K expansion cards
    # when both match the same query.
    if term.get("tier") == "확장 인덱스":
        score *= 0.58
    return score

def search_terms(
    terms: Iterable[dict],
    query: str = "",
    category: str = "전체",
    favorite_ids: Optional[Set[str]] = None,
    favorites_only: bool = False,
    limit: Optional[int] = 300,
) -> List[dict]:
    favorite_ids = favorite_ids or set()
    ranked: List[Tuple[float, str, dict]] = []
    qnorm = normalize(query) if query.strip() else ""
    initial_query = is_initial_query(query) if qnorm else False
    for term in terms:
        if category not in ("", "전체") and term.get("category") != category:
            continue
        if favorites_only and term.get("id") not in favorite_ids:
            continue
        if qnorm:
            blob = term.get("_search_blob", "")
            initials = term.get("_initials_ko", "")
            aliases = term.get("_aliases_norm", [])
            ko = term.get("_ko_norm", "")
            en = term.get("_en_norm", "")
            initial_hit = initial_query and (qnorm in initials or any(qnorm in x for x in term.get("_initials_aliases", [])))
            substring_hit = qnorm in blob or qnorm in ko or qnorm in en or any(qnorm in a for a in aliases)
            fuzzy_candidate = len(qnorm) >= 3 and any(c and (c[:1] == qnorm[:1] or qnorm[:2] in c or c[:2] in qnorm) for c in [ko,en,*aliases])
            if not (initial_hit or substring_hit or fuzzy_candidate):
                continue
        score = score_term(term, query)
        if qnorm and score <= 0:
            continue
        ranked.append((score, term.get("name_ko", ""), term))

    if query.strip():
        ranked.sort(key=lambda row: (-row[0], row[1]))
    else:
        ranked.sort(key=lambda row: row[1])
    results = [row[2] for row in ranked]
    return results if limit is None else results[:limit]


class JsonSetStore:
    def __init__(self, filename: str) -> None:
        self.path = user_data_dir() / filename

    def load(self) -> Set[str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            values = payload.get("values", [])
            return {str(x) for x in values}
        except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
            return set()

    def save(self, values: Set[str]) -> None:
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"values": sorted(values)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)


class JsonListStore:
    def __init__(self, filename: str, maximum: int = 12) -> None:
        self.path = user_data_dir() / filename
        self.maximum = maximum

    def load(self) -> List[str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            values = payload.get("values", [])
            return [str(x) for x in values if str(x).strip()][: self.maximum]
        except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
            return []

    def save(self, values: List[str]) -> None:
        cleaned: List[str] = []
        seen = set()
        for value in values:
            value = str(value).strip()
            key = normalize(value)
            if not value or key in seen:
                continue
            seen.add(key)
            cleaned.append(value)
            if len(cleaned) >= self.maximum:
                break
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"values": cleaned}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)


class JsonDictStore:
    def __init__(self, filename: str) -> None:
        self.path = user_data_dir() / filename

    def load(self) -> Dict[str, str]:
        try:
            payload = json.loads(self.path.read_text(encoding="utf-8"))
            values = payload.get("values", {})
            if not isinstance(values, dict):
                return {}
            return {str(k): str(v) for k, v in values.items() if str(v).strip()}
        except (FileNotFoundError, OSError, json.JSONDecodeError, TypeError):
            return {}

    def save(self, values: Dict[str, str]) -> None:
        cleaned = {str(k): str(v).strip() for k, v in values.items() if str(v).strip()}
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(
            json.dumps({"values": cleaned}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        tmp.replace(self.path)


@dataclass(frozen=True)
class UnitFamily:
    name: str
    units: dict


UNIT_FAMILIES = {
    "길이": UnitFamily("길이", {"m": 1.0, "km": 1000.0, "cm": 0.01, "mm": 0.001, "μm": 1e-6, "nm": 1e-9, "in": 0.0254, "ft": 0.3048, "mi": 1609.344, "au": 149_597_870_700.0, "ly": 9.4607304725808e15, "pc": 3.085677581491367e16}),
    "넓이": UnitFamily("넓이", {"m²": 1.0, "km²": 1e6, "cm²": 1e-4, "mm²": 1e-6, "ha": 1e4, "acre": 4046.8564224}),
    "부피": UnitFamily("부피", {"m³": 1.0, "L": 1e-3, "mL": 1e-6, "cm³": 1e-6, "ft³": 0.028316846592}),
    "질량": UnitFamily("질량", {"kg": 1.0, "g": 1e-3, "mg": 1e-6, "μg": 1e-9, "t": 1000.0, "lb": 0.45359237, "u": 1.66053906892e-27}),
    "시간": UnitFamily("시간", {"s": 1.0, "ms": 1e-3, "μs": 1e-6, "ns": 1e-9, "min": 60.0, "h": 3600.0, "day": 86400.0, "year": 31557600.0}),
    "속력": UnitFamily("속력", {"m/s": 1.0, "km/h": 1 / 3.6, "mph": 0.44704, "knot": 0.5144444444444445, "c": 299_792_458.0}),
    "가속도": UnitFamily("가속도", {"m/s²": 1.0, "cm/s²": 0.01, "g₀": 9.80665}),
    "힘": UnitFamily("힘", {"N": 1.0, "kN": 1000.0, "dyn": 1e-5, "kgf": 9.80665, "lbf": 4.4482216152605}),
    "에너지": UnitFamily("에너지", {"J": 1.0, "kJ": 1000.0, "MJ": 1e6, "Wh": 3600.0, "kWh": 3.6e6, "cal": 4.184, "kcal": 4184.0, "eV": 1.602176634e-19, "keV": 1.602176634e-16, "MeV": 1.602176634e-13, "GeV": 1.602176634e-10}),
    "일률": UnitFamily("일률", {"W": 1.0, "kW": 1000.0, "MW": 1e6, "hp": 745.6998715822702}),
    "압력": UnitFamily("압력", {"Pa": 1.0, "kPa": 1000.0, "MPa": 1e6, "bar": 1e5, "atm": 101325.0, "mmHg": 133.322387415, "psi": 6894.757293168}),
    "주파수": UnitFamily("주파수", {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9, "rpm": 1 / 60.0}),
    "전하": UnitFamily("전하", {"C": 1.0, "mC": 1e-3, "μC": 1e-6, "nC": 1e-9, "e": 1.602176634e-19}),
    "전류": UnitFamily("전류", {"A": 1.0, "mA": 1e-3, "μA": 1e-6, "nA": 1e-9}),
    "전압": UnitFamily("전압", {"V": 1.0, "mV": 1e-3, "kV": 1e3, "MV": 1e6}),
    "저항": UnitFamily("저항", {"Ω": 1.0, "mΩ": 1e-3, "kΩ": 1e3, "MΩ": 1e6, "GΩ": 1e9}),
    "각도": UnitFamily("각도", {"rad": 1.0, "deg": math.pi / 180.0, "rev": 2 * math.pi, "arcmin": math.pi / 10800.0, "arcsec": math.pi / 648000.0}),
}



def convert_unit(value: float, family: str, from_unit: str, to_unit: str) -> float:
    if family == "온도":
        kelvin = _temperature_to_kelvin(value, from_unit)
        return _kelvin_to_temperature(kelvin, to_unit)
    info = UNIT_FAMILIES.get(family)
    if not info:
        raise ValueError("지원하지 않는 단위 종류입니다.")
    try:
        return value * info.units[from_unit] / info.units[to_unit]
    except KeyError as exc:
        raise ValueError("지원하지 않는 단위입니다.") from exc


def _temperature_to_kelvin(value: float, unit: str) -> float:
    if unit == "K":
        return value
    if unit == "°C":
        return value + 273.15
    if unit == "°F":
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    raise ValueError("지원하지 않는 온도 단위입니다.")


def _kelvin_to_temperature(value: float, unit: str) -> float:
    if unit == "K":
        return value
    if unit == "°C":
        return value - 273.15
    if unit == "°F":
        return (value - 273.15) * 9.0 / 5.0 + 32.0
    raise ValueError("지원하지 않는 온도 단위입니다.")


def unit_names(family: str) -> List[str]:
    if family == "온도":
        return ["K", "°C", "°F"]
    info = UNIT_FAMILIES.get(family)
    return list(info.units) if info else []


def format_number(value: float) -> str:
    if value == 0:
        return "0"
    abs_value = abs(value)
    if abs_value >= 1e9 or abs_value < 1e-6:
        mantissa, exponent = f"{value:.10e}".split("e")
        return f"{mantissa} × 10^{int(exponent)}"
    return f"{value:,.10g}"
