# UNIFORM AI

AI-powered school uniform portrait studio. Upload a portrait, choose a uniform style, generate a 3:4 result, and download it.

## Core promise
Preserve the original person's recognizable face as carefully as possible. The backend creates a conservative clothing-only edit mask that leaves the head/face region protected. Generative editing can still introduce small differences; exact identity preservation cannot be guaranteed.

## Stack
- FastAPI backend
- Responsive HTML/CSS/JavaScript frontend
- OpenAI image editing API (gpt-image-1)
- Pillow image processing

## Run locally
1. Python 3.11+
2. python -m venv .venv
3. Activate the environment.
4. pip install -r requirements.txt
5. Copy .env.example to .env and set OPENAI_API_KEY.
6. uvicorn app.main:app --reload

Open http://127.0.0.1:8000

## Render
Create a Python web service:
- Build command: pip install -r requirements.txt
- Start command: uvicorn app.main:app --host 0.0.0.0 --port $PORT
- Environment: OPENAI_API_KEY (secret), optionally MAX_UPLOAD_MB=10

## Privacy
Uploaded photos are processed in memory and are not intentionally stored by this application. Do not upload a photo unless you have permission to use it. Avoid uploading sensitive images. Configure provider-side data controls according to your requirements.

## API
- GET /api/health
- POST /api/generate multipart fields: image, style
