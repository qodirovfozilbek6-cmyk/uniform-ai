import base64
import io

import gradio as gr
import spaces
import torch
from diffusers import StableDiffusionXLInpaintPipeline
from PIL import Image, ImageDraw, ImageFilter, ImageOps

MODEL_ID = "diffusers/stable-diffusion-xl-1.0-inpainting-0.1"
STYLES = {
    "classic": "a neat classic school uniform, crisp white button-up shirt, dark navy blazer, modest dark school tie",
    "modern": "a modern school uniform, crisp white shirt, elegant navy cardigan, simple modest school tie",
    "formal": "a formal school uniform, white shirt, structured dark navy jacket, restrained school tie",
}

# ZeroGPU requires model initialization at module scope.
pipe = StableDiffusionXLInpaintPipeline.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.float16,
    variant="fp16",
    use_safetensors=True,
).to("cuda")


def make_mask(size):
    width, height = size
    mask = Image.new("L", size, 0)
    draw = ImageDraw.Draw(mask)
    # White = editable; black = protected. The face, hair and head stay outside.
    polygon = [
        (int(width * 0.08), int(height * 0.49)),
        (int(width * 0.22), int(height * 0.42)),
        (int(width * 0.78), int(height * 0.42)),
        (int(width * 0.92), int(height * 0.49)),
        (int(width * 0.98), int(height * 0.98)),
        (int(width * 0.02), int(height * 0.98)),
    ]
    draw.polygon(polygon, fill=255)
    return mask.filter(ImageFilter.GaussianBlur(radius=3))


@spaces.GPU(duration=120)
def generate(image, style):
    if image is None:
        raise gr.Error("Avval portret rasmini yuklang.")

    image = ImageOps.exif_transpose(image).convert("RGB")
    image = ImageOps.fit(image, (768, 1024), method=Image.Resampling.LANCZOS)
    mask = make_mask(image.size)

    prompt = (
        "Photorealistic portrait photo of the same person wearing "
        + STYLES[style]
        + ". Preserve the person's original identity, face, facial features, "
        "expression, skin tone, hairstyle, head shape and pose. Only replace "
        "the clothing inside the white mask. Keep all black-mask areas unchanged. "
        "Natural fabric folds, realistic tailoring, modest school-appropriate outfit, "
        "plain clothing without logos, text, badges or watermark."
    )
    negative_prompt = (
        "different person, changed face, altered eyes, altered nose, altered mouth, "
        "different hairstyle, extra fingers, distorted hands, text, logo, watermark, "
        "cartoon, illustration, blurry, low quality, revealing clothing"
    )

    with torch.inference_mode():
        result = pipe(
            prompt=prompt,
            negative_prompt=negative_prompt,
            image=image,
            mask_image=mask,
            num_inference_steps=24,
            guidance_scale=7.0,
            strength=0.98,
        ).images[0]

    result = ImageOps.fit(result.convert("RGB"), (768, 1024), method=Image.Resampling.LANCZOS)
    buffer = io.BytesIO()
    result.save(buffer, format="JPEG", quality=93, optimize=True)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


demo = gr.Interface(
    fn=generate,
    inputs=[
        gr.Image(type="pil", label="Portret"),
        gr.Dropdown(
            choices=[
                ("Klassik", "classic"),
                ("Zamonaviy", "modern"),
                ("Rasmiy", "formal"),
            ],
            value="classic",
            label="Forma uslubi",
        ),
    ],
    outputs=gr.Textbox(label="Natija (Base64)", visible=False),
    api_name="generate",
    title="UNIFORM AI Engine",
    description="Hugging Face ZeroGPU asosidagi maktab formasi inpainting servisi.",
    flagging_mode="never",
)

demo.queue(default_concurrency_limit=1).launch()
