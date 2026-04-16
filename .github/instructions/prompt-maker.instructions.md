---
applyTo: 'src/prompt_maker.py'
description: 'Module for generating and enhancing prompts for Kirsche image generation.'
---

# Prompt Maker

The prompt_make module is responsible for genrateing random promts. It can be included as a library or run as a script.

The core of the generator will be a large gictionary based on four categories: homemaker, exercise, damsel in distress, and snoop. Each category will have four subcategories: clothing, pose, setting, and emotion. Each subcategory will contain a list of 15 relevant words or phrases. The `generate_prompt()` function will randomly select one word or phrase from each subcategory across all categories to create a unique and creative prompt for Kirsche image generation.

When `generate_prompt()` is called, it will randomly select one of the initial categories (homemaker, exercise, damsel in distress, or snoop) and then randomly select one word or phrase from each of the four subcategories (clothing, pose, setting, and emotion) within that category. The selected words or phrases will be combined into a single prompt string that can be used for generating Kirsche images.

The generated prompt will look like this: "A homemaker wearing a floral dress, sitting on a vintage armchair in a cozy living room, looking content." Each prompt will be unique and creative, providing a wide variety of ideas for Kirsche image generation.

## Function

- `generate_prompt()`: This function generates a random prompt by selecting one word or phrase from each subcategory across all categories. It returns the generated prompt as a string.

```python
from prompt_maker import generate_prompt
```

## Script Usage

When run as a script, the `prompt_maker.py` module will generate a random prompt and print it to the console. This allows for quick and easy generation of prompts without needing to import the module into another script. To run the script, use the following command in the terminal:

```bash
python src/prompt_maker.py
```