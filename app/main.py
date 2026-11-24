import base64
import io
import os
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from openai import OpenAI
from PIL import Image, ImageOps, UnidentifiedImageError

load_dotenv()
app = FastAPI(title="UNIFORM AI", version="1.0.0")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
STYLES = {
    "classic": "a neat classic school uniform: white button-up shirt, dark navy blazer, modest school tie",
    "modern": "a modern school uniform: crisp white shirt, elegant navy cardigan and a simple school tie",
    "formal": "a formal school uniform: white shirt, structured dark navy jacket and a restrained tie",
}


def prepare_image(raw: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Rasm faylini o'qib bo'lmadi.")
    # Center-crop to the requested 3:4 portrait ratio.
    target_ratio = 3 / 4
    width, height = image.size
    if width / height > target_ratio:
        new_width = int(height * target_ratio)
        left = (width - new_width) // 2
        image = image.crop((left, 0, left + new_width, height))
    else:
        new_height = int(width / target_ratio)
        top = (height - new_height) // 2
        image = image.crop((0, top, width, top + new_height))
    image.thumbnail((1024, 1365), Image.Resampling.LANCZOS)
    return image


def clothing_edit_mask(size: tuple[int, int]) -> Image.Image:
    """Transparent pixels are editable; opaque pixels are protected.

    The conservative central torso polygon intentionally excludes the head,
    face, hair and most of the background. It is a safety boundary, not a
    semantic clothing segmentation model.
    """
    width, height = size
    mask = Image.new("RGBA", size, (0, 0, 0, 255))
    alpha = Image.new("L", size, 255)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(alpha)
    polygon = [
        (int(width * 0.12), int(height * 0.34)),
        (int(width * 0.30), int(height * 0.30)),
        (int(width * 0.70), int(height * 0.30)),
        (int(width * 0.88), int(height * 0.34)),
        (int(width * 0.98), int(height * 0.98)),
        (int(width * 0.02), int(height * 0.98)),
    ]
    draw.polygon(polygon, fill=0)
    mask.putalpha(alpha)
    return mask


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "uniform-ai"}


@app.post("/api/generate")
async def generate(
    image: Annotated[UploadFile, File(...)],
    style: Annotated[str, Form()] = "classic",
):
    if image.content_type not in ALLOWED_TYPES:
        raise HTTPException(status_code=415, detail="JPG, PNG yoki WEBP rasm yuklang.")
    if style not in STYLES:
        raise HTTPException(status_code=400, detail="Forma uslubi noto'g'ri.")
    raw = await image.read()
    if not raw:
        raise HTTPException(status_code=400, detail="Rasm tanlanmagan.")
    if len(raw) > MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(status_code=413, detail=f"Rasm hajmi {MAX_UPLOAD_MB} MB dan oshmasin.")

    original = prepare_image(raw)
    mask = clothing_edit_mask(original.size)
    image_buffer = io.BytesIO()
    mask_buffer = io.BytesIO()
    original.save(image_buffer, format="PNG")
    mask.save(mask_buffer, format="PNG")
    image_buffer.seek(0)
    mask_buffer.seek(0)

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=503, detail="AI xizmati sozlanmagan. OPENAI_API_KEY kiriting.")

    prompt = (
        "Edit only the clothing inside the transparent mask. Replace the existing "
        f"clothing with {STYLES[style]}. Keep the person's identity and face exactly "
        "as in the source: do not alter facial features, expression, skin tone, age, "
        "hair, head shape or pose. Do not beautify or retouch the face. Keep all "
        "unmasked pixels unchanged. Photorealistic natural fabric, realistic fit, "
        "modest school-appropriate styling. No logos, text, badges or watermark."
    )
    try:
        client = OpenAI(api_key=api_key)
        result = client.images.edit(
            model="gpt-image-1",
            image=("portrait.png", image_buffer, "image/png"),
            mask=("mask.png", mask_buffer, "image/png"),
            prompt=prompt,
            size="1024x1536",
            quality="high",
        )
        encoded = result.data[0].b64_json
        if not encoded:
            raise RuntimeError("Image provider returned no image data")
        generated = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
        # Enforce exact 3:4 output dimensions.
        generated = ImageOps.fit(generated, (768, 1024), method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        generated.save(output, format="JPEG", quality=94, optimize=True)
        return {
            "image": base64.b64encode(output.getvalue()).decode("ascii"),
            "mime_type": "image/jpeg",
            "width": 768,
            "height": 1024,
            "notice": "AI tahriri yuzni biroz o'zgartirishi mumkin. Natijani asl surat bilan tekshiring.",
        }
    except Exception as exc:
        # Avoid returning provider credentials or internal exception details.
        raise HTTPException(status_code=502, detail="AI rasm yaratishda xatolik yuz berdi. API kaliti va billing holatini tekshiring.") from exc


app.mount("/", StaticFiles(directory="static", html=True), name="static")
