"""
Aplicação principal Nuvia - Análise de Artigos da Wikipedia
"""
import streamlit as st
import nest_asyncio
import os
import sys
import pandas as pd

# Adicionar o diretório raiz ao sys.path para permitir importações absolutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Importações do projeto
from app.ui import sidebar_controls, article_grid, show_bias_report
from app.services import registry
from app.utils.state import ss, _init_session_state

# Garantir que o estado da sessão esteja inicializado
_init_session_state()

# Aplicando patch para asyncio funcionar com Streamlit
nest_asyncio.apply()

# Configuração da página
st.set_page_config(
    page_title="Nuvia · Wiki Bias",
    page_icon="📚",
    layout="wide"
)

# Título principal
st.title("📚 Nuvia – Wikipedia Bias Scanner")

# 1. Sidebar -----------------------------------------------------------------
controls = sidebar_controls()

# 2. Busca ao clicar ---------------------------------------------------------
if controls["do_search"]:
    try:
        articles = registry.wiki.get_articles(**controls)
        ss.articles_df = articles if not articles.empty else pd.DataFrame()
        ss.page = 0
        ss.selected = None
    except Exception as e:
        st.error(f"Erro ao buscar artigos: {e}")
        ss.articles_df = pd.DataFrame()

# 3. Grid de artigos + paginação --------------------------------------------
try:
    # Garantir que articles_df existe e é um DataFrame válido
    df = ss.articles_df
    if isinstance(df, pd.DataFrame) and not df.empty:
        article_grid(df, controls.get("per_page", 6))
    elif controls.get("do_search"):
        st.info("Nenhum artigo encontrado. Tente ajustar sua busca.")
except Exception as e:
    st.error(f"Erro ao exibir artigos: {e}")

# 4. Relatório de viés -------------------------------------------------------
if ss.selected is not None:
    try:
        show_bias_report(ss.selected)
    except Exception as e:
        st.error(f"Erro ao exibir relatório de viés: {e}")

# Rodapé com créditos
st.divider() 