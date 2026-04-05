from __future__ import annotations

from pathlib import Path
from typing import List

QUESTION_KEYS = [
    "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7",
    "4.1", "4.2",
]


def build_manual_labeling_file(
    extraction_dir: str,
    out_label_path: str | None = None,
) -> str:
    ext_dir = Path(extraction_dir)
    if not ext_dir.exists():
        raise FileNotFoundError(f"Extraction directory not found: {extraction_dir}")

    txt_files = sorted([
        p for p in ext_dir.glob("*.txt")
        if not p.name.endswith(".labeled.txt")
    ])

    if out_label_path is None:
        out_path = ext_dir / "manual_labels.txt"
    else:
        out_path = Path(out_label_path)

    raw_parts: List[str] = []
    for p in txt_files:
        text = p.read_text(encoding="utf-8").strip()
        if text:
            raw_parts.append(f"\n===== RAW OCR FROM {p.name} =====\n{text}\n")

    raw_ocr_block = "\n".join(raw_parts).strip()

    lines: List[str] = []
    lines.append("MANUAL LABELING FILE")
    lines.append("=" * 80)
    lines.append("")
    lines.append("Instructions:")
    lines.append("1) Put each answer between its opening and closing markers.")
    lines.append('2) Format must be exactly like: with number between quotes and then closed with number between quotes and slach')
    lines.append("3) Leave the block empty if there is no answer.")
    lines.append("4) Do NOT change the question keys.")
    lines.append("5) After editing this file, save it, then return to the terminal and press Enter.")
    lines.append("")

    lines.append("RAW OCR REFERENCE")
    lines.append("=" * 80)
    lines.append(raw_ocr_block if raw_ocr_block else "[No OCR text found]")
    lines.append("")
    lines.append("")
    lines.append("EDITABLE LABEL BLOCKS")
    lines.append("=" * 80)
    lines.append("")

    for qid in QUESTION_KEYS:
        lines.append(f'"{qid}" ')
        lines.append(f'"{qid}/"')
        lines.append("")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text("\n".join(lines).strip() + "\n", encoding="utf-8")

    return str(out_path)