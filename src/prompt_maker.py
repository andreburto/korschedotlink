"""
Module for generating and enhancing prompts for Kirsche image generation.

This module provides functionality to generate random creative prompts
based on predefined categories and subcategories of words and phrases.
"""

import random
import sys

from datetime import datetime


# Prompt dictionary organized by category and subcategory
PROMPT_DATA = {
    "homemaker": {
        "clothing": [
            "a floral dress",
            "a vintage apron",
            "a cozy cardigan",
            "a polka dot blouse",
            "a lace-trimmed skirt",
            "a classic housedress",
            "a knitted sweater",
            "a gingham top",
            "a pastel sundress",
            "a ruffled blouse",
            "a pleated skirt",
            "a tailored shirt",
            "a modest dress",
            "a comfortable robe",
            "a checkered apron"
        ],
        "pose": [
            "sitting on a vintage armchair",
            "arranging flowers in a vase",
            "baking in the kitchen",
            "reading a cookbook",
            "setting the dinner table",
            "watering potted plants",
            "folding fresh laundry",
            "stirring a pot on the stove",
            "knitting by the window",
            "dusting furniture",
            "organizing shelves",
            "ironing clothes",
            "pouring tea from a teapot",
            "preparing ingredients",
            "sweeping the floor"
        ],
        "setting": [
            "in a cozy living room",
            "in a bright kitchen",
            "in a sunlit dining room",
            "on a quaint front porch",
            "in a charming garden",
            "in a vintage cottage",
            "by a fireplace",
            "near a bay window",
            "in a traditional home",
            "in a farmhouse kitchen",
            "in a country estate",
            "in a tidy bedroom",
            "in a warm breakfast nook",
            "in a rustic cabin",
            "in a homey space"
        ],
        "emotion": [
            "looking content",
            "smiling warmly",
            "appearing serene",
            "radiating happiness",
            "looking peaceful",
            "seeming satisfied",
            "appearing cheerful",
            "looking relaxed",
            "with a gentle smile",
            "looking focused",
            "appearing proud",
            "seeming joyful",
            "looking calm",
            "radiating warmth",
            "appearing fulfilled"
        ]
    },
    "fitness enthusiast": {
        "clothing": [
            "athletic leggings",
            "a sports bra",
            "running shorts",
            "a moisture-wicking tank top",
            "yoga pants",
            "a fitted workout top",
            "compression shorts",
            "a racerback athletic shirt",
            "training sneakers",
            "a breathable sports outfit",
            "a gym tracksuit",
            "bicycle shorts",
            "a cropped athletic top",
            "workout leggings",
            "a performance top"
        ],
        "pose": [
            "stretching on a yoga mat",
            "running on a treadmill",
            "lifting dumbbells",
            "doing jumping jacks",
            "performing a plank",
            "cycling on a stationary bike",
            "practicing yoga poses",
            "doing squats",
            "jumping rope",
            "using resistance bands",
            "exercising with kettlebells",
            "doing lunges",
            "performing push-ups",
            "using a rowing machine",
            "stretching arms overhead"
        ],
        "setting": [
            "in a modern gym",
            "at a fitness studio",
            "in a home workout room",
            "at an outdoor park",
            "on a running track",
            "in a yoga studio",
            "at a CrossFit box",
            "on a beach",
            "in a training facility",
            "at a sports center",
            "in a bright exercise room",
            "on a rooftop terrace",
            "in a pilates studio",
            "at a mountain trail",
            "in a community rec center"
        ],
        "emotion": [
            "looking determined",
            "appearing energized",
            "seeming focused",
            "radiating confidence",
            "looking motivated",
            "appearing strong",
            "seeming powerful",
            "looking intense",
            "radiating energy",
            "appearing dedicated",
            "seeming unstoppable",
            "looking fierce",
            "appearing driven",
            "seeming invigorated",
            "looking empowered"
        ]
    },
    "damsel in distress": {
        "clothing": [
            "a torn ball gown",
            "a tattered dress",
            "a disheveled nightgown",
            "a muddied Victorian dress",
            "a ripped skirt",
            "a soiled white dress",
            "a weathered cloak",
            "a frayed gown",
            "a rumpled blouse",
            "a damaged corset",
            "a stained period dress",
            "a dirty apron",
            "a shredded sleeve dress",
            "a worn petticoat",
            "a crumpled formal dress"
        ],
        "pose": [
            "tied to a chair",
            "reaching out desperately",
            "cowering in a corner",
            "looking over her shoulder",
            "hands bound together",
            "clutching a doorframe",
            "backing against a wall",
            "trapped behind bars",
            "kneeling on the floor",
            "struggling with rope",
            "pressed against a window",
            "huddled on the ground",
            "grasping at chains",
            "cornered by shadows",
            "restrained to a post"
        ],
        "setting": [
            "in a dark dungeon",
            "on abandoned railroad tracks",
            "in a crumbling tower",
            "in a dimly lit basement",
            "on a fog-shrouded bridge",
            "in an old castle",
            "in a haunted mansion",
            "on a stormy cliff",
            "in a decrepit attic",
            "in a locked room",
            "in a shadowy alley",
            "in a desolate warehouse",
            "on a rickety scaffold",
            "in a mysterious cave",
            "in an eerie forest clearing"
        ],
        "emotion": [
            "looking terrified",
            "appearing frightened",
            "seeming desperate",
            "radiating fear",
            "looking panicked",
            "appearing distressed",
            "seeming helpless",
            "looking anxious",
            "radiating vulnerability",
            "appearing worried",
            "seeming alarmed",
            "looking scared",
            "appearing threatened",
            "seeming endangered",
            "looking pleading"
        ]
    },
    "snoop": {
        "clothing": [
            "a detective's trench coat",
            "a noir-style fedora",
            "a sleuth outfit",
            "a mysterious cloak",
            "dark sunglasses",
            "a spy jacket",
            "an investigator's suit",
            "a disguise costume",
            "black gloves",
            "a secret agent attire",
            "a stealthy outfit",
            "a private eye ensemble",
            "undercover clothing",
            "a tactical vest",
            "an espionage getup"
        ],
        "pose": [
            "peering through a keyhole",
            "examining with a magnifying glass",
            "hiding behind a curtain",
            "crouching in shadows",
            "eavesdropping at a door",
            "inspecting fingerprints",
            "following footprints",
            "photographing evidence",
            "rifling through files",
            "listening with a stethoscope",
            "lurking around a corner",
            "searching through drawers",
            "watching from behind cover",
            "examining a clue",
            "sneaking through a hallway"
        ],
        "setting": [
            "in a mysterious library",
            "in a foggy alleyway",
            "in a secret office",
            "at a crime scene",
            "in a shadowy corridor",
            "in a private study",
            "at a train station",
            "in an abandoned building",
            "in a smoky detective agency",
            "on a moonlit rooftop",
            "in a hidden laboratory",
            "at a suspicious warehouse",
            "in a hotel lobby",
            "in a dark archive room",
            "at a clandestine meeting spot"
        ],
        "emotion": [
            "looking suspicious",
            "appearing curious",
            "seeming intrigued",
            "radiating alertness",
            "looking investigative",
            "appearing cautious",
            "seeming cunning",
            "looking perceptive",
            "radiating cleverness",
            "appearing analytical",
            "seeming shrewd",
            "looking vigilant",
            "appearing calculating",
            "seeming observant",
            "looking mysterious"
        ]
    }
}

