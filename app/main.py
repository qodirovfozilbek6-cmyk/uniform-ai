import base64
import io
import os
import tempfile
from typing import Annotated

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.staticfiles import StaticFiles
from gradio_client import Client, handle_file
from PIL import Image, ImageOps, UnidentifiedImageError

load_dotenv()
app = FastAPI(title="UNIFORM AI", version="1.1.0")
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "10"))
ALLOWED_TYPES = {"image/jpeg", "image/png", "image/webp"}
STYLES = {"classic", "modern", "formal"}


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

    image = ImageOps.fit(image, (768, 1024), method=Image.Resampling.LANCZOS)
    return image


@app.get("/api/health")
async def health():
    return {"status": "ok", "service": "uniform-ai", "provider": "huggingface-zerogpu"}


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

    space_id = os.getenv("HF_SPACE_ID", "").strip()
    hf_token = os.getenv("HF_TOKEN", "").strip()
    if not space_id or not hf_token:
        raise HTTPException(
            status_code=503,
            detail="Hugging Face xizmati sozlanmagan. HF_SPACE_ID va HF_TOKEN kiriting.",
        )

    original = prepare_image(raw)
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
            original.save(temp_file, format="PNG")
            temp_path = temp_file.name

        client = Client(space_id, hf_token=hf_token, verbose=False)
        encoded = client.predict(
            handle_file(temp_path),
            style,
            api_name="/generate",
        )
        if not isinstance(encoded, str) or not encoded:
            raise RuntimeError("Image provider returned an empty result.")

        generated = Image.open(io.BytesIO(base64.b64decode(encoded))).convert("RGB")
        generated = ImageOps.fit(generated, (768, 1024), method=Image.Resampling.LANCZOS)
        output = io.BytesIO()
        generated.save(output, format="JPEG", quality=94, optimize=True)

        return {
            "image": base64.b64encode(output.getvalue()).decode("ascii"),
            "mime_type": "image/jpeg",
            "width": 768,
            "height": 1024,
            "notice": "AI natijasi asl suratdan biroz farq qilishi mumkin. Yuzni asl surat bilan tekshiring.",
        }
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail="AI servisida xatolik yuz berdi. Hugging Face Space holati, token va kunlik GPU limitini tekshiring.",
        ) from exc
    finally:
        if temp_path and os.path.exists(temp_path):
            os.remove(temp_path)


app.mount("/", StaticFiles(directory="static", html=True), name="static")
