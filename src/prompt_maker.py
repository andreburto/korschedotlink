#!/usr/bin/env python3
"""
Prompt Generator for Kirsche Pictures

This script generates random prompts for picture generation by selecting
random elements from predefined lists of outfits, locations, activities,
and emotions. The generated prompt is then enhanced using a local Ollama
instance for more creative and detailed results.
"""

import random
import os
from google import genai


# Predefined elements for prompt generation
outfits_elements = [
    "a flowing red dress",
    "a cozy winter jacket",
    "a traditional kimono",
    "casual jeans and a t-shirt",
    "an elegant evening gown",
    "athletic workout gear",
    "a futuristic space suit",
    "a cute summer sundress",
    "a professional business suit",
    "a comfy hoodie and sweatpants",
    "a steampunk outfit with goggles",
    "a vintage 1950s dress",
    "a fantasy warrior armor",
    "a beach swimsuit",
    "a punk rock leather jacket",
    "a magical girl outfit",
    "a bohemian flowing skirt",
    "a cyberpunk neon jacket",
    "a medieval princess gown",
    "pajamas with cute patterns"
]

locations_elements = [
    "a sunny park",
    "the beach at sunset",
    "outer space",
    "a cozy coffee shop",
    "a magical forest",
    "a bustling city street",
    "a snowy mountain peak",
    "an underwater coral reef",
    "a futuristic cityscape",
    "a peaceful garden",
    "an ancient temple",
    "a desert oasis",
    "a floating island in the sky",
    "a Gothic cathedral",
    "a neon-lit arcade",
    "a cherry blossom grove",
    "a steampunk airship",
    "a haunted mansion",
    "a tropical rainforest",
    "a starlit rooftop"
]

activities_elements = [
    "reading a book",
    "painting a canvas",
    "playing video games",
    "stargazing",
    "having a picnic",
    "dancing",
    "practicing martial arts",
    "playing guitar",
    "taking photographs",
    "meditating",
    "baking cookies",
    "flying a kite",
    "exploring ruins",
    "skateboarding",
    "writing in a journal",
    "playing with pets",
    "doing yoga",
    "building a sandcastle",
    "singing karaoke",
    "creating digital art",
    "bound to a railroad track",
    "chained to a tree",
    "tied to a chair",
]

emotions_elements = [
    "joyful",
    "peaceful",
    "excited",
    "contemplative",
    "confident",
    "playful",
    "serene",
    "adventurous",
    "mischievous",
    "proud",
    "inspired",
    "dreamy",
    "energetic",
    "content",
    "curious",
    "determined",
    "whimsical",
    "relaxed",
    "enthusiastic",
    "mysterious"
]


def generate_prompt():
    """
    Generate a random prompt by selecting one element from each category.
    
    Returns:
        str: The generated prompt string
    """
    random.seed()
    outfit = random.choice(outfits_elements)
    location = random.choice(locations_elements)
    activity = random.choice(activities_elements)
    emotion = random.choice(emotions_elements)
    
    prompt = (
        f"Draw a picture of Kirsche wearing {outfit} in {location}. "
        f"She is engaged in {activity} and feeling {emotion}."
    )
    
    print(f"Generated prompt: {prompt}")
    return prompt


def enhance_prompt_with_gemini(prompt, model, api_key):
    """
    Enhance the generated prompt using Google Gemini API.
    
    Args:
        prompt (str): The original prompt to enhance
        model (str): The Gemini model to use for improving the prompt
        api_key (str): The Google API key.
    
    Returns:
        str: The enhanced prompt, or the original prompt if enhancement fails
    """    
    enhancement_instruction = (
        f"You are a creative prompt enhancer. Take the following image generation prompt "
        f"and make it more creative, detailed, and vivid while keeping it PG-rated. "
        f"Maintain the core structure and elements but add artistic details, atmosphere, "
        f"lighting, composition, and style elements. Return ONLY the enhanced prompt, "
        f"nothing else.\n\nOriginal prompt: {prompt}"
    )
    
    # Initialize the Gemini client
    client = genai.Client(api_key=api_key)
    
    # Generate content using the model
    response = client.models.generate_content(model=model, contents=enhancement_instruction)
    
    enhanced_prompt = response.text.strip()
    
    if enhanced_prompt:
        print(f"Prompt enhanced successfully using {model}")
        return enhanced_prompt
    else:
        raise ValueError("Received empty response from Gemini")


def make_new_prompt():
    """Main function to generate, enhance, and save a prompt."""
    # Setup Gemini model and API key
    model = os.getenv("GEMINI_PROMPT_MODEL", "gemini-2.5-flash")
    api_key = os.getenv("GEMINI_API_KEY")
    
    # Generate the base prompt
    prompt = generate_prompt()
    
    # Enhance the prompt using Gemini
    enhanced_prompt = enhance_prompt_with_gemini(prompt, model=model, api_key=api_key)
    
    # Save the enhanced prompt to file
    return enhanced_prompt


if __name__ == "__main__":
    final_prompt = make_new_prompt()
    print(f"Prompt:\n\n{final_prompt}")