"""
Componente da barra lateral (sidebar) da aplicação
"""
import streamlit as st
from datetime import datetime
import os
import sys

# Adicionar o diretório raiz ao sys.path para permitir importações absolutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import config

def sidebar_controls():
    """Renderiza a barra lateral com configurações de busca"""
    with st.sidebar:
        st.header("Configurações de Busca")
        
        # Input para tópicos
        topics_input = st.text_area(
            "Tópicos de interesse (um por linha)",
            value="\n".join(config.DEFAULT_TOPICS),
            height=150
        )
        topics = [t.strip() for t in topics_input.split("\n") if t.strip()]
        
        # Sliders para parâmetros
        total_articles = st.slider(
            "Quantidade de artigos relevantes", 
            5, 100, config.DEFAULT_ARTICLES_COUNT, 5
        )
        
        # Artigos por página
        per_page = st.slider(
            "Artigos por página", 
            3, 15, config.DEFAULT_ARTICLES_PER_PAGE, 3
        )
        
        # Data de referência (opcional)
        use_date = st.checkbox("Usar data específica")
        date_str = None
        if use_date:
            date = st.date_input("Data para buscar artigos")
            date_str = date.strftime("%Y/%m/%d")
        
        # Botão para buscar
        do_search = st.button("🔍 Buscar Artigos", type="primary")
        
        return {
            "topics": topics,
            "k": total_articles,  # Renomeado para melhor semântica
            "per_page": per_page,
            "date_str": date_str,
            "do_search": do_search
        } 