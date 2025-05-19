import pandas as pd
import numpy as np
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
import os
import asyncio
from tqdm.auto import tqdm
from .. import config
from ..utils.text_processor import split_sections

class BiasDetector:
    def __init__(self):
        # Name of the model used for bias detection
        self.model_name = config.BIAS_MODEL_NAME
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.initialized = False
        self.labels = ["NEUTRAL", "SUBJECTIVE"]
        
        # Load model and tokenizer only when needed
        self.model = None
        self.tokenizer = None
    
    def _load_model_resources(self):
        """Loads the model and tokenizer if they haven't been loaded yet"""
        if not self.initialized:
            try:
                print(f"Loading bias detection model: {self.model_name}")
                # Tokenizer configuration
                self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
                # Model configuration
                self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)
                self.model.to(self.device)
                self.model.eval()
                self.initialized = True
                print("Model loaded successfully!")
            except Exception as e:
                print(f"Error loading model: {e}")
    
    def detect_bias(self, sentences_df):
        """
        Detects bias in a set of sentences
        
        Args:
            sentences_df: DataFrame with the structured sentences
        
        Returns:
            DataFrame with sentences and bias labels
        """
        self._load_model_resources()
        
        if not self.initialized:
            raise RuntimeError("Bias model not initialized. Cannot perform bias detection.")
        
        results = []
        
        sentences = sentences_df['sentence'].tolist()
        
        batch_size = 16
        
        for i in range(0, len(sentences), batch_size):
            batch = sentences[i:i+batch_size]
            
            inputs = self.tokenizer(batch, padding=True, truncation=True, 
                                    max_length=512, return_tensors="pt")
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.model(**inputs)
                
            # Apply softmax to get probabilities
            probs = torch.nn.functional.softmax(outputs.logits, dim=-1)
            probs = probs.cpu().numpy()
            
            for j, (subj_prob, neut_prob) in enumerate(probs):
                label = "SUBJECTIVE" if subj_prob > 0.6 else "NEUTRAL"
                score = subj_prob if label == "SUBJECTIVE" else neut_prob
                results.append({
                    "label": label,
                    "bias_score": float(score)
                })
        
        for i, res in enumerate(results):
            sentences_df.loc[i, 'label'] = res['label']
            sentences_df.loc[i, 'bias_score'] = res['bias_score']
        return sentences_df

    def analyze_text(self, text):
        """
        Analyzes a complete text, splitting into sections and detecting bias
        Args:
            text: Complete text to be analyzed
            
        Returns:
            DataFrame with sections and analyzed sentences
        """
        sentences_df = split_sections(text)
        result_df = self.detect_bias(sentences_df)
        return result_df
    
    def get_summary(self, df):
        """Returns a summary of the text's bias analysis"""
        if 'label' not in df.columns:
            return {"error": "Text not properly analyzed"}
    
        total = len(df)
        subjective = len(df[df['label'] == 'SUBJECTIVE'])
        neutral = len(df[df['label'] == 'NEUTRAL'])
        
        perc_subjective = (subjective / total) * 100 if total > 0 else 0
        perc_neutral = (neutral / total) * 100 if total > 0 else 0
        
        avg_bias = df['bias_score'].mean() if 'bias_score' in df.columns else 0
        
        if perc_subjective >= 70:
            bias_level = "High"
        elif perc_subjective >= 40:
            bias_level = "Medium"
        else:
            bias_level = "Low"
        
        section_counts = df[df['label'] == 'SUBJECTIVE'].groupby('section').size().to_dict()
        
        return {
            "total_sentences": total,
            "subjective_sentences": subjective,
            "neutral_sentences": neutral,
            "perc_subjective": perc_subjective,
            "perc_neutral": perc_neutral,
            "avg_bias_score": avg_bias,
            "bias_level": bias_level,
            "sections_summary": section_counts
        }