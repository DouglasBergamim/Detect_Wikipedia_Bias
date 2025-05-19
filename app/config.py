"""
Configurações globais e constantes do projeto
"""
import os

# Diretórios do projeto
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(ROOT_DIR, "models")
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Constantes da aplicação
APP_TITLE = "Nuvia - Análise de Artigos"
APP_ICON = "📚"
APP_DESCRIPTION = "Descubra artigos relevantes e analise seu viés"

# Configurações padrão de busca
DEFAULT_TOPICS = ["Artificial Intelligence", "AI", "Business", "Finance", "Machine Learning"]
DEFAULT_ARTICLES_COUNT = 20
DEFAULT_ARTICLES_PER_PAGE = 6

# Configurações do modelo de detecção de viés
BIAS_MODEL_NAME = "cffl/bert-base-styleclassification-subjective-neutral"

# Configurações de UI
HIGHLIGHT_STYLE = "background-color: #ffdddd; font-weight: bold;"
DEFAULT_WIKI_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png"
CARD_HEIGHT = "480px"
CARD_IMAGE_HEIGHT = "150px"

# Níveis de viés e cores
BIAS_LEVELS = {
    "Alto": "red",
    "Médio": "orange",
    "Baixo": "green"
} 