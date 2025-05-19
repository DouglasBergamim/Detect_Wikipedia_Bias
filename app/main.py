"""
Aplicação principal Nuvia - Análise de Artigos da Wikipedia
"""
import streamlit as st
import nest_asyncio
import os
import sys
import pandas as pd
from app.config import APP_TITLE, APP_ICON, APP_DESCRIPTION, DEFAULT_ARTICLES_PER_PAGE

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from app.ui import sidebar_controls, article_grid, show_bias_report
from app.services import registry
from app.utils.state import ss, _init_session_state


_init_session_state()


nest_asyncio.apply()

# header
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# title
st.title(APP_TITLE)

#sidebar
controls = sidebar_controls()

# search
if controls["do_search"]:
    try:
        articles = registry.wiki.get_articles(**controls)
        ss.articles_df = articles if not articles.empty else pd.DataFrame()
        ss.page = 0
        ss.selected = None
    except Exception as e:
        st.error(f"Erro ao buscar artigos: {e}")
        ss.articles_df = pd.DataFrame()

# articles grid
try:
    df = ss.articles_df
    if isinstance(df, pd.DataFrame) and not df.empty:
        article_grid(df, controls.get("per_page", DEFAULT_ARTICLES_PER_PAGE))
    elif controls.get("do_search"):
        st.info("Nenhum artigo encontrado. Tente ajustar sua busca.")
except Exception as e:
    st.error(f"Erro ao exibir artigos: {e}")

# bias report
if ss.selected is not None:
    try:
        show_bias_report(ss.selected)
    except Exception as e:
        st.error(f"Erro ao exibir relatório de viés: {e}")

# footer    
st.divider() 