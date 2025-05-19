import re
from .. import config

def format_text_with_bias_highlights(text, bias_df):
    """
    Formats the complete text, highlighting subjective sentences and formatting section titles.
    
    Args:
        text (str): The text to be formatted
        bias_df (DataFrame): DataFrame containing analyzed sentences
        
    Returns:
        str: Text formatted with HTML to highlight biased passages
    """
    if bias_df is None or bias_df.empty:
        return format_section_titles(text)
    
    # First, let's format the section titles
    formatted_text = format_section_titles(text)
    
    # Sort sentences by length (descending) to avoid incorrect substitutions
    # when one sentence is a subset of another
    sorted_sentences = bias_df.sort_values(by='sentence', key=lambda x: x.str.len(), ascending=False)
    
    for _, row in sorted_sentences.iterrows():
        sentence = row['sentence']
        label = row['label']
        
        if label == 'SUBJECTIVE':
            # Check if the sentence is not empty
            if not sentence or len(sentence.strip()) < 5:
                continue
                
            # Escape special regex characters
            sentence = sentence.strip()
            
            # Replace the sentence with the highlighted version using regex that avoids replacing in HTML attributes
            if sentence in formatted_text:
                pattern = re.compile(rf'(?<!["\w]){re.escape(sentence)}(?![\w"])')
                formatted_text = pattern.sub(
                    f'<span style="{config.HIGHLIGHT_STYLE}">{sentence}</span>',
                    formatted_text,
                    count=1
                )
    
    return formatted_text

def format_text_with_selectable_bias(text, bias_df):
    """
    Formats the text to allow selection of biased passages using checkboxes.
    
    Args:
        text (str): The text to be formatted
        bias_df (DataFrame): DataFrame containing analyzed sentences
        
    Returns:
        str: Text formatted with checkboxes to select biased passages
    """
    if bias_df is None or bias_df.empty:
        return format_section_titles(text)
    
    # First, let's format the section titles
    formatted_text = format_section_titles(text)
    
    # Filter only subjective sentences
    subjective_sentences = bias_df[bias_df['label'] == 'SUBJECTIVE']
    
    # Sort sentences by length (descending) to avoid incorrect substitutions
    sorted_sentences = subjective_sentences.sort_values(by='sentence', key=lambda x: x.str.len(), ascending=False)
    
    for i, (_, row) in enumerate(sorted_sentences.iterrows()):
        sentence = row['sentence']
        
        # Check if the sentence is not empty
        if not sentence or len(sentence.strip()) < 5:
            continue
            
        # Escape special regex characters
        sentence = sentence.strip()
        
        # Replace the sentence with the highlighted version with checkbox
        if sentence in formatted_text:
            pattern = re.compile(rf'(?<!["\w]){re.escape(sentence)}(?![\w"])')
            formatted_text = pattern.sub(
                f'<div style="{config.HIGHLIGHT_STYLE}"><input type="checkbox" id="check_{i}" name="check_{i}" value="{sentence}"> {sentence}</div>',
                formatted_text,
                count=1
            )
    
    return formatted_text

def format_section_titles(text):
    """
    Transforms =, ==, === markings into valid <h1>/<h2>/<h3>
    and converts empty blocks into paragraphs. Ensures that <p>
    never wraps a <h*>.
    """
    # CSS for titles - will be defined once in bias_report.py
    css = ""
    
    # 1. Replace headers, maintaining line breaks
    tmp = text
    
    # Remove any string that looks like an incorrect "section-h"
    tmp = re.sub(r'"section-h[123]">', '', tmp)
    
    # More flexible header patterns that work even if not at the start of the line
    # First process h3 (===), then h2 (==) and finally h1 (=)
    tmp = re.sub(r'===\s*([^=\n]+?)\s*===', r'\n<h3>\1</h3>\n', tmp)
    tmp = re.sub(r'==\s*([^=\n]+?)\s*==', r'\n<h2>\1</h2>\n', tmp)
    tmp = re.sub(r'=\s*([^=\n]+?)\s*=', r'\n<h1>\1</h1>\n', tmp)

    # 2. Build paragraphs: for each block separated by empty line
    html_parts = []
    for block in re.split(r'\n{2,}', tmp.strip()):
        block = block.strip()
        # If the block is **already** a header (<h1|h2|h3>), don't wrap it
        if re.match(r'^<h[1-3]>', block):
            html_parts.append(block)
        else:
            html_parts.append(f'<p>{block}</p>')

    return f'<div class="section-content">\n' + "\n".join(html_parts) + "\n</div>"