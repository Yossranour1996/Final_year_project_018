from __future__ import annotations

import re
import csv
from pathlib import Path
from typing import Dict, List, Tuple, Optional

import pdfplumber


# ========= عدلي هذه المسارات =========
# SHEETS_FOLDER = r"C:\Users\hp\Desktop\sheets_folder"
# GRADES_PDF = r"C:\Users\hp\Desktop\final_marks.pdf"
# OUTPUT_CSV = r"C:\Users\hp\Desktop\sheet_marks.csv"
# # =====================================
SHEETS_FOLDER = r"C:\Users\hp\Downloads\drive-download-20260627T142559Z-3-001"
GRADES_PDF = r"C:/Users/hp/Downloads/Java_exam_final_marks.pdf"
OUTPUT_CSV = r"C:/Users/hp/Desktop/sheet_marks.csv"


def extract_index_and_sheetnum(filename: str) -> Optional[Tuple[str, str]]:
    """
    يتوقع اسم ملف مثل:
    184006__sheet_001.pdf
    184006_abc__sheet_12.pdf
    184006-mix__sheet_7.pdf

    يأخذ:
    - index = كل ما قبل __sheet_
    - sheet_num = الرقم بعد __sheet_
    """
    name = Path(filename).stem  # بدون .pdf
    m = re.match(r"^(.*?)__sheet_(\d+)$", name, flags=re.IGNORECASE)
    if not m:
        return None

    raw_index = m.group(1).strip()
    sheet_num = m.group(2).strip()

    # نأخذ أول رقم طويل داخل الجزء الأول كـ student index
    idx_match = re.search(r"(\d{4,})", raw_index)
    if not idx_match:
        return None

    student_index = idx_match.group(1)
    return student_index, sheet_num


def parse_marks_pdf(pdf_path: str) -> Dict[str, str]:
    """
    يقرأ PDF الدرجات ويحاول استخراج:
    index -> final mark

    يعتمد على وجود نص داخل الـ PDF.
    إذا كان الـ PDF عبارة عن صورة ممسوحة فقط، ستحتاجين OCR.
    """
    marks: Dict[str, str] = {}

    with pdfplumber.open(pdf_path) as pdf:
        full_text = []
        for page in pdf.pages:
            text = page.extract_text() or ""
            full_text.append(text)

    text = "\n".join(full_text)

    # نحاول التقاط الأسطر مثل:
    # 1 184006 Ibrahim Abdelal Ibrahim 70
    # 2 184027 Almonzer Ali 87
    #
    # آخر رقم في السطر = Final Mark
    # الرقم الثاني = Index
    for line in text.splitlines():
        line = " ".join(line.split())
        if not line:
            continue

        # تجاهل الهيدر أو السطور غير المفيدة
        if any(word in line.lower() for word in ["java course final marks", "index", "final mark", "name"]):
            continue

        # نبحث عن: رقم ترتيب + index + أي اسم + mark في آخر السطر
        m = re.match(r"^\d+\s+(\d{4,})\s+.+?\s+(\d{1,3})$", line)
        if m:
            idx = m.group(1)
            mark = m.group(2)
            marks[idx] = mark

    return marks


def collect_sheet_files(folder: str) -> List[Tuple[str, str, str]]:
    """
    يرجع قائمة من:
    (filename, student_index, sheet_num)
    """
    rows: List[Tuple[str, str, str]] = []
    for path in Path(folder).glob("*.pdf"):
        parsed = extract_index_and_sheetnum(path.name)
        if parsed is None:
            print(f"Skipped (bad filename format): {path.name}")
            continue

        student_index, sheet_num = parsed
        rows.append((path.name, student_index, sheet_num))

    return rows


def main() -> None:
    marks_map = parse_marks_pdf(GRADES_PDF)
    sheet_files = collect_sheet_files(SHEETS_FOLDER)

    output_rows = []
    unmatched_files = []
    used_indexes = set()

    for filename, student_index, sheet_num in sheet_files:
        mark = marks_map.get(student_index)
        if mark is None:
            unmatched_files.append((filename, student_index, sheet_num))
            continue

        output_rows.append({
            "sheet_num": sheet_num,
            "mark": mark,
        })
        used_indexes.add(student_index)

    # حفظ الملف النهائي
    with open(OUTPUT_CSV, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["sheet_num", "mark"])
        writer.writeheader()
        writer.writerows(sorted(output_rows, key=lambda x: int(x["sheet_num"])))

    print(f"Done. Saved: {OUTPUT_CSV}")
    print(f"Matched sheets: {len(output_rows)}")

    # ملفات لم نجد لها درجة
    if unmatched_files:
        print("\nUnmatched files:")
        for row in unmatched_files:
            print(row)

    # طلاب في PDF لم نجد لهم sheet file
    missing_sheet_for_index = sorted(set(marks_map.keys()) - used_indexes)
    if missing_sheet_for_index:
        print("\nIndexes in PDF but no matching sheet file:")
        for idx in missing_sheet_for_index:
            print(idx)


if __name__ == "__main__":
    main()