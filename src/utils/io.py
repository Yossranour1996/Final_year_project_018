# src/utils/io.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict

def read_text(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")

def write_text(path: str, text: str) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")

def read_json(path: str) -> Any:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def write_json(path: str, obj: Any) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
