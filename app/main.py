import base64
import io
import os
from typing import Annotated

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from PIL import Image, ImageOps, UnidentifiedImageError

load_dotenv()
app = FastAPI(title="UNIFORM AI", version="2.0.0")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.1-flash-image").strip()
GEMINI_TIMEOUT = float(os.getenv("GEMINI_TIMEOUT_SECONDS", "150"))
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
STYLES = {
    "classic": "classic neat school uniform: a clean white shirt with a dark navy blazer or cardigan, understated and realistic",
    "modern": "modern school uniform: a crisp light shirt with a tasteful dark navy jacket and a simple coordinated tie",
    "formal": "formal school uniform: a white collared shirt, dark tailored blazer and a simple conservative tie",
}


def prepare_image(raw: bytes) -> Image.Image:
    try:
        image = Image.open(io.BytesIO(raw))
        image = ImageOps.exif_transpose(image).convert("RGB")
    except (UnidentifiedImageError, OSError):
        raise HTTPException(status_code=400, detail="Rasm faylini o'qib bo'lmadi.")

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

    return ImageOps.fit(image, (768, 1024), method=Image.Resampling.LANCZOS)


def extract_generated_image(payload: dict) -> bytes:
    candidates = payload.get("candidates") or []
    for candidate in candidates:
        parts = (candidate.get("content") or {}).get("parts") or []
        for part in parts:
            inline = part.get("inlineData") or part.get("inline_data")
            if inline and inline.get("data"):
                return base64.b64decode(inline["data"], validate=True)
    raise ValueError("Gemini response did not contain an image.")


@app.get("/api/health")
async def health():
    return {
        "status": "ok",
        "service": "uniform-ai",
        "provider": "google-gemini",
        "model": GEMINI_MODEL,
        "configured": bool(GEMINI_API_KEY),
    }


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
    if not GEMINI_API_KEY:
        raise HTTPException(status_code=503, detail="Gemini API kaliti sozlanmagan. Render Environment'da GEMINI_API_KEY kiriting.")

    original = prepare_image(raw)
    source = io.BytesIO()
    original.save(source, format="PNG", optimize=True)
    encoded = base64.b64encode(source.getvalue()).decode("ascii")

    prompt = (
        "Edit the supplied portrait photo into a realistic school-uniform portrait. "
        f"Uniform style: {STYLES[style]}. "
        "Preserve the same person and make the smallest possible edit. "
        "Keep the person's face, facial features, identity, expression, hairstyle, ears, "
        "skin tone, head position, body proportions, hands, pose, camera angle, background "
        "and lighting unchanged. Change clothing only. Do not beautify, retouch, age, "
        "recreate, or alter the face. Keep the clothing naturally fitted and appropriate "
        "for a school student. Do not add logos, badges, text, or watermarks. "
        "Return one photorealistic edited image in portrait 3:4 composition."
    )

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{GEMINI_MODEL}:generateContent"
    )
    request_body = {
        "contents": [{
            "parts": [
                {"inline_data": {"mime_type": "image/png", "data": encoded}},
                {"text": prompt},
            ]
        }],
        "generationConfig": {
            "responseModalities": ["IMAGE"],
            "imageConfig": {"aspectRatio": "3:4", "imageSize": "1K"},
        },
    }

    try:
        async with httpx.AsyncClient(timeout=GEMINI_TIMEOUT) as client:
            response = await client.post(
                endpoint,
                headers={
                    "x-goog-api-key": GEMINI_API_KEY,
                    "Content-Type": "application/json",
                },
                json=request_body,
            )

        if response.status_code == 429:
            raise HTTPException(status_code=429, detail="Gemini so'rov limiti tugadi. Birozdan keyin qayta urinib ko'ring.")
        if response.status_code in (401, 403):
            raise HTTPException(status_code=502, detail="Gemini API kaliti yoki billing sozlamasini tekshirish kerak.")
        if response.status_code >= 400:
            raise HTTPException(status_code=502, detail="Gemini AI xizmati so'rovni qabul qilmadi. Model va API sozlamalarini tekshiring.")

        try:
            generated_bytes = extract_generated_image(response.json())
            generated = Image.open(io.BytesIO(generated_bytes)).convert("RGB")
        except (ValueError, KeyError, OSError, UnidentifiedImageError):
            raise HTTPException(status_code=502, detail="Gemini javobida tayyor rasm topilmadi. Boshqa surat bilan qayta urinib ko'ring.")

        generated = ImageOps.fit(generated, (768, 1024), method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        generated.save(output, format="JPEG", quality=94, optimize=True)

        return {
            "image": base64.b64encode(output.getvalue()).decode("ascii"),
            "mime_type": "image/jpeg",
            "width": 768,
            "height": 1024,
            "notice": "AI natijasi asl suratdan farq qilishi mumkin. Yuz va boshqa detallarni asl surat bilan solishtiring.",
        }
    except HTTPException:
        raise
    except httpx.TimeoutException as exc:
        raise HTTPException(status_code=504, detail="Gemini javobi kutilgan vaqtda kelmadi. Birozdan keyin qayta urinib ko'ring.") from exc
    except httpx.HTTPError as exc:
        raise HTTPException(status_code=502, detail="Gemini xizmatiga ulanib bo'lmadi. Keyinroq qayta urinib ko'ring.") from exc


app.mount("/", StaticFiles(directory="static", html=True), name="static")