point_of_views = [
    "first-person perspective",
    "third-person perspective",
    "over-the-shoulder view",
    "bird's-eye view",
    "worm's-eye view",
    "close-up shot",
    "wide-angle view",
    "side profile",
    "rear view",
    "top-down perspective",
    "low-angle shot",
    "high-angle shot",
    "panoramic view",
    "fisheye lens effect",
    "macro perspective"
]


def random_sample(item_list):
    """
    Return a random sample from the given list.

    Args:
        item_list (list): A list of items to sample from.
    Returns:
        A random item from the list.
    """
    return random.choice(random.sample(item_list, len(item_list)))


def generate_prompt(prompt_category=None):
    """
    Generate a random prompt for Kirsche image generation.
    
    Randomly selects one of the four categories (homemaker, exercise,
    damsel in distress, or snoop), then picks one word or phrase from
    each subcategory (clothing, pose, setting, emotion) within that
    category to create a unique prompt.
    
    Returns:
        str: A generated prompt string combining the selected elements.
    
    Example:
        >>> prompt = generate_prompt()
        >>> print(prompt)
        A homemaker wearing a floral dress, sitting on a vintage armchair in a cozy living room, looking content.
    """
    # Randomly select a category
    category = prompt_category if prompt_category else random.choice(list(PROMPT_DATA.keys()))
    category_data = PROMPT_DATA[category]
    
    # Randomly select one item from each subcategory using random.sample
    random.seed(datetime.now().timestamp())
    clothing = random_sample(category_data["clothing"])
    pose = random_sample(category_data["pose"])
    setting = random_sample(category_data["setting"])
    emotion = random_sample(category_data["emotion"])
    pov = random_sample(point_of_views)
    
    # Construct the prompt
    prompt = f"Kirsche is {category} wearing {clothing}, {pose} {setting}, {emotion}. The image is captured from a {pov}."
    
    return prompt


if __name__ == "__main__":
    # Generate and print a random prompt when run as a script
    pc = None if len(sys.argv) == 1 else sys.argv[1]
    print(generate_prompt(pc))
