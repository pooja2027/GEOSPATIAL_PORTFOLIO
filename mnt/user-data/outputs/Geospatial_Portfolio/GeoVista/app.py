"""
app.py
------
GeoVista — Geospatial Market Insights for the AEC Industry
Entry point for the Streamlit application.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

import streamlit as st
import pandas as pd
from streamlit_folium import st_folium

from src.data_utils import validate_csv, preprocess, load_sample_data, summary_stats
from src.clustering import run_kmeans, run_dbscan, cluster_summary
from src.map_utils import build_cluster_map, export_geojson

# ─── Page Config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="GeoVista",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stSidebar"] { background-color: #0f172a; }
  [data-testid="stSidebar"] * { color: #e2e8f0 !important; }
  .metric-card {
    background: linear-gradient(135deg, #1e293b, #0f172a);
    border: 1px solid #334155;
    border-radius: 10px;
    padding: 1rem;
    text-align: center;
  }
  .metric-card h2 { color: #38bdf8; margin: 0; font-size: 2rem; }
  .metric-card p  { color: #94a3b8; margin: 0; font-size: 0.85rem; }
  .stButton > button {
    background: #0ea5e9;
    color: white;
    border: none;
    border-radius: 6px;
  }
  .stButton > button:hover { background: #0284c7; }
</style>
""", unsafe_allow_html=True)

# ─── Header ───────────────────────────────────────────────────────────────────
st.markdown("""
# 🌍 GeoVista
### Geospatial Market Insights for the AEC Industry
""")
st.markdown("---")

# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    # Data source
    st.markdown("### 📂 Data Source")
    use_sample = st.checkbox("Use sample Tamil Nadu AEC data", value=True)

    uploaded_file = None
    if not use_sample:
        uploaded_file = st.file_uploader(
            "Upload your CSV file",
            type=["csv"],
            help="Must contain 'latitude' and 'longitude' columns.",
        )

    st.markdown("---")

    # Clustering settings
    st.markdown("### 🔬 Clustering")
    method = st.radio("Algorithm", ["KMeans", "DBSCAN"], horizontal=True)

    if method == "KMeans":
        n_clusters = st.slider("Number of clusters", min_value=2, max_value=10, value=4)
    else:
        eps_km = st.slider("Max radius (km)", min_value=10, max_value=200, value=80, step=10)
        min_samples = st.slider("Min. samples per cluster", min_value=2, max_value=10, value=2)

    st.markdown("---")

    # Map settings
    st.markdown("### 🗺️ Map Style")
    map_style = st.selectbox(
        "Layer",
        ["cluster_markers", "heatmap", "both"],
        format_func=lambda x: {
            "cluster_markers": "🔵 Cluster Markers",
            "heatmap": "🔥 Cost Heatmap",
            "both": "🌐 Both Layers",
        }[x],
    )

    st.markdown("---")
    st.markdown("### 🔍 Filter")
    filter_status = st.multiselect("Project Status", ["Active", "Completed", "Planning", "Unknown"])

# ─── Load Data ────────────────────────────────────────────────────────────────
df_raw = None

if use_sample:
    df_raw = load_sample_data()
    st.info("📦 Using bundled Tamil Nadu AEC sample dataset (30 projects across 23 districts).")
elif uploaded_file is not None:
    try:
        df_upload = pd.read_csv(uploaded_file)
        valid, err = validate_csv(df_upload)
        if not valid:
            st.error(f"❌ CSV Error: {err}")
            st.stop()
        df_raw = preprocess(df_upload)
        st.success(f"✅ Loaded {len(df_raw)} projects from your file.")
    except Exception as e:
        st.error(f"Failed to read CSV: {e}")
        st.stop()
else:
    st.warning("⬅️ Upload a CSV file or enable sample data from the sidebar.")
    st.stop()

# Apply status filter
if filter_status and "status" in df_raw.columns:
    df_raw = df_raw[df_raw["status"].isin(filter_status)]
    if df_raw.empty:
        st.warning("No projects match the selected filter.")
        st.stop()

# ─── Clustering ───────────────────────────────────────────────────────────────
if method == "KMeans":
    n_clusters = min(n_clusters, len(df_raw))
    df_clustered = run_kmeans(df_raw, n_clusters=n_clusters)
else:
    df_clustered = run_dbscan(df_raw, eps_km=eps_km, min_samples=min_samples)
    noise_count = (df_clustered["cluster"] == "-1").sum()
    if noise_count > 0:
        st.warning(f"⚠️ DBSCAN: {noise_count} project(s) marked as noise/outliers (shown in grey).")

# ─── Metrics Row ──────────────────────────────────────────────────────────────
stats = summary_stats(df_clustered)
n_clusters_found = df_clustered[df_clustered["cluster"] != "-1"]["cluster"].nunique()

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown(f"""<div class="metric-card">
        <h2>{stats['total_projects']}</h2><p>Total Projects</p></div>""", unsafe_allow_html=True)
with col2:
    st.markdown(f"""<div class="metric-card">
        <h2>₹{stats['total_cost_crore']:,.0f} Cr</h2><p>Total Investment</p></div>""", unsafe_allow_html=True)
with col3:
    st.markdown(f"""<div class="metric-card">
        <h2>{n_clusters_found}</h2><p>Clusters Found</p></div>""", unsafe_allow_html=True)
with col4:
    st.markdown(f"""<div class="metric-card">
        <h2>{stats['districts']}</h2><p>Districts Covered</p></div>""", unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# ─── Map + Summary Side by Side ───────────────────────────────────────────────
map_col, info_col = st.columns([3, 1])

with map_col:
    st.markdown("#### 🗺️ Project Map")
    folium_map = build_cluster_map(df_clustered, map_style=map_style)
    st_folium(folium_map, width=None, height=500)

with info_col:
    st.markdown("#### 📊 Cluster Summary")
    summary_df = cluster_summary(df_clustered)
    if not summary_df.empty:
        st.dataframe(summary_df, use_container_width=True, hide_index=True)
    else:
        st.info("No clusters formed. Try adjusting the parameters.")

    # Status breakdown
    if stats["status_counts"]:
        st.markdown("#### 📋 Status Breakdown")
        for status, count in stats["status_counts"].items():
            st.markdown(f"- **{status}**: {count}")

# ─── Data Table ───────────────────────────────────────────────────────────────
with st.expander("📋 View Full Project Data", expanded=False):
    display_cols = [c for c in ["project_id", "project_name", "type", "district",
                                "status", "cost_crore", "year", "cluster"]
                    if c in df_clustered.columns]
    st.dataframe(df_clustered[display_cols], use_container_width=True)

# ─── Export ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("#### 📤 Export Results")
exp1, exp2 = st.columns(2)

with exp1:
    csv_export = df_clustered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Clustered CSV",
        data=csv_export,
        file_name="geovista_clusters.csv",
        mime="text/csv",
    )

with exp2:
    geojson_str = export_geojson(df_clustered)
    st.download_button(
        "⬇️ Download GeoJSON",
        data=geojson_str,
        file_name="geovista_clusters.geojson",
        mime="application/json",
    )

# ─── Footer ───────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:0.8rem'>"
    "GeoVista · Built with Streamlit · "
    "<a href='https://github.com/YOUR_USERNAME/geovista' style='color:#38bdf8'>GitHub</a>"
    "</div>",
    unsafe_allow_html=True,
)
