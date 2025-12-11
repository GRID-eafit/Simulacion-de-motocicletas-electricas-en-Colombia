"""
Final MILP Optimization for LEV Charging Network Design.
Updated for Main Pipeline Integration.

This script integrates physics-based simulation data with advanced optimization
constraints to determine the optimal location and technology mix.
"""

import json5
import json
import math
import pulp
import geopandas as gpd
from shapely.geometry import Point
import folium
from tqdm import tqdm
import os
import sys
import pandas as pd

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running Optimization_FCLP for: {locale_info}")

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
FILE_7_ACCESS_COSTS = os.path.join(data_folder, "access_trip_costs.json")

# Output Files
OUTPUT_MAP = os.path.join(  , f"optimal_locations_map_{locale_info}.html")
OUTPUT_CSV = os.path.join(RESULTS, f"optimal_solution_{locale_info}.csv")

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

# --- 1. LOAD CONFIGURATION ---
print("Step 1: Loading configuration from 'config.jsonc'...")
if not os.path.exists(CONFIG_FILE):
    print(f"CRITICAL ERROR: Config file not found at {CONFIG_FILE}")
    sys.exit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    config = json5.load(f)

opt_cfg = config['optimization_settings']
grid_cfg = opt_cfg['grid_settings']
battery_cfg = opt_cfg['battery_settings']
tech_cfg = opt_cfg['technologies']
opt_params = opt_cfg['parameters']

# --- 2. HELPER FUNCTIONS ---
def get_grid_cell(lat, lon, min_lat, min_lon, cell_size_lat, cell_size_lon, max_rows, max_cols):
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

# --- 3. DATA PREPARATION ---
print("\nStep 2: Loading and preprocessing all required data...")

# Load Simulation Data
if not os.path.exists(FILE_6_SIM_INPUT):
    print(f"CRITICAL ERROR: Simulation input '{FILE_6_SIM_INPUT}' not found.")
    sys.exit(1)
with open(FILE_6_SIM_INPUT, 'r') as f:
    all_routes_results = json.load(f)

# Load Access Costs
if not os.path.exists(FILE_7_ACCESS_COSTS):
    print(f"CRITICAL ERROR: Access costs '{FILE_7_ACCESS_COSTS}' not found.")
    sys.exit(1)
with open(FILE_7_ACCESS_COSTS, 'r') as f:
    access_trip_costs_wh = json.load(f)

print(f"Loaded {len(access_trip_costs_wh)} pre-computed access trip costs.")

# Grid Setup
LAT_DEG_TO_KM, LON_DEG_TO_KM = 111, 110
CELL_HEIGHT_DEG = grid_cfg['grid_size_km'] / LAT_DEG_TO_KM
CELL_WIDTH_DEG = grid_cfg['grid_size_km'] / LON_DEG_TO_KM

# Load Shapefile
try:
    zonal_gdf = gpd.read_file(file_path_shapefile)
    if zonal_gdf.crs != "EPSG:4326":
        zonal_gdf = zonal_gdf.to_crs("EPSG:4326")
except Exception as e:
    print(f"Error loading shapefile: {e}")
    sys.exit(1)

city_polygon = zonal_gdf.geometry.union_all()
min_lon, min_lat, max_lon, max_lat = city_polygon.bounds
GRID_ROWS, GRID_COLS = int((max_lat - min_lat) / CELL_HEIGHT_DEG) + 1, int((max_lon - min_lon) / CELL_WIDTH_DEG) + 1
print(f"Created a {GRID_ROWS}x{GRID_COLS} grid over the area.")

# --- DEMAND-CENTRIC LOCATION GENERATION ---

# 1. Identify demand cells
print("Identifying all unique demand cells from trip origins...")
demand_by_cell = {}
for route in tqdm(all_routes_results, desc="Processing Route Origins"):
    origin_cell = get_grid_cell(route['start_coords']['lat'], route['start_coords']['lon'], min_lat, min_lon, CELL_HEIGHT_DEG, CELL_WIDTH_DEG, GRID_ROWS, GRID_COLS)
    if origin_cell:
        demand_by_cell[origin_cell] = demand_by_cell.get(origin_cell, 0) + 1
demand_cells_from_origins = list(demand_by_cell.keys())
print(f"Found {len(demand_cells_from_origins)} unique cells with trip origins.")

