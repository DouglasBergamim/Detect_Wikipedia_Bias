import os
import google.generativeai as genai
import os
from typing import List, Dict
from app.config import GEMINI_MODEL_NAME

class DebiasService:
    def __init__(self):
        # Configura a API do Gemini (ou outro modelo disponível)
        api_key = os.environ.get("GEMINI_API_KEY")
        if api_key:
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel(GEMINI_MODEL_NAME)
        else:
            self.model = None
            print("AVISO: GEMINI_API_KEY não configurada. Serviço de neutralização limitado.")
    
    def neutralize_text(self, biased_text: str) -> str:
        """
        Neutralizes a biased text excerpt, transforming it into a more objective version.
        Args:
            biased_text: Biased text to be neutralized
        Returns:
            Neutralized version of the text
        """
        if not biased_text or not biased_text.strip():
            return ""
        if not self.model:
            return ""
        try:
            prompt = f"""
            The following text contains biased or subjective language.
            Rewrite it to make it more neutral and objective, maintaining the 
            factual information while removing opinions, value judgments, 
            and emotionally charged language.
            
            Original text: "{biased_text}"
            
            Neutralized text:
            """
            response = self.model.generate_content(prompt)
            print(f"[DEBUG] Raw Gemini response: {response.text}")
            neutral_text = response.text.strip()
            if not neutral_text or len(neutral_text) < 5:
                return ""
            return neutral_text
        except Exception as e:
            print(f"ERROR neutralizing text: {e}")
            return ""
    
    def neutralize_multiple(self, biased_texts: List[str]) -> Dict[str, str]:
        """
        Neutralizes multiple biased text excerpts
        Args:
            biased_texts: List of biased texts
        Returns:
            Dictionary with the original text as the key and the neutralized text as the value
        """
        results = {}
        for text in biased_texts:
            if text and text.strip():
                results[text] = self.neutralize_text(text)
        return results 