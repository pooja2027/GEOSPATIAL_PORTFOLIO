"""
NDVI_Region_Tool.py
-------------------
CLI entry point for NDVI Vegetation Analysis.
Usage: python NDVI_Region_Tool.py
       (reads place name from stdin — used by Streamlit subprocess call)

Outputs:
  ndvi_trend_<place>.png      — NDVI time-series chart
  ndvi_area_<place>.png       — Vegetation class area chart
  ndvi_seasonal_<place>.png   — Seasonal NDVI chart
  ndvi_<place>.html           — Interactive Folium map
  NDVI_report_<place>.txt     — Full analysis report
"""

import os
import sys

# Allow running from any directory
sys.path.insert(0, os.path.dirname(__file__))

from src.ndvi_engine    import (initialize_gee, get_annual_ndvi,
                                build_time_series, compute_mean_ndvi,
                                compute_area_stats, get_seasonal_ndvi,
                                start_geotiff_export)
from src.location_utils import geocode_place, get_boundary, shapely_to_ee, clean_name
from src.viz_utils      import (plot_ndvi_trend, plot_area_stats,
                                plot_seasonal, build_ndvi_map)
from src.report_utils   import generate_report


def run(place: str):
    print(f"\n{'='*50}")
    print(f"  NDVI Analysis: {place}")
    print(f"{'='*50}\n")

    # ── 1. Initialise GEE ────────────────────────────────
    print("[1/7] Initialising Google Earth Engine...")
    initialize_gee()

    # ── 2. Geocode + boundary ────────────────────────────
    print("[2/7] Fetching location boundary...")
    lat, lon = geocode_place(place)
    print(f"      Coordinates: {lat:.5f}, {lon:.5f}")

    gdf, boundary, boundary_source = get_boundary(place)
    print(f"      Boundary source: {boundary_source}")

    region = shapely_to_ee(boundary)
    cname  = clean_name(place)

    # ── 3. NDVI images ───────────────────────────────────
    print("[3/7] Computing NDVI (2018 & 2024)...")
    ndvi_2018 = get_annual_ndvi(region, 2018)
    ndvi_2024 = get_annual_ndvi(region, 2024)
    ndvi_change = ndvi_2024.subtract(ndvi_2018)

    mean_2018 = compute_mean_ndvi(ndvi_2018, region)
    mean_2024 = compute_mean_ndvi(ndvi_2024, region)
    change_pct = ((mean_2024 - mean_2018) / mean_2018) * 100 if mean_2018 else 0.0

    print(f"      NDVI 2018: {mean_2018:.4f}")
    print(f"      NDVI 2024: {mean_2024:.4f}")
    print(f"      Change   : {change_pct:+.2f}%")

    # ── 4. Time series ───────────────────────────────────
    print("[4/7] Building time series (2018–2024)...")
    years = list(range(2018, 2025))
    valid_years, ndvi_values = build_time_series(region, years)

    trend_path = os.path.join("outputs", f"ndvi_trend_{cname}.png")
    plot_ndvi_trend(valid_years, ndvi_values, place, trend_path)
    print(f"      Saved: {trend_path}")

    # ── 5. Area stats + seasonal ─────────────────────────
    print("[5/7] Computing vegetation area statistics...")
    area_stats = compute_area_stats(region, ndvi_2024)
    print(f"      Area stats: {area_stats}")

    area_path = os.path.join("outputs", f"ndvi_area_{cname}.png")
    plot_area_stats(area_stats, place, area_path)
    print(f"      Saved: {area_path}")

    print("      Computing seasonal NDVI (2024)...")
    seasonal_imgs = get_seasonal_ndvi(region, 2024)
    seasonal_values = {}
    for season, img in seasonal_imgs.items():
        if img is not None:
            val = compute_mean_ndvi(img, region)
            if val:
                seasonal_values[season] = val

    if seasonal_values:
        seasonal_path = os.path.join("outputs", f"ndvi_seasonal_{cname}.png")
        plot_seasonal(seasonal_values, place, 2024, seasonal_path)
        print(f"      Saved: {seasonal_path}")

    # ── 6. Interactive map ───────────────────────────────
    print("[6/7] Building interactive map...")
    ndvi_map = build_ndvi_map(gdf, ndvi_2018, ndvi_2024, ndvi_change, place)

    map_path = os.path.join("outputs", f"ndvi_{cname}.html")
    count = 1
    while os.path.exists(map_path):
        map_path = os.path.join("outputs", f"ndvi_{cname}_{count}.html")
        count += 1
    ndvi_map.save(map_path)
    print(f"      Saved: {map_path}")

    # ── 7. Report + GeoTIFF export ───────────────────────
    print("[7/7] Generating report and starting GeoTIFF export...")
    report_path = os.path.join("outputs", f"NDVI_report_{cname}.txt")
    generate_report(
        place=place,
        lat=lat, lon=lon,
        ndvi_2018=mean_2018,
        ndvi_2024=mean_2024,
        area_stats=area_stats,
        time_series=(valid_years, ndvi_values),
        boundary_source=boundary_source,
        output_path=report_path,
    )
    print(f"      Saved: {report_path}")

    task = start_geotiff_export(ndvi_2024, region, cname, year=2024)
    print(f"      GeoTIFF export started (task: {task.id}). Check Google Drive.")

    print(f"\n{'='*50}")
    print("  Analysis complete.")
    print(f"{'='*50}\n")

    # Print machine-readable summary for Streamlit to parse
    print(f"RESULT::ndvi_2018={mean_2018:.6f}")
    print(f"RESULT::ndvi_2024={mean_2024:.6f}")
    print(f"RESULT::change_pct={change_pct:.4f}")
    print(f"RESULT::trend_path={trend_path}")
    print(f"RESULT::area_path={area_path}")
    print(f"RESULT::map_path={map_path}")
    print(f"RESULT::report_path={report_path}")
    if seasonal_values:
        print(f"RESULT::seasonal_path={seasonal_path}")


if __name__ == "__main__":
    place = input("Enter place name: ").strip()
    if not place:
        print("No place entered.")
        sys.exit(1)
    try:
        run(place)
    except Exception as e:
        print(f"ERROR: {e}")
        sys.exit(1)
