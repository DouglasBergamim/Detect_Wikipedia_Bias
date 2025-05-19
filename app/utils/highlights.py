"""
Utilitários para destacar trechos com viés em textos
"""
import re
from .. import config

def format_text_with_bias_highlights(text, bias_df):
    """
    Formata o texto completo, destacando as frases subjetivas e formatando os títulos de seções.
    
    Args:
        text (str): O texto a ser formatado
        bias_df (DataFrame): DataFrame com as sentenças analisadas
        
    Returns:
        str: Texto formatado com HTML para destacar trechos enviesados
    """
    if bias_df is None or bias_df.empty:
        return format_section_titles(text)
    
    # Primeiro, vamos formatar os títulos de seções
    formatted_text = format_section_titles(text)
    
    # Ordenar as sentenças por comprimento (decrescente) para evitar substituições erradas
    # quando uma sentença é subconjunto de outra
    sorted_sentences = bias_df.sort_values(by='sentence', key=lambda x: x.str.len(), ascending=False)
    
    for _, row in sorted_sentences.iterrows():
        sentence = row['sentence']
        label = row['label']
        
        if label == 'SUBJECTIVE':
            # Verificar se a sentença não está vazia
            if not sentence or len(sentence.strip()) < 5:
                continue
                
            # Escapar caracteres especiais do regex
            sentence = sentence.strip()
            
            # Substituir a sentença pela versão destacada usando regex que evita substituir em atributos HTML
            if sentence in formatted_text:
                pattern = re.compile(rf'(?<!["\w]){re.escape(sentence)}(?![\w"])')
                formatted_text = pattern.sub(
                    f'<span style="{config.HIGHLIGHT_STYLE}">{sentence}</span>',
                    formatted_text,
                    count=1
                )
    
    return formatted_text

def format_section_titles(text):
    """
    Transforma marcações =, ==, === em <h1>/<h2>/<h3> válidos
    e converte blocos vazios em parágrafos. Garante que <p>
    nunca abrace um <h*>.
    """
    # CSS para os títulos - será definido uma única vez no bias_report.py
    css = ""
    
    # 1. Substitui cabeçalhos, mantendo quebras de linha
    tmp = text
    
    # Remover qualquer string que pareça um "section-h" incorreto
    tmp = re.sub(r'"section-h[123]">', '', tmp)
    
    # Padrões de cabeçalho mais flexíveis que funcionam mesmo se não estiverem no início da linha
    # Primeiro processamos h3 (===), depois h2 (==) e por fim h1 (=)
    tmp = re.sub(r'===\s*([^=\n]+?)\s*===', r'\n<h3>\1</h3>\n', tmp)
    tmp = re.sub(r'==\s*([^=\n]+?)\s*==', r'\n<h2>\1</h2>\n', tmp)
    tmp = re.sub(r'=\s*([^=\n]+?)\s*=', r'\n<h1>\1</h1>\n', tmp)

    # 2. Constrói parágrafos: para cada bloco separado por linha vazia
    html_parts = []
    for block in re.split(r'\n{2,}', tmp.strip()):
        block = block.strip()
        # Se o bloco **já** é um cabeçalho (<h1|h2|h3>), não embrulhar
        if re.match(r'^<h[1-3]>', block):
            html_parts.append(block)
        else:
            html_parts.append(f'<p>{block}</p>')

    return f'<div class="section-content">\n' + "\n".join(html_parts) + "\n</div>" 