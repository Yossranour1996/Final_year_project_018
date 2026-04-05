from __future__ import annotations

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any

from dotenv import load_dotenv
load_dotenv(override=True)

from google import genai
from google.genai import types

from src.tools.openai_vision import (
    extract_json_from_image_gpt4o,
    OpenAIVisionConfig,
)
from src.tools.manual_labeling_tool import build_manual_labeling_file
from src.tools.labeled_answers_to_json import structure_answers_from_manual_labels

# ============================
# PROMPTS
# ============================

IDENTIFIERS_PROMPT = r"""
You are reading the FIRST PAGE of a scanned Arabic exam answer booklet.

Extract ONLY:
- student_id  = the seat number "رقم الجلوس"
- student_name = the handwritten name next to/after the printed label "اسم الطالب/الطالبة" ONLY

Strict rules:
- Do NOT confuse with subject/course names or "اسم ورقة الامتحان".
- Copy EXACT handwriting; do not correct spelling.
- If truly unreadable -> "[UNK]" (do not guess).

Return ONLY JSON:

{
  "student_id": "...",
  "student_name": "..."
}
"""

GEMINI_OCR_PROMPT_ANSWERS_ONLY = """
You are an OCR engine for handwritten exam answer sheets (Arabic/English).

IMPORTANT: Extract ONLY the student's ANSWERS (solutions).
DO NOT extract printed headers, cover fields, margins, stamps, or table headings.

Ignore (do not output) any lines containing these kinds of fields:
- الكلية، القسم، العام الدراسي، المادة، اسم ورقة الامتحان، رقم السؤال
- اسم الطالب/الطالبة، الاسم، رقم الجلوس
- الصفحة X من Y (page numbers)
- any repeated dashed/line separators or empty ruled lines

Keep:
- actual handwritten answers (Arabic/English)
- code-like text, bullet points, lists, formulas

Rules:
- Preserve line breaks.
- Do NOT invent missing words.
- Use [UNK] ONLY if you truly cannot read a specific word/number.
- If there are no student answers on this page, return EMPTY string.

Return plain text only (no markdown).
"""

# ============================
# HELPERS
# ============================

def _safe_json(text: str) -> Dict[str, Any]:
    t = (text or "").strip()
    i = t.find("{")
    j = t.rfind("}")
    if i == -1 or j == -1 or j <= i:
        return {}
    try:
        obj = json.loads(t[i:j + 1])
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _normalize_ident(obj: Dict[str, Any]) -> Dict[str, str]:
    sid = str(obj.get("student_id", "")).strip() or "[UNK]"
    sname = str(obj.get("student_name", "")).strip() or "[UNK]"
    return {"student_id": sid, "student_name": sname}


def _reduce_unk_noise(text: str) -> str:
    if not text:
        return ""
    lines = []
    for line in text.splitlines():
        while "[UNK] [UNK]" in line:
            line = line.replace("[UNK] [UNK]", "[UNK]")
        if line.strip() == "[UNK]":
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _gemini_ocr_answers_only(image_path: str) -> str:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing GEMINI_API_KEY in environment (.env).")

    model_name = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    client = genai.Client(api_key=api_key)

    img_path = Path(image_path)
    data = img_path.read_bytes()
    mime = "image/png" if img_path.suffix.lower() == ".png" else "image/jpeg"

    resp = client.models.generate_content(
        model=model_name,
        contents=[GEMINI_OCR_PROMPT_ANSWERS_ONLY, types.Part.from_bytes(data=data, mime_type=mime)],
    )
    return (resp.text or "").strip()


_HEADER_PATTERNS = [
    r"^\s*الكلية\s*[:：]",
    r"^\s*القسم\s*[:：]",
    r"^\s*التخصص\s*[:：]",
    r"^\s*العام\s*الدراسي\s*[:：]",
    r"^\s*المادة\s*[:：]",
    r"^\s*اسم\s*ورقة\s*الامتحان\s*[:：]",
    r"^\s*رقم\s*السؤال\s*[:：]",
    r"^\s*اسم\s*الطالب(?:ة)?\s*[:：]",
    r"^\s*إسم\s*الطالب(?:ة)?\s*[:：]",
    r"^\s*الاسم\s*[:：]",
    r"^\s*إسم\s*[:：]",
    r"^\s*اسم\s*[:：]",
    r"^\s*رقم\s*الجلوس\s*[:：]",
    r"^\s*الصفحة\s*\d+\s*من\s*\d+",
    r"^\s*page\s*\d+\s*(of|/)\s*\d+",
    r"^\s*إجابة\s*نموذج",
]


