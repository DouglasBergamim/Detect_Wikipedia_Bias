import json

def parse_llm_json_response(response_text):
    """
    Attempts to parse a JSON response from an LLM, removing markdown blocks and handling common error cases.
    """
    if not response_text:
        return []

    cleaned_text = response_text.strip()
    # Remove ```json ... ``` or ``` ... ``` if present
    if cleaned_text.startswith("```json"):
        cleaned_text = cleaned_text[7:]
        if cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[:-3]
    elif cleaned_text.startswith("```") and cleaned_text.endswith("```"):
        cleaned_text = cleaned_text[3:-3]
    cleaned_text = cleaned_text.strip()

    try:
        return json.loads(cleaned_text)
    except json.JSONDecodeError:
        items = []
        for line in cleaned_text.splitlines():
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                try:
                    if line.endswith(","):
                        line = line[:-1]
                    items.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
            elif line == "[" or line == "]":
                pass
        if len(items) == 1 and not (cleaned_text.startswith("[") and cleaned_text.endswith("]")):
            if cleaned_text.startswith("{") and cleaned_text.endswith("}"):
                return items[0]
        if not items and cleaned_text == "[]":
            return []
        return items if items else []

def extract_response_content(response):
    """
    Extracts the text content from the Gemini model response, handling different formats.
    """
    response_content = ""
    if response and hasattr(response, 'text') and response.text:
        response_content = response.text
    elif response and hasattr(response, 'parts') and response.parts:
        response_content = "".join([part.text for part in response.parts if hasattr(part, 'text')])
    return response_content 