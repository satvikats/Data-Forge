import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import pandas as pd
import json
from datetime import datetime
from frontend.styles import inject_custom_styles
from backend.api.validate import validate_dataset
from backend.api.profile import generate_profile_report
from backend.validators.rules import create_rule_from_dict

def main():
    inject_custom_styles()
    
    st.markdown('<div class="main-title">Quality Verification & Download</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Validate cleaned dataset against custom constraints, review results, and download reports.</div>', unsafe_allow_html=True)
    
    # Verify file is loaded and cleaned
    if st.session_state.get("raw_df") is None:
        st.warning("⚠️ No dataset uploaded yet. Please go to **1_Upload** to import or generate a dataset.")
        return
        
    df_raw = st.session_state["raw_df"]
    df_clean = st.session_state.get("cleaned_df")
    
    # Fallback to raw if clean not executed
    if df_clean is None:
        st.info("💡 Note: The cleaning pipeline has not been executed yet. We are displaying original raw values. Head over to **3_Clean** to configure transforms.")
        df_clean = df_raw.copy()
        
    # --- SECTION 1: Rules Validator Builder ---
    st.markdown("### 🛡️ Rules Validator Builder")
    st.write("Add or edit validation checks to assert that data conform to target logic constraints.")
    
    # Display current rules list
    rules_def = st.session_state.get("rule_definitions", [])
    
    with st.expander("Configure Validation Rules List", expanded=True):
        if rules_def:
            st.markdown("##### Current Configured Rules:")
            # Display as a dataframe
            rules_rows = []
            for idx, r in enumerate(rules_def):
                rules_rows.append({
                    "Index": idx + 1,
                    "Column": r["column"],
                    "Rule Constraint": r["type"].upper(),
                    "Parameters": json.dumps(r.get("params", {}))
                })
            st.dataframe(pd.DataFrame(rules_rows), use_container_width=True, hide_index=True)
            
            # Remove a rule
            rem_idx = st.selectbox("Select Rule Index to Remove", [""] + [str(x) for x in range(1, len(rules_def)+1)])
            if st.button("Delete Selected Rule"):
                if rem_idx:
                    idx_to_pop = int(rem_idx) - 1
                    rules_def.pop(idx_to_pop)
                    st.session_state["rule_definitions"] = rules_def
                    st.success("Rule deleted.")
                    st.rerun()
        else:
            st.info("No validation rules configured yet.")

        st.markdown("---")
        st.markdown("##### ➕ Add Custom Validation Rule:")
        r_c1, r_c2 = st.columns(2)
        with r_c1:
            col_target = st.selectbox("Target Column", list(df_clean.columns), key="val_col")
            rule_type = st.selectbox("Rule Constraint Type", ["non_null", "unique", "range", "regex", "in_set"], key="val_type")
            
        with r_c2:
            params = {}
            if rule_type == "range":
                p_min = st.number_input("Minimum Value", value=0.0)
                p_max = st.number_input("Maximum Value", value=100.0)
                params = {"min": p_min, "max": p_max}
            elif rule_type == "regex":
                p_regex = st.text_input("Regex Pattern", value=".*")
                p_desc = st.text_input("Description (e.g. email format)", value="pattern match")
                params = {"pattern": p_regex, "description": p_desc}
            elif rule_type == "in_set":
                p_set = st.text_input("Allowed Values (comma separated)", value="value1, value2")
                params = {"allowed": [x.strip() for x in p_set.split(",") if x.strip()]}
                
        if st.button("Add Validation Rule"):
            rules_def.append({
                "column": col_target,
                "type": rule_type,
                "params": params
            })
            st.session_state["rule_definitions"] = rules_def
            st.success(f"Added {rule_type.upper()} rule for column '{col_target}'!")
            st.rerun()

    # --- SECTION 2: Run Validations ---
    st.markdown("### 🚦 Validation Results Scan")
    
    validation_failures = []
    if st.button("🔍 Run Quality Validation Check"):
        with st.spinner("Scanning datasets against constraints..."):
            validation_failures = validate_dataset(df_clean, rules_def)
            st.session_state["validation_results"] = validation_failures
            
    failures = st.session_state.get("validation_results", [])
    
    if failures:
        st.markdown(f'<div class="custom-badge badge-red">Failed</div> Validation checks failed with **{len(failures)}** failures.', unsafe_allow_html=True)
        
        fail_rows = []
        for idx, f in enumerate(failures):
            fail_rows.append({
                "Failure ID": idx + 1,
                "Column": f["column"],
                "Row Index": f["row_index"],
                "Value Found": f["value"],
                "Rule Violated": f["rule"].upper(),
                "Error Details": f["message"]
            })
        st.dataframe(pd.DataFrame(fail_rows), use_container_width=True, hide_index=True)
    else:
        st.markdown(f'<div class="custom-badge badge-green">Passed</div> All validation checks passed successfully against the clean dataset!', unsafe_allow_html=True)

    # --- SECTION 3: Quality Comparison ---
    st.markdown("### 📊 Before & After Comparison")
    
    # Profile Cleaned dataset
    clean_report = generate_profile_report(df_clean)
    raw_summary = st.session_state["profile_report"]["summary"]
    clean_summary = clean_report["summary"]
    
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    comp_col1, comp_col2, comp_col3 = st.columns(3)
    
    with comp_col1:
        st.markdown("##### 📝 Record Details")
        st.write(f"Original Rows: **{raw_summary['row_count']}**")
        st.write(f"Cleaned Rows: **{clean_summary['row_count']}**")
        diff_rows = clean_summary['row_count'] - raw_summary['row_count']
        st.write(f"Change: **{'+' if diff_rows > 0 else ''}{diff_rows} rows**")
        
    with comp_col2:
        st.markdown("##### 📉 Completeness Rate")
        st.write(f"Original Missing Cells: **{raw_summary['missing_cells']} ({raw_summary['missing_pct']}%)**")
        st.write(f"Cleaned Missing Cells: **{clean_summary['missing_cells']} ({clean_summary['missing_pct']}%)**")
        st.write(f"Completeness Rate: **{100 - clean_summary['missing_pct']:.1f}%**")
        
    with comp_col3:
        st.markdown("##### 🎯 Quality Score Progression")
        raw_score = raw_summary['quality_score']
        clean_score = clean_summary['quality_score']
        score_color = "#34d399" if clean_score >= 85 else ("#fbbf24" if clean_score >= 60 else "#f87171")
        st.write(f"Original Score: **{raw_score}%**")
        st.write(f"Cleaned Score: <span style='color: {score_color}; font-weight: 700;'>{clean_score}%</span>", unsafe_allow_html=True)
        st.write(f"Score Delta: **{'+' if clean_score - raw_score > 0 else ''}{clean_score - raw_score:.2f}%**")
        
    st.markdown('</div>', unsafe_allow_html=True)

    # --- SECTION 4: Downloads ---
    st.markdown("### 💾 Export Clean Dataset & Quality Report")
    st.write("Download the resulting clean tabular data or export the quality check report summary in JSON format.")
    
    d_col1, d_col2 = st.columns(2)
    
    with d_col1:
        st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown("#### Cleaned Dataset")
        
        # CSV download
        csv_data = df_clean.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Cleaned CSV",
            data=csv_data,
            file_name=f"cleaned_{st.session_state['uploaded_file_name']}",
            mime="text/csv"
        )
        
        # JSON format download
        json_df_data = df_clean.to_json(orient="records", indent=2)
        st.download_button(
            label="Download Cleaned JSON Data",
            data=json_df_data,
            file_name=f"cleaned_{st.session_state['uploaded_file_name']}.json",
            mime="application/json",
            key="json_df_download"
        )
        st.markdown('</div>', unsafe_allow_html=True)
        
    with d_col2:
        st.markdown('<div class="glass-card" style="text-align: center;">', unsafe_allow_html=True)
        st.markdown("#### Quality Assessment Report")
        
        # Construct JSON report
        report_dict = {
            "application": "DataForge",
            "timestamp": datetime.now().isoformat(),
            "original_filename": st.session_state['uploaded_file_name'],
            "industry_context": st.session_state['industry'],
            "metadata": {
                "raw_records": raw_summary['row_count'],
                "cleaned_records": clean_summary['row_count'],
                "cells_evaluated": clean_summary['total_cells'],
                "missing_cells_raw": raw_summary['missing_cells'],
                "missing_cells_cleaned": clean_summary['missing_cells']
            },
            "scores": {
                "original_quality_score": f"{raw_summary['quality_score']}%",
                "final_cleaned_score": f"{clean_summary['quality_score']}%",
                "score_improvement": f"{clean_summary['quality_score'] - raw_summary['quality_score']:.2f}%"
            },
            "validation_checks": {
                "rules_evaluated_count": len(rules_def),
                "failures_count": len(failures),
                "failures_log": failures
            },
            "anomalies_remaining": clean_report["anomalies"]
        }
        
        report_json = json.dumps(report_dict, indent=2)
        st.download_button(
            label="Export JSON Quality Report",
            data=report_json,
            file_name=f"quality_report_{st.session_state['uploaded_file_name']}.json",
            mime="application/json"
        )
        st.markdown('</div>', unsafe_allow_html=True)

if __name__ == "__main__":
    main()
