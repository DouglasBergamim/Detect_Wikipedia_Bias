"""
Componente para exibição de cartões de artigos em grid
"""
import streamlit as st
import math
import os
import sys
import base64
from pathlib import Path
import pandas as pd

# Adicionar o diretório raiz ao sys.path para permitir importações absolutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import config
from app.services import registry
from app.utils.state import ss

# Carrega a imagem padrão da Wikipedia para quando não houver imagem disponível
WIKI_LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "static/images/wiki_logo.png")
DEFAULT_IMAGE = "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Wikipedia-logo-v2.svg/1200px-Wikipedia-logo-v2.svg.png"

# CSS para cards com tamanho padronizado
CARD_CSS = f"""
<style>
    .article-card {{
        height: {config.CARD_HEIGHT};
        overflow: hidden;
        position: relative;
        margin-bottom: 15px;
        border-radius: 8px;
        border: 1px solid #e6e6e6;
        padding: 12px;
        background-color: white;
    }}
    
    .article-image {{
        height: {config.CARD_IMAGE_HEIGHT};
        display: flex;
        align-items: center;
        justify-content: center;
        overflow: hidden;
        margin-bottom: 10px;
    }}
    
    .article-image img {{
        max-height: {config.CARD_IMAGE_HEIGHT};
        max-width: 100%;
        object-fit: contain;
        border-radius: 8px;
    }}
    
    .article-title {{
        font-size: 18px;
        font-weight: bold;
        margin-bottom: 8px;
        height: 50px;
        overflow: hidden;
    }}
    
    .article-topics {{
        font-size: 14px;
        color: #555;
        margin-bottom: 8px;
    }}
    
    .article-views {{
        font-size: 14px;
        color: #666;
        margin-bottom: 12px;
    }}
    
    .article-summary {{
        font-size: 14px;
        color: #333;
        height: 120px;
        overflow: hidden;
        margin-bottom: 15px;
    }}
    
    .article-button {{
        text-align: center;
    }}
    
    /* Esconder botões extras */
    .hidden-button {{
        display: none !important;
    }}
</style>
"""

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

