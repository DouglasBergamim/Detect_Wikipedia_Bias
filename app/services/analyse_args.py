import os
import json
import asyncio
import re
import pandas as pd
from functools import lru_cache
from dotenv import load_dotenv
import google.generativeai as genai
from app.config import GEMINI_MODEL_NAME, GEMINI_DEFAULT_TEMPERATURE
from app.utils.llm_utils import parse_llm_json_response, extract_response_content


load_dotenv()

class ArgumentAnalyzer:
    def __init__(self):
        self.api_key = os.getenv("GEMINI_API_KEY")
        self.model_name = GEMINI_MODEL_NAME
        self.initialized = False
        
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.initialized = True
            except Exception as e:
                print(f"Error configuring Gemini API: {e}")
    
    def _build_prompt(self, section_title, section_text, max_args):
        return f"""
            You are an assistant specialized in critical content analysis.
            Analyze the following excerpt from a Wikipedia article section and identify up to {max_args} arguments, counter-arguments,
            or important viewpoints that appear to be missing or could enrich the discussion about the section's topic.

            For each missing item identified, provide:
            - \"argument\": A clear and concise description of the missing argument/point and how it matters for the text understand.
            - \"priority\": An integer from 1 (most important/impactful) to {max_args} (least important among those identified).

            Return your response as a pure JSON list of objects.
            If no relevant arguments or points are missing, return an empty JSON list: `[]`.

            Section Title (for context): \"{section_title}\"
            Section Excerpt:
            \"\"\"{section_text.strip()}\"\"\"
            """

    async def _call_llm(self, prompt):
        model_client = genai.GenerativeModel(self.model_name)
        generation_config = genai.types.GenerationConfig(
            temperature=GEMINI_DEFAULT_TEMPERATURE,
            max_output_tokens=256
        )
        response = await asyncio.to_thread(
            model_client.generate_content,
            prompt,
            generation_config=generation_config
        )
        return extract_response_content(response)

    def _postprocess(self, response_content):
        if response_content:
            parsed_response = parse_llm_json_response(response_content)
            if isinstance(parsed_response, list):
                return parsed_response
            elif isinstance(parsed_response, dict) and parsed_response:
                return [parsed_response]
            else:
                return []
        else:
            return []

    async def get_missing_args_for_section(self, section_title, section_text, max_args=2):
        """
        Asynchronously analyzes a section of an article and identifies missing arguments.
        Returns a list of dictionaries, each with 'argument' and 'priority'.
        """
        if not self.initialized:
            return []
        prompt = self._build_prompt(section_title, section_text, max_args)
        try:
            response_content = await self._call_llm(prompt)
            return self._postprocess(response_content)
        except Exception as e:
            print(f"ERROR calling Gemini API for section '{section_title}': {e}")
            return []
    
    async def extract_sections(self, article_content):
        """Extracts sections from the article content"""
        print(f"Extracting sections from an article with {len(article_content)} characters")
        try:
            # Use regex to detect sections (more reliable than line split)
            header_pattern = r'^(=+)\s*([^=]+?)\s*\1'
            headers = list(re.finditer(header_pattern, article_content, re.MULTILINE))
            print(f"Found {len(headers)} possible section headers")
            sections = []
            # If no headers found, treat as a single section
            if not headers:
                print("No headers found. Treating entire content as 'Introduction'")
                sections.append({
                    "title": "Introduction",
                    "content": article_content.strip()
                })
                return sections
            # For each header, extract the section content
            for i, match in enumerate(headers):
                title = match.group(2).strip()
                level = len(match.group(1))
                # Determine content start (after header)
                content_start = match.end()
                # Determine content end (start of next header or end of text)
                content_end = headers[i+1].start() if i < len(headers) - 1 else len(article_content)
                # Extract content
                content = article_content[content_start:content_end].strip()
                print(f"Section '{title}' (level {level}): {len(content)} characters")
                sections.append({
                    "title": title,
                    "content": content,
                    "level": level
                })
            return sections
        except Exception as e:
            print(f"ERROR extracting sections: {e}")
            # Fallback: return a single section with all content
            return [{"title": "Article Content", "content": article_content}]
    
    async def analyze_article_missing_args(self, article_content, max_args_per_section=2, max_sections=5):
        """
        Asynchronously analyzes an entire article and returns missing arguments by section.
        
        Args:
            article_content (str): Complete article content
            max_args_per_section (int): Maximum number of arguments to identify per section
            max_sections (int): Maximum number of sections to analyze
            
        Returns:
            dict: Dictionary with structure {section: [list of missing arguments]}
        """
        print(f"Starting missing arguments analysis for an article with {len(article_content)} characters")
        
        if not self.initialized:
            print("ERROR: Argument analysis service not initialized. API key not configured?")
            return {}
            
        # Extract article sections
        sections = await self.extract_sections(article_content)
        print(f"Extracted {len(sections)} sections from article")
        
        # Limit number of sections (if needed)
        if max_sections and len(sections) > max_sections:
            print(f"Limiting analysis to first {max_sections} sections (of {len(sections)} total)")
            sections = sections[:max_sections]
        
        # Process each section in parallel
        print(f"Starting parallel analysis for {len(sections)} sections")
        tasks = []
        for section in sections:
            section_title = section["title"]
            section_text = section["content"]
            
            # Check if section has enough content to analyze
            if len(section_text.split()) < 10:
                print(f"Section '{section_title}' has too little content for analysis ({len(section_text.split())} words). Skipping.")
                continue
                
            print(f"Adding task for section '{section_title}' with {len(section_text)} characters")
            task = self.get_missing_args_for_section(
                section_title=section_title,
                section_text=section_text,
                max_args=max_args_per_section
            )
            tasks.append((section_title, task))
        
        # Wait for all results
        print(f"Waiting for results from {len(tasks)} tasks")
        missing_args = {}
        
        for section_title, task in tasks:
            try:
                result = await task
                print(f"Result for section '{section_title}': {len(result) if result else 0} arguments")
                if result:  # Only add if there are missing arguments
                    missing_args[section_title] = result
            except Exception as e:
                print(f"ERROR processing section '{section_title}': {e}")
        
        print(f"Análise concluída. Encontrados argumentos faltantes em {len(missing_args)} seções")
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
            
        # Flatten: Create a single list of all missing arguments with their sections
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

        # Build the prompt for the LLM, asking to consolidate and rank
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
        - "argument": The text of the consolidated missing argument.
        - "section": The name of the section where the argument was originally identified.

        If the input list is empty or contains no valid arguments, return an empty JSON list: `[]`.

        List of missing arguments for analysis:
        {input_arguments_str}
        """

        try:
            model_client = genai.GenerativeModel(self.model_name)
            generation_config = genai.types.GenerationConfig(temperature=GEMINI_DEFAULT_TEMPERATURE)
            
            response = await asyncio.to_thread(
                model_client.generate_content,
                prompt,
                generation_config=generation_config
            )
            
            response_content = extract_response_content(response)
            if response_content:
                parsed_response = parse_llm_json_response(response_content)
                if isinstance(parsed_response, list):
                    return parsed_response
                elif isinstance(parsed_response, dict) and parsed_response:
                    return [parsed_response]
                else:
                    return []
            else:
                return []

        except Exception as e:
            print(f"ERROR calling Gemini API for summary: {e}")
            return [] 