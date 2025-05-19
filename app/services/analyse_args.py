"""
Serviço para detecção de argumentos faltantes em artigos usando Gemini API
"""
import os
import json
import asyncio
import pandas as pd
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai

# Carregar variáveis de ambiente
load_dotenv()

class ArgumentAnalyzer:
    """Classe para análise de argumentos faltantes em artigos"""
    
    # Constantes
    DEFAULT_MODEL_NAME = "gemini-1.5-flash-latest"
    DEFAULT_TEMPERATURE = 0.3
    
    def __init__(self):
        """Inicializa o serviço de análise de argumentos"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = self.DEFAULT_MODEL_NAME
        self.initialized = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception as e:
                print(f"Erro ao configurar a API Gemini: {e}")
    
    def _parse_llm_json_response(self, response_text):
        """
        Tenta analisar a string de resposta JSON do LLM.
        Remove possíveis blocos de código Markdown e, se a análise direta falhar,
        tenta um fallback analisando linha por linha objetos JSON.
        """
        if not response_text:
            return []

        cleaned_text = response_text.strip()
        
        # Remove ```json ... ``` ou ``` ... ``` se presentes
        if cleaned_text.startswith("```json"):
            cleaned_text = cleaned_text[7:]
            if cleaned_text.endswith("```"):
                cleaned_text = cleaned_text[:-3]
        elif cleaned_text.startswith("```") and cleaned_text.endswith("```"):
            cleaned_text = cleaned_text[3:-3]
                
        cleaned_text = cleaned_text.strip()

        try:
            # Tenta carregar o JSON diretamente
            return json.loads(cleaned_text)
        
        except json.JSONDecodeError:
            # Fallback para análise linha a linha
            items = []
            for line in cleaned_text.splitlines():
                line = line.strip()
                if line.startswith("{") and line.endswith("}"):
                    try:
                        # Remove vírgulas no final de uma linha, se houver
                        if line.endswith(","):
                            line = line[:-1]
                        items.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
                elif line == "[" or line == "]": # Ignora colchetes de lista em linhas separadas
                    pass
            
            # Se 'items' contém apenas um dicionário, e o JSON original não parecia ser uma lista, retorna o dicionário.
            if len(items) == 1 and not (cleaned_text.startswith("[") and cleaned_text.endswith("]")):
                if cleaned_text.startswith("{") and cleaned_text.endswith("}"):
                    return items[0]
            
            if not items and cleaned_text == "[]": 
                return []
            return items if items else []
    
    async def get_missing_args_for_section(self, section_title, section_text, max_args=2):
        """
        Analisa assincronamente um trecho de uma seção de artigo e identifica argumentos faltantes.
        Retorna uma lista de dicionários, cada um com 'argument' e 'priority'.
        """
        if not self.initialized:
            return []
        
        prompt = f"""
You are an assistant specialized in critical content analysis.
Analyze the following excerpt from a Wikipedia article section and identify up to {max_args} arguments, counter-arguments,
or important viewpoints that appear to be missing or could enrich the discussion about the section's topic.

For each missing item identified, provide:
- "argument": A clear and concise description of the missing argument/point and how it matters for the text understand.
- "priority": An integer from 1 (most important/impactful) to {max_args} (least important among those identified).

Return your response as a pure JSON list of objects.
If no relevant arguments or points are missing, return an empty JSON list: `[]`.

