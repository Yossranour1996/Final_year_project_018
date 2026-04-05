from __future__ import annotations

from pathlib import Path
from PIL import Image

def crop_region(image_path: str, out_path: str, box: tuple[float, float, float, float]) -> str:
    """
    Crop region using relative box coordinates (0..1):
      box = (x0, y0, x1, y1)
    """
    p = Path(image_path)
    img = Image.open(p)
    w, h = img.size

    x0, y0, x1, y1 = box
    crop = img.crop((int(w * x0), int(h * y0), int(w * x1), int(h * y1)))

    outp = Path(out_path)
    outp.parent.mkdir(parents=True, exist_ok=True)
    crop.save(outp)
    return str(outp)