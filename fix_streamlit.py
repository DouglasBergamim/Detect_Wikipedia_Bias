#!/usr/bin/env python3
"""
Script para diagnosticar e corrigir problemas com o Streamlit
"""

import os
import sys
import shutil
import subprocess
from pathlib import Path

def main():
    print("Iniciando diagnóstico do Streamlit...")
    
    # Verificar versão do Python
    python_version = sys.version
    print(f"Python version: {python_version}")
    
    # Verificar ambiente virtual
    venv_active = 'VIRTUAL_ENV' in os.environ
    venv_path = os.environ.get('VIRTUAL_ENV', 'Não ativado')
    print(f"Ambiente virtual: {'Ativado' if venv_active else 'Não ativado'}")
    print(f"Caminho do venv: {venv_path}")
    
    # Verificar instalação do Streamlit
    try:
        import streamlit
        streamlit_version = streamlit.__version__
        streamlit_path = streamlit.__file__
        print(f"Streamlit instalado: versão {streamlit_version}")
        print(f"Caminho do Streamlit: {streamlit_path}")
    except ImportError:
        print("Streamlit não está instalado no ambiente atual")
        streamlit_version = None
    
    # Verificar presença de cache
    home = Path.home()
    streamlit_cache = home / ".streamlit"
    streamlit_cache_exists = streamlit_cache.exists()
    print(f"Cache do Streamlit: {'Existe' if streamlit_cache_exists else 'Não existe'}")
    
    # Verificar dependências do Streamlit
    if streamlit_version:
        print("\nVerificando dependências do Streamlit...")
        try:
            import torch
            print(f"PyTorch instalado: versão {torch.__version__}")
        except ImportError:
            print("PyTorch não está instalado")
        
        try:
            import tensorflow
            print(f"TensorFlow instalado: versão {tensorflow.__version__}")
        except ImportError:
            print("TensorFlow não está instalado")
        
        try:
            import nltk
            print(f"NLTK instalado: versão {nltk.__version__}")
        except ImportError:
            print("NLTK não está instalado")
    
    # Verificar portas em uso
    print("\nVerificando portas em uso...")
    try:
        result = subprocess.run(["lsof", "-i", ":8501"], capture_output=True, text=True)
        if result.stdout:
            print("Porta 8501 em uso:")
            print(result.stdout)
        else:
            print("Porta 8501 está livre")
    except FileNotFoundError:
        print("Comando 'lsof' não disponível para verificar portas")
    
    # Mostrar sugestões
    print("\nSugestões para corrigir problemas:")
    print("1. Limpar o cache do Streamlit: streamlit cache clear")
    print("2. Reinstalar o Streamlit: pip uninstall -y streamlit && pip install streamlit==1.28.0")
    print("3. Tentar uma versão mais antiga do Streamlit que pode ser mais estável")
    print("4. Verificar se há arquivos de configuração em conflito em ~/.streamlit/")
    print("5. Executar com flags de depuração: streamlit run --logger.level=info app.py")
    print("6. Verificar se há algum processo do Streamlit ainda em execução")
    
    if streamlit_cache_exists and input("Deseja limpar o cache do Streamlit? (s/n): ").lower() == 's':
        try:
            # Fazer backup do cache
            backup_path = str(streamlit_cache) + '.backup'
            shutil.copytree(streamlit_cache, backup_path, dirs_exist_ok=True)
            print(f"Backup do cache salvo em: {backup_path}")
            
            # Limpar o cache
            for item in streamlit_cache.iterdir():
                if item.is_dir():
                    shutil.rmtree(item)
                else:
                    item.unlink()
            print("Cache do Streamlit limpo com sucesso")
        except Exception as e:
            print(f"Erro ao limpar cache: {e}")
    
    print("\nDiagnóstico concluído!")

if __name__ == "__main__":
    main() 