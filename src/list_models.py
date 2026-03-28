#!/usr/bin/env python3
"""List available Gemini models"""

import os
from google import genai

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    print("Error: GEMINI_API_KEY not set")
    exit(1)

client = genai.Client(api_key=api_key)

print("Available models:")
print("=" * 60)

try:
    models = client.models.list()
    for model in models:
        print(f"- {model.name}")
        if hasattr(model, 'supported_generation_methods'):
            print(f"  Methods: {', '.join(model.supported_generation_methods)}")
except Exception as e:
    print(f"Error listing models: {e}")
