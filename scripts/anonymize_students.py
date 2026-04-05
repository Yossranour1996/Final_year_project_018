# scripts/anonymize_students.py
from __future__ import annotations

import json
import random
from pathlib import Path
from typing import Dict, Any, List, Tuple

# =========================
# إعدادات
# =========================

FAKE_FIRST_NAMES = [
    "أحمد", "محمد", "علي", "عمر", "خالد", "يوسف", "محمود", "حسن", "إبراهيم", "مصطفى",
    "سارة", "مريم", "فاطمة", "نور", "آية", "هدى", "دينا", "ملك", "رحمة", "سلمى",
    "لينا", "ياسمين", "رنا", "زينب", "شيماء", "ريم", "مي", "نجلاء", "إسراء", "دعاء"
]

FAKE_MIDDLE_NAMES = [
    "عبد الله", "عبد الرحمن", "عبد الكريم", "حسن", "حسين", "صالح", "سامي", "طارق",
    "سعيد", "جمال", "نبيل", "مروان", "نادر", "شريف", "أمين", "باسم", "رامي", "وسام",
    "عادل", "مازن", "كريم", "هشام", "وليد", "رائد"
]

FAKE_LAST_NAMES = [
    "علي", "محمد", "إبراهيم", "حسن", "عبد الرحيم", "عبد السلام", "السيد", "محمود",
    "صابر", "مصطفى", "النجار", "الشافعي", "الأنصاري", "الهاشمي", "الزيدي", "العمري",
    "الفقي", "السعدي", "العطار", "الحمادي", "الكتبي", "المالكي", "التميمي", "القحطاني"
]


# =========================
# أدوات عامة
# =========================

