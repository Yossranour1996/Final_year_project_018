from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Dict

QUESTION_KEYS = [
    "1.1", "1.2", "1.3", "1.4", "1.5", "1.6", "1.7", "1.8", "1.9", "1.10",
    "2.1", "2.2", "2.3", "2.4", "2.5", "2.6", "2.7",
    "3.1", "3.2", "3.3", "3.4", "3.5", "3.6", "3.7",
    "4.1", "4.2",
]


def _empty_answer_map() -> Dict[str, str]:
    return {qid: "" for qid in QUESTION_KEYS}


def _extract_blocks(text: str) -> Dict[str, str]:
    out: Dict[str, str] = {}

    if not text.strip():
        return out

    for qid in QUESTION_KEYS:
        pattern = rf'"{re.escape(qid)}"\s*(.*?)\s*"{re.escape(qid)}/"'
        m = re.search(pattern, text, flags=re.DOTALL)
        if m:
            ans = m.group(1).strip()
            out[qid] = ans

    return out


def structure_answers_from_manual_labels(
    label_file_path: str,
    out_json_path: str,
) -> Dict[str, str]:
    label_path = Path(label_file_path)
    if not label_path.exists():
        raise FileNotFoundError(f"Manual label file not found: {label_file_path}")

    text = label_path.read_text(encoding="utf-8")
    found = _extract_blocks(text)

    answer_map = _empty_answer_map()
    for qid, ans in found.items():
        answer_map[qid] = ans

    out_path = Path(out_json_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(
        json.dumps(answer_map, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    return answer_map