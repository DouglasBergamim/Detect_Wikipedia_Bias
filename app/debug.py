#!/usr/bin/env python3
"""
Script para depurar problemas de importação na aplicação.
"""
try:
    import streamlit as st
    import asyncio
    import pandas as pd
    import nest_asyncio
    import time
    import os
    print("Módulos básicos importados com sucesso")
    
    # Verificar o diretório atual
    print(f"Diretório atual: {os.getcwd()}")
    
    # Verificar caminhos
    print(f"__file__: {__file__}")
    print(f"Diretório do script: {os.path.dirname(os.path.abspath(__file__))}")
    print(f"Diretório pai: {os.path.dirname(os.path.dirname(os.path.abspath(__file__)))}")
    
    # Verificar existência dos arquivos de módulos
    wiki_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wiki_service.py")
    bias_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "bias_detector.py")
    print(f"wiki_service.py existe: {os.path.exists(wiki_path)}")
    print(f"bias_detector.py existe: {os.path.exists(bias_path)}")
    
    # Tentar importar os módulos da aplicação
    from wiki_service import WikiService
    from bias_detector import BiasDetector
    print("Módulos da aplicação importados com sucesso")
    
    # Tentar instanciar os serviços
    wiki = WikiService()
    print("WikiService instanciado com sucesso")
    
    bias = BiasDetector()
    print("BiasDetector instanciado com sucesso")
    
    print("Todos os componentes carregados com sucesso!")
    
except Exception as e:
    import traceback
    print(f"Erro: {type(e).__name__}: {str(e)}")
    print("\nStack trace:")
    traceback.print_exc() 