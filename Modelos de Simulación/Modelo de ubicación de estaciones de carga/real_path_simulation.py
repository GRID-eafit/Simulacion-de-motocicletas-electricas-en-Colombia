# -*- coding: utf-8 -*-
"""
Created on Thu Jun 12 17:39:49 2025
Updated for Main Pipeline Integration (Circuit Breaker Removed)
"""

import os
import time
import requests
import pickle
import numpy as np
import pandas as pd
import json
import json5
import sys

# --- Local Model Import ---
try:
    from HybridBikeConsumptionModel.Modelo_moto import bike_model_particle as detailed_particle_model
except ImportError:
    print("CRITICAL ERROR: Could not import 'HybridBikeConsumptionModel'.")
    print("Ensure the folder 'HybridBikeConsumptionModel' exists in the 'Scripts' directory.")
    sys.exit(1)

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running real_path_simulation for: {locale_info}")

# 2. Define Dynamic Paths based on Territory
if locale_info == "Medellin":
    shapefile_folder_name = 'Limites Medellin'
elif locale_info == "Valle de aburra":
    shapefile_folder_name = 'Limites Valle de Aburra'
elif locale_info == "Bogota":
    shapefile_folder_name = 'Limites Bogota DC'
else:
    print(f"Error: Unknown locale '{locale_info}'")
    sys.exit(1)

# 3. Standardized File Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, 'Archivos de apoyo')
RESULTS = os.path.join(script_dir, "Results")

# Input Files
CONFIG_FILE = os.path.join(data_folder, 'config.jsonc')
FILE_5_SAMPLE = os.path.join(RESULTS, f"5_final_sample_{locale_info}.csv")

# Output File (Standardized Name for Pipeline - Shared JSON)
FILE_6_SIM_INPUT = os.path.join(data_folder, "milp_input_data.json")

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