# 2. Filter grid cells by boundary
all_cells_in_boundary = []
all_grid_cells = [(r, c) for r in range(GRID_ROWS) for c in range(GRID_COLS)]
for r, c in tqdm(all_grid_cells, desc="Filtering grid cells by main boundary"):
    lon, lat = min_lon + (c + 0.5) * CELL_WIDTH_DEG, min_lat + (r + 0.5) * CELL_HEIGHT_DEG
    if city_polygon.contains(Point(lon, lat)):
        all_cells_in_boundary.append((r, c))

# 3. Generate potential station locations
print("\nGenerating potential station locations based on proximity to demand...")
potential_station_cells_set = set()
search_radius = opt_params['coverage_radius_km']

for demand_cell in tqdm(demand_cells_from_origins, desc="Finding candidate sites near demand"):
    potential_station_cells_set.add(demand_cell) 
    for candidate_cell in all_cells_in_boundary:
        if calculate_distance_km(demand_cell, candidate_cell, grid_cfg['grid_size_km'], grid_cfg['grid_size_km']) <= search_radius:
            potential_station_cells_set.add(candidate_cell)

potential_station_cells = list(potential_station_cells_set)
print(f"Smart Filtering Complete: Reduced search space to {len(potential_station_cells)} potential locations.")

# --- MAPPING, FEASIBILITY, AND FINAL PREP ---

cell_to_zone_map = {}
if opt_cfg['zonal_constraints']['enabled']:
    print("Mapping grid cells to municipal zones...")
    zone_id_col = opt_cfg['zonal_constraints']['zone_id_column']
    if zone_id_col not in zonal_gdf.columns:
        print(f"WARNING: Zone column '{zone_id_col}' not found. Available: {zonal_gdf.columns.tolist()}")
        print("Skipping zonal mapping.")
    else:
        for cell in tqdm(potential_station_cells, desc="Mapping cells to zones"):
            point = Point(min_lon + (cell[1] + 0.5) * CELL_WIDTH_DEG, min_lat + (cell[0] + 0.5) * CELL_HEIGHT_DEG)
            for _, zone in zonal_gdf.iterrows():
                if zone.geometry.contains(point):
                    cell_to_zone_map[cell] = zone[zone_id_col]
                    break

print("\nApplying Safe-Range Feasibility check using pre-computed costs...")
eligible_stations_per_demand_cell = {}
start_wh = battery_cfg["total_capacity_wh"] * (battery_cfg["starting_soc_pct"] / 100)
reserve_wh = battery_cfg["total_capacity_wh"] * (battery_cfg["low_soc_threshold_pct"] / 100)

for route in tqdm(all_routes_results, desc="Processing Routes for Feasibility"):
    origin_cell = get_grid_cell(route['start_coords']['lat'], route['start_coords']['lon'], min_lat, min_lon, CELL_HEIGHT_DEG, CELL_WIDTH_DEG, GRID_ROWS, GRID_COLS)
    if not origin_cell: continue

    eligible_stations_for_this_route = []
    for station_cell in potential_station_cells:
        if calculate_distance_km(origin_cell, station_cell, grid_cfg['grid_size_km'], grid_cfg['grid_size_km']) > opt_params['coverage_radius_km']:
            continue

        key = str((route['end_coords']['lat'], route['end_coords']['lon'], station_cell[0], station_cell[1]))
        access_trip_wh = access_trip_costs_wh.get(key)

        if access_trip_wh is not None:
            total_consumed_wh = route['electric_wh_consumed'] + access_trip_wh
            if (start_wh - total_consumed_wh) >= reserve_wh:
                eligible_stations_for_this_route.append(station_cell)

    if eligible_stations_for_this_route:
        eligible_stations_per_demand_cell[origin_cell] = list(set(eligible_stations_per_demand_cell.get(origin_cell, []) + eligible_stations_for_this_route))

demand_cells = list(demand_by_cell.keys())
print(f"Finished processing. Found {len(demand_cells)} unique demand cells with at least one feasible station.")

# --- 4. MILP MODEL FORMULATION ---
print(f"\nStep 3: Formulating MILP with objective: {opt_cfg['objective_function']['type']}...")
prob = pulp.LpProblem("Advanced_EV_Station_Location", pulp.LpMaximize)

tech_keys = list(tech_cfg.keys())
station_tech = pulp.LpVariable.dicts("StationTech", (potential_station_cells, tech_keys), cat='Binary')
is_station_built = pulp.LpVariable.dicts("IsStationBuilt", potential_station_cells, cat='Binary')

