from __future__ import annotations

import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set


# =========================================================
# عدلي المسارات فقط
# =========================================================

TRAIN_FOLDER = Path(
    r"C:\Users\hp\Desktop\tr"
)

TEST_FOLDER = Path(
    r"C:\Users\hp\Desktop\ts"
)

OUTPUT_REPORT = Path(
    r"C:\Users\hp\Desktop\018_Final\data\train_test_overlap_report.txt"
)

# True يعني البحث داخل المجلدات الفرعية أيضًا
RECURSIVE = True

# جميع أنواع الملفات التي تريدين فحصها
ALLOWED_EXTENSIONS = {
    ".pdf",
    ".png",
    ".jpg",
    ".jpeg",
    ".txt",
    ".json",
    ".xlsx",
}


# =========================================================
# استخراج رقم الجلوس
# =========================================================

def extract_student_id(filename: str) -> str | None:
    """
    يستخرج أول 6 أرقام من بداية اسم الملف.

    أمثلة:
        184006_letters__sheet_001.pdf -> 184006
        184006__sheet_001.pdf         -> 184006
        184006mix__sheet_001.pdf      -> 184006

    إذا لم يبدأ الاسم بستة أرقام، يرجع None.
    """
    name = Path(filename).name.strip()

    match = re.match(r"^(\d{6})", name)
    if not match:
        return None

    return match.group(1)


# =========================================================
# جمع الملفات حسب رقم الجلوس
# =========================================================

def collect_files_by_student(
    folder: Path,
) -> tuple[Dict[str, List[Path]], List[Path]]:
    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    pattern = "**/*" if RECURSIVE else "*"

    students: Dict[str, List[Path]] = defaultdict(list)
    invalid_files: List[Path] = []

    for file_path in sorted(folder.glob(pattern)):
        if not file_path.is_file():
            continue

        if ALLOWED_EXTENSIONS and file_path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        student_id = extract_student_id(file_path.name)

        if student_id is None:
            invalid_files.append(file_path)
            continue

        students[student_id].append(file_path)

    return dict(students), invalid_files


# =========================================================
# اكتشاف التكرار داخل المجموعة نفسها
# =========================================================

def find_internal_duplicates(
    files_by_student: Dict[str, List[Path]],
) -> Dict[str, List[Path]]:
    """
    يعرض أرقام الجلوس التي ظهرت في أكثر من ملف داخل نفس المجموعة.

    قد يكون هذا طبيعيًا إذا كان لكل طالب عدة ملفات،
    لكنه مفيد للمراجعة.
    """
    return {
        student_id: paths
        for student_id, paths in files_by_student.items()
        if len(paths) > 1
    }


# =========================================================
# بناء التقرير
# =========================================================

