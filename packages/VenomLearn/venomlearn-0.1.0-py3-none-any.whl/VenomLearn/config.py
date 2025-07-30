"""Configuration settings for VenomLearn package."""

import os
import pathlib

# Base directory for the package
BASE_DIR = pathlib.Path(__file__).parent.absolute()

# Data directory
DATA_DIR = os.path.join(BASE_DIR, "data")

# Ensure data directory exists
os.makedirs(DATA_DIR, exist_ok=True)

# Paths to data files
LESSONS_FILE = os.path.join(DATA_DIR, "lessons.json")
QUIZZES_FILE = os.path.join(DATA_DIR, "quizzes.json")
PROGRESS_FILE = os.path.join(DATA_DIR, "progress.json")

# UI settings
UI_THEME = {
    "primary": "cyan",
    "secondary": "yellow",
    "accent": "green",
    "error": "red",
    "info": "blue",
}

# Difficulty levels
DIFFICULTY_LEVELS = ["beginner", "intermediate", "advanced"]

# Badge levels
BADGE_LEVELS = {
    "novice": 1,
    "apprentice": 3,
    "journeyman": 5,
    "expert": 7,
    "master": 10,
}