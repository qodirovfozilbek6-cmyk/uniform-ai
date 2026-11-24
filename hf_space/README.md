---
title: UNIFORM AI Engine
emoji: 🎓
colorFrom: blue
colorTo: indigo
sdk: gradio
app_file: app.py
python_version: "3.10"
---

# UNIFORM AI Engine

Private inference backend for the UNIFORM AI website.

## Hardware
Select **ZeroGPU** in the Space Settings. This project uses the `spaces.GPU` decorator and PyTorch Diffusers.

## Model
`diffusers/stable-diffusion-xl-1.0-inpainting-0.1`

## API
The Gradio API endpoint is `/generate`. It accepts a PIL image and one of:
- `classic`
- `modern`
- `formal`

It returns a Base64-encoded JPEG image.

## Notes
ZeroGPU availability and free daily GPU quota are limited. The model can take time to initialize and generate. The inpainting mask is deliberately conservative to protect the head and face, but generated edits cannot guarantee exact identity preservation.
