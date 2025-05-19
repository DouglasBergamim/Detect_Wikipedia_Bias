"""
Component for displaying bias analysis report
"""
import streamlit as st
import pandas as pd
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app import config
from app.utils.highlights import format_text_with_bias_highlights
from app.utils.text_processor import get_sentence_context, highlight_sentence_in_context
from app.utils.state import ss
from app.services import registry

# CSS for the bias report
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
    
    /* Styles for section headers */
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
    
    .context-block {
        background-color: #f9f9f9;
        padding: 8px 12px;
        border-radius: 4px;
        margin-bottom: 8px;
        border-left: 3px solid #ddd;
    }
    
    .highlight-sentence {
        background-color: #fff4bf;
        font-weight: bold;
        padding: 2px 0;
    }
</style>
"""

def show_bias_report(article):
    """Renders the complete bias analysis report for an article"""
    if article is None:
        return
    
    # Inject custom CSS
    st.markdown(REPORT_CSS, unsafe_allow_html=True)
    
    st.markdown("---")
    
    #---------------------------------------#
    # REPORT HEADER & SUMMARY SECTION
    #---------------------------------------#
    st.markdown('<div class="bias-report-container">', unsafe_allow_html=True)
    st.header(f"Bias Analysis: {article['title']}")
    
    if ss.bias_df.empty or not ss.bias_summary:
        st.warning("Could not analyze the bias of this article.")
        st.markdown('</div>', unsafe_allow_html=True)
        return
    
    # Bias analysis summary
    bias_level = ss.bias_summary['bias_level']
    perc_subjective = ss.bias_summary['perc_subjective']
    
    color = config.BIAS_LEVELS.get(bias_level, "gray")
    
    # Show bias summary at the top
    st.markdown(f"""
    <div class="bias-summary">
        <h3>Bias Analysis Summary</h3>
        <p>This article has <span style="color: {color}; font-weight: bold;">{perc_subjective:.1f}% subjective content</span>, 
        indicating a bias level <span style="color: {color}; font-weight: bold;">{bias_level}</span>.</p>
        <p>A total of {ss.bias_summary['total_sentences']} sentences were analyzed.</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.progress(perc_subjective / 100, text=f"Subjective content: {perc_subjective:.1f}%")
    
    st.markdown(f"[📄 View original article on Wikipedia]({article['url']})")
    
    # Tabs to display different views
    tab1, tab2, tab3 = st.tabs(["Text with Highlights", "Select Passages for Correction", "Neutralized Text"])
    
    #---------------------------------------#
    # TAB 1: TEXT WITH HIGHLIGHTS
    #---------------------------------------#
    with tab1:
        if not ss.bias_df.empty:
            st.markdown("### Article with highlights for subjective passages")
            
            # Format the text with highlights for subjective passages and formatted titles
            highlighted_text = format_text_with_bias_highlights(
                article['content'], 
                ss.bias_df
            )
            
            # Display the formatted text in a scrollable content area
            st.markdown('<div class="bias-content">', unsafe_allow_html=True)
            st.markdown(highlighted_text, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
            
    #---------------------------------------#
    # TAB 2: SELECT PASSAGES FOR CORRECTION
    #---------------------------------------#
    with tab2:
        st.markdown("### Select subjective passages for correction")
        st.info("Select subjective passages grouped by section. Each passage is shown with context for better understanding.")
        
        # Check if we have the DataFrame structured by sections
        df = ss.structured_bias_df
        
        if df.empty:
            st.warning("Could not structure text into sections. Using legacy method.")
            # Show legacy method (as it was before)
            show_simple_selection_interface()
        else:
            # Filter only subjective passages
            subj_df = df[df['label'] == 'SUBJECTIVE'].copy()
            subj_df['orig_idx'] = subj_df.index  # Save the original index for context

            if subj_df.empty:
                st.success("No subjective passages found in this article!")
            else:
                filter_option = st.radio(
                    "Show:",
                    ["All sections", "Only sections with selected passages"],
                    horizontal=True
                )

                if 'section_uid' in subj_df.columns:
                    grouped = subj_df.groupby('section_uid')
                else:
                    st.warning("Improved section structure not found. Using legacy method.")
                    subj_df['section_normalized'] = subj_df['section'].str.strip()
                    grouped = subj_df.groupby('section_normalized')

                selection = dict(st.session_state.get("selection", {}))  # mutable copy
                tmp_selection = {}

                selected_count = sum(1 for v in selection.values() if v)
                st.info(f"**{selected_count}** passage(s) selected for neutralization.")

                sections_to_show = grouped.groups.keys()
                if filter_option == "Only sections with selected passages" and selected_count > 0:
                    sections_with_selection = set()
                    for key, is_selected in selection.items():
                        if is_selected:
                            section_key, _ = key.rsplit("-", 1)  # split correct UID
                            sections_with_selection.add(section_key)
                    sections_to_show = (s for s in sections_to_show if s in sections_with_selection)

                for section_id in sections_to_show:
                    section_df = grouped.get_group(section_id)
                    count_in_section = len(section_df)
                    original_section = section_df['section'].iloc[0] if not section_df.empty else section_id
                    if 'section_uid' in subj_df.columns:
                        selected_in_section = sum(1 for key, val in selection.items()
                                                  if key.startswith(f"{section_id}-") and val)
                    else:
                        selected_in_section = sum(1 for key, val in selection.items()
                                                  if key.startswith(f"{section_id}-") and val)
                    with st.expander(f"§ {original_section} — {selected_in_section}/{count_in_section} passage(s) selected"):
                        for i, row in section_df.iterrows():
                            sent = row['sentence']
                            uid = row.get('section_uid', section_id)
                            key = f"{uid}-{row['start_char']}"
                            cb_id = f"tab2-cb-{key}"  # ensures global uniqueness
                            checked = selection.get(key, False)
                            col1, col2 = st.columns([0.07, 0.93])
                            with col1:
                                new_val = st.checkbox("", key=cb_id, value=checked)
                            with col2:
                                ctx = get_sentence_context(df, row['orig_idx'], 1, 1)
                                st.markdown(f"<div class='context-block' style='max-width:700px;line-height:1.6'>{highlight_sentence_in_context(ctx, sent)}</div>", unsafe_allow_html=True)
                            tmp_selection[key] = new_val
                st.session_state.selection = tmp_selection
                selected_keys = [k for k, v in tmp_selection.items() if v]

                if selected_keys:
                    if st.button("Neutralize Selected Passages", type="primary"):
                        with st.spinner("Neutralizing passages..."):
                            selected_texts = []
                            for key in sorted(selected_keys, key=lambda k: int(k.rsplit('-', 1)[1])):
                                section_id, pos = key.rsplit("-", 1)
                                try:
                                    pos_int = int(pos)
                                    if 'section_uid' in subj_df.columns:
                                        matching_rows = subj_df[(subj_df['section_uid'] == section_id) &
                                                               (subj_df['start_char'] == pos_int)]
                                    else:
                                        matching_rows = subj_df[(subj_df['section_normalized'] == section_id) &
                                                               (subj_df['start_char'] == pos_int)]
                                    if matching_rows.empty:
                                        print(f"DEBUG: No exact sentence found with criteria in {section_id}-{pos_int}, trying alternative search")
                                        if 'section_uid' in subj_df.columns:
                                            matching_rows = subj_df[subj_df['section_uid'] == section_id]
                                        else:
                                            matching_rows = subj_df[subj_df['section_normalized'] == section_id]
                                except ValueError:
                                    print(f"DEBUG: Error converting position: {pos}")
                                    if 'section_uid' in subj_df.columns:
                                        matching_rows = subj_df[subj_df['section_uid'] == section_id]
                                    else:
                                        matching_rows = subj_df[subj_df['section_normalized'] == section_id]
                                if not matching_rows.empty:
                                    selected_texts.append(matching_rows.iloc[0]['sentence'])
                            ss.selected_biased_texts = selected_texts
                            neutralized = registry.debias.neutralize_multiple(selected_texts)
                            ss.neutralized_texts = neutralized
                            st.success(f"{len(neutralized)} passages successfully neutralized!")
                            # (Optional) st.session_state.active_tab = 3
                            st.rerun()
                else:
                    st.warning("Select at least one passage to neutralize.")
    
    #---------------------------------------#
    # TAB 3: NEUTRALIZED TEXT
    #---------------------------------------#
    with tab3:
        if ss.neutralized_texts:
            st.markdown("### Neutralization Results")
            display_mode = st.radio(
                "View:",
                ["Side by Side", "Before and After"],
                horizontal=True
            )
            if display_mode == "Side by Side":
                # Display side by side: original vs neutralized
                for original in ss.selected_biased_texts:
                    # Try to find the corresponding neutralized text
                    neutral = ss.neutralized_texts.get(original)
                    if not neutral:
                        # Try with strip
                        neutral = ss.neutralized_texts.get(original.strip())
                    if not neutral:
                        # Try finding by simple similarity (optional)
                        for k in ss.neutralized_texts:
                            if k.strip() == original.strip():
                                neutral = ss.neutralized_texts[k]
                                break
                    if not neutral:
                        neutral = "(No neutralization suggestion or matching error)"
                    with st.container():
                        col1, col2 = st.columns(2)
                        with col1:
                            st.markdown("**Original Text:**")
                            st.markdown(f'<div style="{config.HIGHLIGHT_STYLE}">{original}</div>', unsafe_allow_html=True)
                        with col2:
                            st.markdown("**Neutralized Text:**")
                            st.markdown(f'<div style="background-color: #e6f7ff; padding: 8px; border-radius: 4px;">{neutral}</div>', unsafe_allow_html=True)
                        st.divider()
            else:
                # Display before/after in list format
                for i, original in enumerate(ss.selected_biased_texts, 1):
                    neutral = ss.neutralized_texts.get(original)
                    if not neutral:
                        neutral = ss.neutralized_texts.get(original.strip())
                    if not neutral:
                        for k in ss.neutralized_texts:
                            if k.strip() == original.strip():
                                neutral = ss.neutralized_texts[k]
                                break
                    if not neutral:
                        neutral = "(No neutralization suggestion or matching error)"
                    st.markdown(f"#### Example {i}")
                    st.markdown("**Original Text:**")
                    st.markdown(f'<div style="{config.HIGHLIGHT_STYLE}">{original}</div>', unsafe_allow_html=True)
                    st.markdown("**Neutralized Text:**")
                    st.markdown(f'<div style="background-color: #e6f7ff; padding: 8px; border-radius: 4px;">{neutral}</div>', unsafe_allow_html=True)
                    st.divider()
        else:
            if ss.selected_biased_texts:
                st.info("Passages are selected but not yet neutralized. Go to the 'Select Passages' tab and click 'Neutralize'.")
            else:
                st.info("Select passages in the 'Select Passages' tab to see the neutralization results here.")
    
    #---------------------------------------#
    # ANALYSIS DETAILS EXPANDER
    #---------------------------------------#
    with st.expander("📊 View analysis details"):
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric(
                "Subjective Sentences", 
                f"{ss.bias_summary['subjective_sentences']} ({ss.bias_summary['perc_subjective']:.1f}%)"
            )
        
        with col2:
            st.metric(
                "Neutral Sentences", 
                f"{ss.bias_summary['neutral_sentences']} ({ss.bias_summary['perc_neutral']:.1f}%)"
            )
        
        # If you have the summary by sections, show it too
        if 'sections_summary' in ss.bias_summary:
            st.markdown("### Bias distribution by section")
            section_data = {}
            for section, count in ss.bias_summary['sections_summary'].items():
                section_data[section] = count
            
            if section_data:
                section_df = pd.DataFrame(list(section_data.items()), 
                                       columns=['Section', 'Subjective Passages'])
                section_df = section_df.sort_values('Subjective Passages', ascending=False)
                st.dataframe(section_df, use_container_width=True)
        
        # Optional filter to see only biased sentences
        filter_option = st.radio(
            "Show sentences:", 
            ["Only Subjective", "Only Neutral", "All"],
            horizontal=True
        )
        
        filtered_df = ss.bias_df
        if filter_option == "Only Subjective":
            filtered_df = filtered_df[filtered_df['label'] == 'SUBJECTIVE']
        elif filter_option == "Only Neutral":
            filtered_df = filtered_df[filtered_df['label'] == 'NEUTRAL']
        
        st.dataframe(
            filtered_df[['section', 'sentence', 'label', 'bias_score']],
            column_config={
                "section": "Section",
                "sentence": "Sentence",
                "label": "Classification",
                "bias_score": st.column_config.NumberColumn("Confidence", format="%.2f")
            },
            use_container_width=True
        )
    
    #---------------------------------------#
    # MISSING ARGUMENTS EXPANDER
    #---------------------------------------#
    with st.expander("🔍 Missing Arguments and Perspectives"):
        print(f"DEBUG - Checking for missing arguments. Available: {bool(ss.missing_args_summary)}")
        print(f"DEBUG - State: missing_args={bool(ss.missing_args)}, missing_args_summary={len(ss.missing_args_summary) if isinstance(ss.missing_args_summary, list) else 'not a list'}")
        
        if ss.missing_args_summary:
            st.info(
                "This section identifies important arguments, counter-arguments, or perspectives "
                "that could enrich the article and provide a more balanced view of the topic."
            )
            
            # Show summarized arguments
            for i, arg in enumerate(ss.missing_args_summary):
                with st.container():
                    st.markdown(f"""
                    **Point #{i+1}:** {arg.get('argument')}
                    
                    *Origin: Section '{arg.get('section')}'*
                    """)
                    st.divider()
                    
            # Full details (without using expander)
            if ss.missing_args:
                if st.button("📑 View full details by section", key="btn_missing_args_details"):
                    st.markdown("### Full details by section")
                    for section, args_list in ss.missing_args.items():
                        st.markdown(f"#### Section: {section}")
                        for arg in args_list:
                            priority = arg.get('priority', 'N/A')
                            st.markdown(f"""
                            **Priority {priority}:** {arg.get('argument')}
                            """)
                        st.markdown("---")
        else:
            st.warning("No missing argument or perspective was identified in this article.")
            
            # Show state status for diagnosis
            if st.checkbox("Show diagnostic details"):
                st.markdown("#### Diagnostic Information:")
                st.markdown(f"- missing_args_summary: {type(ss.missing_args_summary)} with {len(ss.missing_args_summary) if hasattr(ss.missing_args_summary, '__len__') else 'N/A'} items")
                st.markdown(f"- missing_args: {type(ss.missing_args)} with {len(ss.missing_args) if hasattr(ss.missing_args, '__len__') else 'N/A'} items")
                
                # Show content if available
                if ss.missing_args:
                    st.json(ss.missing_args)
                if ss.missing_args_summary:
                    st.json(ss.missing_args_summary)
                
                # Link to verify API configuration
                st.markdown("Verify if the API key in `.env` is configured correctly")
    
    st.markdown('</div>', unsafe_allow_html=True)

def show_simple_selection_interface():
    """Shows the simple selection interface (without section structure)"""
    # Filter only subjective passages
    if not ss.bias_df.empty:
        subj_df = ss.bias_df[ss.bias_df['label'] == 'SUBJECTIVE'].copy()
        
        # If there are no subjective passages, show a message
        if subj_df.empty:
            st.success("No subjective passages found in this article!")
        else:
            st.info("This is a simplified view. The section-structured version offers better organization.")
            
            # Group by section to show number of passages
            if 'section_uid' in subj_df.columns:
                sections_count = subj_df.groupby(['section', 'section_uid']).size().reset_index(name='count')
                sections_msg = ", ".join([f"{row['section']} ({row['count']})" for _, row in sections_count.iterrows()])
            else:
                sections_count = subj_df.groupby('section').size().reset_index(name='count')
                sections_msg = ", ".join([f"{row['section']} ({row['count']})" for _, row in sections_count.iterrows()])
            
            st.info(f"Sections with subjective passages: {sections_msg}")
            
            # Create checkboxes for each subjective passage
            selected_texts = []
            
            for i, row in subj_df.iterrows():
                sentence = row['sentence'].strip()
                if len(sentence) > 10:  # Avoid very short phrases
                    # Create an identifier for the checkbox that includes section reference
                    if 'section_uid' in row:
                        cb_key = f"bias_check_{row['section_uid']}_{i}"
                    else:
                        cb_key = f"bias_check_{row['section']}_{i}"
                    
                    # Add section information
                    section_info = f"[{row['section']}] "
                    
                    is_selected = st.checkbox(
                        f"{section_info}{sentence}", 
                        key=cb_key,
                        value=sentence in ss.selected_biased_texts
                    )
                    if is_selected and sentence not in selected_texts:
                        selected_texts.append(sentence)
            
            # Button to process selected passages
            if selected_texts:
                if st.button("Neutralize Selected Passages", type="primary"):
                    with st.spinner("Neutralizing passages..."):
                        # Update the list of selected passages
                        ss.selected_biased_texts = selected_texts
                        
                        # Correct the selected passages
                        neutralized = registry.debias.neutralize_multiple(selected_texts)
                        ss.neutralized_texts = neutralized
                        
                        # Show success message
                        st.success(f"{len(neutralized)} passages successfully neutralized!")
                        
                        # Automatically switch to the neutralized text tab
                        st.rerun()
            else:
                st.warning("Select at least one passage to neutralize.") 