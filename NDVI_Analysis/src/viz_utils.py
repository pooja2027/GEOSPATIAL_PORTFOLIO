"""
viz_utils.py
------------
Chart generation (matplotlib) and interactive map building (Folium) for NDVI analysis.
"""

import os
import folium
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import geopandas as gpd


# ── Visualization parameters ──────────────────────────────────────────────────
NDVI_VIS = {
    "min": 0,
    "max": 1,
    "palette": ["#8b0000", "#ff4500", "#ffa500", "#ffff00", "#9acd32", "#006400"],
}

CHANGE_VIS = {
    "min": -0.5,
    "max": 0.5,
    "palette": ["#d73027", "#f7f7f7", "#1a9850"],
}

CLASS_COLORS = {
    "Water / Built-up":      "#4575b4",
    "Bare Soil":             "#d9b382",
    "Moderate Vegetation":   "#91cf60",
    "Dense Vegetation":      "#1a9850",
}


# ── Time-series chart ──────────────────────────────────────────────────────────
def plot_ndvi_trend(years: list, values: list, place: str, output_path: str):
    """
    Save an enhanced NDVI time-series line chart.
    Highlights min/max years, adds a linear trend line.
    """
    fig, ax = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    ax.plot(years, values, color="#38bdf8", linewidth=2.5, marker="o",
            markersize=7, markerfacecolor="#ffffff", zorder=3)

    # Shade area under curve
    ax.fill_between(years, values, min(values) - 0.005,
                    alpha=0.25, color="#38bdf8")

    # Highlight min and max
    idx_max = values.index(max(values))
    idx_min = values.index(min(values))
    ax.annotate(f"Peak\n{years[idx_max]}", xy=(years[idx_max], values[idx_max]),
                xytext=(0, 14), textcoords="offset points",
                ha="center", fontsize=8, color="#4ade80",
                arrowprops=dict(arrowstyle="->", color="#4ade80"))
    ax.annotate(f"Low\n{years[idx_min]}", xy=(years[idx_min], values[idx_min]),
                xytext=(0, -22), textcoords="offset points",
                ha="center", fontsize=8, color="#f87171",
                arrowprops=dict(arrowstyle="->", color="#f87171"))

    # Trend line
    if len(years) > 2:
        z = np.polyfit(years, values, 1)
        p = np.poly1d(z)
        ax.plot(years, p(years), "--", color="#fbbf24", linewidth=1.5,
                alpha=0.8, label=f"Trend: {z[0]:+.4f}/yr")
        ax.legend(facecolor="#1e293b", edgecolor="#334155", labelcolor="#e2e8f0",
                  fontsize=9)

    ax.set_title(f"NDVI Trend — {place} (2018–2024)",
                 color="#e2e8f0", fontsize=14, fontweight="bold", pad=12)
    ax.set_xlabel("Year", color="#94a3b8", fontsize=11)
    ax.set_ylabel("Average NDVI", color="#94a3b8", fontsize=11)
    ax.tick_params(colors="#94a3b8")
    ax.set_xticks(years)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.grid(True, color="#334155", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()


# ── Vegetation area bar chart ──────────────────────────────────────────────────
def plot_area_stats(area_stats: dict, place: str, output_path: str):
    """Save a styled bar chart of vegetation class areas."""
    labels = list(area_stats.keys())
    areas  = list(area_stats.values())
    colors = [CLASS_COLORS.get(l, "#888888") for l in labels]

    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    bars = ax.bar(labels, areas, color=colors, edgecolor="#0f172a", linewidth=0.8)
    for bar, area in zip(bars, areas):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(areas) * 0.01,
                f"{area:.1f} km²", ha="center", va="bottom",
                color="#e2e8f0", fontsize=9, fontweight="bold")

    total = sum(areas)
    ax.set_title(f"Vegetation Cover — {place} (2024)  |  Total: {total:.1f} km²",
                 color="#e2e8f0", fontsize=12, fontweight="bold", pad=12)
    ax.set_ylabel("Area (km²)", color="#94a3b8", fontsize=11)
    ax.tick_params(colors="#94a3b8", axis="both")
    ax.tick_params(axis="x", rotation=10)
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.grid(True, axis="y", color="#334155", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()


# ── Seasonal NDVI bar chart ────────────────────────────────────────────────────
def plot_seasonal(seasonal_values: dict, place: str, year: int, output_path: str):
    """Save a seasonal NDVI bar chart for a given year."""
    labels = list(seasonal_values.keys())
    vals   = list(seasonal_values.values())
    colors = ["#60a5fa", "#fbbf24", "#4ade80", "#c084fc"]

    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#0f172a")
    ax.set_facecolor("#1e293b")

    bars = ax.bar(labels, vals, color=colors, edgecolor="#0f172a")
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + 0.002,
                f"{val:.3f}", ha="center", va="bottom",
                color="#e2e8f0", fontsize=9)

    ax.set_title(f"Seasonal NDVI — {place} ({year})",
                 color="#e2e8f0", fontsize=12, fontweight="bold", pad=10)
    ax.set_ylabel("Mean NDVI", color="#94a3b8")
    ax.tick_params(colors="#94a3b8")
    for spine in ax.spines.values():
        spine.set_edgecolor("#334155")
    ax.grid(True, axis="y", color="#334155", linestyle="--", alpha=0.4)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close()