def article_grid(articles_df, per_page):
    """Renderiza os cartões de artigos em grid com paginação"""
    if not isinstance(articles_df, pd.DataFrame) or articles_df.empty:
        st.info("Nenhum artigo encontrado. Tente ajustar os tópicos de busca.")
        return
    
    try:
        # Inject CSS
        st.markdown(CARD_CSS, unsafe_allow_html=True)
        
        total_pages = max(1, math.ceil(len(articles_df) / per_page))
        
        st.header(f"Artigos Encontrados ({len(articles_df)} resultados)")
        
        # Botões de navegação
        col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
        
        # Garantir que o índice da página é válido
        if ss.page < 0 or ss.page >= total_pages:
            ss.page = 0
        
        with col1:
            if st.button("⬅️ Anterior", disabled=ss.page <= 0):
                ss.page -= 1
                st.rerun()
                
        with col2:
            st.markdown(f"**Página {ss.page + 1} de {total_pages}**")
            
        with col3:
            page_options = [i+1 for i in range(total_pages)]
            selected_page = st.selectbox("Ir para página", page_options, index=min(ss.page, len(page_options)-1))
            if selected_page - 1 != ss.page:
                ss.page = selected_page - 1
                st.rerun()
        
        with col4:
            if st.button("Próxima ➡️", disabled=ss.page >= total_pages - 1):
                ss.page += 1
                st.rerun()

        # Calcular o slice para a página atual
        start_idx = ss.page * per_page
        end_idx = min(start_idx + per_page, len(articles_df))
        
        # Mostrar artigos da página atual
        st.markdown("---")
        
        # Criar cards em grid de 3 colunas para os artigos
        cols = st.columns(3)
        
        # Verificar se o slice é válido
        if start_idx < len(articles_df) and end_idx <= len(articles_df):
            for i, (_, row) in enumerate(articles_df.iloc[start_idx:end_idx].iterrows()):
                col_idx = i % 3
                
                try:
                    # Extrair tópicos e preparar dados
                    topics = []
                    if 'topics' in ss.articles_df.iloc[0]:
                        topics = ss.articles_df.iloc[0].get('topics', [])
                    article_topics = extract_topics(row, topics)
                    
                    image_url = row.get('image') if row.get('image') else config.DEFAULT_WIKI_IMAGE
                    
                    # Criar um ID único para este card
                    card_id = f"card_{start_idx + i}"
                    
                    # Adicionar uma div vazia para servir como espaçador
                    cols[col_idx].markdown("<div style='height: 0px;'></div>", unsafe_allow_html=True)
                    
                    # Exibir o card usando HTML para melhor controle do design
                    card_html = f"""
                    <div class="article-card" id="{card_id}">
                        <div class="article-image">
                            <img src="{image_url}" alt="{row['title']}">
                        </div>
                        <div class="article-title">{row['title']}</div>
                        <div class="article-topics"><b>Assuntos:</b> {', '.join(article_topics)}</div>
                        <div class="article-views"><b>Visualizações:</b> {row['views']:,}</div>
                        <div class="article-summary">{row['summary'][:250]}...</div>
                    </div>
                    """
                    
                    cols[col_idx].markdown(card_html, unsafe_allow_html=True)
                    
                    # Botão real para analisar viés
                    if cols[col_idx].button(f"📝 Analisar Viés", key=f"btn_{start_idx + i}"):
                        # Analisar o viés diretamente aqui
                        with st.spinner("Analisando viés e argumentos faltantes no texto..."):
                            content = row['content']
                            
                            try:
                                # Analisar viés
                                structured_bias_df = registry.bias.analyze_text(content)
                                bias_df = structured_bias_df.copy()  # Manter compatibilidade com código existente
                                bias_summary = registry.bias.get_summary(structured_bias_df)
                                
                                # Iniciar análise assíncrona de argumentos faltantes
                                import asyncio
                                async def run_args_analysis():
                                    # Análise de argumentos faltantes (em paralelo)
                                    try:
                                        print("Iniciando análise de argumentos faltantes...")
                                        missing_args = await registry.args_analyzer.analyze_article_missing_args(content)
                                        print(f"Análise de argumentos concluída. Resultados: {bool(missing_args)}, tipo: {type(missing_args)}")
                                        
                                        if missing_args:
                                            print(f"Seções encontradas com argumentos faltantes: {list(missing_args.keys())}")
                                        else:
                                            print("Nenhum argumento faltante encontrado.")
                                            
                                        missing_args_summary = await registry.args_analyzer.summarize_missing_args(missing_args)
                                        print(f"Resumo de argumentos concluído. Resultados: {len(missing_args_summary)} itens")
                                        
                                        return missing_args, missing_args_summary
                                    except Exception as e:
                                        print(f"ERRO detalhado na análise de argumentos: {type(e).__name__} - {str(e)}")
                                        # Tentar registrar mais detalhes da exceção
                                        import traceback
                                        traceback.print_exc()
                                        return {}, []
                                
                                # Aplicar patch para asyncio funcionar com Streamlit
                                import nest_asyncio
                                nest_asyncio.apply()
                                
                                # Executar análise assíncrona
                                try:
                                    missing_args, missing_args_summary = asyncio.run(run_args_analysis())
                                    print(f"Análise de argumentos completa. Dados: args={bool(missing_args)}, summary={len(missing_args_summary)}")
                                except Exception as e:
                                    st.warning(f"Erro na análise de argumentos: {e}")
                                    print(f"ERRO ao executar análise de argumentos: {e}")
                                    missing_args, missing_args_summary = {}, []
                                
                                # Armazenar resultados
                                from app.utils.state import store_analysis_results
                                store_analysis_results(
                                    article=row,
                                    bias_df=bias_df,
                                    structured_bias_df=structured_bias_df,
                                    bias_summary=bias_summary,
                                    missing_args=missing_args,
                                    missing_args_summary=missing_args_summary
                                )
                                print(f"Resultados armazenados no estado. missing_args={bool(missing_args)}, summary={len(missing_args_summary)}")
                                
                                # Rerun para mostrar o relatório
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erro ao analisar o artigo: {e}")
                except Exception as e:
                    st.error(f"Erro ao renderizar card: {e}")
        else:
            st.error("Problema na paginação. Tente navegar de volta para a primeira página.")
    except Exception as e:
        st.error(f"Erro ao renderizar os artigos: {e}")
        return 