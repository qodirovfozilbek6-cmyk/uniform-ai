# UNIFORM AI

AI-powered school-uniform portrait editor. Upload a portrait, choose a uniform style, generate a 3:4 result, and download it.

## Architecture
- FastAPI + responsive HTML/CSS/JavaScript frontend on Render
- Google Gemini API image editing using Nano Banana 2.1 (`gemini-nano-banana-2.1`) through the Interactions API
- Pillow image validation, 3:4 crop, and output formatting

## Important limitations
- Gemini image generation/editing has no free API tier. Check the current official pricing before enabling paid billing: https://ai.google.dev/gemini-api/docs/pricing/
- The current Standard price shown for Nano Banana 2 is approximately $0.0336 per 1K output image, plus input usage. The exact current price and tiers are listed on Google's pricing page. Actual cost depends on model, output size, and current pricing.
- Generative editing cannot guarantee pixel-identical identity preservation. The prompt asks Gemini to change clothing only and preserve the face, but always compare the result with the original photo.
- Keep the API key private. Never put it in GitHub, frontend JavaScript, or chat.
- Before making this service public, add stronger abuse protection and monitor usage. A public endpoint can consume API credits.

## 1. Get a Gemini API key
Create a key in Google AI Studio: https://aistudio.google.com/apikey

## 2. Configure billing carefully
Image generation with this model is not available on the free API tier. A Google Cloud Billing account must be linked to the AI Studio project to use the paid tier. Review the billing terms and costs with a parent or guardian before enabling payment. Set a project monthly spend cap where available, and monitor Dashboard > Usage and Billing. Spend caps can have a short enforcement delay, so they are not an absolute instant stop.

Google's billing setup guide: https://aistudio.google.com/docs/get-started

## 3. Deploy on Render
Create or use a Python web service:
- Build command: `pip install -r requirements.txt`
- Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`

Add these Render environment variables:
- `GEMINI_API_KEY`: your private Google AI Studio API key
- `GEMINI_MODEL`: `gemini-nano-banana-2.1`
- `GEMINI_TIMEOUT_SECONDS`: `150`
- `MAX_UPLOAD_MB`: `10`

Do not add the API key to GitHub or the browser. Render injects it into the server process.

## Run locally
1. Python 3.11+
2. `python -m venv .venv`
3. Activate the environment.
4. `pip install -r requirements.txt`
5. Set the environment variables above.
6. `uvicorn app.main:app --reload`

Open http://127.0.0.1:8000

## Privacy
The server processes the upload in memory and sends the image to Google's Gemini API for editing. Do not upload a photo unless you have permission to use it. Review Google's current API data-use and privacy terms before use.

## API
- GET `/api/health`
- POST `/api/generate` multipart fields: `image`, `style`