def relative_or_full(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def build_report(
    train_students: Dict[str, List[Path]],
    test_students: Dict[str, List[Path]],
    train_invalid: List[Path],
    test_invalid: List[Path],
) -> str:
    train_ids: Set[str] = set(train_students)
    test_ids: Set[str] = set(test_students)

    overlap_ids = sorted(train_ids & test_ids)
    train_only_ids = sorted(train_ids - test_ids)
    test_only_ids = sorted(test_ids - train_ids)

    train_file_count = sum(len(paths) for paths in train_students.values())
    test_file_count = sum(len(paths) for paths in test_students.values())

    train_duplicates = find_internal_duplicates(train_students)
    test_duplicates = find_internal_duplicates(test_students)

    lines: List[str] = []

    lines.append("TRAIN / TEST OVERLAP CHECK")
    lines.append("=" * 80)
    lines.append("")

    lines.append("SUMMARY")
    lines.append("-" * 80)
    lines.append(f"Train folder: {TRAIN_FOLDER}")
    lines.append(f"Test folder:  {TEST_FOLDER}")
    lines.append("")
    lines.append(f"Train files with valid IDs: {train_file_count}")
    lines.append(f"Test files with valid IDs:  {test_file_count}")
    lines.append(f"Unique train students:      {len(train_ids)}")
    lines.append(f"Unique test students:       {len(test_ids)}")
    lines.append(f"Overlapping student IDs:    {len(overlap_ids)}")
    lines.append("")

    if overlap_ids:
        lines.append("FINAL STATUS: LEAKAGE DETECTED")
        lines.append(
            "The same student ID appears in both the training and test sets."
        )
    else:
        lines.append("FINAL STATUS: PASS")
        lines.append(
            "No student ID appears in both the training and test sets."
        )

    lines.append("")

    lines.append("OVERLAPPING STUDENTS")
    lines.append("-" * 80)

    if not overlap_ids:
        lines.append("None")
    else:
        for student_id in overlap_ids:
            lines.append(f"Student ID: {student_id}")

            lines.append("  Train file(s):")
            for path in train_students[student_id]:
                lines.append(
                    f"    - {relative_or_full(path, TRAIN_FOLDER)}"
                )

            lines.append("  Test file(s):")
            for path in test_students[student_id]:
                lines.append(
                    f"    - {relative_or_full(path, TEST_FOLDER)}"
                )

            lines.append("")

    lines.append("")
    lines.append("TRAIN-ONLY STUDENTS")
    lines.append("-" * 80)
    lines.append(
        ", ".join(train_only_ids) if train_only_ids else "None"
    )

    lines.append("")
    lines.append("")
    lines.append("TEST-ONLY STUDENTS")
    lines.append("-" * 80)
    lines.append(
        ", ".join(test_only_ids) if test_only_ids else "None"
    )

    lines.append("")
    lines.append("")
    lines.append("FILES WITHOUT A VALID SIX-DIGIT ID")
    lines.append("-" * 80)

    lines.append(f"Train invalid files: {len(train_invalid)}")
    for path in train_invalid:
        lines.append(
            f"  - {relative_or_full(path, TRAIN_FOLDER)}"
        )

    lines.append("")
    lines.append(f"Test invalid files: {len(test_invalid)}")
    for path in test_invalid:
        lines.append(
            f"  - {relative_or_full(path, TEST_FOLDER)}"
        )

    lines.append("")
    lines.append("")
    lines.append("REPEATED IDs INSIDE TRAIN")
    lines.append("-" * 80)

    if not train_duplicates:
        lines.append("None")
    else:
        for student_id, paths in sorted(train_duplicates.items()):
            lines.append(
                f"{student_id}: {len(paths)} files"
            )
            for path in paths:
                lines.append(
                    f"  - {relative_or_full(path, TRAIN_FOLDER)}"
                )

    lines.append("")
    lines.append("")
    lines.append("REPEATED IDs INSIDE TEST")
    lines.append("-" * 80)

    if not test_duplicates:
        lines.append("None")
    else:
        for student_id, paths in sorted(test_duplicates.items()):
            lines.append(
                f"{student_id}: {len(paths)} files"
            )
            for path in paths:
                lines.append(
                    f"  - {relative_or_full(path, TEST_FOLDER)}"
                )

    lines.append("")
    lines.append("")
    lines.append("END OF REPORT")

    return "\n".join(lines)


# =========================================================
# التشغيل
# =========================================================

def main() -> None:
    train_students, train_invalid = collect_files_by_student(
        TRAIN_FOLDER
    )
    test_students, test_invalid = collect_files_by_student(
        TEST_FOLDER
    )

    report = build_report(
        train_students=train_students,
        test_students=test_students,
        train_invalid=train_invalid,
        test_invalid=test_invalid,
    )

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_REPORT.write_text(report, encoding="utf-8")

    overlap_ids = sorted(
        set(train_students) & set(test_students)
    )

    print("=" * 70)
    print("TRAIN / TEST OVERLAP CHECK")
    print("=" * 70)
    print(f"Unique train students: {len(train_students)}")
    print(f"Unique test students:  {len(test_students)}")
    print(f"Overlap count:         {len(overlap_ids)}")

    if overlap_ids:
        print("\n❌ DATA LEAKAGE DETECTED")
        print("Student IDs appearing in both sets:")
        for student_id in overlap_ids:
            print(f"- {student_id}")
    else:
        print("\n✅ PASS: No overlapping student IDs found.")

    print(f"\nReport saved to:\n{OUTPUT_REPORT}")


if __name__ == "__main__":
    main()