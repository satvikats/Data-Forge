import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
from frontend.styles import inject_custom_styles
from backend.api.upload import load_file
from backend.api.profile import generate_profile_report
from backend.validators.rules import suggest_validation_rules

def main():
    inject_custom_styles()
    
    st.markdown('<div class="main-title">Upload Raw Data</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Import CSV, Excel or JSON files to start profiling and validation.</div>', unsafe_allow_html=True)
    
    # Check if a file is already loaded
    if st.session_state.get("raw_df") is not None:
        st.info(f"Currently loaded file: **{st.session_state['uploaded_file_name']}** ({len(st.session_state['raw_df'])} rows, {len(st.session_state['raw_df'].columns)} columns). Uploading a new file will overwrite current session progress.")

    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        col1, col2 = st.columns([2, 1])
        
        with col1:
            uploaded_file = st.file_uploader("Choose a file", type=["csv", "xlsx", "xls", "json"])
            
        with col2:
            industry = st.selectbox(
                "Select Target Industry Context",
                ["General", "E-commerce", "Healthcare & Pharma", "Logistics & Supply Chain", "Energy & Environment", "Finance"],
                index=["General", "E-commerce", "Healthcare & Pharma", "Logistics & Supply Chain", "Energy & Environment", "Finance"].index(st.session_state.get("industry", "General"))
            )
            st.session_state["industry"] = industry
            
        st.markdown('</div>', unsafe_allow_html=True)

    if uploaded_file is not None:
        filename = uploaded_file.name
        ext = filename.split(".")[-1]
        
        # Read file bytes
        file_bytes = uploaded_file.read()
        
        try:
            # Load the file
            df = load_file(file_bytes, ext)
            
            # Save raw state
            st.session_state["raw_df"] = df
            st.session_state["uploaded_file_name"] = filename
            st.session_state["uploaded_file_ext"] = ext
            
            # Generate profile report
            with st.spinner("Generating initial profile report..."):
                report = generate_profile_report(df)
                st.session_state["profile_report"] = report
                
                # Auto recommend rules
                st.session_state["rule_definitions"] = suggest_validation_rules(report["columns"])
                
            # Clear downstream processed data states to avoid caching old results
            st.session_state["cleaned_df"] = None
            st.session_state["fuzzy_replacements"] = {}
            st.session_state["column_translations"] = {}
            st.session_state["normalized_values"] = {}
            
            st.success(f"Successfully loaded '{filename}'!")
            
        except Exception as e:
            st.error(f"Error parsing file: {e}")

    # Display Preview of raw data
    if st.session_state.get("raw_df") is not None:
        df = st.session_state["raw_df"]
        st.markdown("### 📋 Raw Data Preview")
        st.dataframe(df.head(10), use_container_width=True)
        
        # Stats summary block
        st.markdown("### 📊 Metadata Details")
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        m_col1, m_col2, m_col3 = st.columns(3)
        with m_col1:
            st.markdown(f'<div class="metric-container"><span class="metric-label">Total Rows</span><span class="metric-value">{len(df)}</span></div>', unsafe_allow_html=True)
        with m_col2:
            st.markdown(f'<div class="metric-container"><span class="metric-label">Total Columns</span><span class="metric-value">{len(df.columns)}</span></div>', unsafe_allow_html=True)
        with m_col3:
            total_cells = len(df) * len(df.columns)
            missing = int(df.isnull().sum().sum())
            missing_pct = (missing / total_cells * 100) if total_cells > 0 else 0
            st.markdown(f'<div class="metric-container"><span class="metric-label">Missing Cells</span><span class="metric-value">{missing_pct:.1f}% ({missing})</span></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Guide next step
        st.markdown(
            '<div style="margin-top: 30px; text-align: right;"><p style="color: #a78bfa; font-size: 1rem; font-weight: 500;">Next Step: Head to the <b>2_Profile</b> page to analyze structure & anomalies.</p></div>',
            unsafe_allow_html=True
        )

if __name__ == "__main__":
    main()
