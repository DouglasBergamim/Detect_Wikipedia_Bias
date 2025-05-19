"""
Componente para exibição de relatório de análise de viés
"""
import streamlit as st
import pandas as pd
import os
import sys

# Adicionar o diretório raiz ao sys.path para permitir importações absolutas
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import config
from app.utils.highlights import format_text_with_bias_highlights
from app.utils.state import ss

# CSS para o relatório de viés
REPORT_CSS = """
<style>
    .bias-report-container {
        background-color: white;
        padding: 20px;
        border-radius: 8px;
        border: 1px solid #e6e6e6;
        margin-top: 20px;
    }
    
    .bias-summary {
        padding: 15px;
        background-color: #f0f2f6; 
        border-radius: 5px;
        margin-bottom: 20px;
    }
    
    .bias-summary h3 {
        margin-top: 0;
        margin-bottom: 10px;
    }
    
    .bias-content {
        max-height: 600px;
        overflow-y: auto;
        padding: 10px;
        border: 1px solid #eee;
        border-radius: 5px;
        background-color: #fafafa;
    }
    
    /* Estilos para títulos de seção */
    .section-content {
        margin-bottom: 15px;
        line-height: 1.5;
    }
    
    .section-content h1 {
        font-size: 24px;
        font-weight: bold;
        margin-top: 20px;
        margin-bottom: 10px;
        padding-bottom: 5px;
        border-bottom: 1px solid #ddd;
        color: #333;
    }
    
    .section-content h2 {
        font-size: 20px;
        font-weight: bold;
        margin-top: 15px;
        margin-bottom: 8px;
        color: #444;
    }
    
    .section-content h3 {
        font-size: 18px;
        font-weight: bold;
        margin-top: 12px;
        margin-bottom: 6px;
        color: #555;
    }
    
    .section-content p {
        margin-bottom: 10px;
    }
</style>
"""

def show_bias_report(article):
    """Renderiza o relatório completo de análise de viés de um artigo"""
    if article is None:
        return
    
    # Inject custom CSS
    st.markdown(REPORT_CSS, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Container para a análise de viés
    st.markdown('<div class="bias-report-container">', unsafe_allow_html=True)
    
    st.header(f"Análise de Viés: {article['title']}")
    
    # Verifica se temos resultados válidos
    if ss.bias_df.empty or not ss.bias_summary:
        st.warning("Não foi possível analisar o viés deste artigo.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Resumo da análise de viés
    # Informações sobre o viés no topo
    bias_level = ss.bias_summary['bias_level']
    perc_subjective = ss.bias_summary['perc_subjective']
    
    # Cores baseadas no nível de viés
    color = config.BIAS_LEVELS.get(bias_level, "gray")
    
    # Mostrar resumo do viés no topo
    st.markdown(f"""
    <div class="bias-summary">
        <h3>Resumo da Análise</h3>
        <p>Este artigo tem <span style="color: {color}; font-weight: bold;">{perc_subjective:.1f}% de conteúdo subjetivo</span>, 
        indicando um nível de viés <span style="color: {color}; font-weight: bold;">{bias_level}</span>.</p>
        <p>Foram analisadas {ss.bias_summary['total_sentences']} sentenças no total.</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Barra de progresso para visualizar o viés
    st.progress(perc_subjective / 100, text=f"Conteúdo subjetivo: {perc_subjective:.1f}%")
    
    # Botão para ver o artigo original
    st.markdown(f"[📄 Ver artigo original na Wikipedia]({article['url']})")
    
    # Mostrar o texto completo com trechos destacados
    if not ss.bias_df.empty:
        st.markdown("### Artigo com destaques para trechos subjetivos")
        
        # Formatar o texto com destaques para os trechos subjetivos e títulos formatados
        highlighted_text = format_text_with_bias_highlights(
            article['content'], 
            ss.bias_df
        )
        
        # Exibir o texto formatado em uma área de conteúdo rolável
        st.markdown('<div class="bias-content">', unsafe_allow_html=True)
        st.markdown(highlighted_text, unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Informações adicionais
        with st.expander("📊 Ver detalhes da análise"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric(
                    "Sentenças Subjetivas", 
                    f"{ss.bias_summary['subjective_sentences']} ({ss.bias_summary['perc_subjective']:.1f}%)"
                )
            
            with col2:
                st.metric(
                    "Sentenças Neutras", 
                    f"{ss.bias_summary['neutral_sentences']} ({ss.bias_summary['perc_neutral']:.1f}%)"
                )
            
            # Filtro opcional para ver apenas as frases com viés
            filter_option = st.radio(
                "Mostrar sentenças:", 
                ["Apenas Subjetivas", "Apenas Neutras", "Todas"],
                horizontal=True
            )
            
            filtered_df = ss.bias_df
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
    
    # Mostrar argumentos faltantes, se disponíveis
    if ss.missing_args_summary:
        st.markdown("### 🔍 Argumentos e Pontos de Vista Ausentes")
        
        st.info(
            "Esta seção identifica argumentos, contra-argumentos ou perspectivas importantes "
            "que poderiam enriquecer o artigo e fornecer uma visão mais equilibrada do tema."
        )
        
        # Exibir os argumentos resumidos
        for i, arg in enumerate(ss.missing_args_summary):
            with st.container():
                st.markdown(f"""
                **Ponto #{i+1}:** {arg.get('argument')}
                
                *Origem: Seção '{arg.get('section')}'*
                """)
                st.divider()
                
        # Botão para ver detalhes completos
        if ss.missing_args:
            with st.expander("📑 Ver detalhes completos por seção"):
                for section, args_list in ss.missing_args.items():
                    st.markdown(f"#### Seção: {section}")
                    for arg in args_list:
                        priority = arg.get('priority', 'N/A')
                        st.markdown(f"""
                        **Prioridade {priority}:** {arg.get('argument')}
                        """)
                    st.markdown("---")
    
    st.markdown('</div>', unsafe_allow_html=True) 