def _looks_like_header_or_margin(line: str) -> bool:
    s = (line or "").strip()
    if not s:
        return True

    if re.fullmatch(r"[-–—_\. ]{6,}", s):
        return True

    if len(s) <= 2:
        return True

    if re.search(r"الصفحة\s*\d+\s*من\s*\d+", s):
        return True

    for pat in _HEADER_PATTERNS:
        if re.search(pat, s, flags=re.IGNORECASE):
            return True

    header_keywords = [
        "الكلية", "القسم", "التخصص", "العام الدراسي", "اسم ورقة الامتحان",
        "رقم الجلوس", "اسم الطالب", "اسم الطالبة", "المادة", "رقم السؤال"
    ]
    if any(k in s for k in header_keywords) and len(s) < 80:
        return True

    return False


def _keep_answers_only(text: str) -> str:
    if not text:
        return ""

    lines = []
    for line in text.splitlines():
        if _looks_like_header_or_margin(line):
            continue
        lines.append(line.rstrip())

    cleaned = "\n".join(lines).strip()
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


# ============================
# MAIN
# ============================

def extract_exam_pages(
    pages_dir: str,
    out_dir: str,
    max_pages: int | None = None,
    manual_review: bool = True,
) -> List[Dict[str, Any]]:
    pages_dir = Path(pages_dir)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    images = sorted(
        list(pages_dir.glob("*.png")) +
        list(pages_dir.glob("*.jpg")) +
        list(pages_dir.glob("*.jpeg"))
    )

    if max_pages:
        images = images[:max_pages]

    if not images:
        (out_dir / "sheet_identifiers.json").write_text(
            json.dumps({"student_id": "[UNK]", "student_name": "[UNK]"},
                       ensure_ascii=False, indent=2),
            encoding="utf-8"
        )
        (out_dir / "raw_extraction.json").write_text("[]", encoding="utf-8")
        return []

    # 1) Extract identifiers ONLY from first page using GPT-4o
    cfg = OpenAIVisionConfig(model="gpt-4o", temperature=0.0)

    first_page = images[0]
    print(f"🪪 Extracting ID/Name (first page only) -> {first_page.name}")

    raw = extract_json_from_image_gpt4o(str(first_page), IDENTIFIERS_PROMPT, cfg=cfg)
    ident = _normalize_ident(_safe_json(raw))

    (out_dir / "sheet_identifiers.json").write_text(
        json.dumps(ident, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 2) OCR all pages
    results: List[Dict[str, Any]] = []

    for img_path in images:
        print(f"🧠 Gemini OCR (answers only) -> {img_path.name}")

        text = _gemini_ocr_answers_only(str(img_path))
        text = _reduce_unk_noise(text)
        text = _keep_answers_only(text)

        (out_dir / f"{img_path.stem}.txt").write_text(text, encoding="utf-8")
        results.append({"page": img_path.name, "text": text})

    (out_dir / "raw_extraction.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )

    # 3) Create manual labeling file
    manual_label_path = build_manual_labeling_file(
        extraction_dir=str(out_dir),
        out_label_path=str(out_dir / "manual_labels.txt"),
    )

    print(f"📝 Manual labeling file created -> {manual_label_path}")

    # 4) Human in the loop: user edits and confirms
    if manual_review:
        print("\n" + "=" * 80)
        print("HUMAN REVIEW REQUIRED")
        print("=" * 80)
        print(f"Open this file and label the answers manually:\n{manual_label_path}")
        print('Use exact format like: "1.1" answer text "1.1" slach')
        print("After saving the file, return here and press Enter to continue...")
        input()

    # 5) Build structured answers from manual labels
    structured_path = out_dir / "structured_answers.json"
    structure_answers_from_manual_labels(
        label_file_path=str(manual_label_path),
        out_json_path=str(structured_path),
    )
    print(f"✅ Structured answers saved -> {structured_path}")

    return results