assign_keys = [(j, i) for j in demand_cells for i in eligible_stations_per_demand_cell.get(j, [])]
assignment = pulp.LpVariable.dicts("Assignment", assign_keys, cat='Binary')

total_demand_covered = pulp.lpSum(assignment[(j, i)] * demand_by_cell[j] for j, i in assign_keys)

if opt_cfg['objective_function']['type'] == "profit_maximization":
    profit_params = opt_cfg['objective_function']['profit_parameters']
    total_revenue = total_demand_covered * profit_params['revenue_per_charge_session'] * profit_params['days_per_year']
    annualized_capital_cost = pulp.lpSum(station_tech[i][t] * tech_cfg[t]['cost'] for i in potential_station_cells for t in tech_keys) / opt_params['lifespan_years']
    annual_op_cost = pulp.lpSum(station_tech[i][t] * tech_cfg[t]['annual_op_cost'] for i in potential_station_cells for t in tech_keys)
    prob += total_revenue - (annualized_capital_cost + annual_op_cost), "Maximize_Annual_Profit"
else:
    utility_weights = opt_cfg['objective_function']['utility_weights']
    total_travel_distance = pulp.lpSum(assignment[(j, i)] * demand_by_cell[j] * calculate_distance_km(j, i, grid_cfg['grid_size_km'], grid_cfg['grid_size_km']) for j, i in assign_keys)
    prob += utility_weights['coverage'] * total_demand_covered - utility_weights['travel_distance'] * total_travel_distance, "Weighted_Multi_Objective"

# --- Constraints ---
for i in potential_station_cells:
    prob += pulp.lpSum(station_tech[i][t] for t in tech_keys) == is_station_built[i], f"Link_Tech_To_Station_{i}"

total_cost = pulp.lpSum(station_tech[i][t] * tech_cfg[t]['cost'] for i in potential_station_cells for t in tech_keys)
prob += total_cost <= opt_params['total_budget'], "Budget_Constraint"

# Allow flexible station count: use exact if specified, otherwise use max
if 'exact_stations_to_build' in opt_params:
    exact_count = opt_params['exact_stations_to_build']
    # Check if we should enforce exact count or just maximum
    if opt_params.get('enforce_exact_station_count', False):
        # Enforce exact number of stations
        prob += pulp.lpSum(is_station_built[i] for i in potential_station_cells) == exact_count, "Exact_Stations_Constraint"
        print(f"Enforcing exact number of stations: {exact_count}")
    else:
        # Allow up to the specified number (original behavior)
        prob += pulp.lpSum(is_station_built[i] for i in potential_station_cells) <= exact_count, "Max_Stations_Constraint"
        print(f"Maximum number of stations allowed: {exact_count} (may build fewer if optimal)")

# Optional minimum station count constraint
if 'minimum_stations_to_build' in opt_params:
    min_count = opt_params['minimum_stations_to_build']
    prob += pulp.lpSum(is_station_built[i] for i in potential_station_cells) >= min_count, "Min_Stations_Constraint"
    print(f"Minimum number of stations required: {min_count}")

total_resources_used = pulp.lpSum(station_tech[i][t] * tech_cfg[t]['resource_units_required'] for i in potential_station_cells for t in tech_keys)
prob += total_resources_used <= opt_params['total_resource_units_available'], "Total_Resource_Units_Constraint"

if opt_cfg['zonal_constraints']['enabled']:
    print("Enforcing Zonal Station Density Constraints...")
    zone_limits = opt_cfg['zonal_constraints']['max_stations_per_zone']
    cells_by_zone = {}
    for cell, zone_name in cell_to_zone_map.items():
        if zone_name not in cells_by_zone: cells_by_zone[zone_name] = []
        cells_by_zone[zone_name].append(cell)
    for zone_name, cells_in_zone in cells_by_zone.items():
        limit = zone_limits.get(zone_name, zone_limits.get("DEFAULT", 999))
        prob += pulp.lpSum(is_station_built[i] for i in cells_in_zone) <= limit, f"Zone_Limit_{zone_name.replace(' ', '_')}"

for j in tqdm(demand_cells, desc="Building Assignment Constraints"):
    eligible_stations = eligible_stations_per_demand_cell.get(j, [])
    if not eligible_stations:
        continue
    prob += pulp.lpSum(assignment[(j, i)] for i in eligible_stations) <= 1, f"Assign_Demand_{j}_Once"
    for i in eligible_stations:
        prob += assignment[(j, i)] <= is_station_built[i], f"Link_Assign_{j}_to_Station_{i}"

