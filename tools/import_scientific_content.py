"""Validate official source snapshots and build an append-only supplementary corpus.

This script never edits data/terms.json. MeSH definitions remain in their source
language. PubChem cards are computed structural facts, not textbook explanations.
"""
from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal, InvalidOperation
import gzip
import hashlib
import json
from pathlib import Path
import re
import unicodedata
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
VERSION = "3.5.5-beta"
TARGETS = {"수학": 10000, "물리": 15000, "화학": 20000, "생명과학": 9000,
           "지구과학": 9500, "천문학": 9000, "국어": 50000}
NLM_NOTICE = ("Courtesy of the U.S. National Library of Medicine. "
              "NLM은 이 앱을 보증하지 않습니다. 이 자료는 내려받은 시점의 스냅샷이며 "
              "NLM의 가장 최신 자료와 다를 수 있습니다.")


def canonical_hash(value) -> str:
    encoded = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def file_hash(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def normalize(value: str) -> str:
    return " ".join(unicodedata.normalize("NFKC", value).casefold().split())


def search_text(term: dict) -> str:
    values = [term.get(key, "") for key in ("name_ko", "name_en", "summary", "detail",
              "formula", "unit", "subject", "category", "example", "caution")]
    return " ".join(values + term.get("aliases", []) + term.get("related", []))


def mesh_records(path: Path):
    with path.open("rb") as probe:
        compressed = probe.read(2) == b"\x1f\x8b"
    opener = gzip.open if compressed else open
    with opener(path, "rb") as stream:
        for _, item in ET.iterparse(stream, events=("end",)):
            if item.tag != "DescriptorRecord":
                continue
            trees = [node.text or "" for node in item.findall("./TreeNumberList/TreeNumber")]
            if not any(number.startswith(("A", "B", "G")) for number in trees):
                item.clear()
                continue
            identity = item.findtext("DescriptorUI", "")
            title = item.findtext("./DescriptorName/String", "")
            preferred = next((node for node in item.findall("./ConceptList/Concept")
                              if node.attrib.get("PreferredConceptYN") == "Y"), None)
            definition = preferred.findtext("ScopeNote", "").strip() if preferred is not None else ""
            aliases = sorted({node.text.strip() for node in item.findall("./ConceptList/Concept/TermList/Term/String")
                              if node.text and node.text.strip() != title})
            if not re.fullmatch(r"D\d{6,9}", identity) or not title or not definition:
                item.clear()
                continue
            original = {"DescriptorUI": identity, "DescriptorName": title, "ScopeNote": definition,
                        "TreeNumbers": trees, "Terms": aliases}
            group = "해부학" if any(t.startswith("A") for t in trees) else (
                "생물" if any(t.startswith("B") for t in trees) else "생물학적 현상·과정")
            term = {
                "id": "nlm-mesh-" + identity.lower(), "name_ko": title, "name_en": title,
                "aliases": aliases, "category": "생명과학 · MeSH " + group, "level": "대학",
                "summary": "NLM MeSH 공식 영어 정의 · " + group,
                "detail": definition + "\n\n[원문 안내] 영어 원문을 보존한 용어집입니다. "
                          "한국어 번역·교과 학습 해설은 아직 검토하지 않았습니다.\n" + NLM_NOTICE,
                "formula": "", "unit": "", "example": "", "caution":
                "의생명 분류·검색용 정의이며 개인의 진단이나 치료 지침이 아닙니다.",
                "related": [], "related_ids": [], "sources": ["nlm_mesh_2026"],
                "subject": "생명과학", "simulator": "", "tier": "공식 영어 원문",
                "language": "en", "definition_original": definition,
                "reference_url": "https://id.nlm.nih.gov/mesh/" + identity + ".html",
                "provenance": {
                    "source_id": "nlm_mesh_2026", "record_id": identity, "production_year": 2026,
                    "source_record_sha256": canonical_hash(original), "tree_numbers": trees,
                    "verification": "official-source-record-and-schema",
                    "korean_translation_reviewed": False, "curriculum_reviewed": False,
                    "license_url": "https://www.nlm.nih.gov/databases/download/terms_and_conditions.html",
                },
            }
            term["search_text"] = search_text(term)
            yield term
            item.clear()


def pubchem_records(path: Path):
    document = json.loads(path.read_text(encoding="utf-8"))
    for row in document.get("PropertyTable", {}).get("Properties", []):
        cid, formula, name = row.get("CID"), row.get("MolecularFormula"), row.get("IUPACName")
        key, mass = row.get("InChIKey"), row.get("MolecularWeight")
        try:
            valid_mass = Decimal(str(mass))
        except InvalidOperation:
            continue
        if (not isinstance(cid, int) or cid < 1 or not isinstance(name, str) or not name or
                not isinstance(formula, str) or not formula or not isinstance(key, str) or
                not re.fullmatch(r"[A-Z]{14}-[A-Z]{10}-[A-Z]", key) or
                not valid_mass.is_finite() or valid_mass <= 0):
            continue
        title = name
        term = {
            "id": f"pubchem-cid-{cid}", "name_ko": title, "name_en": title,
            "aliases": [f"CID {cid}", key, formula], "category": "화학 · PubChem 구조 자료",
            "level": "대학", "summary": f"분자식 {formula} · PubChem 분자량 {mass} g/mol",
            "detail": f"PubChem CID {cid}\nIUPAC명: {name}\n분자식: {formula}\n"
                      f"분자량(PubChem MolecularWeight): {mass} g/mol\nInChIKey: {key}\n\n"
                      "공식 API의 계산 구조 속성을 가져온 화합물 자료입니다. "
                      "서로 같은 분자식도 원자 연결·입체배치가 다를 수 있어 CID와 InChIKey를 함께 확인합니다. "
                      "교과서 해설이나 실험 측정값의 검증 완료를 뜻하지 않습니다.\n" + NLM_NOTICE,
            "formula": "", "unit": "", "molecular_formula": formula,
            "structured_properties": {"MolecularFormula": formula, "MolecularWeight": str(mass),
                                      "MolecularWeightUnit": "g/mol", "InChIKey": key},
            "example": "", "caution": "이 카드에는 제조법·복용법·안전성 판정이 포함되어 있지 않습니다.",
            "related": [], "related_ids": [], "sources": ["pubchem_computed_properties"],
            "subject": "화학", "simulator": "", "tier": "공식 구조 자료",
            "language": "en", "reference_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
            "provenance": {
                "source_id": "pubchem_computed_properties", "record_id": str(cid),
                "source_record_sha256": canonical_hash(row), "inchikey": key,
                "verification": "official-source-record-and-schema",
                "korean_translation_reviewed": False, "curriculum_reviewed": False,
                "reuse_scope": "Computed factual properties; third-party prose and annotations excluded",
                "license_url": "https://pubchem.ncbi.nlm.nih.gov/docs/downloads",
            },
        }
        term["search_text"] = search_text(term)
        yield term


def combine(base: list[dict], candidates, chemistry_target: int):
    """Deduplicate source IDs, chemical structures and exact existing titles.

    English synonyms of existing detailed cards are matched, while generated
    expansion-index aliases never suppress a genuine source record.
    """
    identities = {term["id"] for term in base}
    labels = set()
    for term in base:
        if term.get("tier") == "확장 인덱스":
            continue
        for value in [term.get("name_ko", ""), term.get("name_en", "")]:
            if value:
                labels.add((term.get("subject"), normalize(value)))
    structures = set()
    result, skipped = [], Counter()
    chemistry = sum(term.get("subject") == "화학" for term in base)
    for term in candidates:
        identity, label = term["id"], (term["subject"], normalize(term["name_en"]))
        structure = term.get("provenance", {}).get("inchikey")
        if identity in identities:
            skipped["duplicate_id"] += 1
            continue
        if structure and structure in structures:
            skipped["duplicate_structure"] += 1
            continue
        if label in labels:
            skipped["duplicate_title"] += 1
            continue
        if term["subject"] == "화학" and chemistry >= chemistry_target:
            skipped["chemistry_target_reached"] += 1
            continue
        result.append(term)
        identities.add(identity)
        labels.add(label)
        if structure:
            structures.add(structure)
        chemistry += term["subject"] == "화학"
    return result, dict(skipped)


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mesh", type=Path, required=True)
    parser.add_argument("--pubchem", type=Path, required=True)
    parser.add_argument("--base", type=Path, default=ROOT / "data/terms.json")
    parser.add_argument("--output", type=Path, default=ROOT / "data/imports/science_terms_355.json")
    parser.add_argument("--chemistry-total", type=int, default=20000)
    parser.add_argument("--retrieved-date", default="2026-10-20")
    args = parser.parse_args()
    if args.chemistry_total < 0:
        parser.error("chemistry-total cannot be negative")
    baseline = json.loads((ROOT / "tests/content_baseline.json").read_text(encoding="utf-8"))
    base_document = json.loads(args.base.read_text(encoding="utf-8"))
    base = base_document["terms"]
    if canonical_hash(base[:baseline["original_count"]]) != baseline["canonical_sha256"]:
        raise ValueError("Original 50,000-record preservation check failed; input was not modified.")
    mesh, chemistry = list(mesh_records(args.mesh)), list(pubchem_records(args.pubchem))
    terms, skipped = combine(base, mesh + chemistry, args.chemistry_total)
    source_rows = [
        {"id": "nlm_mesh_2026", "name": "NLM MeSH 2026 · 공식 영어 원문", "organization": "U.S. National Library of Medicine",
         "url": "https://www.nlm.nih.gov/databases/download/mesh.html",
         "download_url": "https://nlmpubs.nlm.nih.gov/projects/mesh/MESH_FILES/xmlmesh/desc2026.gz",
         "snapshot_sha256": file_hash(args.mesh), "validated_records": len(mesh),
         "source_language": "en", "selection": "Descriptor tree prefixes A, B or G; nonempty preferred ScopeNote",
         "license": "NLM Terms and Conditions", "license_url":
         "https://www.nlm.nih.gov/databases/download/terms_and_conditions.html", "notice": NLM_NOTICE},
        {"id": "pubchem_computed_properties", "name": "PubChem · 공식 계산 구조 속성", "organization": "NCBI, U.S. National Library of Medicine",
         "url": "https://pubchem.ncbi.nlm.nih.gov/", "snapshot_sha256": file_hash(args.pubchem),
         "validated_records": len(chemistry), "source_language": "en",
         "selection": "CID, MolecularFormula, MolecularWeight, IUPACName, InChIKey only",
         "license": "NLM terms; contributor annotations excluded", "license_url":
         "https://pubchem.ncbi.nlm.nih.gov/docs/downloads", "notice": NLM_NOTICE},
    ]
    for term in terms:
        term["provenance"]["retrieved_date"] = args.retrieved_date
    output = {
        "version": VERSION, "count": len(terms), "retrieved_date": args.retrieved_date,
        "scope_note": "공식 영어 정의와 계산 구조 자료. 한국어 교과 상세 설명·전문가 검토 수와 별도 집계합니다.",
        "sources": source_rows, "deduplication": skipped, "terms": terms,
    }
    write_json(args.output, output)
    combined = base + terms
    distribution = Counter(term["subject"] for term in combined)
    manifest = {
        "version": VERSION, "build": 35500, "total": len(combined),
        "base_file_count": len(base), "supplement_count": len(terms),
        "distribution": dict(distribution), "targets": TARGETS, "target_total": sum(TARGETS.values()),
        "target_shortfall": {subject: max(0, count - distribution[subject]) for subject, count in TARGETS.items()},
        "core_detailed_count": sum(term.get("tier") != "확장 인덱스" for term in base),
        "core_detailed_count_note": "기존 비인덱스 항목 수. 모든 항목이 상세 해설·예제까지 검증되었다는 뜻이 아닙니다.",
        "extended_index_count": sum(term.get("tier") == "확장 인덱스" for term in base),
        "official_original_count": sum(term.get("tier") == "공식 영어 원문" for term in terms),
        "official_structure_count": sum(term.get("tier") == "공식 구조 자료" for term in terms),
        "authored_316_count": sum(term.get("curation_version") == "3.1.6" for term in base),
        "original_50000_sha256": canonical_hash(base[:50000]),
        "supplement_sha256": file_hash(args.output),
        "note": "목표와 실제 수록량을 분리합니다. 기존 확장 인덱스는 상세 카드로 세지 않으며 "
                "공식 원문·구조 자료도 한국어 교과 해설로 세지 않습니다. 전 과목 목표는 아직 미달입니다.",
        "sources": source_rows, "deduplication": skipped,
    }
    write_json(ROOT / "data/corpus_manifest.json", manifest)
    print(json.dumps({k: v for k, v in manifest.items() if k not in ("sources",)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
