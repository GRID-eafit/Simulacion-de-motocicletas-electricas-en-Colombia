# -*- coding: utf-8 -*-
"""
Pre-computes the energy cost (Wh) for "access trips" - the final leg of a 
journey from a trip's destination to a potential charging station.

Updated for Main Pipeline Integration.
"""

import json
import os
import sys
import math
from tqdm import tqdm
import json5
import numpy as np
import geopandas as gpd
from shapely.geometry import Point

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running precompute_access_costs for: {locale_info}")

# 2. Define Dynamic Paths based on Territory
if locale_info == "Medellin":
    shapefile_folder_name = 'Limites Medellin'
    shapefile_name = 'Medellin_Urbano_y_Rural.shp'
elif locale_info == "Valle de aburra":
    shapefile_folder_name = 'Limites Valle de Aburra'
    shapefile_name = 'Valle_De_Aburra_Urbano_y_Rural.shp'
elif locale_info == "Bogota":
    shapefile_folder_name = 'Limites Bogota DC'
    shapefile_name = 'Bogota_Urbano_y_Rural.shp'
else:
    print(f"Error: Unknown locale '{locale_info}'")
    sys.exit(1)

# 3. Standardized File Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, 'Archivos de apoyo')
shapefile_folder = os.path.join(script_dir, shapefile_folder_name)
RESULTS = os.path.join(script_dir, "Results")

# Input Files
CONFIG_FILE = os.path.join(data_folder, 'config.jsonc')
file_path_shapefile = os.path.join(shapefile_folder, shapefile_name)
FILE_6_SIM_INPUT = os.path.join(data_folder, "milp_input_data.json")

# Output File (Standardized Name for Pipeline - Shared JSON)
FILE_7_ACCESS_COSTS = os.path.join(data_folder, "access_trip_costs.json")

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

print("Starting pre-computation of access costs with DYNAMIC station generation.")

# --- 1. Load Configuration ---
print("\nStep 1: Loading configuration from 'config.jsonc'...")
if not os.path.exists(CONFIG_FILE):
    print(f"CRITICAL ERROR: Config file not found at {CONFIG_FILE}")
    sys.exit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json5.load(f)

sim_cfg = config.get('simulation_settings', {})
opt_cfg = config['optimization_settings']
grid_cfg = opt_cfg['grid_settings']
opt_params = opt_cfg['parameters']

# --- 2. HELPER FUNCTIONS ---
def get_grid_cell(lat, lon, min_lat, min_lon, cell_size_lat, cell_size_lon, max_rows, max_cols, max_lat, max_lon):
    if not (min_lat <= lat <= max_lat and min_lon <= lon <= max_lon): return None
    col = int((lon - min_lon) / cell_size_lon)
    row = int((lat - min_lat) / cell_size_lat)
    if 0 <= row < max_rows and 0 <= col < max_cols: return (row, col)
    return None

def calculate_distance_km(cell1, cell2, cell_height_km, cell_width_km):
    row1, col1 = cell1; row2, col2 = cell2
    delta_x = (col1 - col2) * cell_width_km
    delta_y = (row1 - row2) * cell_height_km
    return math.sqrt(delta_x**2 + delta_y**2)

# --- 3. DYNAMICALLY GENERATE POTENTIAL STATION LOCATIONS ---
print("\nStep 2: Dynamically generating potential station locations...")

if not os.path.exists(FILE_6_SIM_INPUT):
    print(f"CRITICAL ERROR: Simulation input file '{FILE_6_SIM_INPUT}' not found.")
    print("Please run 'real_path_simulation.py' first.")
    sys.exit(1)

with open(FILE_6_SIM_INPUT, 'r') as f:
    all_routes_results = json.load(f)

# Grid and Shapefile Setup
LAT_DEG_TO_KM, LON_DEG_TO_KM = 111, 110
CELL_HEIGHT_DEG = grid_cfg['grid_size_km'] / LAT_DEG_TO_KM
CELL_WIDTH_DEG = grid_cfg['grid_size_km'] / LON_DEG_TO_KM

# Load Shapefile (Dynamic Path)
try:
    zonal_gdf = gpd.read_file(file_path_shapefile)
    # Ensure CRS is EPSG:4326 for lat/lon calculations
    if zonal_gdf.crs != "EPSG:4326":
        zonal_gdf = zonal_gdf.to_crs("EPSG:4326")
except Exception as e:
    print(f"Error loading shapefile: {e}")
    sys.exit(1)

