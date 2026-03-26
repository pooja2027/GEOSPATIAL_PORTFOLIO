import ee
import folium
from geopy.geocoders import Nominatim
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point
import matplotlib.pyplot as plt
import os

print("\nNDVI Vegetation Monitoring Tool\n")

# Initialize Earth Engine
try:
    ee.Initialize()
except:
    ee.Authenticate()
    ee.Initialize(project="earthengine-pooja")

# User input
place = input("Enter place name: ")

geolocator = Nominatim(user_agent="geo_app")
location = geolocator.geocode(place)

if location is None:
    print("Location not found")
    exit()

lat = location.latitude
lon = location.longitude
print(f"Coordinates: {lat}, {lon}")

# Get boundary from OpenStreetMap
print("Downloading boundary from OpenStreetMap...")

try:
    gdf = ox.geocode_to_gdf(place)
    boundary = gdf.geometry.iloc[0]
    print("Boundary loaded successfully")
except:
    print("Polygon not found. Creating 20 km buffer.")
    point = Point(lon, lat)
    boundary = point.buffer(0.2)
    gdf = gpd.GeoDataFrame(geometry=[boundary], crs="EPSG:4326")

region = ee.Geometry.Polygon(boundary.__geo_interface__['coordinates'])

# NDVI calculation
def add_ndvi(image):
    ndvi = image.normalizedDifference(['B8','B4']).rename('NDVI')
    return image.addBands(ndvi)

def get_ndvi(year):
    collection = (
        ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED")
        .filterBounds(region)
        .filterDate(f"{year}-01-01", f"{year}-12-31")
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE',20))
        .map(add_ndvi)
    )
    return collection.select("NDVI").median().clip(region)

ndvi_2018 = get_ndvi(2018)
ndvi_2024 = get_ndvi(2024)

# NDVI change
ndvi_change = ndvi_2024.subtract(ndvi_2018)

# NDVI statistics
def ndvi_mean(image):
    stat = image.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=30,
        maxPixels=1e13,
        bestEffort=True
    )
    return stat.getInfo()['NDVI']

ndvi18 = ndvi_mean(ndvi_2018)
ndvi24 = ndvi_mean(ndvi_2024)

print("\nAverage NDVI 2018:", ndvi18)
print("Average NDVI 2024:", ndvi24)

change_percent = ((ndvi24 - ndvi18) / ndvi18) * 100
print("Vegetation change:", round(change_percent,2), "%")

# NDVI time-series
years = list(range(2018,2025))
ndvi_values = []

for y in years:
    img = get_ndvi(y)
    stat = img.reduceRegion(
        reducer=ee.Reducer.mean(),
        geometry=region,
        scale=30,
        maxPixels=1e13,
        bestEffort=True
    )
    ndvi_values.append(stat.getInfo()['NDVI'])

plt.figure(figsize=(8,5))
plt.plot(years, ndvi_values, marker='o')
plt.title("NDVI Trend (2018-2024)")
plt.xlabel("Year")
plt.ylabel("Average NDVI")
plt.grid(True)

clean = place.replace(" ","_")
trend_file = f"ndvi_trend_{clean}.png"
plt.savefig(trend_file)

print("NDVI trend graph saved:", trend_file)

# Vegetation classification
pixel_area = ee.Image.pixelArea()

veg_classes = ndvi_2024.expression(
"(b('NDVI') < 0.2) ? 1"
": (b('NDVI') < 0.4) ? 2"
": (b('NDVI') < 0.6) ? 3"
": 4"
).rename("class")

area_image = pixel_area.addBands(veg_classes)

area_stats = area_image.reduceRegion(
    reducer=ee.Reducer.sum().group(
        groupField=1,
        groupName='class'
    ),
    geometry=region,
    scale=30,
    maxPixels=1e13
)

print("\nVegetation Area Statistics:")
print(area_stats.getInfo())

# Visualization parameters
ndvi_vis = {
'min':0,
'max':1,
'palette':['8b0000','ff0000','ffa500','ffff00','9acd32','006400']
}

change_vis = {
'min':-0.5,
'max':0.5,
'palette':['red','white','green']
}

# Create interactive map
m = folium.Map()

ndvi_layer = ndvi_2024.getMapId(ndvi_vis)

folium.TileLayer(
    tiles=ndvi_layer['tile_fetcher'].url_format,
    attr="NDVI",
    name="NDVI 2024",
    overlay=True
).add_to(m)

change_layer = ndvi_change.getMapId(change_vis)

folium.TileLayer(
    tiles=change_layer['tile_fetcher'].url_format,
    attr="NDVI Change",
    name="NDVI Change 2018-2024",
    overlay=True
).add_to(m)

geojson = folium.GeoJson(gdf)
geojson.add_to(m)

m.fit_bounds(geojson.get_bounds())
folium.LayerControl().add_to(m)

# Map legend
legend_html = """
<div style="
position: fixed;
bottom: 50px;
left: 50px;
width: 230px;
background-color: white;
border:2px solid grey;
z-index:9999;
font-size:14px;
padding: 10px;
">
<b>NDVI Vegetation Health</b><br><br>
<i style="background:#8b0000;width:15px;height:15px;float:left;margin-right:8px;"></i>Bare Soil<br>
<i style="background:#ff0000;width:15px;height:15px;float:left;margin-right:8px;"></i>Very Low Vegetation<br>
<i style="background:#ffa500;width:15px;height:15px;float:left;margin-right:8px;"></i>Low Vegetation<br>
<i style="background:#ffff00;width:15px;height:15px;float:left;margin-right:8px;"></i>Moderate Vegetation<br>
<i style="background:#9acd32;width:15px;height:15px;float:left;margin-right:8px;"></i>Healthy Vegetation<br>
<i style="background:#006400;width:15px;height:15px;float:left;margin-right:8px;"></i>Dense Vegetation
<br><br>
<b>NDVI Change</b><br>
<i style="background:red;width:15px;height:15px;float:left;margin-right:8px;"></i>Loss<br>
<i style="background:white;width:15px;height:15px;float:left;margin-right:8px;border:1px solid black;"></i>No Change<br>
<i style="background:green;width:15px;height:15px;float:left;margin-right:8px;"></i>Gain
</div>
"""

m.get_root().html.add_child(folium.Element(legend_html))

# Save map
map_file = f"ndvi_{clean}.html"

count = 1
while os.path.exists(map_file):
    map_file = f"ndvi_{clean}_{count}.html"
    count += 1

m.save(map_file)
print("\nMap saved:", map_file)

# Export NDVI GeoTIFF
task = ee.batch.Export.image.toDrive(
image=ndvi_2024,
description='NDVI_export',
folder='NDVI_Exports',
fileNamePrefix=f"ndvi_{clean}",
region=region,
scale=10,
maxPixels=1e13
)

task.start()
print("GeoTIFF export started (check Google Drive).")

# Auto report
report_file = f"NDVI_report_{clean}.txt"

with open(report_file,"w") as f:
    f.write("NDVI Vegetation Monitoring Report\n")
    f.write("---------------------------------\n")
    f.write(f"Location: {place}\n")
    f.write(f"Coordinates: {lat},{lon}\n\n")
    f.write(f"NDVI 2018: {ndvi18}\n")
    f.write(f"NDVI 2024: {ndvi24}\n")
    f.write(f"\nVegetation Change: {round(change_percent,2)} %\n")

    if change_percent > 0:
        f.write("Vegetation increased\n")
    else:
        f.write("Vegetation decreased\n")
print("Report saved:", report_file)