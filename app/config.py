import os

# Project directories
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Application constants
APP_TITLE = "Nuvia - Bias Report"
APP_ICON = "📚"
APP_DESCRIPTION = "Bias Analysis from wikipedia articles"

# Default search settings
DEFAULT_TOPICS = ["Artificial Intelligence", "AI", "Business", "Finance", "Machine Learning"]
DEFAULT_ARTICLES_COUNT = 20
DEFAULT_ARTICLES_PER_PAGE = 6

# Bias detection model settings
BIAS_MODEL_NAME = "cffl/bert-base-styleclassification-subjective-neutral"

# Gemini model configuration
GEMINI_MODEL_NAME = "gemini-1.5-flash-latest"
GEMINI_DEFAULT_TEMPERATURE = 0.3

# UI settings
HIGHLIGHT_STYLE = "background-color: #ffdddd; font-weight: bold;"
DEFAULT_WIKI_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png"
CARD_HEIGHT = "480px"
CARD_IMAGE_HEIGHT = "150px"

# Bias levels and colors
BIAS_LEVELS = {
    "Alto": "red",
    "Médio": "orange",
    "Baixo": "green"
} 