def _load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _save_json(path: Path, obj: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")


def _norm(x: Any) -> str:
    return str(x or "").strip()


def _is_unknown(x: str) -> bool:
    x = _norm(x)
    return x == "" or x == "[UNK]"


def _stable_seed_from_key(key: str) -> int:
    # seed ثابت من النص
    return abs(hash(key)) % (10**9)


def _make_fake_name(seed_key: str) -> str:
    rnd = random.Random(_stable_seed_from_key(seed_key))
    first = rnd.choice(FAKE_FIRST_NAMES)
    middle = rnd.choice(FAKE_MIDDLE_NAMES)
    last = rnd.choice(FAKE_LAST_NAMES)
    return f"{first} {middle} {last}"


def _make_fake_id(seed_key: str, used_ids: set[str], digits: int = 6) -> str:
    rnd = random.Random(_stable_seed_from_key("ID::" + seed_key))
    low = 10**(digits - 1)
    high = (10**digits) - 1

    # نحاول عدة مرات لتجنب التكرار
    for _ in range(10000):
        fake_id = str(rnd.randint(low, high))
        if fake_id not in used_ids:
            used_ids.add(fake_id)
            return fake_id

    raise RuntimeError("Could not generate unique fake_id")


# =========================
# إدارة الـ mapping
# =========================

def load_or_create_mapping(map_path: Path) -> Dict[str, Any]:
    if map_path.exists():
        return _load_json(map_path)

    return {
        "by_real_id": {},
        "by_real_name": {},
        "meta": {
            "description": "Stable pseudonym map for students"
        }
    }


def save_mapping(map_path: Path, mapping: Dict[str, Any]) -> None:
    _save_json(map_path, mapping)


def get_or_create_pseudonym(
    real_id: str,
    real_name: str,
    mapping: Dict[str, Any],
    used_fake_ids: set[str]
) -> Tuple[str, str]:
    real_id = _norm(real_id)
    real_name = _norm(real_name)

    # 1) لو عندي real_id معروف، نعتمد عليه كأساس
    if not _is_unknown(real_id):
        by_id = mapping.setdefault("by_real_id", {})
        if real_id in by_id:
            entry = by_id[real_id]
            return entry["fake_id"], entry["fake_name"]

        seed_key = f"RID::{real_id}"
        fake_id = _make_fake_id(seed_key, used_fake_ids)
        fake_name = _make_fake_name(seed_key)

        by_id[real_id] = {
            "real_name": real_name if real_name else "[UNK]",
            "fake_id": fake_id,
            "fake_name": fake_name,
        }
        return fake_id, fake_name

    # 2) إذا الـ id مجهول لكن الاسم معروف، استخدمي الاسم
    if not _is_unknown(real_name):
        by_name = mapping.setdefault("by_real_name", {})
        if real_name in by_name:
            entry = by_name[real_name]
            return entry["fake_id"], entry["fake_name"]

        seed_key = f"RNAME::{real_name}"
        fake_id = _make_fake_id(seed_key, used_fake_ids)
        fake_name = _make_fake_name(seed_key)

        by_name[real_name] = {
            "fake_id": fake_id,
            "fake_name": fake_name,
        }
        return fake_id, fake_name

    # 3) لو الاثنين مجهولين
    return "[UNK]", "[UNK]"


def collect_used_fake_ids(mapping: Dict[str, Any]) -> set[str]:
    used = set()

    for v in mapping.get("by_real_id", {}).values():
        fid = _norm(v.get("fake_id"))
        if fid and fid != "[UNK]":
            used.add(fid)

    for v in mapping.get("by_real_name", {}).values():
        fid = _norm(v.get("fake_id"))
        if fid and fid != "[UNK]":
            used.add(fid)

    return used


# =========================
# anonymize single student object
# =========================

def anonymize_student_obj(obj: Dict[str, Any], mapping: Dict[str, Any], used_fake_ids: set[str]) -> Dict[str, Any]:
    real_id = _norm(obj.get("student_id", "[UNK]"))
    real_name = _norm(obj.get("student_name", "[UNK]"))

    fake_id, fake_name = get_or_create_pseudonym(real_id, real_name, mapping, used_fake_ids)

    new_obj = dict(obj)
    if "student_id" in new_obj:
        new_obj["student_id"] = fake_id
    if "student_name" in new_obj:
        new_obj["student_name"] = fake_name

    return new_obj


def anonymize_student_list(items: List[Dict[str, Any]], mapping: Dict[str, Any], used_fake_ids: set[str]) -> List[Dict[str, Any]]:
    out = []
    for item in items:
        out.append(anonymize_student_obj(item, mapping, used_fake_ids))
    return out


# =========================
# attendance_compare report
# =========================

def anonymize_compare_report(report: Dict[str, Any], mapping: Dict[str, Any], used_fake_ids: set[str]) -> Dict[str, Any]:
    out = dict(report)

    # all_present
    if isinstance(out.get("all_present"), list):
        out["all_present"] = anonymize_student_list(out["all_present"], mapping, used_fake_ids)

    # all_sheets
    if isinstance(out.get("all_sheets"), list):
        new_sheets = []
        for sh in out["all_sheets"]:
            new_sh = dict(sh)
            anon = anonymize_student_obj(sh, mapping, used_fake_ids)
            new_sh["student_id"] = anon.get("student_id", "[UNK]")
            new_sh["student_name"] = anon.get("student_name", "[UNK]")
            new_sheets.append(new_sh)
        out["all_sheets"] = new_sheets

    # present_but_missing_sheet
    if isinstance(out.get("present_but_missing_sheet"), list):
        out["present_but_missing_sheet"] = anonymize_student_list(
            out["present_but_missing_sheet"], mapping, used_fake_ids
        )

    # sheet_but_not_marked_present
    if isinstance(out.get("sheet_but_not_marked_present"), list):
        new_items = []
        for item in out["sheet_but_not_marked_present"]:
            new_item = dict(item)
            anon = anonymize_student_obj(item, mapping, used_fake_ids)
            new_item["student_id"] = anon.get("student_id", "[UNK]")
            # غالبًا هذا الجزء لا يحتوي student_name أصلاً
            if "student_name" in new_item:
                new_item["student_name"] = anon.get("student_name", "[UNK]")
            new_items.append(new_item)
        out["sheet_but_not_marked_present"] = new_items

    # duplicates
    if isinstance(out.get("duplicates"), list):
        new_dups = []
        for item in out["duplicates"]:
            new_item = dict(item)
            anon = anonymize_student_obj(item, mapping, used_fake_ids)
            new_item["student_id"] = anon.get("student_id", "[UNK]")
            new_dups.append(new_item)
        out["duplicates"] = new_dups

    # unidentified_sheets غالبًا لا يحتاج تغيير لأنه لا يحتوي student data
    return out


# =========================
# ملفات sheet_identifiers
# =========================

def anonymize_sheet_identifiers_under_output(
    out_root: Path,
    extraction_dir: str,
    mapping: Dict[str, Any],
    used_fake_ids: set[str],
    overwrite: bool = False
) -> None:
    for d in sorted([x for x in out_root.iterdir() if x.is_dir() and not x.name.startswith("_")]):
        ident_path = d / extraction_dir / "sheet_identifiers.json"
        if not ident_path.exists():
            continue

        obj = _load_json(ident_path)

        anon = anonymize_student_obj(obj, mapping, used_fake_ids)

        if overwrite:
            target = ident_path
        else:
            target = d / extraction_dir / "sheet_identifiers_anonymized.json"

        _save_json(target, anon)


# =========================
# ملفات attendance reports
# =========================

def anonymize_reports(
    reports_dir: Path,
    mapping: Dict[str, Any],
    used_fake_ids: set[str],
    overwrite: bool = False
) -> None:
    present_path = reports_dir / "attendance_present.json"
    compare_path = reports_dir / "attendance_compare.json"

    if present_path.exists():
        present_obj = _load_json(present_path)
        present_list = present_obj.get("present", [])
        if not isinstance(present_list, list):
            present_list = []
        anon_present = {
            "present": anonymize_student_list(present_list, mapping, used_fake_ids)
        }

        target = present_path if overwrite else reports_dir / "attendance_present_anonymized.json"
        _save_json(target, anon_present)

    if compare_path.exists():
        compare_obj = _load_json(compare_path)
        anon_compare = anonymize_compare_report(compare_obj, mapping, used_fake_ids)

        target = compare_path if overwrite else reports_dir / "attendance_compare_anonymized.json"
        _save_json(target, anon_compare)


# =========================
# main
# =========================

def main():
    import argparse

    p = argparse.ArgumentParser()
    p.add_argument("--out_root", default="data/output")
    p.add_argument("--extraction_dir", default="answers")
    p.add_argument("--map_file", default="data/output/_reports/student_pseudonym_map.json")
    p.add_argument("--overwrite", action="store_true", help="overwrite original files instead of creating anonymized copies")
    args = p.parse_args()

    out_root = Path(args.out_root)
    reports_dir = out_root / "_reports"
    map_path = Path(args.map_file)

    mapping = load_or_create_mapping(map_path)
    used_fake_ids = collect_used_fake_ids(mapping)

    anonymize_sheet_identifiers_under_output(
        out_root=out_root,
        extraction_dir=args.extraction_dir,
        mapping=mapping,
        used_fake_ids=used_fake_ids,
        overwrite=args.overwrite,
    )

    anonymize_reports(
        reports_dir=reports_dir,
        mapping=mapping,
        used_fake_ids=used_fake_ids,
        overwrite=args.overwrite,
    )

    save_mapping(map_path, mapping)
    print("✅ Anonymization completed.")
    print("Map saved to:", map_path)


if __name__ == "__main__":
    main()