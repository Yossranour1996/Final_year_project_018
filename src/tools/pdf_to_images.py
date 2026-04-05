# src/tools/pdf_to_images.py
from __future__ import annotations
from pathlib import Path
from pdf2image import convert_from_path

def pdf_to_images(pdf_path: str, out_dir: str, dpi: int = 300, max_pages: int = 0) -> list[str]:
    pdf_path = Path(pdf_path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    pages = convert_from_path(str(pdf_path), dpi=dpi)
    if max_pages and max_pages > 0:
        pages = pages[:max_pages]

    out_paths = []
    for i, img in enumerate(pages, start=1):
        p = out_dir / f"page_{i:02d}.png"
        img.save(p, "PNG")
        out_paths.append(str(p))
    return out_paths