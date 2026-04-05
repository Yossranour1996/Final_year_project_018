# scripts/attendance_compare_onefile.py
from __future__ import annotations

import os
import json
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

ATTENDANCE_PROMPT = """You are extracting PRESENT students from an Arabic scanned attendance sheet.
Return ONLY valid JSON (no markdown, no extra text).

Output schema:
{
  "present": [
    {"student_id":"184006", "student_name":"ابراهيم عبد العال محمد"},
    ...
  ]
}

Rules:
- A student is PRESENT if the signature cell (الإمضاء) for that row contains handwriting/ink marks (not empty).
- Usually a present row has: student_id + student_name + signature.
- Sometimes a student is added manually: id + signature exist but name is missing → set student_name to "[UNK]".
- Ignore supervisor/proctor names and any notes outside the table.
- If you are unsure about a digit in the student_id, use "[UNK]" but still include the row if signature exists.
- Return exactly one JSON object only.
"""


def _safe_json_load(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    i = t.find("{")
    j = t.rfind("}")
    if i == -1 or j == -1 or j <= i:
        raise ValueError(f"Gemini did not return JSON. Got:\n{t[:800]}")
    return json.loads(t[i:j+1])


def _gemini_json_from_image(image_path: str, prompt: str) -> Dict[str, Any]:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY env var. Put it in .env")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

    img_path = Path(image_path)
    data = img_path.read_bytes()
    mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

    client = genai.Client(api_key=api_key)
    resp = client.models.generate_content(
        model=model_name,
        contents=[prompt, types.Part.from_bytes(data=data, mime_type=mime)],
    )
    return _safe_json_load(resp.text or "")


def _pdf_to_first_image(pdf_path: str, out_dir: str, dpi: int = 300) -> str:
    from pdf2image import convert_from_path
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(pdf_path, dpi=dpi)
    if not pages:
        raise ValueError("PDF has no pages")
    img_path = out / "attendance_page_01.png"
    pages[0].save(img_path, "PNG")
    return str(img_path)

def _read_sheet_identifiers(out_root: str, extraction_dir: str = "answers") -> List[Dict[str, Any]]:
    root = Path(out_root)
    sheets: List[Dict[str, Any]] = []

    for d in sorted([x for x in root.iterdir() if x.is_dir() and not x.name.startswith("_")]):
        ident_path = d / extraction_dir / "sheet_identifiers.json"
        if not ident_path.exists():
            continue

        try:
            obj = json.loads(ident_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        # ✅ يدعم الشكل الجديد (بدون best)
        if "student_id" in obj:
            sid = str(obj.get("student_id", "[UNK]")).strip()
            sname = str(obj.get("student_name", "[UNK]")).strip()
        else:
            # دعم احتياطي للشكل القديم
            best = obj.get("best") or {}
            sid = str(best.get("student_id", "[UNK]")).strip()
            sname = str(best.get("student_name", "[UNK]")).strip()

        sheets.append({
            "sheet_id": d.name,
            "student_id": sid if sid else "[UNK]",
            "student_name": sname if sname else "[UNK]",
            "ident_path": str(ident_path),
        })

    return sheets

def _norm_id(x: str) -> str:
    return (x or "").strip()


def compare(present: List[Dict[str, Any]], sheets: List[Dict[str, Any]]) -> Dict[str, Any]:
    present_ids = {_norm_id(p.get("student_id", "")) for p in present if _norm_id(p.get("student_id", ""))}
    present_by_id = { _norm_id(p["student_id"]): p for p in present if _norm_id(p.get("student_id", "")) }

    extracted_by_id: Dict[str, List[str]] = {}
    unidentified_sheets = []

    for sh in sheets:
        sid = _norm_id(sh.get("student_id", ""))
        if not sid or sid == "[UNK]":
            unidentified_sheets.append({"sheet_id": sh["sheet_id"], "flag": "UNIDENTIFIED_SHEET"})
            continue
        extracted_by_id.setdefault(sid, []).append(sh["sheet_id"])

    # حضروا لكن كراساتهم غير موجودة
    present_but_missing_sheet = []
    for sid in sorted(present_ids):
        if sid not in extracted_by_id:
            present_but_missing_sheet.append({
                "student_id": sid,
                "student_name": present_by_id.get(sid, {}).get("student_name"),
                "flag": "PRESENT_BUT_MISSING_SHEET",
            })

    # كراسة موجودة لكن الطالب غير موجود ضمن الحضور (قد يكون غائب أو خطأ استخراج)
    sheet_but_not_present = []
    duplicates = []

    for sid, sh_list in extracted_by_id.items():
        if sid not in present_ids:
            for shid in sh_list:
                sheet_but_not_present.append({
                    "sheet_id": shid,
                    "student_id": sid,
                    "flag": "SHEET_BUT_NOT_MARKED_PRESENT",
                })
        if len(sh_list) > 1:
            duplicates.append({
                "student_id": sid,
                "sheets": sh_list,
                "flag": "DUPLICATE_ID_IN_SHEETS",
            })

    return {
        "counts": {
            "present_total": len(present),
            "sheets_total": len(sheets),
            "present_but_missing_sheet": len(present_but_missing_sheet),
            "sheet_but_not_marked_present": len(sheet_but_not_present),
            "unidentified_sheets": len(unidentified_sheets),
            "duplicates": len(duplicates),
        },
        "present_but_missing_sheet": present_but_missing_sheet,
        "sheet_but_not_marked_present": sheet_but_not_present,
        "unidentified_sheets": unidentified_sheets,
        "duplicates": duplicates,
        "all_present": present,
        "all_sheets": sheets,
    }


def main():
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("--attendance", required=True, help="attendance scan: .png/.jpg/.pdf")
    p.add_argument("--out_root", default="data/output")
    p.add_argument("--extraction_dir", default="answers")
    p.add_argument("--dpi", type=int, default=300)
    args = p.parse_args()

    out_root = Path(args.out_root)
    reports_dir = out_root / "_reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    att_path = Path(args.attendance)
    if not att_path.exists():
        raise FileNotFoundError(att_path)

    # 1) Convert attendance PDF to image if needed
    if att_path.suffix.lower() == ".pdf":
        att_img = _pdf_to_first_image(str(att_path), str(reports_dir), dpi=args.dpi)
    else:
        att_img = str(att_path)

    # 2) Extract present students using LLM
    att_obj = _gemini_json_from_image(att_img, ATTENDANCE_PROMPT)
    present = att_obj.get("present", [])
    if not isinstance(present, list):
        present = []

    (reports_dir / "attendance_present.json").write_text(
        json.dumps({"present": present}, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 3) Load sheet identifiers extracted by Agent A
    sheets = _read_sheet_identifiers(str(out_root), extraction_dir=args.extraction_dir)

    # 4) Compare
    report = compare(present, sheets)
    (reports_dir / "attendance_compare.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    print("✅ Saved:")
    print("-", reports_dir / "attendance_present.json")
    print("-", reports_dir / "attendance_compare.json")
    print("Counts:", report["counts"])


if __name__ == "__main__":
    main() 