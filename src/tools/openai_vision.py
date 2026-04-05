from __future__ import annotations

import base64
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Tuple, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv(override=True)

from PIL import Image, ImageEnhance


@dataclass
class OpenAIVisionConfig:
    model: str = "gpt-4o"
    temperature: float = 0.0
    max_output_tokens: int = 1200


def _client() -> OpenAI:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("Missing OPENAI_API_KEY in .env or environment.")
    return OpenAI(api_key=api_key)


def _encode_image_bytes(img_bytes: bytes, mime: str) -> str:
    b64 = base64.b64encode(img_bytes).decode("utf-8")
    return f"data:{mime};base64,{b64}"


def _enhance_for_handwriting(img: Image.Image) -> Image.Image:
    g = img.convert("L")
    g = ImageEnhance.Contrast(g).enhance(1.8)
    return g.convert("RGB")


def _img_to_bytes(img: Image.Image, fmt: str = "PNG") -> bytes:
    import io
    buf = io.BytesIO()
    img.save(buf, format=fmt)
    return buf.getvalue()


def _clean_ocr_text(text: str) -> str:
    """Remove unwanted refusal/apology boilerplate."""
    if not text:
        return ""
    t = text.strip()

    bad_phrases = [
        "i can't extract",
        "i cannot extract",
        "can't extract",
        "cannot extract",
        "no student answers",
        "no answers",
        "unable to extract",
        "i’m unable",
        "i am unable",
    ]
    low = t.lower()
    # إذا النص كله عبارة عن اعتذار -> رجّع فارغ
    if any(p in low for p in bad_phrases) and len(t) < 120:
        return ""

    # لو فيه سطر اعتذار وسط النص، احذفيه سطر-بسطر
    lines = []
    for line in t.splitlines():
        ll = line.strip().lower()
        if any(p in ll for p in bad_phrases) and len(line.strip()) < 200:
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def _chat_with_image(prompt: str, img_bytes: bytes, mime: str, cfg: OpenAIVisionConfig) -> str:
    client = _client()
    data_url = _encode_image_bytes(img_bytes, mime)

    # 🔒 تعليمات ثابتة تمنع "I can't..." وتفرض empty string لو مافي إجابة
    guard = (
        "Output rules:\n"
        "- Return plain text only.\n"
        "- If there is NO readable student answer text in the image region, return an EMPTY string.\n"
        "- Do NOT output any apologies or explanations like 'I can't extract...'.\n"
        "- Use [UNK] only when you truly cannot read a specific word/number.\n"
    )

    resp = client.chat.completions.create(
        model=cfg.model,
        temperature=cfg.temperature,
        messages=[
            {"role": "system", "content": guard},
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            },
        ],
        max_tokens=cfg.max_output_tokens,
    )
    return _clean_ocr_text((resp.choices[0].message.content or "").strip())


def extract_json_from_image_gpt4o(
    image_path: str,
    prompt: str,
    cfg: Optional[OpenAIVisionConfig] = None,
) -> str:
    cfg = cfg or OpenAIVisionConfig()
    p = Path(image_path)
    img = Image.open(p)
    img = _enhance_for_handwriting(img)
    img_bytes = _img_to_bytes(img, "PNG")
    return _chat_with_image(prompt=prompt, img_bytes=img_bytes, mime="image/png", cfg=cfg)


def _tile_boxes(w: int, h: int, rows: int, cols: int, margin_px: int = 12) -> List[Tuple[int, int, int, int]]:
    boxes = []
    tile_w = w // cols
    tile_h = h // rows
    for r in range(rows):
        for c in range(cols):
            x0 = max(0, c * tile_w - margin_px)
            y0 = max(0, r * tile_h - margin_px)
            x1 = min(w, (c + 1) * tile_w + margin_px)
            y1 = min(h, (r + 1) * tile_h + margin_px)
            boxes.append((x0, y0, x1, y1))
    return boxes


def ocr_image_openai_tiled(
    image_path: str,
    prompt: str,
    rows: int = 3,
    cols: int = 1,
    cfg: Optional[OpenAIVisionConfig] = None,
) -> str:
    cfg = cfg or OpenAIVisionConfig()
    p = Path(image_path)

    img0 = Image.open(p)
    img0 = _enhance_for_handwriting(img0)
    w, h = img0.size
    boxes = _tile_boxes(w, h, rows=rows, cols=cols)

    parts: List[str] = []
    for idx, (x0, y0, x1, y1) in enumerate(boxes, start=1):
        crop = img0.crop((x0, y0, x1, y1))
        crop_bytes = _img_to_bytes(crop, "PNG")

        tile_prompt = (
            prompt
            + f"\n\nTile {idx}/{len(boxes)}: extract ONLY student answers in this tile. "
              "If no answers, return empty string."
        )

        text = _chat_with_image(prompt=tile_prompt, img_bytes=crop_bytes, mime="image/png", cfg=cfg)
        if text:
            parts.append(text)

    merged = "\n".join(parts).strip()
    return merged