# --- Data Generation Function ---
def generate_route_from_ors(start_point, end_point, api_key):
    """
    Generates a detailed route using the ORS API with a bike-specific profile.
    """
    # Check for identical points to save an API call
    if start_point['lat'] == end_point['lat'] and start_point['lon'] == end_point['lon']:
        print("  -> Skipping route: Start and end coordinates are the same.")
        return None, 0
    
    print(f"Fetching e-bike route from {start_point} to {end_point}...")
    
    MAX_RETRIES = 3 # Reduced retries to speed up skipping bad routes
    RETRY_DELAY_SECONDS = 2
    
    start_coords_ors = [start_point['lon'], start_point['lat']]
    end_coords_ors = [end_point['lon'], end_point['lat']]
    headers = {"Authorization": api_key, "Content-Type": "application/json"}
    
    # 1. Get Directions
    directions_data = None
    attempt = 0
    for attempt in range(MAX_RETRIES):
        try:
            directions_url = "https://api.openrouteservice.org/v2/directions/cycling-electric"
            payload = {"coordinates": [start_coords_ors, end_coords_ors], "instructions": True}
            response = requests.post(directions_url, json=payload, headers=headers, timeout=10)
            
            # Handle specific API errors gracefully
            if response.status_code == 404: # Route not found (points too close or impossible)
                print("  -> ORS Error 404: Route could not be found (points likely too close).")
                return None, attempt + 1
            
            response.raise_for_status()
            data = response.json()
            if "routes" in data and data["routes"]:
                directions_data = data
                print("  -> Directions received successfully.")
                break
        except requests.exceptions.RequestException as e:
            print(f"  -> Directions API error: {e}. Attempt {attempt + 1}/{MAX_RETRIES}...")
        time.sleep(RETRY_DELAY_SECONDS)
    directions_api_calls = attempt + 1
    
    if not directions_data:
        print("  ERROR: Failed to fetch valid directions.")
        return None, directions_api_calls

    # 2. Get Elevation
    elevation_data = None
    geometry_encoded = directions_data["routes"][0]["geometry"]
    for attempt in range(MAX_RETRIES):
        try:
            elevation_url = "https://api.openrouteservice.org/elevation/line"
            payload = {"format_in": "encodedpolyline", "format_out": "geojson", "geometry": geometry_encoded}
            response = requests.post(elevation_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            data = response.json()
            if "geometry" in data and "coordinates" in data["geometry"] and data["geometry"]["coordinates"]:
                elevation_data = data['geometry']['coordinates']
                print("  -> Elevation received successfully.")
                break
        except requests.exceptions.RequestException as e:
            print(f"  -> Elevation API error: {e}. Attempt {attempt + 1}/{MAX_RETRIES}...")
        time.sleep(RETRY_DELAY_SECONDS)
    elevation_api_calls = attempt + 1    
    
    if not elevation_data:
        print("  ERROR: Failed to fetch valid elevation.")
        return None, directions_api_calls + elevation_api_calls

    # 3. Process data
    print("  -> Processing route data...")
    route_points = []
    total_time = 0
    total_distance = 0
    steps = directions_data["routes"][0]["segments"][0]["steps"]

    for step in steps:
        start_idx, end_idx = step["way_points"]
        step_duration, step_distance = step["duration"], step["distance"]
        num_points = end_idx - start_idx
        if num_points == 0: continue
        duration_per_point, distance_per_point = step_duration / num_points, step_distance / num_points
        for i in range(num_points):
            idx = start_idx + i
            if idx >= len(elevation_data): continue
            
            lng, lat, alt = elevation_data[idx]
            slope = (alt - (route_points[-1]["altitude"] if route_points else alt)) / distance_per_point * 100 if distance_per_point > 0 else 0
            
            route_points.append({
                "latitude": lat, "longitude": lng, "altitude": round(alt, 2),
                "distance_km": round((total_distance + distance_per_point) / 1000, 2),
                "time_sec": round(total_time + duration_per_point, 2),
                "slope_pct": round(slope, 2),
                "speed_kmh": round((distance_per_point / duration_per_point) * 3.6, 2) if duration_per_point > 0 else 0,
            })
            total_time += duration_per_point
            total_distance += distance_per_point
            
    return route_points, directions_api_calls + elevation_api_calls

# --- Main Execution Block ---
if __name__ == '__main__':
    
    # 1. Load Configurations
    print(f"Loading configuration from '{CONFIG_FILE}'...")
    if not os.path.exists(CONFIG_FILE):
        print(f"FATAL ERROR: Config file not found at {CONFIG_FILE}")
        sys.exit(1)

    with open(CONFIG_FILE, 'r',  encoding='latin-1') as f:
        config = json5.load(f)

    # 2. Load Input Data (Sampled Paths)
    if not os.path.exists(FILE_5_SAMPLE):
        print(f"FATAL ERROR: Input file '{FILE_5_SAMPLE}' not found.")
        print("Please run 'Stratified_sampling.py' first.")
        sys.exit(1)

    paths_to_process_df = pd.read_csv(FILE_5_SAMPLE)
    print(f"Successfully loaded {len(paths_to_process_df)} paths to process.")

    # 3. Setup Simulation Parameters
    sim_config = config['simulation_settings']
    vehicle_to_use = sim_config['vehicle_model_to_use']
    vehicle_params = sim_config['vehicle_models'][vehicle_to_use]
    api_key = sim_config.get("ors_api_key")
    
    if not api_key or api_key == "PASTE_YOUR_API_KEY_HERE":
        print("FATAL ERROR: Please add your OpenRouteService API key to config.jsonc")
        sys.exit(1)
    
    # 4. Processing Loop
    if not paths_to_process_df.empty:
        all_routes_results = []
        total_api_calls_made = 0
        API_CALL_LIMIT = 1900 # Standard free tier limit is 2000/day
        
        for index, row in paths_to_process_df.iterrows():
            print(f"\n--- Processing Path {index + 1}/{len(paths_to_process_df)} ---")
            
            # Extract start and end points
            start_point = {'lat': row['ORIGIN_CENTROID_LAT'], 'lon': row['ORIGIN_CENTROID_LON']}
            end_point = {'lat': row['DESTINATION_CENTROID_LAT'], 'lon': row['DESTINATION_CENTROID_LON']}
            
            # Cache Logic
            cache_folder = os.path.join(script_dir, "Route Cache")
            os.makedirs(cache_folder, exist_ok=True)
            cache_filename = f"route_cache_{start_point['lat']}_{start_point['lon']}_to_{end_point['lat']}_{end_point['lon']}.pkl"
            full_path_cache = os.path.join(cache_folder, cache_filename)
            
            if os.path.exists(full_path_cache):
                print(f"Loading route data from local cache: {cache_filename}")
                with open(full_path_cache, 'rb') as f:
                    route_data = pickle.load(f)
            else:
                # Check Daily Limit before calling API
                if total_api_calls_made >= API_CALL_LIMIT:
                    print("\n!!! DAILY LIMIT REACHED !!!")
                    print(f"Stopping to avoid exceeding API quota ({total_api_calls_made} calls).")
                    break 

                route_data, api_calls_this_run = generate_route_from_ors(start_point, end_point, api_key)
                total_api_calls_made += api_calls_this_run
                
                if route_data is None:
                    print(f"  -> Skipping this route due to API/Data error. Continuing to next...")
                    continue # <--- THIS IS THE FIX: Just skip, don't break
                else:
                    # Save to cache only on success
                    with open(full_path_cache, 'wb') as f:
                        pickle.dump(route_data, f)

            # Run Physics Simulation
            if route_data:
                print("  -> Data loaded successfully. Running simulation...")
                final_speeds = [p['speed_kmh'] for p in route_data]
                final_slopes = [np.degrees(np.arctan(p['slope_pct'] / 100)) for p in route_data]
                
                final_battery, fuel_gallons, combus_wh, total_energy_wh = detailed_particle_model(
                    hybrid_cont=sim_config['hybrid_contribution'],
                    speeds=final_speeds,
                    slopes=final_slopes,
                    vehicle_params=vehicle_params
                )
                
                result_summary = {
                    "route_index": index + 1,
                    "start_coords": start_point,
                    "end_coords": end_point,
                    "distance_km": route_data[-1]['distance_km'],
                    "duration_minutes": route_data[-1]['time_sec'] / 60,
                    "electric_wh_consumed": sum(total_energy_wh) - sum(combus_wh),
                    "combustion_wh_consumed": sum(combus_wh),
                    "fuel_gallons_consumed": sum(fuel_gallons),
                    "final_battery_wh": final_battery
                }
                all_routes_results.append(result_summary)
                print("  -> Simulation complete. Results recorded.")
        
        # 5. Save Results
        print(f"\n--- All routes processed. Saving summary to '{FILE_6_SIM_INPUT}' ---")
        with open(FILE_6_SIM_INPUT, 'w') as f:
            json.dump(all_routes_results, f, indent=2, ensure_ascii=False)
            
        print("Process complete.")