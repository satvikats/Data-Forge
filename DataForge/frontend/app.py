import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import streamlit as st
from frontend.styles import inject_custom_styles

def main():
    inject_custom_styles()
    
    # Initialize session state keys if they don't exist
    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = None
    if "uploaded_file_name" not in st.session_state:
        st.session_state["uploaded_file_name"] = None
    if "uploaded_file_ext" not in st.session_state:
        st.session_state["uploaded_file_ext"] = None
    if "profile_report" not in st.session_state:
        st.session_state["profile_report"] = None
    if "industry" not in st.session_state:
        st.session_state["industry"] = "General"
    if "pipeline_config" not in st.session_state:
        st.session_state["pipeline_config"] = {
            "standardize_headers": "snake_case",
            "trim_whitespace": True,
            "remove_duplicates": True,
            "imputations": [],
            "conversions": [],
            "drop_null_rows": []
        }
    if "cleaned_df" not in st.session_state:
        st.session_state["cleaned_df"] = None
    if "rule_definitions" not in st.session_state:
        st.session_state["rule_definitions"] = []
    if "validation_results" not in st.session_state:
        st.session_state["validation_results"] = []
    if "fuzzy_groups" not in st.session_state:
        st.session_state["fuzzy_groups"] = {}
    if "fuzzy_replacements" not in st.session_state:
        st.session_state["fuzzy_replacements"] = {}
    if "column_translations" not in st.session_state:
        st.session_state["column_translations"] = {}
    if "normalized_values" not in st.session_state:
        st.session_state["normalized_values"] = {}

    # Welcome UI
    st.markdown('<div class="main-title">DataForge</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Automated Schema Profiling, Clean Data Pipelines & Intelligent AI Normalization</div>', unsafe_allow_html=True)
    
    # High impact banner introduction
    st.markdown(
        """
        <div class="glass-card">
            <h3>Welcome to the Data Engine Room of 2026</h3>
            <p>DataForge bridges the gap between raw, messy datasets and production-ready pipelines. 
            By combining rigorous rule-based transformations with advanced LLM semantic heuristics, DataForge automatically 
            profiles schemas, cleans structure, clusters typos with fuzzy matching, and normalizes values intelligently.</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # 2 Column layout
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(
            """
            <div class="glass-card">
                <h4>🚀 Features & Capabilities</h4>
                <ul>
                    <li><b>In-Depth Profiling:</b> Automated semantic data type detection (Datetime, Categorical, Numeric, Text, Boolean) and null matrix analysis.</li>
                    <li><b>Flexible Cleaning:</b> Impute missing records (Mean, Median, Mode, Constant), parse date formats, convert column types, and drop duplicates.</li>
                    <li><b>Fuzzy Grouping:</b> Typo clustering using RapidFuzz Levenshtein scoring to group and merge categorical variations.</li>
                    <li><b>LLM-Assisted Enrichment:</b> Semantic column translation (e.g., <i>"Ctn Wgt"</i> &rarr; <i>"carton_weight_grams"</i>) and category normalization using Gemini / Claude.</li>
                    <li><b>Custom Rules Engine:</b> Range, uniqueness, regex formats, and set membership validator constraints.</li>
                </ul>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    with col2:
        st.markdown(
            """
            <div class="glass-card">
                <h4>🛠️ The Interactive Workflow</h4>
                <ol>
                    <li><b>Upload</b>: Import raw CSV, XLSX, or JSON and select industry context.</li>
                    <li><b>Profile</b>: Inspect completeness scores, anomalies, distributions, and schema parameters.</li>
                    <li><b>Clean & Enrich</b>: Build cleaning steps, inspect side-by-side previews, cluster duplicates, and invoke AI normalizers.</li>
                    <li><b>Download Report</b>: Fetch cleaned data and a comprehensive JSON data quality verification summary.</li>
                </ol>
                <div style="margin-top: 25px; text-align: center;">
                    <p style="color: #94a3b8; font-size: 0.9rem;">To get started, select <b>1_Upload</b> from the sidebar navigation.</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # Let the user load the sample dataset as a quick-start helper
    st.markdown("### 💡 Quick-Start Demonstration")
    st.write("Don't have a dataset ready? Click below to load a built-in messy mock dataset to explore all features.")
    
    if st.button("Load Mock Messy Dataset"):
        from backend.tests.fixtures.sample_data import generate_messy_dataset
        from backend.api.profile import generate_profile_report
        from backend.validators.rules import suggest_validation_rules
        
        st.session_state["raw_df"] = generate_messy_dataset()
        st.session_state["uploaded_file_name"] = "sample_messy_data.csv"
        st.session_state["uploaded_file_ext"] = "csv"
        st.session_state["industry"] = "E-commerce"
        
        # Profile it
        report = generate_profile_report(st.session_state["raw_df"])
        st.session_state["profile_report"] = report
        
        # Suggest rules
        st.session_state["rule_definitions"] = suggest_validation_rules(report["columns"])
        
        # Reset downstreams
        st.session_state["cleaned_df"] = None
        st.session_state["fuzzy_replacements"] = {}
        st.session_state["column_translations"] = {}
        st.session_state["normalized_values"] = {}
        
        st.success("Loaded 'sample_messy_data.csv' successfully! Head over to the **2_Profile** or **3_Clean** pages in the sidebar to inspect and clean the data.")

if __name__ == "__main__":
    main()
