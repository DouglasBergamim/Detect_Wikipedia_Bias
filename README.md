# Detect Wikipedia Bias

Web application for analyzing Wikipedia articles, including bias detection using NLP techniques and argument analysis.

## Project Structure

```
app/
├── main.py               # Main orchestration and layout file
├── config.py             # Global configurations and constants
├── ui/                   # User interface components
│   ├── sidebar.py        # Settings sidebar
│   ├── article_cards.py  # Card layout for displaying articles
│   └── bias_report.py    # Bias analysis report
├── services/             # Data access and ML layers
│   ├── wiki.py           # Wikipedia API access
│   ├── bias.py           # Bias detector using BERT
│   ├── debias.py         # Text neutralization service
│   └── analyse_args.py   # Missing arguments detection
├── utils/                # Utility functions
│   ├── highlights.py     # Text highlighting formatting
│   ├── text_processor.py # Text processing utilities
│   ├── llm_utils.py      # LLM response handling utilities
│   └── state.py          # Session state management
└── download_model.py     # Script for pre-downloading the model
```

## Requirements

- Python 3.9+
- Libraries: streamlit, transformers, torch, aiohttp, nltk, pandas, google-generativeai

## Installation

1. Clone the repository:
```bash
git clone https://github.com/your-user/detect_wikipedia_bias.git
cd detect_wikipedia_bias
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create a `.env` file with your API keys:
```
GEMINI_API_KEY=your_gemini_api_key
```

4. (Optional) Pre-download the ML model:
```bash
python app/download_model.py
```

## Running the Application

```bash
PYTHONPATH=/path/to/detect_wikipedia_bias streamlit run app/main.py
```

Example:
```bash
PYTHONPATH=/home/dods/matrix/nuvia streamlit run app/main.py
```

## Features

- Search for articles by topics and time period
- Detect bias in texts using a pre-trained BERT model
- Display articles in paginated card format
- Highlight subjective sections in analyzed texts
- Provide metrics and statistics on the bias level in articles
- Identify missing arguments and perspectives in articles
- Neutralize biased text to create more objective versions

## Models and Services

### Bias Detection
- Uses `cffl/bert-base-styleclassification-subjective-neutral` BERT model
- Classifies sentences as either NEUTRAL or SUBJECTIVE
- Calculates overall bias level (High, Medium, Low) based on percentage of subjective content
- Provides sentence-level bias scores and section-by-section analysis

### Text Neutralization
- Uses Google's Gemini API (`gemini-1.5-flash-latest`)
- Transforms biased/subjective text into more neutral and objective language
- Preserves factual information while removing opinions and emotionally charged language

### Missing Arguments Analysis
- Uses Google's Gemini API to analyze article sections
- Identifies potential missing arguments, counter-arguments, or perspectives
- Provides prioritized recommendations for enhancing content balance
- Summarizes missing viewpoints across the entire article

### Wikipedia Data Service
- Searches for articles by topics
- Retrieves article content, metadata, and page view statistics
- Extracts and structures article sections for analysis
