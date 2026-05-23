# 🌍 GeoVista — Geospatial Market Insights for the AEC Industry

<div align="center">

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=flat-square&logo=python&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.32%2B-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![scikit-learn](https://img.shields.io/badge/scikit--learn-1.4%2B-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)
![License: MIT](https://img.shields.io/badge/License-MIT-22c55e?style=flat-square)
![Built at Hackathon](https://img.shields.io/badge/Built%20at-Code%3B%20Without%20Barriers-6366f1?style=flat-square)

**An interactive geospatial dashboard for analyzing, clustering, and visualizing AEC project locations.**

[Features](#-features) · [Demo](#-demo) · [Getting Started](#-getting-started) · [Project Structure](#-project-structure) · [Tech Stack](#-tech-stack)

</div>

---

## 🔍 Problem

Architecture, Engineering & Construction (AEC) project planners make location-based decisions — site selection, resource allocation, regional expansion — without spatial context. Raw spreadsheets with lat/lon coordinates give no insight into geographic patterns, cluster density, or investment concentration.

**GeoVista bridges that gap.**

---

## 💡 Solution

GeoVista lets you upload any CSV of project locations and instantly:
- Detect geographic clusters using **KMeans** or **DBSCAN**
- Visualize them on an interactive map with per-project popups
- Overlay a **cost-weighted heatmap** to surface high-investment zones
- Export results as **GeoJSON** for downstream GIS workflows

---

## ✨ Features

| Feature | Description |
|---|---|
| 📂 **CSV Upload** | Upload any CSV with `latitude` / `longitude` columns |
| 🔵 **KMeans Clustering** | User-defined number of geographic clusters |
| 🔴 **DBSCAN Clustering** | Density-based clustering; flags outlier projects as noise |
| 🔥 **Cost Heatmap** | Investment-weighted spatial heatmap layer |
| 📊 **Cluster Summary** | Per-cluster stats: count, total cost, dominant type/status |
| 📤 **GeoJSON Export** | One-click export compatible with QGIS, ArcGIS, Mapbox |
| 📋 **Data Table** | Sortable, filterable project table with cluster labels |
| 🇮🇳 **Tamil Nadu Demo Data** | 30 real-category AEC projects across 23 TN districts |

---

## 🎬 Demo

> **Live sample:** Load the app and enable *"Use sample Tamil Nadu AEC data"* in the sidebar — no upload needed.

```
Upload CSV → Choose clustering algorithm → Explore map → Export results
```

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- pip

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/YOUR_USERNAME/geovista.git
cd geovista

# 2. Create a virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the app
streamlit run app.py
```

The app opens at `http://localhost:8501`.

### CSV Format

Your CSV must contain at minimum:

| Column | Type | Example |
|---|---|---|
| `latitude` | float | `13.0827` |
| `longitude` | float | `80.2707` |

Optional enrichment columns (used for popups and summaries):

`project_name`, `type`, `cost_crore`, `status`, `district`, `year`, `project_id`

See [`data/sample_data.csv`](data/sample_data.csv) for a full example.

---

## 📁 Project Structure

```
geovista/
├── app.py                  # Streamlit entry point
├── requirements.txt
├── README.md
├── .gitignore
│
├── src/
│   ├── __init__.py
│   ├── clustering.py       # KMeans & DBSCAN logic
│   ├── map_utils.py        # Folium map builder + GeoJSON export
│   └── data_utils.py       # CSV validation, preprocessing, stats
│
└── data/
    └── sample_data.csv     # Tamil Nadu AEC demo dataset (30 projects)
```

---

## 🛠️ Tech Stack

| Library | Purpose |
|---|---|
| [Streamlit](https://streamlit.io) | Web app framework |
| [Pandas](https://pandas.pydata.org) | Data loading and manipulation |
| [GeoPandas](https://geopandas.org) | Geospatial data structures |
| [scikit-learn](https://scikit-learn.org) | KMeans and DBSCAN clustering |
| [Folium](https://python-visualization.github.io/folium/) | Interactive Leaflet.js maps |
| [streamlit-folium](https://folium.streamlit.app) | Folium ↔ Streamlit bridge |

---

## 🧭 Roadmap

- [ ] Time-series animation of project activity by year
- [ ] Multi-file upload and merge
- [ ] Choropleth layer by district investment density
- [ ] OpenStreetMap geocoding for address-to-coordinate conversion
- [ ] Streamlit Cloud deployment

---

## 🏆 Origin

Built for the **[Code; Without Barriers Hackathon](https://github.com)** as a 1st-year undergraduate project.  
Rebuilt and restructured in Year 3 as part of a portfolio-grade geospatial portfolio.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

> **Disclaimer:** This project titled "GeoVista" is independent and not affiliated with any existing organization of the same name. Used for educational and non-commercial purposes only.

---

<div align="center">
Made with 🌊 from Chennai &nbsp;·&nbsp;
<a href="https://github.com/YOUR_USERNAME">@YOUR_USERNAME</a>
</div>
