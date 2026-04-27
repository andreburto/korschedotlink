---
applyTo: 'src/scratch.py'
description: This file describes the app.
---

# Scratch App

This is a prototype app for testing new ideas. It is not intended for production use and may be deleted or refactored in the future.

# Workflow

1. Pick a random image from the `refs` directory, the format can be any image format.
2. Send the prompt "Create an image of Kirsche holding a red balloon. Kirsche is in the attached image."
3. Use the `google-genai` library to generate an image based on the prompt and the reference image.
4. Save the generated image to the `images` directory with a unique filename using uuid4.

# Rules

* Use the `gemini-2.5-flash-image` model from the `google-genai` library for image generation.
* Get the Gemini API key from the `GEMINI_API_KEY` environment variable.
* The generated image should be saved in PNG format with a unique filename generated using `uuid4`.


# Requirements

google-genai
pillow