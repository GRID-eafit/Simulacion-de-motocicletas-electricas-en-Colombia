# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 09:35:02 2025
Updated for Main Pipeline Integration
"""
import pandas as pd
import numpy as np
import os
import sys
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString, Point

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running Stratified_sampling for: {locale_info}")

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
file_path_shapefile = os.path.join(shapefile_folder, shapefile_name)
FILE_3_CLUSTERED = os.path.join(RESULTS, f"3_clustered_{locale_info}.csv")
FILE_4_FLOWS = os.path.join(RESULTS, f"4_flows_{locale_info}.csv")

# Output File (Standardized Name for Pipeline)
FILE_5_SAMPLE = os.path.join(RESULTS, f"5_final_sample_{locale_info}.csv")

# Sampling Configuration
FINAL_SAMPLE_SIZE = 500
STRATA_PROPORTIONS = {
    'AM_PEAK': {'Short': 0.10, 'Medium': 0.20, 'Long': 0.10},
    'MIDDAY':  {'Short': 0.05, 'Medium': 0.10, 'Long': 0.05},
    'PM_PEAK': {'Short': 0.10, 'Medium': 0.20, 'Long': 0.10}
}
DISTANCE_BINS = {
    'Short': (0, 5), 'Medium': (5, 15), 'Long': (15, 1000)
}

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

# --- Helper Functions ---
def haversine_distance(lat1, lon1, lat2, lon2):
    R = 6371
    lat1_rad, lon1_rad, lat2_rad, lon2_rad = map(np.radians, [lat1, lon1, lat2, lon2])
    dlon, dlat = lon2_rad - lon1_rad, lat2_rad - lat1_rad
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))
    return R * c

def get_time_bin(hour):
    if pd.isna(hour): return 'OFF_PEAK'
    try:
        hour = int(float(hour)) # Handle strings like "8.0"
    except ValueError:
        return 'OFF_PEAK'
        
    if 6 <= hour < 9: return 'AM_PEAK'
    elif 9 <= hour < 16: return 'MIDDAY'
    elif 16 <= hour < 19: return 'PM_PEAK'
    else: return 'OFF_PEAK'

def get_distance_bin(distance):
    for bin_name, (lower, upper) in DISTANCE_BINS.items():
        if lower <= distance < upper:
            return bin_name
    return None

# --- 1. Load Data ---
print("Loading data...")
if not os.path.exists(FILE_4_FLOWS) or not os.path.exists(FILE_3_CLUSTERED):
    print("CRITICAL ERROR: Input files not found.")
    print(f"Looking for: {FILE_4_FLOWS} AND {FILE_3_CLUSTERED}")
    print("Please run 'Representative_flows_super_paths.py' first.")
    sys.exit(1)

flows_df = pd.read_csv(FILE_4_FLOWS)
full_df = pd.read_csv(FILE_3_CLUSTERED)
initial_trip_count = len(full_df)

# --- 2. Advanced Filtering and Enrichment ---
print("Applying advanced filtering and enrichment...")
vehicular_trips_df = full_df
vehicular_trips_df_filtered = vehicular_trips_df[(vehicular_trips_df['ORIGIN_CLUSTER'] != -1) & (vehicular_trips_df['DESTINATION_CLUSTER'] != -1)].copy()

# --- Enrich with Time and Geographic Strata ---
# NOTE: Column names updated to match AnalisisOD.py output (English names)
origin_hour = pd.to_datetime(vehicular_trips_df_filtered['ORIGIN_TIME'], errors='coerce').dt.hour
vehicular_trips_df_filtered['TIME_BIN'] = origin_hour.apply(get_time_bin)

dominant_time_bins = vehicular_trips_df_filtered.groupby(['ORIGIN_CLUSTER', 'DESTINATION_CLUSTER'])['TIME_BIN'].agg(lambda x: x.mode()[0]).reset_index()
dominant_origin_zones = vehicular_trips_df_filtered.groupby('ORIGIN_CLUSTER')['ORIGIN_COMUNA'].agg(lambda x: x.mode()[0]).reset_index()
dominant_dest_zones = vehicular_trips_df_filtered.groupby('DESTINATION_CLUSTER')['DESTINATION_COMUNA'].agg(lambda x: x.mode()[0]).reset_index()

enriched_flows_df = pd.merge(flows_df, dominant_time_bins.rename(columns={'TIME_BIN': 'DOMINANT_TIME_BIN'}), on=['ORIGIN_CLUSTER', 'DESTINATION_CLUSTER'], how='left')
enriched_flows_df = pd.merge(enriched_flows_df, dominant_origin_zones.rename(columns={'ORIGIN_COMUNA': 'DOMINANT_ORIGIN_ZONE'}), on='ORIGIN_CLUSTER', how='left')
enriched_flows_df = pd.merge(enriched_flows_df, dominant_dest_zones.rename(columns={'DESTINATION_COMUNA': 'DOMINANT_DESTINATION_ZONE'}), on='DESTINATION_CLUSTER', how='left')

# Calculate and bin distances
enriched_flows_df['DISTANCE_KM'] = haversine_distance(
    enriched_flows_df['ORIGIN_CENTROID_LAT'], enriched_flows_df['ORIGIN_CENTROID_LON'],
    enriched_flows_df['DESTINATION_CENTROID_LAT'], enriched_flows_df['DESTINATION_CENTROID_LON']
)
enriched_flows_df['DISTANCE_BIN'] = enriched_flows_df['DISTANCE_KM'].apply(get_distance_bin)

# --- 3. Perform Two-Level Stratified Sampling ---
print("\nCalculating stratum proportions based on total flow weight...")

# Calculate the total flow weight across all relevant strata
total_weight = enriched_flows_df['FLOW_WEIGHT'].sum()

# Calculate the proportion of total weight that each stratum represents
strata_proportions_calculated = enriched_flows_df.groupby(['DOMINANT_TIME_BIN', 'DISTANCE_BIN'])['FLOW_WEIGHT'].sum() / total_weight

print("Calculated Proportions:\n", strata_proportions_calculated)

print("\nPerforming two-level stratified sampling (Time and Distance)...")
final_sample_list = []
for (time_bin, dist_bin), proportion in strata_proportions_calculated.items():
    stratum_df = enriched_flows_df[(enriched_flows_df['DOMINANT_TIME_BIN'] == time_bin) & (enriched_flows_df['DISTANCE_BIN'] == dist_bin)]
    n_samples = round(FINAL_SAMPLE_SIZE * proportion) # Use round() for better allocation

    if len(stratum_df) == 0 or n_samples == 0:
        continue

    sampled_stratum = stratum_df.sample(n=min(n_samples, len(stratum_df)), weights='FLOW_WEIGHT', random_state=42)
    final_sample_list.append(sampled_stratum)
    print(f"Sampled {len(sampled_stratum)} paths from {time_bin} / {dist_bin} bin.")

final_sample_df = pd.concat(final_sample_list)

# --- 4. Save the Final Sample ---
final_sample_df.to_csv(FILE_5_SAMPLE, index=False)

print(f"\n--- Advanced Sampling Complete! ---")
print(f"Created a final, highly representative sample of {len(final_sample_df)} paths.")
print(f"This is your final input for the MILP model. Saved to '{FILE_5_SAMPLE}'")
print("\nFinal Sample Preview:")
print(final_sample_df.head())


# --- 5. VISUALIZE THE STRATIFIED SAMPLE ---
# Traducir nombre de ciudad al español (antes del try para que esté disponible)
ciudad_nombre = {
    'Bogota': 'Bogotá',
    'Medellin': 'Medellín',
    'Valle de aburra': 'Valle de Aburrá'
}
ciudad_es = ciudad_nombre.get(locale_info, locale_info)

print("\nGenerating map of the stratified sample...")
try:
    municipalities_gdf = gpd.read_file(file_path_shapefile)
    
    # Ensure CRS match
    if municipalities_gdf.crs != "EPSG:4326":
        municipalities_gdf = municipalities_gdf.to_crs("EPSG:4326")

    geometry = [LineString([(lon_o, lat_o), (lon_d, lat_d)])
                for lon_o, lat_o, lon_d, lat_d in zip(final_sample_df['ORIGIN_CENTROID_LON'],
                                                      final_sample_df['ORIGIN_CENTROID_LAT'],
                                                      final_sample_df['DESTINATION_CENTROID_LON'],
                                                      final_sample_df['DESTINATION_CENTROID_LAT'])]
    final_sample_gdf = gpd.GeoDataFrame(final_sample_df, geometry=geometry, crs="EPSG:4326")
    
    fig, axes = plt.subplots(3, 3, figsize=(15, 18), sharex=True, sharey=True)
    fig.suptitle(f'Muestra Estratificada de Flujos de Desplazamientos ({ciudad_es})', fontsize=20, y=0.98)
    time_order = ['AM_PEAK', 'MIDDAY', 'PM_PEAK']
    dist_order = ['Short', 'Medium', 'Long']
    
    for i, time_bin in enumerate(time_order):
        for j, dist_bin in enumerate(dist_order):
            ax = axes[i, j]
            municipalities_gdf.plot(ax=ax, color='#EFEFEF', edgecolor='white', linewidth=0.5)
            stratum_gdf = final_sample_gdf[
                (final_sample_gdf['DOMINANT_TIME_BIN'] == time_bin) &
                (final_sample_gdf['DISTANCE_BIN'] == dist_bin)
            ]
            if not stratum_gdf.empty:
                stratum_gdf.plot(ax=ax, color='dodgerblue', linewidth=0.8, alpha=0.7)
            sample_count = len(stratum_gdf)
            # Traducir bins al español
            time_bin_es = {
                'AM_PEAK': 'Hora Pico Mañana',
                'MIDDAY': 'Medio Día',
                'PM_PEAK': 'Hora Pico Tarde',
                'OFF_PEAK': 'Fuera de Pico'
            }
            dist_bin_es = {
                'Short': 'Corta',
                'Medium': 'Media',
                'Long': 'Larga'
            }
            time_es = time_bin_es.get(time_bin, time_bin)
            dist_es = dist_bin_es.get(dist_bin, dist_bin)
            ax.set_title(f"{time_es} / {dist_es}\n({sample_count} rutas)", fontsize=10)
            ax.set_axis_off()
            
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_figure_stratified = os.path.join(RESULTS, f"5_stratified_sample_map_{locale_info}.png")
    plt.savefig(output_figure_stratified, dpi=300, bbox_inches='tight')
    print(f"\nSuccessfully saved map of stratified sample to '{output_figure_stratified}'")
    # plt.show()
    plt.close()

    # --- 6. VISUALIZE ORIGIN & DESTINATION DENSITY BY TIME (NEW SECTION) ---
    print("\nGenerating map of Origin/Destination density by time...")

    # Create a GeoDataFrame for ORIGIN points from the pre-sampled data
    origins_gdf = gpd.GeoDataFrame(
        enriched_flows_df,
        geometry=gpd.points_from_xy(enriched_flows_df.ORIGIN_CENTROID_LON, enriched_flows_df.ORIGIN_CENTROID_LAT),
        crs="EPSG:4326"
    )

    # Create a GeoDataFrame for DESTINATION points
    destinations_gdf = gpd.GeoDataFrame(
        enriched_flows_df,
        geometry=gpd.points_from_xy(enriched_flows_df.DESTINATION_CENTROID_LON, enriched_flows_df.DESTINATION_CENTROID_LAT),
        crs="EPSG:4326"
    )

    # Create a 3x2 grid of plots (3 time bins, 2 for origin/destination)
    fig, axes = plt.subplots(3, 2, figsize=(12, 18), sharex=True, sharey=True)
    fig.suptitle(f'Hotspots de Orígenes y Destinos por Hora ({ciudad_es})', fontsize=20, y=0.98)

    for i, time_bin in enumerate(time_order):
        # --- Left Column: Plot Origins ---
        ax_origin = axes[i, 0]
        municipalities_gdf.plot(ax=ax_origin, color='#EFEFEF', edgecolor='white', linewidth=0.5)
        origins_subset = origins_gdf[origins_gdf['DOMINANT_TIME_BIN'] == time_bin]
        
        if not origins_subset.empty:
            # Scale point size by flow weight to show hotspots
            origins_subset.plot(
                ax=ax_origin, color='crimson', markersize=origins_subset['FLOW_WEIGHT'] / 2,
                alpha=0.6, edgecolor='black', linewidth=0.5
            )
        # Traducir time_bin al español
        time_bin_es = {
            'AM_PEAK': 'Hora Pico Mañana',
            'MIDDAY': 'Medio Día',
            'PM_PEAK': 'Hora Pico Tarde',
            'OFF_PEAK': 'Fuera de Pico'
        }
        time_es = time_bin_es.get(time_bin, time_bin)
        ax_origin.set_title(f"{time_es} - Orígenes", fontsize=12)
        ax_origin.set_axis_off()

        # --- Right Column: Plot Destinations ---
        ax_dest = axes[i, 1]
        municipalities_gdf.plot(ax=ax_dest, color='#EFEFEF', edgecolor='white', linewidth=0.5)
        destinations_subset = destinations_gdf[destinations_gdf['DOMINANT_TIME_BIN'] == time_bin]
        
        if not destinations_subset.empty:
            # Scale point size by flow weight to show hotspots
            destinations_subset.plot(
                ax=ax_dest, color='mediumblue', markersize=destinations_subset['FLOW_WEIGHT'] / 2,
                alpha=0.6, edgecolor='black', linewidth=0.5
            )
        # Usar la misma traducción definida arriba
        ax_dest.set_title(f"{time_es} - Destinos", fontsize=12)
        ax_dest.set_axis_off()

    # Finalize and save the new map
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    output_figure_hotspots = os.path.join(RESULTS, f"5_hotspots_map_{locale_info}.png")
    plt.savefig(output_figure_hotspots, dpi=300, bbox_inches='tight')
    print(f"\nSuccessfully saved Origin/Destination hotspot map to '{output_figure_hotspots}'")
    # plt.show()
    plt.close()

except Exception as e:
    print(f"Warning: Visualization failed. Error: {e}")