for i in tqdm(potential_station_cells, desc="Building Capacity Constraints"):
    station_capacity = pulp.lpSum(station_tech[i][t] * tech_cfg[t]['service_capacity_routes_per_day'] for t in tech_keys)
    demand_assigned_to_i = pulp.lpSum(assignment[(j, i)] * demand_by_cell.get(j, 0) for j in demand_cells if (j, i) in assign_keys)
    prob += demand_assigned_to_i <= station_capacity, f"Capacity_of_Station_{i}"

# --- Minimum Station Separation Constraint ---
if 'minimum_station_separation_km' in opt_params:
    min_separation_km = opt_params['minimum_station_separation_km']
    print(f"\nEnforcing Minimum Station Separation: {min_separation_km} km...")
    
    # Pre-compute pairs of stations that are too close
    too_close_pairs = []
    for idx1, i1 in enumerate(potential_station_cells):
        for idx2, i2 in enumerate(potential_station_cells):
            if idx1 < idx2:  # Avoid duplicate pairs and self-pairs
                dist = calculate_distance_km(i1, i2, grid_cfg['grid_size_km'], grid_cfg['grid_size_km'])
                if dist < min_separation_km:
                    too_close_pairs.append((i1, i2))
    
    print(f"Found {len(too_close_pairs)} pairs of potential stations that violate minimum separation.")
    
    # Add constraint: for each pair that's too close, at most one can be built
    for i1, i2 in tqdm(too_close_pairs, desc="Building Minimum Separation Constraints"):
        prob += is_station_built[i1] + is_station_built[i2] <= 1, f"MinSep_{i1}_and_{i2}"
else:
    print("\nWARNING: 'minimum_station_separation_km' not found in parameters. Stations may be placed too close together.")

if opt_params['enforce_closest_assignment']:
    print("Enforcing Closest Assignment Constraint...")
    for j in tqdm(demand_cells, desc="Building Closest Assignment Constraints"):
        eligible_stations = eligible_stations_per_demand_cell.get(j, [])
        if not eligible_stations: continue
        sorted_stations = sorted(eligible_stations, key=lambda i: calculate_distance_km(j, i, grid_cfg['grid_size_km'], grid_cfg['grid_size_km']))
        for idx, i in enumerate(sorted_stations):
            closer_stations = sorted_stations[:idx]
            for k in closer_stations:
                prob += assignment[(j, i)] + is_station_built[k] <= 1, f"Closest_Assign_{j}_to_{i}_over_{k}"


# --- 5. SOLVE THE MODEL ---
print("\nStep 4: Solving the optimization problem...")

# NOTE: Update this path if your MOSEK installation is different
mosek_path = r'C:\Program Files\Mosek\11.0\tools\platform\win64x86\bin\mosek.exe'

start_time = pd.Timestamp.now()
try:
    print("Attempting to solve with MOSEK...")
    solver = pulp.MOSEK(msg=True) # PuLP usually finds MOSEK if on PATH, otherwise use path
    prob.solve(solver)
except (pulp.PulpSolverError, FileNotFoundError):
    print("\n--- MOSEK Error ---")
    print("Falling back to the default CBC solver...")
    prob.solve() 

end_time = pd.Timestamp.now()
print(f"Solver finished in {(end_time - start_time).total_seconds():.2f} seconds.")

#------------------------ Additional function----------------------------------
def convert_cell_to_coords(cell, min_lat, min_lon, cell_height_deg, cell_width_deg):
    row, col = cell
    longitude = min_lon + (col + 0.5) * cell_width_deg
    latitude = min_lat + (row + 0.5) * cell_height_deg
    return {"latitude": latitude, "longitude": longitude}

# --- 6. RESULTS & VISUALIZATION ---
print("\n--- Optimization Results ---")
print(f"Status: {pulp.LpStatus[prob.status]}")

