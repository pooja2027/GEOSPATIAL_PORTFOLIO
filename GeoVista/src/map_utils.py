"""
map_utils.py
------------
Folium map construction for GeoVista: cluster markers, heatmap, GeoJSON export.
"""

import json
import folium
import pandas as pd
from folium.plugins import HeatMap, MarkerCluster


# Distinct colors for up to 12 clusters
CLUSTER_COLORS = [
    "#E63946", "#457B9D", "#2A9D8F", "#E9C46A", "#F4A261",
    "#6A4C93", "#1982C4", "#8AC926", "#FF595E", "#6A994E",
    "#BC4749", "#A8DADC",
]

STATUS_ICONS = {
    "Active": "play",
    "Completed": "check",
    "Planning": "clock",
    "Unknown": "question",
}


def _get_color(cluster_label: str, unique_labels: list) -> str:
    if cluster_label == "-1":
        return "#999999"  # Noise points = grey
    try:
        idx = unique_labels.index(cluster_label) % len(CLUSTER_COLORS)
        return CLUSTER_COLORS[idx]
    except ValueError:
        return "#333333"


def build_cluster_map(df: pd.DataFrame, map_style: str = "cluster_markers") -> folium.Map:
    """
    Build a Folium map. map_style options:
      - 'cluster_markers' : colored markers grouped by cluster
      - 'heatmap'         : cost-weighted heatmap layer
      - 'both'            : cluster markers + heatmap overlay
    """
    center_lat = df["latitude"].mean()
    center_lon = df["longitude"].mean()

    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="CartoDB positron",
    )

    unique_labels = sorted(df["cluster"].unique().tolist(), key=lambda x: int(x) if x.lstrip("-").isdigit() else 0)

    if map_style in ("cluster_markers", "both"):
        _add_cluster_markers(m, df, unique_labels)

    if map_style in ("heatmap", "both"):
        _add_heatmap(m, df)

    # Cluster center circles
    if "center_lat" in df.columns and map_style != "heatmap":
        _add_center_circles(m, df, unique_labels)

    folium.LayerControl().add_to(m)
    return m


def _add_cluster_markers(m: folium.Map, df: pd.DataFrame, unique_labels: list):
    """Add individual project markers colored by cluster."""
    feature_group = folium.FeatureGroup(name="Project Markers")

    for _, row in df.iterrows():
        color = _get_color(row["cluster"], unique_labels)
        noise_tag = " (Noise)" if row.get("is_noise", False) else ""
        cluster_label = f"Cluster {row['cluster']}{noise_tag}"

        popup_html = f"""
        <div style="font-family: monospace; min-width: 180px;">
          <b style="color:{color}">{row.get('project_name', 'N/A')}</b><br>
          <hr style="margin:4px 0">
          <b>Type:</b> {row.get('type', 'N/A')}<br>
          <b>Status:</b> {row.get('status', 'N/A')}<br>
          <b>Cost:</b> ₹{row.get('cost_crore', 0):,.0f} Cr<br>
          <b>District:</b> {row.get('district', 'N/A')}<br>
          <b>Year:</b> {row.get('year', 'N/A')}<br>
          <b>{cluster_label}</b>
        </div>
        """

        folium.CircleMarker(
            location=[row["latitude"], row["longitude"]],
            radius=8,
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.75,
            popup=folium.Popup(popup_html, max_width=220),
            tooltip=row.get("project_name", "Project"),
        ).add_to(feature_group)

    feature_group.add_to(m)


def _add_heatmap(m: folium.Map, df: pd.DataFrame):
    """Add a cost-weighted heatmap layer."""
    heat_data = [
        [row["latitude"], row["longitude"], float(row.get("cost_crore", 1)) or 1]
        for _, row in df.iterrows()
    ]
    HeatMap(heat_data, name="Cost Heatmap", radius=35, blur=20, min_opacity=0.4).add_to(m)


def _add_center_circles(m: folium.Map, df: pd.DataFrame, unique_labels: list):
    """Add translucent circles at cluster centroids."""
    centers_seen = set()
    for _, row in df.iterrows():
        key = (round(row.get("center_lat", 0), 4), round(row.get("center_lon", 0), 4))
        if key in centers_seen or row["cluster"] == "-1":
            continue
        centers_seen.add(key)
        color = _get_color(row["cluster"], unique_labels)
        folium.Circle(
            location=[row["center_lat"], row["center_lon"]],
            radius=40000,
            color=color,
            fill=True,
            fill_opacity=0.08,
            weight=1.5,
            tooltip=f"Cluster {row['cluster']} centroid",
        ).add_to(m)


def export_geojson(df: pd.DataFrame) -> str:
    """
    Export clustered project data as a GeoJSON FeatureCollection string.
    """
    features = []
    for _, row in df.iterrows():
        props = {col: (str(row[col]) if pd.notna(row[col]) else None)
                 for col in df.columns if col not in ("latitude", "longitude")}
        feature = {
            "type": "Feature",
            "geometry": {
                "type": "Point",
                "coordinates": [row["longitude"], row["latitude"]],
            },
            "properties": props,
        }
        features.append(feature)

    geojson = {"type": "FeatureCollection", "features": features}
    return json.dumps(geojson, indent=2)
