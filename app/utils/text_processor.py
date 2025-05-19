"""
Utilities for structured text processing
"""
import re
import pandas as pd
from typing import List, Dict, Tuple, Optional
import nltk
from nltk.tokenize import sent_tokenize

# Ensure we have the necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

def split_sections(wiki_text: str) -> pd.DataFrame:
    """
    Structures the text into sections and sentences.
    Args:
        wiki_text: Wikipedia article text
    Returns:
        DataFrame with columns: section, section_uid, sentence, sent_idx, start_char, end_char
    """
    print(f"Processing text with {len(wiki_text)} characters to extract sections...")
    # Improved pattern to capture headers with indentation
    header_pat = re.compile(r'^\s*(={2,6})\s*(.*?)\s*\1\s*$', re.M)
    sections = []
    current = None
    # Process each header found
    for idx, m in enumerate(header_pat.finditer(wiki_text)):
        header_text = m.group(0)
        section_title = m.group(2).strip()
        header_level = len(m.group(1))
        print(f"Header found: '{header_text}' → Title: '{section_title}', Level: {header_level}")
        if current is not None:  # Explicitly check if not None
            current["end"] = m.start()
            sections.append(current)
        # Create new section as explicit dictionary
        current = dict(
            title=section_title,
            level=header_level,
            uid=f"{header_level}-{idx}",  # Unique identifier: level-counter
            start=m.end(),
            end=None,
            raw_header=header_text
        )
    
    # Last section (or entire article without headers)
    if current is not None:
        current["end"] = len(wiki_text)
        sections.append(current)
    elif not sections:  # Entire article without headers
        sections = [{
            "title": "Introduction",
            "uid": "0-0",
            "level": 2,
            "start": 0,
            "end": len(wiki_text),
            "raw_header": "Introduction"
        }]
        print("No headers found. Treating entire text as 'Introduction'.")
    
    # Check for overlaps or gaps
    for i in range(len(sections) - 1):
        if sections[i]["end"] != sections[i + 1]["start"]:
            print(f"WARNING: Possible problem between sections '{sections[i]['title']}' and '{sections[i+1]['title']}'")
            print(f"  End of previous section: {sections[i]['end']}")
            print(f"  Start of next section: {sections[i+1]['start']}")
    
    # Process each section and extract sentences
    print(f"Processing {len(sections)} sections to extract sentences...")
    rows = []
    
    for sec_idx, sec in enumerate(sections):
        # Extract text from this section without strip() to keep exact positions
        chunk = wiki_text[sec["start"]:sec["end"]]
        
        # Skip if section is empty
        if not chunk or chunk.isspace():
            print(f"Empty section: '{sec['title']}' - Skipping")
            continue
        
        # Calculate leading whitespace offset if necessary (for debug)
        leading_whitespace = len(chunk) - len(chunk.lstrip())
        if leading_whitespace > 0:
            print(f"Section '{sec['title']}' has {leading_whitespace} characters of whitespace at the beginning")
        
        # Initial offset is exactly the start of the section
        offset = sec["start"]
        
        # Use NLTK to divide into sentences
        try:
            sentences = sent_tokenize(chunk)
            print(f"Section '{sec['title']}': {len(sentences)} sentences found")
            
            for sent_idx, sent in enumerate(sentences):
                # Don't strip() the sentence to keep its relative position in the text
                if not sent:
                    continue
                
                # Find exact position from current offset
                start = wiki_text.find(sent, offset)
                if start >= 0:
                    end = start + len(sent)  # end calculated before any strip()
                    offset = end  # next search starts after this sentence
                else:
                    # Simple fallback if sentence not found exactly
                    print(f"WARNING: Unable to find exact position for sentence in '{sec['title']}': {sent[:30]}...")
                    start = offset  # Estimate starting at current offset
                    end = start + len(sent)
                    offset = end  # Continue from here
                
                # Add sentence to DataFrame
                rows.append({
                    "section_uid": sec["uid"],
                    "section": sec["title"],
                    "section_level": sec["level"],
                    "section_index": sec_idx,  # Use loop index directly, more efficient
                    "sentence": sent.strip(),  # Strip only for display, doesn't affect calculated positions above
                    "sent_idx": sent_idx,
                    "start_char": start,
                    "end_char": end
                })
        except Exception as e:
            print(f"ERROR processing section '{sec['title']}': {e}")
    
    # Create and return DataFrame
    result_df = pd.DataFrame(rows)
    print(f"Final dataframe created with {len(result_df)} rows.")
    return result_df

def get_sentence_context(df: pd.DataFrame, idx: int, n_before: int = 1, n_after: int = 1) -> str:
    """
    Gets the context (sentences before and after) of a specific sentence.
    
    Args:
        df: DataFrame with sentences
        idx: Index of target sentence
        n_before: Number of sentences to include before
        n_after: Number of sentences to include after
        
    Returns:
        Text with target sentence and its context
    """
    if df.empty or idx < 0 or idx >= len(df):
        return ""
    
    # Ensure we're within the same section
    section_uid = df.iloc[idx].get('section_uid', None)
    
    # If no section_uid, use section as fallback
    if section_uid is not None:
        same_section = df[df['section_uid'] == section_uid]
    else:
        section = df.iloc[idx]['section']
        same_section = df[df['section'] == section]
    
    # Find index within section
    section_idx = same_section.index.get_loc(idx)
    
    # Define limits
    start = max(0, section_idx - n_before)
    end = min(len(same_section), section_idx + n_after + 1)
    
    # Extract sentences
    context_sentences = same_section.iloc[start:end]['sentence'].tolist()
    
    # Join sentences with space
    return " ".join(context_sentences)

def highlight_sentence_in_context(context: str, target_sentence: str) -> str:
    """
    Highlights the target sentence within the context with HTML.
    
    Args:
        context: Text with context sentences
        target_sentence: Sentence to be highlighted
        
    Returns:
        HTML with highlighted sentence
    """
    if not target_sentence in context:
        return context
        
    # Replace target sentence with highlighted version
    highlighted = context.replace(
        target_sentence,
        f"<span style='background-color: #fff4bf; font-weight: bold;'>{target_sentence}</span>"
    )
    
    return highlighted 