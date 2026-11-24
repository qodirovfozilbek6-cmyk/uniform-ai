# UNIFORM AI

AI-powered school uniform portrait studio. Upload a portrait, choose a uniform style, generate a 3:4 result, and download it.

## Architecture
- FastAPI + responsive HTML/CSS/JavaScript frontend on Render
- Hugging Face Gradio Space for image inpainting
- Stable Diffusion XL Inpainting model on Hugging Face ZeroGPU
- Pillow image processing

## Important limitations
Hugging Face ZeroGPU is a limited free demo resource, not unlimited production hosting. Free accounts currently receive up to 5 minutes of GPU time per day, subject to queue availability and account eligibility. A generation may take a substantial portion of that quota. Limits and availability can change.

The model edits only a conservative torso mask to reduce changes to the head and face. Generative editing cannot guarantee pixel-identical identity preservation. Always compare the result with the original photo.

## 1. Create the Hugging Face Space
1. Create or sign in to a Hugging Face account.
2. Create a new **Gradio Space**.
3. Set the Space hardware to **ZeroGPU** in its Settings.
4. Upload the three files from the `hf_space/` folder to the root of the Space:
   - `app.py`
   - `requirements.txt`
   - `README.md`
5. Wait for the Space to build and become **Running**.
6. Copy the Space ID in the form `username/space-name`.

Free ZeroGPU hosting has eligibility requirements, including a verified email and an account at least 30 days old. If the account is not eligible, the Space may not be able to use free ZeroGPU.

## 2. Create a Hugging Face access token
Create a token with **Read** access only. Keep it private. Do not put it in GitHub or share it in chat.

## 3. Deploy the website on Render
Create a Python web service:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Add these Render environment variables:
- `HF_SPACE_ID`: your Space ID, for example `username/uniform-ai-engine`
- `HF_TOKEN`: your private Hugging Face read token
- `MAX_UPLOAD_MB`: `10`

Do not add an OpenAI key. The website calls the Hugging Face Space from the server; the token is never sent to the browser.

## Run locally
1. Python 3.11+
2. `python -m venv .venv`
3. Activate the environment.
4. `pip install -r requirements.txt`
5. Set `HF_SPACE_ID` and `HF_TOKEN` in your environment.
6. `uvicorn app.main:app --reload`

Open http://127.0.0.1:8000

## Privacy
The Render app processes uploads in memory and uses a temporary file that is deleted after the inference request. The image is sent to the Hugging Face Space for processing. Do not upload a photo unless you have permission to use it. Avoid sensitive photos. Review Hugging Face's current privacy and data policies before using the service.

## API
- GET `/api/health`
- POST `/api/generate` multipart fields: `image`, `style`
