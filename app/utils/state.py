
import streamlit as st
import pandas as pd

# Garantir que as variáveis de estado existam
def _init_session_state():
    """Inicializa as variáveis de estado da sessão se não existirem"""
    if 'articles_df' not in st.session_state:
        st.session_state.articles_df = pd.DataFrame()
    if 'selected' not in st.session_state:
        st.session_state.selected = None
    if 'bias_df' not in st.session_state:
        st.session_state.bias_df = pd.DataFrame()
    if 'bias_summary' not in st.session_state:
        st.session_state.bias_summary = {}
    if 'missing_args' not in st.session_state:
        st.session_state.missing_args = {}
    if 'missing_args_summary' not in st.session_state:
        st.session_state.missing_args_summary = []
    if 'page' not in st.session_state:
        st.session_state.page = 0
    if 'selected_biased_texts' not in st.session_state:
        st.session_state.selected_biased_texts = []
    if 'neutralized_texts' not in st.session_state:
        st.session_state.neutralized_texts = {}
    if 'selection' not in st.session_state:
        st.session_state.selection = {}
    if 'structured_bias_df' not in st.session_state:
        st.session_state.structured_bias_df = pd.DataFrame()

# Inicializa variáveis de estado
_init_session_state()

# Inicialização do estado da sessão (conveniente alias 'ss')
class SessionState:
    def __init__(self):
        """Inicializa as variáveis de estado da sessão"""
        _init_session_state()
    
    @property
    def articles_df(self):
        if 'articles_df' not in st.session_state:
            st.session_state.articles_df = pd.DataFrame()
        return st.session_state.articles_df
    
    @articles_df.setter
    def articles_df(self, value):
        st.session_state.articles_df = value
    
    @property
    def selected(self):
        if 'selected' not in st.session_state:
            st.session_state.selected = None
        return st.session_state.selected
    
    @selected.setter
    def selected(self, value):
        st.session_state.selected = value
    
    @property
    def bias_df(self):
        if 'bias_df' not in st.session_state:
            st.session_state.bias_df = pd.DataFrame()
        return st.session_state.bias_df
    
    @bias_df.setter
    def bias_df(self, value):
        st.session_state.bias_df = value
    
    @property
    def bias_summary(self):
        if 'bias_summary' not in st.session_state:
            st.session_state.bias_summary = {}
        return st.session_state.bias_summary
    
    @bias_summary.setter
    def bias_summary(self, value):
        st.session_state.bias_summary = value
        
    @property
    def missing_args(self):
        if 'missing_args' not in st.session_state:
            st.session_state.missing_args = {}
        return st.session_state.missing_args
    
    @missing_args.setter
    def missing_args(self, value):
        st.session_state.missing_args = value
        
    @property
    def missing_args_summary(self):
        if 'missing_args_summary' not in st.session_state:
            st.session_state.missing_args_summary = []
        return st.session_state.missing_args_summary
    
    @missing_args_summary.setter
    def missing_args_summary(self, value):
        st.session_state.missing_args_summary = value
    
    @property
    def page(self):
        if 'page' not in st.session_state:
            st.session_state.page = 0
        return st.session_state.page
    
    @page.setter
    def page(self, value):
        st.session_state.page = value
    
    @property
    def selected_biased_texts(self):
        if 'selected_biased_texts' not in st.session_state:
            st.session_state.selected_biased_texts = []
        return st.session_state.selected_biased_texts
    
    @selected_biased_texts.setter
    def selected_biased_texts(self, value):
        st.session_state.selected_biased_texts = value
    
    @property
    def neutralized_texts(self):
        if 'neutralized_texts' not in st.session_state:
            st.session_state.neutralized_texts = {}
        return st.session_state.neutralized_texts
    
    @neutralized_texts.setter
    def neutralized_texts(self, value):
        st.session_state.neutralized_texts = value
    
    @property
    def structured_bias_df(self):
        """DataFrame com análise de viés estruturada por seções"""
        if 'structured_bias_df' not in st.session_state:
            st.session_state.structured_bias_df = pd.DataFrame()
        return st.session_state.structured_bias_df
    
    @structured_bias_df.setter
    def structured_bias_df(self, value):
        st.session_state.structured_bias_df = value
    
    @property
    def selection(self):
        """Mapa de seleção de trechos por ID"""
        if 'selection' not in st.session_state:
            st.session_state.selection = {}
        return st.session_state.selection
    
    @selection.setter
    def selection(self, value):
        st.session_state.selection = value
    
    def reset_selected(self):
        """Limpa a seleção de artigo e resultados de análise"""
        st.session_state.selected = None
        st.session_state.bias_df = pd.DataFrame()
        st.session_state.structured_bias_df = pd.DataFrame()
        st.session_state.bias_summary = {}
        st.session_state.missing_args = {}
        st.session_state.missing_args_summary = []
        st.session_state.selected_biased_texts = []
        st.session_state.neutralized_texts = {}
        st.session_state.selection = {}

# Instância global para acesso ao estado
ss = SessionState()

def reset_search_results():
    """Limpa os resultados de busca e seleção"""
    st.session_state.articles_df = pd.DataFrame()
    ss.reset_selected()
    st.session_state.page = 0

def set_page(page_number):
    """Configura a página atual"""
    st.session_state.page = page_number
    
def get_current_page():
    """Retorna o número da página atual"""
    return st.session_state.page

def store_analysis_results(article, bias_df, structured_bias_df, bias_summary, missing_args=None, missing_args_summary=None):
    """Armazena os resultados da análise de viés e argumentos faltantes"""
    st.session_state.selected = article
    st.session_state.bias_df = bias_df
    st.session_state.structured_bias_df = structured_bias_df
    st.session_state.bias_summary = bias_summary
    
    if missing_args is not None:
        st.session_state.missing_args = missing_args
    
    if missing_args_summary is not None:
        st.session_state.missing_args_summary = missing_args_summary
    
    # Resetar os trechos selecionados e neutralizados quando um novo artigo é selecionado
    st.session_state.selected_biased_texts = []
    st.session_state.neutralized_texts = {}
    st.session_state.selection = {} 