"""
location_utils.py
-----------------
Geocoding and boundary acquisition via OSMnx and Nominatim.
"""

import ee
import geopandas as gpd
from geopy.geocoders import Nominatim
from shapely.geometry import Point


def geocode_place(place: str) -> tuple[float, float]:
    """
    Return (lat, lon) for a place name using Nominatim.
    Raises ValueError if not found.
    """
    geolocator = Nominatim(user_agent="ndvi_analysis_geo")
    location = geolocator.geocode(place, timeout=10)
    if location is None:
        raise ValueError(f"Location not found: '{place}'. Try a more specific name.")
    return location.latitude, location.longitude


def get_boundary(place: str, buffer_deg: float = 0.2) -> tuple[gpd.GeoDataFrame, object]:
    """
    Fetch administrative boundary from OSM.
    Falls back to a circular buffer around the geocoded point if no polygon found.
    Returns (gdf, shapely_geometry).
    """
    import osmnx as ox

    try:
        gdf = ox.geocode_to_gdf(place)
        boundary = gdf.geometry.iloc[0]
        source = "OSM boundary"
    except Exception:
        lat, lon = geocode_place(place)
        point = Point(lon, lat)
        boundary = point.buffer(buffer_deg)
        gdf = gpd.GeoDataFrame(geometry=[boundary], crs="EPSG:4326")
        source = f"Buffer ({buffer_deg}° radius)"

    return gdf, boundary, source


def shapely_to_ee(geometry) -> ee.Geometry:
    """Convert a Shapely geometry to an Earth Engine geometry."""
    geo_interface = geometry.__geo_interface__
    geom_type = geo_interface["type"]

    if geom_type == "Polygon":
        return ee.Geometry.Polygon(geo_interface["coordinates"])
    elif geom_type == "MultiPolygon":
        return ee.Geometry.MultiPolygon(geo_interface["coordinates"])
    else:
        raise TypeError(f"Unsupported geometry type: {geom_type}")


def clean_name(place: str) -> str:
    """Convert place name to a filesystem-safe string."""
    return place.strip().replace(" ", "_").replace(",", "")
