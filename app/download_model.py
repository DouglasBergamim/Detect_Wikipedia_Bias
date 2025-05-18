#!/usr/bin/env python3
"""
Script para baixar previamente o modelo BERT usado na aplicação.
Execute antes de iniciar a aplicação para melhorar o tempo de carregamento inicial:
   python download_model.py
"""
import os
import nltk
from transformers import AutoTokenizer, TFAutoModelForSequenceClassification

def main():
    print("Baixando e configurando recursos...")
    
    # Define o diretório de cache
    cache_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
    os.makedirs(cache_dir, exist_ok=True)
    
    # Download dos recursos NLTK
    print("Baixando recursos NLTK...")
    nltk.download('punkt', download_dir=cache_dir, quiet=False)
    nltk.data.path.append(cache_dir)
    
    # Download do modelo BERT
    print("Baixando modelo BERT (isso pode levar alguns minutos)...")
    model_name = "cffl/bert-base-styleclassification-subjective-neutral"
    
    # Baixar o tokenizer
    print("Baixando tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(model_name, cache_dir=cache_dir)
    
    # Baixar o modelo
    print("Baixando modelo...")
    model = TFAutoModelForSequenceClassification.from_pretrained(
        model_name, 
        from_pt=True, 
        cache_dir=cache_dir
    )
    
    print("\nModelo baixado com sucesso na pasta:", cache_dir)
    print("Agora a aplicação Streamlit vai carregar mais rapidamente!")

if __name__ == "__main__":
    main() 