import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import pandas as pd
import numpy as np
from frontend.styles import inject_custom_styles
from backend.core.cleaner import DataCleaner
from backend.core.fuzzy_matcher import find_fuzzy_groups, apply_fuzzy_mapping
from backend.core.llm_integrations import LLMIntegrations
from backend.api.clean import run_cleaning_pipeline

def main():
    inject_custom_styles()
    
    st.markdown('<div class="main-title">Clean & Enrich Pipeline</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Configure data transformations, merge near-duplicates, and leverage LLM semantic mapping.</div>', unsafe_allow_html=True)
    
    # Verify file is loaded
    if st.session_state.get("raw_df") is None:
        st.warning("⚠️ No dataset uploaded yet. Please go to **1_Upload** to import or generate a dataset.")
        return
        
    df = st.session_state["raw_df"]
    report = st.session_state["profile_report"]
    columns_stats = report["columns"]
    industry = st.session_state.get("industry", "General")
    
    # 0. API Key Config Expander
    st.sidebar.markdown("### 🔑 AI API Keys Configuration")
    gemini_key = st.sidebar.text_input("Gemini API Key", value=st.session_state.get("GEMINI_API_KEY", ""), type="password")
    anthropic_key = st.sidebar.text_input("Anthropic API Key", value=st.session_state.get("ANTHROPIC_API_KEY", ""), type="password")
    
    # Update environment variables if provided
    if gemini_key:
        import os
        os.environ["GEMINI_API_KEY"] = gemini_key
        st.session_state["GEMINI_API_KEY"] = gemini_key
    if anthropic_key:
        import os
        os.environ["ANTHROPIC_API_KEY"] = anthropic_key
        st.session_state["ANTHROPIC_API_KEY"] = anthropic_key
        
    llm_service = LLMIntegrations()
    ai_status = llm_service.is_ai_active()
    
    if ai_status:
        st.sidebar.success("🟢 AI Engine Active (Keys Loaded)")
    else:
        st.sidebar.info("🟡 Running in offline heuristic mode. To unlock Claude or Gemini integrations, supply API keys above.")

    # Tabs for different cleaning actions
    tab_rules, tab_fuzzy, tab_ai = st.tabs(["🛠️ Tabular Cleaning Rules", "🔀 Fuzzy Grouping (Deduplication)", "🧠 AI-Assisted Enrichment"])
    
    # Retrieve current config or set default
    p_config = st.session_state["pipeline_config"]
    
    # Initialize working dataframe representing clean target
    # If not already created, start from raw
    if st.session_state.get("cleaned_df") is None:
        st.session_state["cleaned_df"] = df.copy()

    # --- TAB 1: Tabular Cleaning Rules ---
    with tab_rules:
        st.markdown("### Standard Cleaning Rules")
        
        c_col1, c_col2 = st.columns(2)
        
        with c_col1:
            header_style = st.selectbox(
                "Standardize Column Headers Case",
                ["None", "snake_case", "camelCase", "uppercase", "lowercase", "title_case"],
                index=["None", "snake_case", "camelCase", "uppercase", "lowercase", "title_case"].index(p_config.get("standardize_headers", "snake_case"))
            )
            p_config["standardize_headers"] = None if header_style == "None" else header_style
            
            trim_white = st.checkbox("Trim trailing/leading whitespaces from strings", value=p_config.get("trim_whitespace", True))
            p_config["trim_whitespace"] = trim_white
            
            dedup = st.checkbox("Remove exact duplicate rows", value=p_config.get("remove_duplicates", True))
            p_config["remove_duplicates"] = dedup
            
        with c_col2:
            # Drop Null Rows check
            drop_null_cols = st.multiselect(
                "Drop rows where these columns are empty/null",
                options=list(df.columns),
                default=p_config.get("drop_null_rows", [])
            )
            p_config["drop_null_rows"] = drop_null_cols

        st.markdown("---")
        st.markdown("### Advanced Type Conversions & Imputations")
        
        # Add new Type Conversion Rule
        conv_col, add_conv_col = st.columns([3, 1])
        with conv_col:
            conv_sel_col = st.selectbox("Select Column to Cast", [""] + list(df.columns), key="conv_col")
            conv_sel_type = st.selectbox("Target Type", ["int", "float", "str", "datetime", "boolean", "category"], key="conv_type")
            conv_date_fmt = st.text_input("Date Format (optional, e.g. %Y-%m-%d)", value="", key="conv_fmt")
        with add_conv_col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("Add Casting Rule"):
                if conv_sel_col:
                    # Remove existing for same column
                    p_config["conversions"] = [c for c in p_config["conversions"] if c["column"] != conv_sel_col]
                    p_config["conversions"].append({
                        "column": conv_sel_col,
                        "type": conv_sel_type,
                        "format": conv_date_fmt if conv_date_fmt else None
                    })
                    st.success(f"Added type casting for '{conv_sel_col}'")
                else:
                    st.error("Please select a column first.")

        # Show current casting rules
        if p_config["conversions"]:
            st.markdown("Current Type Casts:")
            for idx, c in enumerate(p_config["conversions"]):
                st.code(f"Cast '{c['column']}' to {c['type'].upper()}" + (f" with format '{c['format']}'" if c['format'] else ""))
                if st.button("Remove", key=f"del_conv_{idx}"):
                    p_config["conversions"].pop(idx)
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        # Add Imputation Rule
        imp_col, add_imp_col = st.columns([3, 1])
        with imp_col:
            imp_sel_col = st.selectbox("Select Column to Impute Nulls", [""] + list(df.columns), key="imp_col")
            imp_sel_method = st.selectbox("Imputation Method", ["mean", "median", "mode", "constant"], key="imp_method")
            imp_const_val = st.text_input("Constant Fill Value (only for constant method)", value="", key="imp_val")
        with add_imp_col:
            st.markdown("<br><br>", unsafe_allow_html=True)
            if st.button("Add Imputation Rule"):
                if imp_sel_col:
                    p_config["imputations"] = [i for i in p_config["imputations"] if i["column"] != imp_sel_col]
                    p_config["imputations"].append({
                        "column": imp_sel_col,
                        "method": imp_sel_method,
                        "value": imp_const_val if imp_sel_method == "constant" else None
                    })
                    st.success(f"Added imputation for '{imp_sel_col}'")
                else:
                    st.error("Please select a column first.")

        # Show current imputation rules
        if p_config["imputations"]:
            st.markdown("Current Imputations:")
            for idx, i in enumerate(p_config["imputations"]):
                st.code(f"Fill nulls in '{i['column']}' using {i['method'].upper()}" + (f" (Value: '{i['value']}')" if i['value'] is not None else ""))
                if st.button("Remove", key=f"del_imp_{idx}"):
                    p_config["imputations"].pop(idx)
                    st.rerun()

    # --- TAB 2: Fuzzy Grouping ---
    with tab_fuzzy:
        st.markdown("### Fuzzy Duplicate Categorical Grouping")
        st.write("Merge slightly misspelled or alternate textual names into a single clean canonical representation.")
        
        # Select target column (categorical or text)
        cand_cols = [col for col, stats in columns_stats.items() if stats.get("inferred_type") in ("categorical", "text")]
        
        if not cand_cols:
            st.info("No categorical or text columns found to run fuzzy groupings.")
        else:
            f_col = st.selectbox("Fuzzy Standardize Column", cand_cols)
            f_threshold = st.slider("Fuzzy Match Similarity Threshold", min_value=50, max_value=99, value=80, help="Lower value matches broader variations; higher value matches closer spellings.")
            
            if st.button("Scan Column for Fuzzy Variations"):
                with st.spinner("Scanning similarities..."):
                    groups = find_fuzzy_groups(df[f_col], threshold=f_threshold)
                    st.session_state["fuzzy_groups"][f_col] = groups
                    
            # Display scanning results
            col_groups = st.session_state["fuzzy_groups"].get(f_col, [])
            
            if col_groups:
                st.markdown(f"DataForge found **{len(col_groups)}** cluster groups with spelling differences.")
                
                # Checkbox selection to build replacement dictionary
                replacements = {}
                for idx, g in enumerate(col_groups):
                    canonical = g["canonical"]
                    members = g["members"]
                    freqs = g["frequencies"]
                    
                    st.markdown(f'<div class="glass-card">', unsafe_allow_html=True)
                    st.markdown(f"🗳️ **Group {idx+1}:** Merge into canonical standard: **`{canonical}`** (occurs {freqs[canonical]} times)")
                    
                    # Checkbox for each member
                    members_to_replace = []
                    for m in members:
                        if m != canonical:
                            is_checked = st.checkbox(f"Map '{m}' ({freqs[m]} occurrences) &rarr; '{canonical}'", value=True, key=f"f_merge_{f_col}_{idx}_{m}")
                            if is_checked:
                                replacements[m] = canonical
                                
                    st.markdown('</div>', unsafe_allow_html=True)
                
                # Store replacements in session state
                if replacements:
                    if f_col not in st.session_state["fuzzy_replacements"]:
                        st.session_state["fuzzy_replacements"][f_col] = {}
                    st.session_state["fuzzy_replacements"][f_col].update(replacements)
                    st.success(f"Configured {len(replacements)} fuzzy replacements mappings for column '{f_col}'!")
            elif f_col in st.session_state["fuzzy_groups"]:
                st.success("No near-duplicate groups found. Column is clean.")

    # --- TAB 3: AI Enrichment ---
    with tab_ai:
        st.markdown("### AI-Assisted Enrichment")
        st.write("Leverage Gemini or Claude APIs for semantic mapping. The heuristics fallback is used if keys are absent.")
        
        # Action 1: Column Inference
        st.markdown("#### 1. AI Column Inference (Standardization)")
        st.write("Understand cryptically named headers based on actual cell samples and translate them to clear formats.")
        
        if st.button("Generate Clean Headers Suggestions"):
            with st.spinner("AI analyzing column semantics..."):
                translations = {}
                for col in df.columns:
                    sample_vals = [str(x) for x in df[col].dropna().head(5).tolist()]
                    meta = llm_service.infer_column_metadata(col, sample_vals, industry=industry)
                    translations[col] = meta
                st.session_state["column_translations"] = translations
                st.success("Inference complete!")

        # Display suggestions and allow applying them
        if st.session_state["column_translations"]:
            st.markdown("##### Clean Columns Configuration Mapping:")
            trans_df_rows = []
            for col, res in st.session_state["column_translations"].items():
                trans_df_rows.append({
                    "Original Header": col,
                    "Suggested Snake Header": res.get("standardized_name"),
                    "AI Inferred Datatype": res.get("clean_datatype"),
                    "Description Concept": res.get("description")
                })
            trans_df = pd.DataFrame(trans_df_rows)
            st.dataframe(trans_df, use_container_width=True, hide_index=True)
            
            apply_ai_headers = st.checkbox("Apply AI Inferred snake_case headers to pipeline config", value=True)
            if apply_ai_headers:
                # Add columns to custom map or override headers style
                pass

        st.markdown("---")
        # Action 2: Semantic Value Normalization
        st.markdown("#### 2. AI Category Value Normalization")
        st.write("Map inconsistent text inputs to a clean normalized vocabulary (e.g. materials standard, transaction status tags).")
        
        ai_norm_col = st.selectbox("Select Value Column to Normalize", list(df.columns), key="ai_norm_col")
        ai_norm_context = st.text_input("Provide domain context description (e.g., 'material composition of clothing items', 'payment transaction status')", value="general categorization")
        
        if st.button("Run Value Normalization Scan"):
            raw_vals = [str(x) for x in df[ai_norm_col].dropna().unique().tolist()]
            if not raw_vals:
                st.warning("No values found to normalize.")
            else:
                with st.spinner("AI normalizing categories..."):
                    norm_map = llm_service.normalize_column_values(raw_vals, ai_norm_context)
                    st.session_state["normalized_values"][ai_norm_col] = norm_map
                    st.success("Value mapping scanned successfully!")
                    
        # Display normalization suggestions
        norm_map_col = st.session_state["normalized_values"].get(ai_norm_col, {})
        if norm_map_col:
            st.markdown("##### AI Suggested Mappings:")
            norm_rows = [{"Messy Original Value": k, "Standard Normalized Value": v} for k, v in norm_map_col.items()]
            st.dataframe(pd.DataFrame(norm_rows), use_container_width=True, hide_index=True)
            
            if st.button("Apply AI Mappings to Pipeline"):
                if ai_norm_col not in st.session_state["fuzzy_replacements"]:
                    st.session_state["fuzzy_replacements"][ai_norm_col] = {}
                st.session_state["fuzzy_replacements"][ai_norm_col].update(norm_map_col)
                st.success(f"Applied AI value normalization mappings for column '{ai_norm_col}'!")

    # --- PIPELINE COMPLIANCE TRIGGER & SIDE-BY-SIDE PREVIEW ---
    st.markdown("---")
    st.markdown("### 🎛️ Pipeline Processor")
    st.write("Compile all tabular configurations, fuzzy clustering, and AI mappings to run the pipeline.")
    
    if st.button("⚡ Run DataForge Cleaning Pipeline"):
        with st.spinner("Executing cleaning pipeline operations..."):
            # 1. Run core cleaner rules
            processed = run_cleaning_pipeline(df, p_config)
            
            # 2. Check if AI Headers translation needs to be applied
            if st.session_state["column_translations"] and st.get_value("apply_ai_headers", False, default=True):
                # Translate headers based on suggestions mapping
                header_mapping = {col: stats.get("standardized_name") for col, stats in st.session_state["column_translations"].items()}
                processed = processed.rename(columns=header_mapping)
                
            # 3. Apply all fuzzy and AI value replacements mappings
            for col, mapping in st.session_state["fuzzy_replacements"].items():
                target_col = col
                # If column headers were translated, search for translated target header name
                if col not in processed.columns and st.session_state["column_translations"]:
                    target_col = st.session_state["column_translations"].get(col, {}).get("standardized_name", col)
                if target_col in processed.columns:
                    processed = apply_fuzzy_mapping(processed, target_col, mapping)
                    
            st.session_state["cleaned_df"] = processed
            st.success("Pipeline executed successfully! Scroll down to inspect the cleaned output preview.")

    # Side-by-Side Preview Block
    st.markdown("### 🔄 Side-by-Side Verification Preview")
    
    preview_col1, preview_col2 = st.columns(2)
    
    with preview_col1:
        st.markdown("#### Raw Original Data (First 8 Rows)")
        st.dataframe(df.head(8), use_container_width=True)
        
    with preview_col2:
        st.markdown("#### Cleaned Processed Data (First 8 Rows)")
        cleaned = st.session_state.get("cleaned_df")
        if cleaned is not None:
            st.dataframe(cleaned.head(8), use_container_width=True)
        else:
            st.info("Pipeline not executed yet. Rerun using the processor button above to generate a preview.")

    # Guide next step
    st.markdown(
        '<div style="margin-top: 30px; text-align: right;"><p style="color: #a78bfa; font-size: 1rem; font-weight: 500;">Next Step: Head to the <b>4_Report</b> page to run validations & download results.</p></div>',
        unsafe_allow_html=True
    )

def get_value(key, default_val, default=True):
    # Safe session state value fetcher
    return st.session_state.get(key, default_val) if default else default_val

if __name__ == "__main__":
    main()
