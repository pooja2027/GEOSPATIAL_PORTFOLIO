"""
ndvi_engine.py
--------------
Core NDVI computation and GEE operations.
Handles: image collection, NDVI calculation, time-series, classification, export.
"""

import ee


def initialize_gee(project: str = "earthengine-pooja"):
    """Initialize Google Earth Engine, authenticating if needed."""
    try:
        ee.Initialize(project=project)
    except Exception:
        ee.Authenticate()
        ee.Initialize(project=project)


def add_ndvi(image: ee.Image) -> ee.Image:
    """Compute NDVI from Sentinel-2 B8 (NIR) and B4 (Red) bands."""
    ndvi = image.normalizedDifference(["B8", "B4"]).rename("NDVI")
    return image.addBands(ndvi)


def get_annual_ndvi(region: ee.Geometry, year: int) -> ee.Image:
    """
    Return median annual NDVI image for a given year and region.
    Uses Sentinel-2 SR Harmonized with <20% cloud cover.
    """
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
        .map(add_ndvi)
    )
    return collection.select("NDVI").median().clip(region)


def get_seasonal_ndvi(region: ee.Geometry, year: int) -> dict:
    """
    Return NDVI images for each season of a year.
    Seasons: NE Monsoon (Jan-Feb), Summer (Mar-May),
             SW Monsoon (Jun-Sep), Post-Monsoon (Oct-Dec).
    """
    seasons = {
        "NE_Monsoon": (f"{year}-01-01", f"{year}-02-28"),
        "Summer":     (f"{year}-03-01", f"{year}-05-31"),
        "SW_Monsoon": (f"{year}-06-01", f"{year}-09-30"),
        "Post_Monsoon": (f"{year}-10-01", f"{year}-12-31"),
    }
    result = {}
    for name, (start, end) in seasons.items():
        col = (
            ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
            .filterBounds(region)
            .filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 20))
            .map(add_ndvi)
        )
        count = col.size().getInfo()
        if count > 0:
            result[name] = col.select("NDVI").median().clip(region)
        else:
            result[name] = None
    return result


def compute_mean_ndvi(image: ee.Image, region: ee.Geometry, scale: int = 30) -> float:
    """Compute mean NDVI for the region at given scale."""
    stat = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
        bestEffort=True,
    )
    val = stat.getInfo().get("NDVI")
    return float(val) if val is not None else 0.0


def build_time_series(region: ee.Geometry, years: list, scale: int = 30) -> tuple:
    """
    Compute annual mean NDVI for a list of years.
    Returns (years, ndvi_values) as parallel lists.
    """
    values = []
    valid_years = []
    for year in years:
        img = get_annual_ndvi(region, year)
        val = compute_mean_ndvi(img, region, scale)
        if val != 0.0:
            values.append(val)
            valid_years.append(year)
    return valid_years, values


def classify_vegetation(ndvi_image: ee.Image) -> ee.Image:
    """
    Classify NDVI into 4 vegetation classes:
      1 = Water/Built-up (NDVI < 0.1)
      2 = Bare Soil       (0.1 – 0.2)
      3 = Moderate Veg    (0.2 – 0.4)
      4 = Dense Veg       (>= 0.4)
    """
    classified = (
        ndvi_image
        .where(ndvi_image.lt(0.1), 1)
        .where(ndvi_image.gte(0.1).And(ndvi_image.lt(0.2)), 2)
        .where(ndvi_image.gte(0.2).And(ndvi_image.lt(0.4)), 3)
        .where(ndvi_image.gte(0.4), 4)
        .rename("class")
    )
    return classified


def compute_area_stats(region: ee.Geometry, ndvi_image: ee.Image, scale: int = 30) -> dict:
    """
    Compute area (km²) per vegetation class.
    Returns dict: {class_label: area_km2}
    """
    pixel_area = ee.Image.pixelArea()
    classified = classify_vegetation(ndvi_image)
    area_image = pixel_area.addBands(classified)

    raw = area_image.reduceRegion(
        reducer=ee.Reducer.sum().group(groupField=1, groupName="class"),
        geometry=region,
        scale=scale,
        maxPixels=1e13,
    ).getInfo()

    label_map = {
        1: "Water / Built-up",
        2: "Bare Soil",
        3: "Moderate Vegetation",
        4: "Dense Vegetation",
    }
    result = {}
    for group in raw.get("groups", []):
        cls = int(group["class"])
        area_km2 = group["sum"] / 1_000_000
        result[label_map.get(cls, f"Class {cls}")] = round(area_km2, 2)
    return result


def start_geotiff_export(
    ndvi_image: ee.Image,
    region: ee.Geometry,
    place_clean: str,
    year: int,
    scale: int = 10,
) -> ee.batch.Task:
    """Start a GEE batch export of NDVI GeoTIFF to Google Drive."""
    task = ee.batch.Export.image.toDrive(
        image=ndvi_image,
        description=f"NDVI_{place_clean}_{year}",
        folder="NDVI_Exports",
        fileNamePrefix=f"ndvi_{place_clean}_{year}",
        region=region,
        scale=scale,
        maxPixels=1e13,
    )
    task.start()
    return task
