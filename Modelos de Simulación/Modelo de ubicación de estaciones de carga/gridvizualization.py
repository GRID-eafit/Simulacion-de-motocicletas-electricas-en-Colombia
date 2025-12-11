# -*- coding: utf-8 -*-
"""
Created on Thu Jul 24 04:48:08 2025
"""

import json5
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Point, Polygon
from tqdm import tqdm
import os

#
#          For analysis please define the correct territory to analyze and trips coords
#  
#      Possible analysis include:                   Folder/name of shapefile
#       * Medellin                                 Limites Medellin / Medellin_Urbano_y_Rural.shp
#       * Valle de aburra                          Limites Valle de Aburra / Valle_De_Aburra_Urbano_y_Rural.shp
#       * Bogota                                   Limites Bogota DC / Bogota_Urbano_y_Rural.shp
#
#
#
#     All shapefiles are found in the parent folder where this py file is currently        
# 

print("Starting grid visualization script...")

# --- 1. LOAD CONFIGURATION FROM EXTERNAL FILE ---
print("Step 1: Loading configuration from 'config.jsonc'...")
script_dir = os.path.dirname(os.path.abspath(__file__))
SUPPORT_FOLDER = os.path.join(script_dir, "Archivos de apoyo")
config_path = os.path.join(SUPPORT_FOLDER, 'config.jsonc')
try:
    with open(config_path, 'r', encoding='utf-8') as f:
        config = json5.load(f)
except FileNotFoundError:
    raise FileNotFoundError("CRITICAL: 'config.jsonc' not found. Please ensure it's in the project directory.")

grid_cfg = config['optimization_settings']['grid_settings']

# --- 2. LOAD SHAPEFILE ---
print(f"Step 2: Loading shapefile")
SUPPORT_FOLDER_1 = os.path.join(script_dir, "Limites Bogota DC") #EDIT HERE
shapefile_path = os.path.join(SUPPORT_FOLDER_1, 'Bogota_Urbano_y_Rural.shp') #EDIT HERE
zonal_gdf = gpd.read_file(shapefile_path)
# Ensure the GeoDataFrame is using a standard coordinate system (WGS84)
zonal_gdf = zonal_gdf.to_crs(epsg=4326)
city_polygon = zonal_gdf.geometry.union_all()

# --- 3. CREATE GRID GEOMETRY ---
print("Step 3: Generating grid geometry based on shapefile bounds...")
min_lon, min_lat, max_lon, max_lat = city_polygon.bounds

LAT_DEG_TO_KM, LON_DEG_TO_KM = 111, 110
CELL_HEIGHT_DEG = grid_cfg['grid_size_km'] / LAT_DEG_TO_KM
CELL_WIDTH_DEG = grid_cfg['grid_size_km'] / LON_DEG_TO_KM

GRID_ROWS = int((max_lat - min_lat) / CELL_HEIGHT_DEG) + 1
GRID_COLS = int((max_lon - min_lon) / CELL_WIDTH_DEG) + 1
print(f"Calculated a {GRID_ROWS}x{GRID_COLS} grid to overlay the area.")

all_cells_polygons = []
for r in tqdm(range(GRID_ROWS), desc="Generating and filtering grid cells"):
    for c in range(GRID_COLS):
        # Calculate the four corners of the grid cell
        bottom_left_lon = min_lon + c * CELL_WIDTH_DEG
        bottom_left_lat = min_lat + r * CELL_HEIGHT_DEG
        
        top_left = (bottom_left_lon, bottom_left_lat + CELL_HEIGHT_DEG)
        top_right = (bottom_left_lon + CELL_WIDTH_DEG, bottom_left_lat + CELL_HEIGHT_DEG)
        bottom_right = (bottom_left_lon + CELL_WIDTH_DEG, bottom_left_lat)
        bottom_left = (bottom_left_lon, bottom_left_lat)

        cell_poly = Polygon([top_left, top_right, bottom_right, bottom_left])
        
        # Only include the cell if its center is within the actual city boundary
        if city_polygon.contains(cell_poly.centroid):
            all_cells_polygons.append(cell_poly)

# Create a new GeoDataFrame for the grid
grid_gdf = gpd.GeoDataFrame(geometry=all_cells_polygons, crs="EPSG:4326")
print(f"Generated {len(grid_gdf)} valid grid cells that are inside the metropolitan area.")

# --- 4. PLOT THE MAP AND GRID ---
print("\nStep 4: Creating visualization...")
fig, ax = plt.subplots(1, 1, figsize=(12, 16))

# Plot the base map of Valle de Aburrá
zonal_gdf.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.7)

# Overlay the grid on top
grid_gdf.plot(ax=ax, facecolor='none', edgecolor='blue', linewidth=0.5, alpha=0.7)

# Add titles and labels for clarity
ax.set_title('Superposición de Grilla', fontdict={'fontsize': 16, 'fontweight': 'bold'})
ax.set_xlabel('Longitud')
ax.set_ylabel('Latitud')
ax.tick_params(axis='x', rotation=45)
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()

# Save the figure
output_folder = os.path.join(script_dir, "Results")
output_filename = "grid_visualization.png"
output_path = os.path.join(output_folder, output_filename)
plt.savefig(output_path, dpi=300)
print(f"Visualization saved to '{output_path}'")

# Display the plot
plt.show()