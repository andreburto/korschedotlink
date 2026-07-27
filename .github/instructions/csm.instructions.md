---
applyTo: 'src/character_sheet_maker.py'
description: 'A script to generate new character sheets using the Gemini prompt model.'
---

# Integration Rules

1. Import the `DEFAULT_GEMINI_PROMPT_MODEL` and `DEFAULT_GEMINI_IMAGE_MODEL` from the `korsche_sync` module when defining which models to use in calls to the Gemini API.
2. Use `PROMPT_DATA` from the `prompt_maker.py` module to display all available character types.
3. Use `get_random_reference_image` from `utils.py` to get a random reference image for character sheet generation baseline. 
4. Use environment variables to store any sensitive information such as API keys, and access them securely in the code. Source these environment variables from the `.env.example` file in the project root.
5. When generating content with the Gemini API, specify the model using the imported constants instead of hardcoding model names.

# Workflow

1. Send a request to the Gemini API to generate a new profession for the character sheet using the `DEFAULT_GEMINI_PROMPT_MODEL`. Include the keys from `PROMPT_DATA` to ensure the generated profession do not duplicate existing character types. Ask for a single profession in the response, without any additional text or formatting.
2. Use the given profession and ask the Gemini API to generate a description of the standard outfit for that profession, again using the `DEFAULT_GEMINI_PROMPT_MODEL`. The response should be a single sentence describing the pieces of the outfit, without any additional text or formatting.
3. Get a random reference image using the `get_random_reference_image` function from `scratch.py`. This image will be used as a baseline for the character sheet generation.
4. Send a request to the Gemini API to generate an image of the character sheet using the `DEFAULT_GEMINI_IMAGE_MODEL`. Include the generated profession and outfit description in the prompt, and use the reference image as a visual guide for the generation. The response should be an image that visually represents the character sheet based on the provided profession, outfit description, and reference image.
5. Save the generated character sheet image to the `refs` directory in the project root for further use or display.
