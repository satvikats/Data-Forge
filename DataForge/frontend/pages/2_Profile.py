import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import streamlit as st
import pandas as pd
import altair as alt
from frontend.styles import inject_custom_styles

def main():
    inject_custom_styles()
    
    st.markdown('<div class="main-title">Data Profiling & Anomalies</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-title">Review inferred schema type alignments, outlier signals, and completeness reports.</div>', unsafe_allow_html=True)
    
    # Verify file is loaded
    if st.session_state.get("raw_df") is None:
        st.warning("⚠️ No dataset uploaded yet. Please go to **1_Upload** to import or generate a dataset.")
        return
        
    df = st.session_state["raw_df"]
    report = st.session_state["profile_report"]
    summary = report["summary"]
    columns_stats = report["columns"]
    anomalies = report["anomalies"]
    
    # 1. Quality Score Header Block
    st.markdown("### 📈 Quality Score Card")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    
    score_col, metrics_col = st.columns([1, 2])
    
    with score_col:
        score = summary["quality_score"]
        # Apply color based on score
        score_color = "#34d399" if score >= 85 else ("#fbbf24" if score >= 60 else "#f87171")
        st.markdown(
            f"""
            <div style="text-align: center; padding: 10px;">
                <span style="font-size: 0.85rem; text-transform: uppercase; color: #94a3b8; letter-spacing: 0.05em;">Overall Data Quality</span>
                <div style="font-size: 3.5rem; font-weight: 800; color: {score_color}; font-family: 'Outfit'; margin-top: 5px;">
                    {score}%
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    with metrics_col:
        st.markdown(
            f"""
            <div style="margin-top: 10px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #94a3b8; font-size: 0.9rem;">Record Count completeness</span>
                    <span style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">{summary['row_count']} rows</span>
                </div>
                <div style="background-color: rgba(255, 255, 255, 0.05); border-radius: 4px; height: 8px;">
                    <div style="background-color: #8b5cf6; width: 100%; border-radius: 4px; height: 100%;"></div>
                </div>
            </div>
            
            <div style="margin-top: 15px;">
                <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
                    <span style="color: #94a3b8; font-size: 0.9rem;">Data Density (Filled Cells)</span>
                    <span style="color: #ffffff; font-weight: 600; font-size: 0.9rem;">{100 - summary['missing_pct']:.1f}% ({summary['total_cells'] - summary['missing_cells']}/{summary['total_cells']})</span>
                </div>
                <div style="background-color: rgba(255, 255, 255, 0.05); border-radius: 4px; height: 8px;">
                    <div style="background-color: #3b82f6; width: {100 - summary['missing_pct']}%; border-radius: 4px; height: 100%;"></div>
                </div>
            </div>
            """, 
            unsafe_allow_html=True
        )
        
    st.markdown('</div>', unsafe_allow_html=True)

    # 2. Inferred Columns Schema Table
    st.markdown("### 📋 Inferred Schema Summary")
    
    schema_rows = []
    for col, stats in columns_stats.items():
        col_type = stats.get("inferred_type")
        null_pct = stats.get("null_pct", 0.0)
        unique_pct = stats.get("unique_count", 0) / len(df) if len(df) > 0 else 0
        
        # Format sample string
        samples = ", ".join(stats.get("sample_values", []))
        
        schema_rows.append({
            "Column Header": col,
            "Inferred Type": col_type.upper(),
            "Pandas Type": stats.get("pandas_type"),
            "Null rate": f"{null_pct * 100:.1f}%",
            "Uniqueness": f"{unique_pct * 100:.1f}%",
            "Sample Values": samples
        })
        
    schema_df = pd.DataFrame(schema_rows)
    st.dataframe(schema_df, use_container_width=True, hide_index=True)

    # 3. Anomalies Scan Section
    st.markdown("### 🚨 Detected Anomalies")
    if anomalies:
        st.markdown(f"DataForge scanned your dataset and detected **{len(anomalies)}** potential structural, outlier, or null anomalies.")
        
        anomaly_rows = []
        for idx, a in enumerate(anomalies):
            anomaly_rows.append({
                "Anomaly ID": idx + 1,
                "Target Column": a["column"],
                "Row Index": a["row_index"] if a["row_index"] is not None else "Column Level",
                "Flagged Value": a["value"],
                "Issue Type": a["type"].upper(),
                "Description": a["message"]
            })
            
        anom_df = pd.DataFrame(anomaly_rows)
        
        # Display table with specific colors if we want, or just standard Streamlit dataframe
        st.dataframe(anom_df, use_container_width=True, hide_index=True)
    else:
        st.success("🎉 No obvious data structure or numerical outliers detected in this scan.")

    # 4. Interactive Column Explorer
    st.markdown("### 🔍 Interactive Column Explorer")
    st.write("Select a column to view detailed distribution statistics and charts.")
    
    selected_col = st.selectbox("Explore Column", list(columns_stats.keys()))
    
    if selected_col:
        stats = columns_stats[selected_col]
        col_type = stats["inferred_type"]
        
        col_c1, col_c2 = st.columns([1, 1])
        
        with col_c1:
            st.markdown(f"#### Metadata for **{selected_col}**")
            
            # General details table
            m_data = {
                "Inferred Type": col_type.upper(),
                "Null Records": f"{stats['null_count']} ({stats['null_pct']*100:.1f}%)",
                "Unique Values": str(stats["unique_count"])
            }
            
            # Numeric specific stats
            if col_type == "numeric":
                m_data.update({
                    "Minimum": f"{stats.get('min'):.4f}" if stats.get("min") is not None else "N/A",
                    "Maximum": f"{stats.get('max'):.4f}" if stats.get("max") is not None else "N/A",
                    "Mean Average": f"{stats.get('mean'):.4f}" if stats.get("mean") is not None else "N/A",
                    "Median (P50)": f"{stats.get('median'):.4f}" if stats.get("median") is not None else "N/A",
                    "Std Dev": f"{stats.get('std'):.4f}" if stats.get("std") is not None else "N/A"
                })
            elif col_type == "datetime":
                m_data.update({
                    "Earliest Date": stats.get("min", "N/A"),
                    "Latest Date": stats.get("max", "N/A")
                })
                
            stats_table_df = pd.DataFrame(list(m_data.items()), columns=["Metric", "Value"])
            st.dataframe(stats_table_df, use_container_width=True, hide_index=True)
            
        with col_c2:
            st.markdown(f"#### Value Distribution Chart")
            
            # Drop nulls for charting
            chart_df = df[[selected_col]].dropna()
            
            if chart_df.empty:
                st.write("No values to display.")
            
            elif col_type == "numeric":
                # Convert to numeric to ensure float types for chart
                chart_df[selected_col] = pd.to_numeric(chart_df[selected_col], errors='coerce')
                chart_df = chart_df.dropna()
                
                # Render Histogram
                hist_chart = alt.Chart(chart_df).mark_bar(color='#8b5cf6').encode(
                    alt.X(f"{selected_col}:Q", bin=alt.Bin(maxbins=20), title=selected_col),
                    alt.Y('count()', title="Count")
                ).properties(height=250)
                st.altair_chart(hist_chart, use_container_width=True)
                
            elif col_type in ("categorical", "boolean"):
                # Render Bar Chart
                counts = chart_df[selected_col].value_counts().reset_index()
                counts.columns = [selected_col, "count"]
                
                bar_chart = alt.Chart(counts.head(10)).mark_bar(color='#3b82f6').encode(
                    alt.X(f"{selected_col}:N", sort='-y', title=selected_col),
                    alt.Y("count:Q", title="Count")
                ).properties(height=250)
                st.altair_chart(bar_chart, use_container_width=True)
                
            else:
                # Render Word frequencies list or simple count plot
                counts = chart_df[selected_col].astype(str).value_counts().reset_index()
                counts.columns = [selected_col, "count"]
                
                bar_chart = alt.Chart(counts.head(10)).mark_bar(color='#60a5fa').encode(
                    alt.X(f"{selected_col}:N", sort='-y', title="Unique String Values"),
                    alt.Y("count:Q", title="Count")
                ).properties(height=250)
                st.altair_chart(bar_chart, use_container_width=True)

    # Next step guide
    st.markdown(
        '<div style="margin-top: 30px; text-align: right;"><p style="color: #a78bfa; font-size: 1rem; font-weight: 500;">Next Step: Head to the <b>3_Clean</b> page to customize cleaning operations & activate AI normalization.</p></div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()
