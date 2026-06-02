"""
clustering.py
-------------
KMeans and DBSCAN clustering for geospatial project data.
"""

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler


def run_kmeans(df: pd.DataFrame, n_clusters: int, random_state: int = 42) -> pd.DataFrame:
    """
    Apply KMeans clustering on lat/lon coordinates.
    Adds 'cluster' column to returned DataFrame.
    """
    coords = df[["latitude", "longitude"]].values
    scaler = StandardScaler()
    coords_scaled = scaler.fit_transform(coords)

    model = KMeans(n_clusters=n_clusters, random_state=random_state, n_init=10)
    df = df.copy()
    df["cluster"] = model.fit_predict(coords_scaled).astype(str)
    df["cluster_method"] = "KMeans"

    # Compute cluster centers (back in original space)
    centers_scaled = model.cluster_centers_
    centers = scaler.inverse_transform(centers_scaled)
    center_df = pd.DataFrame(centers, columns=["center_lat", "center_lon"])
    center_df["cluster"] = [str(i) for i in range(n_clusters)]

    df = df.merge(center_df, on="cluster", how="left")
    return df


def run_dbscan(df: pd.DataFrame, eps_km: float = 50.0, min_samples: int = 2) -> pd.DataFrame:
    """
    Apply DBSCAN clustering using haversine metric (distance in km).
    Cluster label -1 = noise/outlier points.
    Adds 'cluster' column to returned DataFrame.
    """
    coords_rad = np.radians(df[["latitude", "longitude"]].values)
    earth_radius_km = 6371.0
    eps_rad = eps_km / earth_radius_km

    model = DBSCAN(eps=eps_rad, min_samples=min_samples, algorithm="ball_tree", metric="haversine")
    df = df.copy()
    labels = model.fit_predict(coords_rad)
    df["cluster"] = labels.astype(str)
    df["cluster_method"] = "DBSCAN"

    # Label noise points clearly
    df["is_noise"] = labels == -1

    # Compute cluster centers for non-noise clusters
    centers = []
    for label in set(labels):
        if label == -1:
            continue
        mask = labels == label
        center_lat = df.loc[mask, "latitude"].mean()
        center_lon = df.loc[mask, "longitude"].mean()
        centers.append({"cluster": str(label), "center_lat": center_lat, "center_lon": center_lon})

    if centers:
        center_df = pd.DataFrame(centers)
        df = df.merge(center_df, on="cluster", how="left")
    else:
        df["center_lat"] = df["latitude"]
        df["center_lon"] = df["longitude"]

    return df


def cluster_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Return a per-cluster summary: count, total cost, dominant type, dominant status.
    """
    agg = {
        "project_name": "count",
    }
    if "cost_crore" in df.columns:
        agg["cost_crore"] = "sum"
    if "type" in df.columns:
        agg["type"] = lambda x: x.mode()[0] if not x.empty else "N/A"
    if "status" in df.columns:
        agg["status"] = lambda x: x.mode()[0] if not x.empty else "N/A"

    noise_mask = df["cluster"] == "-1"
    summary = (
        df[~noise_mask]
        .groupby("cluster")
        .agg(agg)
        .reset_index()
    )
    summary.rename(columns={"project_name": "project_count"}, inplace=True)
    return summary