if pulp.LpStatus[prob.status] == 'Optimal':
    demand_covered_val = pulp.value(total_demand_covered)
    print(f"Total Demand (All Routes): {len(all_routes_results)}")
    print(f"Demand Covered: {int(demand_covered_val)} ({ (demand_covered_val / len(all_routes_results)) * 100 if all_routes_results else 0:.2f}%)")
    
    if opt_cfg['objective_function']['type'] == "profit_maximization":
        print(f"Optimal Solution (Maximized Annual Profit): ${pulp.value(prob.objective):,.2f}")
    else:
        total_distance_val = pulp.value(total_travel_distance)
        print(f"Average Travel Distance for Served Routes: {(total_distance_val / demand_covered_val) if demand_covered_val > 0 else 0:.2f} km")

    station_locations = {i: t for i in potential_station_cells for t in tech_keys if station_tech[i][t].varValue > 0.9}
    final_cost = sum(tech_cfg[t]['cost'] for t in station_locations.values())
    final_resources = sum(tech_cfg[t]['resource_units_required'] for t in station_locations.values())
    
    print(f"\nNumber of Stations Built: {len(station_locations)}")
    print(f"Total Cost: ${final_cost:,.2f} (Budget: ${opt_params['total_budget']:,.2f})")
    print(f"Total Resource Units Used: {final_resources} (System Limit: {opt_params['total_resource_units_available']})")
    
    # Save CSV Results
    results_data = []
    print("\nOptimal Station Locations:")
    for loc, tech in sorted(station_locations.items()):
        coords = convert_cell_to_coords(loc, min_lat, min_lon, CELL_HEIGHT_DEG, CELL_WIDTH_DEG)
        print(f"  - Cell: {loc}, Type: {tech}, Lat: {coords['latitude']:.6f}, Lon: {coords['longitude']:.6f}")
        results_data.append({
            "Cell_Row": loc[0], "Cell_Col": loc[1],
            "Technology": tech,
            "Latitude": coords['latitude'], "Longitude": coords['longitude']
        })
    
    pd.DataFrame(results_data).to_csv(OUTPUT_CSV, index=False)
    print(f"Solution saved to {OUTPUT_CSV}")

    print(f"\nStep 5: Generating interactive map ('{OUTPUT_MAP}')...")
    map_center_lat, map_center_lon = min_lat + (max_lat - min_lat) / 2, min_lon + (max_lon - min_lon) / 2
    m = folium.Map(location=[map_center_lat, map_center_lon], zoom_start=10, tiles="cartodbpositron")

    if city_polygon:
        folium.GeoJson(zonal_gdf, name='Municipal Boundaries', style_function=lambda x: {'color': 'black', 'weight': 1, 'fillOpacity': 0.1}).add_to(m)

    station_assignments = {loc: [] for loc in station_locations}
    
    for j, i in assign_keys:
        if assignment[(j, i)].varValue > 0.9:
            if i in station_assignments:
                station_assignments[i].append(j)

    for station, assigned_cells in station_assignments.items():
        station_lon, station_lat = min_lon + (station[1] + 0.5) * CELL_WIDTH_DEG, min_lat + (station[0] + 0.5) * CELL_HEIGHT_DEG
        for demand_cell in assigned_cells:
            demand_lon, demand_lat = min_lon + (demand_cell[1] + 0.5) * CELL_WIDTH_DEG, min_lat + (demand_cell[0] + 0.5) * CELL_HEIGHT_DEG
            folium.PolyLine(locations=[(station_lat, station_lon), (demand_lat, demand_lon)], color='gray', weight=0.5, opacity=0.7).add_to(m)

    for cell, demand in demand_by_cell.items():
        r, c = cell
        lon, lat = min_lon + (c + 0.5) * CELL_WIDTH_DEG, min_lat + (r + 0.5) * CELL_HEIGHT_DEG
        folium.CircleMarker(location=[lat, lon], radius=2 + math.log(demand + 1), color='#0078A8', fill=True, fill_opacity=0.6, popup=f"Demand Cell: {cell}<br>Routes: {demand}").add_to(m)

    for loc, tech in station_locations.items():
        r, c = loc
        lon, lat = min_lon + (c + 0.5) * CELL_WIDTH_DEG, min_lat + (r + 0.5) * CELL_HEIGHT_DEG
        station_info = tech_cfg[tech]
        folium.Circle(location=[lat, lon], radius=opt_params['coverage_radius_km'] * 1000, color=station_info['color'], weight=2, fill_opacity=0.1).add_to(m)
        folium.Marker(location=[lat, lon], popup=f"<b>Station {loc}</b><br>Type: {tech}", icon=folium.Icon(color='red', icon=station_info['icon'], prefix='fa')).add_to(m)
        
    folium.LayerControl().add_to(m)
    m.save(OUTPUT_MAP)
    print(f"Map saved! Open '{OUTPUT_MAP}' in your browser.")
else:
    print("Could not find an optimal solution.")