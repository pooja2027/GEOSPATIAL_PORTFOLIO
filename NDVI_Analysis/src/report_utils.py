"""
report_utils.py
---------------
Auto-generate structured NDVI analysis reports as .txt files.
"""

from datetime import datetime


HEALTH_THRESHOLDS = [
    (0.6,  "Excellent — Dense, healthy vegetation dominates the region."),
    (0.4,  "Good — Moderate-to-healthy vegetation present."),
    (0.2,  "Fair — Sparse vegetation; significant non-vegetated surfaces."),
    (0.0,  "Poor — Mostly bare soil, built-up, or water surfaces."),
    (-1.0, "Critical — Negligible or no vegetation detected."),
]

CHANGE_THRESHOLDS = [
    (10,   "Significant vegetation increase. Possible reforestation or seasonal improvement."),
    (2,    "Marginal increase. Stable or slowly improving vegetation cover."),
    (-2,   "Stable. No significant vegetation change detected."),
    (-10,  "Marginal decrease. Monitor for continued degradation."),
    (-100, "Significant vegetation loss. Likely urbanisation, deforestation, or drought stress."),
]


def _interpret(value: float, thresholds: list) -> str:
    for threshold, message in thresholds:
        if value >= threshold:
            return message
    return "Insufficient data."


def generate_report(
    place: str,
    lat: float,
    lon: float,
    ndvi_2018: float,
    ndvi_2024: float,
    area_stats: dict,
    time_series: tuple,
    boundary_source: str,
    output_path: str,
):
    """
    Write a full NDVI analysis report to a .txt file.
    """
    change_pct = ((ndvi_2024 - ndvi_2018) / ndvi_2018) * 100 if ndvi_2018 else 0.0
    direction  = "increased" if change_pct > 0 else "decreased"

    health_note  = _interpret(ndvi_2024, HEALTH_THRESHOLDS)
    change_note  = _interpret(change_pct, CHANGE_THRESHOLDS)

    years, values = time_series
    peak_year = years[values.index(max(values))] if values else "N/A"
    low_year  = years[values.index(min(values))] if values else "N/A"

    total_area = sum(area_stats.values()) if area_stats else 0
    veg_area   = sum(v for k, v in area_stats.items() if "Vegetation" in k)
    veg_pct    = (veg_area / total_area * 100) if total_area > 0 else 0

    lines = [
        "=" * 60,
        "  NDVI VEGETATION MONITORING REPORT",
        "  GeoSpatial Portfolio — Pooja P.",
        "=" * 60,
        f"  Generated : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"  Location  : {place}",
        f"  Lat / Lon : {lat:.5f}, {lon:.5f}",
        f"  Boundary  : {boundary_source}",
        f"  Data      : Sentinel-2 SR Harmonized (GEE)",
        "=" * 60,
        "",
        "── NDVI STATISTICS ──────────────────────────────────────",
        f"  Mean NDVI 2018 : {ndvi_2018:.4f}",
        f"  Mean NDVI 2024 : {ndvi_2024:.4f}",
        f"  Change         : {change_pct:+.2f}% ({direction})",
        f"  Peak Year      : {peak_year}",
        f"  Lowest Year    : {low_year}",
        "",
        "── VEGETATION HEALTH (2024) ─────────────────────────────",
        f"  {health_note}",
        "",
        "── CHANGE INTERPRETATION ────────────────────────────────",
        f"  {change_note}",
        "",
        "── AREA STATISTICS (2024) ───────────────────────────────",
    ]

    if area_stats:
        for cls, area in area_stats.items():
            pct = (area / total_area * 100) if total_area > 0 else 0
            lines.append(f"  {cls:<25} : {area:>8.2f} km²  ({pct:.1f}%)")
        lines += [
            f"  {'Total Area':<25} : {total_area:>8.2f} km²",
            f"  {'Total Vegetated':<25} : {veg_area:>8.2f} km²  ({veg_pct:.1f}%)",
        ]

    lines += [
        "",
        "── TIME SERIES (2018–2024) ──────────────────────────────",
    ]
    if years:
        for yr, val in zip(years, values):
            bar_len = int((val / 0.5) * 30)
            bar = "█" * min(bar_len, 30)
            lines.append(f"  {yr} | {bar:<30} | {val:.4f}")

    lines += [
        "",
        "── METHODOLOGY ──────────────────────────────────────────",
        "  Index    : NDVI = (B8 - B4) / (B8 + B4)",
        "  Sensor   : Sentinel-2 MSI Level-2A (SR Harmonized)",
        "  Platform : Google Earth Engine",
        "  Cloud    : < 20% per scene, annual median composite",
        "  Scale    : 30 m spatial resolution for statistics",
        "",
        "── NOTES ────────────────────────────────────────────────",
        "  • NDVI range: -1 (water/built-up) to +1 (dense veg)",
        "  • Values > 0.4 indicate healthy vegetation canopy",
        "  • Year-to-year variation may reflect seasonal effects",
        "  • For calibrated change detection, use Level-2A only",
        "",
        "=" * 60,
        "  Built with Sentinel-2 + Google Earth Engine",
        "  github.com/pooja2027/Geospatial_Portfolio",
        "=" * 60,
    ]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return change_pct, veg_pct