city_polygon = zonal_gdf.geometry.union_all()
min_lon, min_lat, max_lon, max_lat = city_polygon.bounds
GRID_ROWS, GRID_COLS = int((max_lat - min_lat) / CELL_HEIGHT_DEG) + 1, int((max_lon - min_lon) / CELL_WIDTH_DEG) + 1
print(f"Created a {GRID_ROWS}x{GRID_COLS} grid over the area.")

# 3.1. Identify where the demand is coming from.
demand_by_cell = {}
for route in tqdm(all_routes_results, desc="Processing Route Origins"):
    origin_cell = get_grid_cell(route['start_coords']['lat'], route['start_coords']['lon'], min_lat, min_lon, CELL_HEIGHT_DEG, CELL_WIDTH_DEG, GRID_ROWS, GRID_COLS, max_lat, max_lon)
    if origin_cell:
        demand_by_cell[origin_cell] = demand_by_cell.get(origin_cell, 0) + 1
demand_cells_from_origins = list(demand_by_cell.keys())
print(f"Found {len(demand_cells_from_origins)} unique cells with trip origins.")

# 3.2. Pre-filter all grid cells to only include those inside the city boundary.
all_cells_in_boundary = []
all_grid_cells = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)]
for r, c in tqdm(all_grid_cells, desc="Filtering grid cells by main boundary"):
    lon_cell, lat_cell = min_lon + (c + 0.5) * CELL_WIDTH_DEG, min_lat + (r + 0.5) * CELL_HEIGHT_DEG
    if city_polygon.contains(Point(lon_cell, lat_cell)):
        all_cells_in_boundary.append((r, c))

# 3.3. Generate potential station locations based on proximity to demand.
potential_station_cells_set = set()
search_radius = opt_params['coverage_radius_km']
for demand_cell in tqdm(demand_cells_from_origins, desc="Finding candidate sites near demand"):
    potential_station_cells_set.add(demand_cell)
    for candidate_cell in all_cells_in_boundary:
        if calculate_distance_km(demand_cell, candidate_cell, grid_cfg['grid_size_km'], grid_cfg['grid_size_km']) <= search_radius:
            potential_station_cells_set.add(candidate_cell)

potential_station_cells = list(potential_station_cells_set)
print(f"Dynamic Generation Complete: Found {len(potential_station_cells)} potential locations.")

# --- 4. Prepare Data for Vectorization ---
print("\nStep 3: Preparing data for vectorized calculation...")
unique_destinations_dict = { (r['end_coords']['lat'], r['end_coords']['lon']): r['end_coords'] for r in all_routes_results }
print(f"Found {len(unique_destinations_dict)} unique destination points.")

dest_coords_array = np.array([[data['lat'], data['lon']] for data in unique_destinations_dict.values()])
station_coords_array = np.array([
    [min_lat + (r + 0.5) * CELL_HEIGHT_DEG, min_lon + (c + 0.5) * CELL_WIDTH_DEG]
    for r, c in potential_station_cells
])

# --- 5. Perform High-Speed Vectorized Calculation ---
print("\nStep 4: Performing vectorized distance and cost calculation...")

delta_coords = dest_coords_array[:, np.newaxis, :] - station_coords_array[np.newaxis, :, :]
delta_coords[:, :, 0] *= LAT_DEG_TO_KM
delta_coords[:, :, 1] *= LON_DEG_TO_KM
distance_matrix_km = np.sqrt(np.sum(delta_coords**2, axis=2))

total_wh = sum(r['electric_wh_consumed'] for r in all_routes_results)
total_km = sum(r['distance_km'] for r in all_routes_results)
AVG_WH_PER_KM = (total_wh / total_km) if total_km > 0 else 75
print(f"Using an average vehicle energy rate of: {AVG_WH_PER_KM:.2f} Wh/km")

cost_matrix_wh = distance_matrix_km * AVG_WH_PER_KM

# --- 6. Format and Save Results ---
print("\nStep 5: Formatting and saving results...")
access_trip_costs_wh = {}
unique_dest_list = list(unique_destinations_dict.values())

for i in tqdm(range(len(unique_dest_list)), desc="Saving Costs"):
    dest_point = unique_dest_list[i]
    for j in range(len(potential_station_cells)):
        station_cell = potential_station_cells[j]
        
        final_cost = cost_matrix_wh[i, j]

        key = str((dest_point['lat'], dest_point['lon'], station_cell[0], station_cell[1]))
        access_trip_costs_wh[key] = final_cost

with open(FILE_7_ACCESS_COSTS, 'w') as f:
    json.dump(access_trip_costs_wh, f) # Using compact format for speed

print(f"\nPre-computation complete.")
print(f"A complete set of access trip costs ({len(access_trip_costs_wh)} entries) has been saved to '{FILE_7_ACCESS_COSTS}'.")