Section Title (for context): "{section_title}"
Section Excerpt:
\"\"\"{section_text.strip()}\"\"\"
"""

        try:
            model_client = genai.GenerativeModel(self.model_name)
            generation_config = genai.types.GenerationConfig(
                temperature=self.DEFAULT_TEMPERATURE,
                max_output_tokens=256
            )
                
            response = await asyncio.to_thread(
                model_client.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            response_content = ""
            if response and hasattr(response, 'text') and response.text:
                response_content = response.text
            elif response and response.parts:  # Modelos mais novos podem usar 'parts'
                response_content = "".join([part.text for part in response.parts if hasattr(part, 'text')])

            if response_content:
                parsed_response = self._parse_llm_json_response(response_content)
                if isinstance(parsed_response, list):
                    return parsed_response
                elif isinstance(parsed_response, dict) and parsed_response:  # Se retornou um dict único, envolve em lista
                    return [parsed_response]
                else:
                    return []
            else:
                return []

        except Exception as e:
            print(f"ERRO ao chamar a API Gemini para a seção '{section_title}': {e}")
            return []
    
    async def extract_sections(self, article_content):
        """Extrai as seções do conteúdo do artigo"""
        lines = article_content.split('\n')
        sections = []
        current_section = {"title": "Introduction", "content": ""}
        
        for line in lines:
            if line.strip().startswith('=') and line.strip().endswith('='):
                # Adicionar a seção atual (se tiver conteúdo) e começar uma nova
                if current_section["content"].strip():
                    sections.append(current_section)
                
                # Determinar o nível de título e criar nova seção
                level = line.count('=') // 2  # Conta quantos pares de '=' (== é h2, === é h3, etc)
                title = line.strip('= \t')
                current_section = {"title": title, "content": ""}
            else:
                # Adicionar linha ao conteúdo da seção atual
                current_section["content"] += line + "\n"
        
        # Adicionar a última seção
        if current_section["content"].strip():
            sections.append(current_section)
            
        return sections
    
    async def analyze_article_missing_args(self, article_content, max_args_per_section=2, max_sections=5):
        """
        Analisa assincronamente um artigo inteiro e retorna os argumentos faltantes por seção.
        
        Args:
            article_content (str): Conteúdo completo do artigo
            max_args_per_section (int): Número máximo de argumentos a identificar por seção
            max_sections (int): Número máximo de seções a analisar
            
        Returns:
            dict: Dicionário com estrutura {seção: [lista de argumentos faltantes]}
        """
        if not self.initialized:
            return {}
            
        # Extrair as seções do artigo
        sections = await self.extract_sections(article_content)
        
        # Limitar o número de seções (se necessário)
        if max_sections and len(sections) > max_sections:
            sections = sections[:max_sections]
        
        # Processar cada seção em paralelo
        tasks = []
        for section in sections:
            task = self.get_missing_args_for_section(
                section_title=section["title"],
                section_text=section["content"],
                max_args=max_args_per_section
            )
            tasks.append(task)
        
        # Aguardar todos os resultados
        results = await asyncio.gather(*tasks)
        
        # Montar o dicionário de resultados
        missing_args = {}
        for i, section in enumerate(sections):
            if results[i]:  # Adiciona apenas se houver argumentos faltantes
                missing_args[section["title"]] = results[i]
                
        return missing_args
    
    async def summarize_missing_args(self, missing_args_by_section, max_summary_items=5):
        """
        A partir do dicionário {seção: [lista de args faltantes]}, agrupa todos os argumentos,
        remove duplicatas e rankeia os principais argumentos faltantes.
        
        Returns:
            list: Lista de dicionários com argumentos resumidos
        """
        if not self.initialized or not missing_args_by_section:
            return []
            
        # Flatten: Cria uma lista única de todos os argumentos faltantes com suas seções
        all_missing_entries = []
        for section, args_list in missing_args_by_section.items():
            if isinstance(args_list, list):
                for arg_item in args_list:
                    if isinstance(arg_item, dict) and "argument" in arg_item:
                        all_missing_entries.append({
                            "section": section,
                            "argument": arg_item["argument"],
                            "priority": arg_item.get("priority", 1)
                        })
        
        if not all_missing_entries:
            return []

        # Monta o prompt para o LLM, pedindo para consolidar e rankear
        prompt_lines = []
        for entry in all_missing_entries:
            prompt_lines.append(
                f"- Da seção '{entry['section']}' (prioridade original {entry['priority']}): "
                f"{entry['argument']}"
            )
        
        input_arguments_str = "\n".join(prompt_lines)

        prompt = f"""
You are a senior research assistant and editor.
The list below contains suggestions for missing arguments or points identified in different sections of a Wikipedia article.
Your task is to consolidate this list by:
1. Removing any arguments that are duplicated or semantically very similar to each other, keeping the clearer or more comprehensive version.
2. Based on relevance and potential impact for article completeness, select the {max_summary_items} most important missing arguments.
3. For each of the {max_summary_items} selected, maintain the information about the source section and original priority.

Return your response as a pure JSON list of objects. Each object should have the fields:
- "argument": A clear and concise description of the missing argument/point and how it matters for the text understand.
- "section": The name of the section where the argument was originally identified.

If the input list is empty or contains no valid arguments, return an empty JSON list: `[]`.

List of missing arguments for analysis:
{input_arguments_str}
"""

        try:
            model_client = genai.GenerativeModel(self.model_name)
            generation_config = genai.types.GenerationConfig(temperature=self.DEFAULT_TEMPERATURE)
            
            response = await asyncio.to_thread(
                model_client.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            response_content = ""
            if response and hasattr(response, 'text') and response.text:
                response_content = response.text
            elif response and response.parts:
                response_content = "".join([part.text for part in response.parts if hasattr(part, 'text')])

            if response_content:
                parsed_response = self._parse_llm_json_response(response_content)
                if isinstance(parsed_response, list):
                    return parsed_response
                elif isinstance(parsed_response, dict) and parsed_response:
                    return [parsed_response]
                else:
                    return []
            else:
                return []

        except Exception as e:
            print(f"ERRO ao chamar a API Gemini para sumarização: {e}")
            return [] 