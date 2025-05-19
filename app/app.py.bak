import streamlit as st
import asyncio
import pandas as pd
import nest_asyncio
import time
import os
import sys
import math
import re

# Log para debugar
print("1. Iniciando aplicação...")

# Aplicando patch para asyncio funcionar com Streamlit
nest_asyncio.apply()

# Configuração da página
st.set_page_config(
    page_title="Nuvia - Análise de Artigos",
    page_icon="📚",
    layout="wide"
)

print("2. Configuração da página concluída")

# Título principal
st.title("📚 Nuvia - Análise de Artigos da Wikipedia")
st.markdown("Descubra artigos relevantes e analise seu viés")

print("3. Título e descrição adicionados")

# Verificar se os modelos já foram baixados
models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "models")
models_downloaded = os.path.exists(models_dir) and len(os.listdir(models_dir)) > 0

print("4. Verificação de modelos concluída. Modelos baixados:", models_downloaded)

# Mostrar informações sobre o carregamento inicial
if not models_downloaded:
    st.warning("⚠️ Primeira execução: O modelo BERT será baixado automaticamente. Isso pode levar alguns minutos.")
    st.info("💡 Dica: Para acelerar futuras execuções, você pode executar o script de download antecipado: `python app/download_model.py`")

print("5. Iniciando carregamento dos serviços...")

# Inicialização dos serviços com barra de progresso
with st.spinner("Carregando serviços..."):
    try:
        # Importações
        from wiki_service import WikiService
        from bias_detector import BiasDetector
        
        # Inicialização dos serviços (uma única vez)
        @st.cache_resource
        def load_services():
            print("5.5 Iniciando WikiService")
            wiki = WikiService()
            print("5.6 Iniciando BiasDetector")
            bias = BiasDetector()
            print("5.7 Serviços carregados com sucesso")
            return wiki, bias
        
        print("5.8 Chamando load_services")
        wiki_service, bias_detector = load_services()
        print("5.9 Serviços atribuídos às variáveis")
    except Exception as e:
        import traceback
        print("ERRO no carregamento:", str(e))
        traceback.print_exc()
        st.error(f"Erro ao carregar serviços: {str(e)}")
        sys.exit(1)

print("6. Carregamento de serviços concluído")

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
    total_articles = st.slider("Quantidade de artigos relevantes", 5, 100, 20, 5)
    
    # Artigos por página
    articles_per_page = st.slider("Artigos por página", 3, 15, 6, 3)
    
    # Data de referência (opcional)
    use_date = st.checkbox("Usar data específica")
    date_str = None
    if use_date:
        date = st.date_input("Data para buscar artigos")
        date_str = date.strftime("%Y/%m/%d")
    
    # Botão para buscar
    search_button = st.button("🔍 Buscar Artigos", type="primary")

print("7. Sidebar configurada")

# Função para extrair assuntos de um artigo
def extract_topics(article, all_topics):
    """Extrai os tópicos mencionados no artigo baseado nos tópicos de busca"""
    article_text = (article['title'] + ' ' + article['summary'] + ' ' + article['content']).lower()
    mentioned_topics = []
    
    for topic in all_topics:
        if topic.lower() in article_text:
            mentioned_topics.append(topic)
    
    # Se não encontrou nenhum tópico, pega o primeiro tópico da busca
    if not mentioned_topics and all_topics:
        mentioned_topics = [all_topics[0]]
        
    return mentioned_topics

