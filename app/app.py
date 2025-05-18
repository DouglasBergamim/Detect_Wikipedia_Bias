import streamlit as st
import asyncio
import pandas as pd
import nest_asyncio
import time
import os
from wiki_service import WikiService
from bias_detector import BiasDetector

# Configuração da página
st.set_page_config(
    page_title="Nuvia - Análise de Artigos",
    page_icon="📚",
    layout="wide"
)

# Título principal
st.title("📚 Nuvia - Análise de Artigos da Wikipedia")
st.markdown("Descubra artigos relevantes e analise seu viés")

# Verificar se os modelos já foram baixados
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
models_downloaded = os.path.exists(models_dir) and len(os.listdir(models_dir)) > 0

# Mostrar informações sobre o carregamento inicial
if not models_downloaded:
    st.warning("⚠️ Primeira execução: O modelo BERT será baixado automaticamente. Isso pode levar alguns minutos.")
    st.info("💡 Dica: Para acelerar futuras execuções, você pode executar o script de download antecipado: `python app/download_model.py`")

# Inicialização dos serviços com barra de progresso se necessário
with st.spinner("Carregando serviços..."):
    # Aplicando patch para asyncio funcionar com Streamlit
    nest_asyncio.apply()
    
    # Importa depois do aviso para mostrar progresso durante a importação
    from wiki_service import WikiService
    from bias_detector import BiasDetector
    
    # Inicialização dos serviços (uma única vez)
    @st.cache_resource
    def load_services():
        return WikiService(), BiasDetector()
    
    wiki_service, bias_detector = load_services()

# Sidebar para configurações de busca
with st.sidebar:
    st.header("Configurações de Busca")
    
    # Input para tópicos
    default_topics = ["Artificial Intelligence", "AI", "Business", "Finance", "Machine Learning"]
    topics_input = st.text_area(
        "Tópicos de interesse (um por linha)",
        value="\n".join(default_topics),
        height=150
    )
    topics = [t.strip() for t in topics_input.split("\n") if t.strip()]
    
    # Sliders para parâmetros
    max_candidates = st.slider("Máximo de candidatos a buscar", 100, 1000, 500, 100)
    top_k = st.slider("Número de artigos a exibir", 5, 50, 10, 5)
    
    # Data de referência (opcional)
    use_date = st.checkbox("Usar data específica")
    date_str = None
    if use_date:
        date = st.date_input("Data para buscar artigos")
        date_str = date.strftime("%Y/%m/%d")
    
    # Botão para buscar
    search_button = st.button("🔍 Buscar Artigos", type="primary")

# Função para processar a busca de artigos
async def search_articles():
    with st.spinner("Buscando artigos relevantes..."):
        try:
            df = await wiki_service.get_trending_articles(
                topics=topics,
                max_candidates=max_candidates,
                top_k=top_k,
                date_str=date_str
            )
            return df
        except Exception as e:
            st.error(f"Erro ao buscar artigos: {str(e)}")
            return pd.DataFrame()

# Função para processar análise de viés
def analyze_bias(text):
    with st.spinner("Analisando viés no texto..."):
        try:
            df_bias = bias_detector.analyze_text(text)
            summary = bias_detector.get_summary(df_bias)
            return df_bias, summary
        except Exception as e:
            st.error(f"Erro ao analisar viés: {str(e)}")
            return pd.DataFrame(), {}

# Armazenamento de estado na sessão
if 'articles_df' not in st.session_state:
    st.session_state.articles_df = pd.DataFrame()
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'bias_df' not in st.session_state:
    st.session_state.bias_df = pd.DataFrame()
if 'bias_summary' not in st.session_state:
    st.session_state.bias_summary = {}

# Processar busca quando o botão é clicado
if search_button:
    st.session_state.articles_df = asyncio.run(search_articles())
    st.session_state.selected_article = None
    st.session_state.bias_df = pd.DataFrame()
    st.session_state.bias_summary = {}

# Exibir resultados da busca
if not st.session_state.articles_df.empty:
    st.header("Artigos Encontrados")
    
    # Cria cards para cada artigo
    cols = st.columns(3)
    
    for i, (_, row) in enumerate(st.session_state.articles_df.iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                st.subheader(row['title'])
                if row.get('image'):
                    st.image(row['image'], width=200)
                st.markdown(f"**Views:** {row['views']}")
                st.markdown(f"**Resumo:** {row['summary'][:150]}...")
                
                # Botão para selecionar artigo
                if st.button(f"📝 Analisar Viés", key=f"btn_{i}"):
                    st.session_state.selected_article = row
                    content = row['content']
                    st.session_state.bias_df, st.session_state.bias_summary = analyze_bias(content)

# Exibir análise de viés se um artigo foi selecionado
if st.session_state.selected_article is not None:
    st.divider()
    st.header(f"Análise de Viés: {st.session_state.selected_article['title']}")
    
    # Resumo do artigo
    with st.expander("Detalhes do Artigo", expanded=True):
        st.markdown(f"**URL:** [{st.session_state.selected_article['url']}]({st.session_state.selected_article['url']})")
        st.markdown(f"**Resumo:** {st.session_state.selected_article['summary']}")
    
    # Resumo da análise de viés
    if st.session_state.bias_summary:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Nível de Viés", st.session_state.bias_summary['bias_level'])
        
        with col2:
            st.metric("Sentenças Subjetivas", 
                     f"{st.session_state.bias_summary['subjective_sentences']} ({st.session_state.bias_summary['perc_subjective']:.1f}%)")
        
        with col3:
            st.metric("Sentenças Neutras", 
                     f"{st.session_state.bias_summary['neutral_sentences']} ({st.session_state.bias_summary['perc_neutral']:.1f}%)")
        
        # Detalhes da análise por sentença
        if not st.session_state.bias_df.empty:
            st.subheader("Análise Detalhada por Sentença")
            
            # Adiciona cor às sentenças baseada no viés
            def highlight_bias(s):
                if s['label'] == 'SUBJECTIVE':
                    return ['background-color: #ffd6d6'] * len(s)
                elif s['label'] == 'NEUTRAL':
                    return ['background-color: #d6ffd6'] * len(s)
                return [''] * len(s)
            
            styled_df = st.session_state.bias_df.style.apply(highlight_bias, axis=1)
            st.dataframe(styled_df, use_container_width=True)

# Rodapé com créditos
st.divider()
st.markdown("**Nuvia** - Desenvolvido com Streamlit ❤️") 