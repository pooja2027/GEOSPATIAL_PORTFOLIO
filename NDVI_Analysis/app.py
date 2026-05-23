"""
app.py
------
GeoVista NDVI — Vegetation Monitoring Dashboard
Streamlit frontend that invokes NDVI_Region_Tool.py as a subprocess
and displays the outputs.
"""

import os
import sys
import subprocess
import streamlit as st
import pandas as pd

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="NDVI Vegetation Monitor",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
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
  .metric-card h2 { color: #4ade80; margin: 0; font-size: 1.8rem; }
  .metric-card p  { color: #94a3b8; margin: 4px 0 0 0; font-size: 0.85rem; }
  .stButton > button {
    background: #16a34a; color: white;
    border: none; border-radius: 6px; font-weight: bold;
  }
  .stButton > button:hover { background: #15803d; }
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("# 🌿 NDVI Vegetation Monitoring Dashboard")
st.markdown("*Sentinel-2 + Google Earth Engine · Annual & Seasonal Analysis · 2018–2024*")
st.markdown("---")

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Analysis Settings")

    place = st.text_input(
        "📍 Location",
        placeholder="e.g. Chennai, Ooty, Coimbatore",
        help="Enter any city, district, or region name.",
    )

    st.markdown("---")
    st.markdown("### 📂 Example Locations")
    examples = ["Chennai", "Ooty", "Sundarbans", "Coimbatore", "Mumbai"]
    for ex in examples:
        if st.button(ex, key=f"ex_{ex}"):
            place = ex

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    - **Data**: Sentinel-2 SR Harmonized  
    - **Platform**: Google Earth Engine  
    - **Resolution**: 10 m (map) / 30 m (stats)  
    - **Cloud filter**: < 20% per scene  
    - **Composite**: Annual median  
    """)

# ── Run Analysis ───────────────────────────────────────────────────────────────
run_btn = st.button("🚀 Run Analysis", type="primary", disabled=not bool(place.strip() if place else ""))

if run_btn and place:
    place = place.strip()

    with st.status(f"Analysing **{place}**…", expanded=True) as status:
        st.write("Initialising GEE and fetching boundary…")

        try:
            result = subprocess.run(
                [sys.executable, "NDVI_Region_Tool.py"],
                input=place,
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(os.path.abspath(__file__)),
            )

            stdout = result.stdout
            stderr = result.stderr

            if result.returncode != 0:
                status.update(label="Analysis failed", state="error")
                st.error("The analysis script returned an error:")
                st.code(stderr or stdout, language="text")
                st.stop()

            status.update(label=f"✅ Analysis complete — {place}", state="complete")

        except subprocess.TimeoutExpired:
            status.update(label="Timed out", state="error")
            st.error("⏰ Analysis timed out (5 min limit). Try a smaller region.")
            st.stop()
        except Exception as e:
            status.update(label="Unexpected error", state="error")
            st.error(f"Unexpected error: {e}")
            st.stop()

    # ── Parse RESULT lines ─────────────────────────────────────────────────────
    results = {}
    for line in stdout.splitlines():
        if line.startswith("RESULT::"):
            key, _, val = line[8:].partition("=")
            results[key] = val.strip()

    ndvi_2018  = float(results.get("ndvi_2018", 0))
    ndvi_2024  = float(results.get("ndvi_2024", 0))
    change_pct = float(results.get("change_pct", 0))
    trend_path    = results.get("trend_path", "")
    area_path     = results.get("area_path", "")
    map_path      = results.get("map_path", "")
    report_path   = results.get("report_path", "")
    seasonal_path = results.get("seasonal_path", "")

    # ── Metrics ────────────────────────────────────────────────────────────────
    direction = "▲" if change_pct > 0 else "▼"
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f"""<div class="metric-card">
            <h2>{ndvi_2018:.3f}</h2><p>Mean NDVI 2018</p></div>""",
            unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="metric-card">
            <h2>{ndvi_2024:.3f}</h2><p>Mean NDVI 2024</p></div>""",
            unsafe_allow_html=True)
    with c3:
        color = "#4ade80" if change_pct > 0 else "#f87171"
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:{color}">{direction}{abs(change_pct):.1f}%</h2>
            <p>Vegetation Change</p></div>""",
            unsafe_allow_html=True)
    with c4:
        health = "Good" if ndvi_2024 > 0.3 else "Fair" if ndvi_2024 > 0.2 else "Poor"
        hcolor = "#4ade80" if ndvi_2024 > 0.3 else "#fbbf24" if ndvi_2024 > 0.2 else "#f87171"
        st.markdown(f"""<div class="metric-card">
            <h2 style="color:{hcolor}">{health}</h2>
            <p>Vegetation Health (2024)</p></div>""",
            unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Charts ─────────────────────────────────────────────────────────────────
    chart_col, map_col = st.columns([1, 1])

    with chart_col:
        st.markdown("#### 📈 NDVI Trend (2018–2024)")
        if trend_path and os.path.exists(trend_path):
            st.image(trend_path, use_container_width=True)
        else:
            st.warning("Trend chart not found.")

        if area_path and os.path.exists(area_path):
            st.markdown("#### 🌱 Vegetation Cover (2024)")
            st.image(area_path, use_container_width=True)

        if seasonal_path and os.path.exists(seasonal_path):
            st.markdown("#### 🗓️ Seasonal NDVI (2024)")
            st.image(seasonal_path, use_container_width=True)

    with map_col:
        st.markdown("#### 🗺️ Interactive NDVI Map")
        if map_path and os.path.exists(map_path):
            with open(map_path, "r", encoding="utf-8") as f:
                html_content = f.read()
            st.components.v1.html(html_content, height=620)
        else:
            st.warning("Map file not found.")

    # ── Exports ────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("#### 📤 Export Results")
    dl1, dl2, dl3 = st.columns(3)

    with dl1:
        if report_path and os.path.exists(report_path):
            with open(report_path, "rb") as f:
                st.download_button("📄 Download Report (.txt)", f,
                                   file_name=os.path.basename(report_path),
                                   mime="text/plain")
    with dl2:
        if map_path and os.path.exists(map_path):
            with open(map_path, "rb") as f:
                st.download_button("🗺️ Download Map (.html)", f,
                                   file_name=os.path.basename(map_path),
                                   mime="text/html")
    with dl3:
        st.info("🛰️ GeoTIFF export started to Google Drive automatically.")

    # ── Raw log (collapsible) ───────────────────────────────────────────────────
    with st.expander("🔍 View Analysis Log", expanded=False):
        st.code(stdout, language="text")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center;color:#64748b;font-size:0.8rem'>"
    "NDVI Monitor · Sentinel-2 + Google Earth Engine · "
    "<a href='https://github.com/pooja2027/Geospatial_Portfolio' style='color:#4ade80'>"
    "Geospatial Portfolio</a></div>",
    unsafe_allow_html=True,
)