# Função para processar a busca de artigos
async def search_articles():
    with st.spinner("Buscando artigos relevantes..."):
        try:
            df = await wiki_service.get_trending_articles(
                topics=topics,
                top_k=total_articles,
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

# Função para formatar o texto com destaque aos trechos enviesados
def format_text_with_bias_highlights(text, bias_df):
    """Formata o texto completo, destacando as frases subjetivas"""
    if bias_df.empty:
        return text
    
    # Criar uma versão do texto onde cada sentença subjetiva é destacada
    highlighted_text = text
    
    # Ordenar as sentenças por comprimento (decrescente) para evitar substituições erradas
    # quando uma sentença é subconjunto de outra
    sorted_sentences = bias_df.sort_values(by='sentence', key=lambda x: x.str.len(), ascending=False)
    
    for _, row in sorted_sentences.iterrows():
        sentence = row['sentence']
        label = row['label']
        
        if label == 'SUBJECTIVE':
            # Escapar caracteres especiais do regex
            escaped_sentence = re.escape(sentence)
            # Substituir a sentença pela versão destacada
            highlighted_text = re.sub(
                f"({escaped_sentence})", 
                r'<span style="background-color: #ffdddd; font-weight: bold;">\1</span>', 
                highlighted_text
            )
    
    return highlighted_text

print("8. Funções de busca e análise definidas")

# Armazenamento de estado na sessão
if 'articles_df' not in st.session_state:
    st.session_state.articles_df = pd.DataFrame()
if 'selected_article' not in st.session_state:
    st.session_state.selected_article = None
if 'bias_df' not in st.session_state:
    st.session_state.bias_df = pd.DataFrame()
if 'bias_summary' not in st.session_state:
    st.session_state.bias_summary = {}
if 'current_page' not in st.session_state:
    st.session_state.current_page = 0

print("9. Estado da sessão inicializado")

# Processar busca quando o botão é clicado
if search_button:
    with st.spinner("Buscando artigos... Isso pode levar alguns segundos."):
        st.session_state.articles_df = asyncio.run(search_articles())
        st.session_state.selected_article = None
        st.session_state.bias_df = pd.DataFrame()
        st.session_state.bias_summary = {}
        st.session_state.current_page = 0

print("10. Busca concluída")

print("11. Verificando resultados da busca")

# Exibir resultados da busca com paginação
if not st.session_state.articles_df.empty:
    total_pages = math.ceil(len(st.session_state.articles_df) / articles_per_page)
    
    st.header(f"Artigos Encontrados ({len(st.session_state.articles_df)} resultados)")
    
    # Botões de navegação
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️ Anterior", disabled=st.session_state.current_page <= 0):
            st.session_state.current_page -= 1
            st.rerun()
            
    with col2:
        st.markdown(f"**Página {st.session_state.current_page + 1} de {total_pages}**")
        
    with col3:
        page_options = [i+1 for i in range(total_pages)]
        selected_page = st.selectbox("Ir para página", page_options, index=st.session_state.current_page)
        if selected_page - 1 != st.session_state.current_page:
            st.session_state.current_page = selected_page - 1
            st.rerun()
    
    with col4:
        if st.button("Próxima ➡️", disabled=st.session_state.current_page >= total_pages - 1):
            st.session_state.current_page += 1
            st.rerun()

    # Calcular o slice para a página atual
    start_idx = st.session_state.current_page * articles_per_page
    end_idx = min(start_idx + articles_per_page, len(st.session_state.articles_df))
    
    # Mostrar artigos da página atual
    st.markdown("---")
    
    # Criar cards em grid de 3 colunas para os artigos
    cols = st.columns(3)
    
    for i, (_, row) in enumerate(st.session_state.articles_df.iloc[start_idx:end_idx].iterrows()):
        with cols[i % 3]:
            with st.container(border=True):
                # Título do artigo
                st.subheader(row['title'])
                
                # Imagem do artigo
                if row.get('image'):
                    st.image(row['image'], width=200)
                else:
                    # Placeholder para quando não há imagem
                    st.markdown("📄")
                
                # Assuntos abordados
                article_topics = extract_topics(row, topics)
                st.markdown(f"**Assuntos:** {', '.join(article_topics)}")
                
                # Número de visualizações
                st.markdown(f"**Visualizações:** {row['views']:,}")
                
                # Botão para selecionar artigo
                if st.button(f"📝 Analisar Viés", key=f"btn_{start_idx + i}"):
                    st.session_state.selected_article = row
                    content = row['content']
                    st.session_state.bias_df, st.session_state.bias_summary = analyze_bias(content)
                    # Rola a página para a análise
                    st.rerun()

print("12. Verificando se há artigo selecionado")

# Exibir análise de viés se um artigo foi selecionado
if st.session_state.selected_article is not None:
    st.markdown("---")
    
    # Container para a análise de viés
    with st.container(border=True):
        st.header(f"Análise de Viés: {st.session_state.selected_article['title']}")
        
        # Resumo da análise de viés
        if st.session_state.bias_summary:
            # Informações sobre o viés no topo
            bias_level = st.session_state.bias_summary['bias_level']
            perc_subjective = st.session_state.bias_summary['perc_subjective']
            
            # Cores baseadas no nível de viés
            if bias_level == "Alto":
                color = "red"
            elif bias_level == "Médio":
                color = "orange"
            else:
                color = "green"
            
            # Mostrar resumo do viés no topo
            st.markdown(f"""
            <div style="padding: 10px; background-color: #f0f2f6; border-radius: 5px; margin-bottom: 20px;">
                <h3>Resumo da Análise</h3>
                <p>Este artigo tem <span style="color: {color}; font-weight: bold;">{perc_subjective:.1f}% de conteúdo subjetivo</span>, 
                indicando um nível de viés <span style="color: {color}; font-weight: bold;">{bias_level}</span>.</p>
                <p>Foram analisadas {st.session_state.bias_summary['total_sentences']} sentenças no total.</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Barra de progresso para visualizar o viés
            st.progress(perc_subjective / 100, text=f"Conteúdo subjetivo: {perc_subjective:.1f}%")
            
            # Botão para ver o artigo original
            st.markdown(f"[📄 Ver artigo original na Wikipedia]({st.session_state.selected_article['url']})")
            
            # Mostrar o texto completo com trechos destacados
            if not st.session_state.bias_df.empty:
                st.markdown("### Artigo com destaques para trechos subjetivos")
                
                # Formatar o texto com destaques para os trechos subjetivos
                highlighted_text = format_text_with_bias_highlights(
                    st.session_state.selected_article['content'], 
                    st.session_state.bias_df
                )
                
                # Exibir o texto formatado
                st.markdown(highlighted_text, unsafe_allow_html=True)
                
                # Informações adicionais
                with st.expander("📊 Ver detalhes da análise"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.metric(
                            "Sentenças Subjetivas", 
                            f"{st.session_state.bias_summary['subjective_sentences']} ({st.session_state.bias_summary['perc_subjective']:.1f}%)"
                        )
                    
                    with col2:
                        st.metric(
                            "Sentenças Neutras", 
                            f"{st.session_state.bias_summary['neutral_sentences']} ({st.session_state.bias_summary['perc_neutral']:.1f}%)"
                        )
                    
                    # Filtro opcional para ver apenas as frases com viés
                    filter_option = st.radio(
                        "Mostrar sentenças:", 
                        ["Apenas Subjetivas", "Apenas Neutras", "Todas"],
                        horizontal=True
                    )
                    
                    filtered_df = st.session_state.bias_df
                    if filter_option == "Apenas Subjetivas":
                        filtered_df = filtered_df[filtered_df['label'] == 'SUBJECTIVE']
                    elif filter_option == "Apenas Neutras":
                        filtered_df = filtered_df[filtered_df['label'] == 'NEUTRAL']
                    
                    st.dataframe(
                        filtered_df[['sentence', 'label', 'bias_score']],
                        column_config={
                            "sentence": "Sentença",
                            "label": "Classificação",
                            "bias_score": st.column_config.NumberColumn("Confiança", format="%.2f")
                        },
                        use_container_width=True
                    )

print("13. Adicionando rodapé")

# Rodapé com créditos
st.divider()

print("14. Aplicação carregada completamente!") 