# ── Folium interactive map ─────────────────────────────────────────────────────
def build_ndvi_map(
    gdf: gpd.GeoDataFrame,
    ndvi_2018,
    ndvi_2024,
    ndvi_change,
    place: str,
) -> folium.Map:
    """
    Build a multi-layer Folium map with NDVI 2018, NDVI 2024, change layer,
    boundary overlay, and a styled legend.
    """
    import ee

    bounds = gdf.total_bounds  # [minx, miny, maxx, maxy]
    center = [(bounds[1] + bounds[3]) / 2, (bounds[0] + bounds[2]) / 2]

    m = folium.Map(location=center, zoom_start=11, tiles=None)

    # Base tiles
    folium.TileLayer("CartoDB positron", name="Base Map (Light)", control=True).add_to(m)
    folium.TileLayer("CartoDB dark_matter", name="Base Map (Dark)", control=True).add_to(m)

    # GEE NDVI layers
    for img, vis, name in [
        (ndvi_2018, NDVI_VIS, "🌿 NDVI 2018"),
        (ndvi_2024, NDVI_VIS, "🌿 NDVI 2024"),
        (ndvi_change, CHANGE_VIS, "📊 NDVI Change 2018→2024"),
    ]:
        try:
            layer = img.getMapId(vis)
            folium.TileLayer(
                tiles=layer["tile_fetcher"].url_format,
                attr="Google Earth Engine / Sentinel-2",
                name=name,
                overlay=True,
                show=(name == "🌿 NDVI 2024"),
            ).add_to(m)
        except Exception:
            pass

    # Boundary
    boundary_layer = folium.GeoJson(
        gdf,
        name="📍 Region Boundary",
        style_function=lambda _: {
            "color": "#38bdf8",
            "weight": 2.5,
            "fillOpacity": 0.05,
        },
        tooltip=place,
    )
    boundary_layer.add_to(m)
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

    folium.LayerControl(collapsed=False).add_to(m)
    _add_legend(m)
    _add_title(m, place)

    return m


def _add_legend(m: folium.Map):
    legend_html = """
    <div style="
        position:fixed; bottom:40px; left:40px;
        background:#1e293b; border:1px solid #334155;
        border-radius:8px; z-index:9999;
        font-family:monospace; font-size:12px;
        color:#e2e8f0; padding:12px 16px; min-width:200px;">
      <b style="color:#38bdf8">NDVI Vegetation Health</b>
      <hr style="border-color:#334155;margin:6px 0">
      <div><span style="background:#8b0000;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Bare Soil / Water</div>
      <div><span style="background:#ff4500;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Very Low Vegetation</div>
      <div><span style="background:#ffa500;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Low Vegetation</div>
      <div><span style="background:#ffff00;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Moderate Vegetation</div>
      <div><span style="background:#9acd32;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Healthy Vegetation</div>
      <div><span style="background:#006400;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Dense Vegetation</div>
      <br>
      <b style="color:#38bdf8">Change Layer</b>
      <hr style="border-color:#334155;margin:6px 0">
      <div><span style="background:#d73027;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Vegetation Loss</div>
      <div><span style="background:#f7f7f7;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px;border:1px solid #555"></span>No Change</div>
      <div><span style="background:#1a9850;display:inline-block;width:12px;height:12px;margin-right:6px;border-radius:2px"></span>Vegetation Gain</div>
      <br><span style="color:#64748b;font-size:10px">Sentinel-2 SR | Google Earth Engine</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))


def _add_title(m: folium.Map, place: str):
    title_html = f"""
    <div style="
        position:fixed; top:15px; left:50%; transform:translateX(-50%);
        background:#1e293b; border:1px solid #334155;
        border-radius:8px; z-index:9999;
        font-family:monospace; font-size:14px;
        color:#38bdf8; padding:8px 20px; font-weight:bold;">
      🌿 NDVI Vegetation Monitor — {place}
    </div>
    """
    m.get_root().html.add_child(folium.Element(title_html))
