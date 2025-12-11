# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 08:52:05 2025
Updated for Main Pipeline Integration

This script creates representative commute flows from clustered data and
generates two visualizations: one for all flows and one for the top-tier flows.
"""
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import LineString, MultiPoint
from matplotlib.colors import LogNorm
import numpy as np
import os
import sys

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running Representative_flows for: {locale_info}")

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

# Output File (Standardized Name for Pipeline)
FILE_4_FLOWS = os.path.join(RESULTS, f"4_flows_{locale_info}.csv")

# Visualization Parameters
PERCENTILE_THRESHOLD = 0.90 # For the top-tier map

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

# --- 1. Load Your Clustered Data ---
print("Loading clustered commute data...")
if not os.path.exists(FILE_3_CLUSTERED):
    print(f"CRITICAL ERROR: Input file '{FILE_3_CLUSTERED}' not found.")
    print("Please run 'DBSCAN_Clustering.py' first.")
    sys.exit(1)

df = pd.read_csv(FILE_3_CLUSTERED)

# --- 2. Filter Out Noise ---
print("Filtering out noise points...")
df_filtered = df[(df['ORIGIN_CLUSTER'] != -1) & (df['DESTINATION_CLUSTER'] != -1)].copy()
print(f"Working with {len(df_filtered)} trips that belong to defined clusters.")

# --- 3. Calculate Representative Points for Each Cluster ---

print("Calculating origin cluster representative points...")
# Create a GeoDataFrame to work with geometries
origin_gdf = gpd.GeoDataFrame(
    df_filtered, geometry=gpd.points_from_xy(df_filtered.o_long, df_filtered.o_lat), crs="EPSG:4326"
)
# Group points by cluster, create a single 'MultiPoint' shape for each cluster, then find its representative point
origin_centroids = origin_gdf.groupby('ORIGIN_CLUSTER')['geometry'].apply(
    lambda pts: MultiPoint(pts.to_list()).representative_point()
).reset_index(name='geometry')
# Extract lat/lon from the point geometry
origin_centroids['ORIGIN_CENTROID_LON'] = origin_centroids.geometry.x
origin_centroids['ORIGIN_CENTROID_LAT'] = origin_centroids.geometry.y
origin_centroids = origin_centroids.drop(columns='geometry')


print("Calculating destination cluster representative points...")
dest_gdf = gpd.GeoDataFrame(
    df_filtered, geometry=gpd.points_from_xy(df_filtered.d_long, df_filtered.d_lat), crs="EPSG:4326"
)
destination_centroids = dest_gdf.groupby('DESTINATION_CLUSTER')['geometry'].apply(
    lambda pts: MultiPoint(pts.to_list()).representative_point()
).reset_index(name='geometry')
destination_centroids['DESTINATION_CENTROID_LON'] = destination_centroids.geometry.x
destination_centroids['DESTINATION_CENTROID_LAT'] = destination_centroids.geometry.y
destination_centroids = destination_centroids.drop(columns='geometry')

# --- 4. Calculate the Weight of Each Flow ---
print("Calculating the weight of each inter-cluster flow...")
flow_weights = df_filtered.groupby(['ORIGIN_CLUSTER', 'DESTINATION_CLUSTER']).size().reset_index(name='FLOW_WEIGHT')

# --- 5. Combine Everything into a Final DataFrame ---
print("Merging data to create final representative flows...")
flows_with_origins = pd.merge(flow_weights, origin_centroids, on='ORIGIN_CLUSTER', how='left')
final_flows_df = pd.merge(flows_with_origins, destination_centroids, on='DESTINATION_CLUSTER', how='left')
final_flows_df = final_flows_df.sort_values(by='FLOW_WEIGHT', ascending=False)

# --- 6. Save the Results ---
final_flows_df.to_csv(FILE_4_FLOWS, index=False)
print(f"\n--- Flow Creation Complete! ---")
print(f"Distilled {len(df)} trips down to {len(final_flows_df)} representative flows.")
print(f"Saved the results to '{FILE_4_FLOWS}'")

# --- 7. VISUALIZE ALL REPRESENTATIVE FLOWS ---
# Traducir nombre de ciudad al español (antes del try para que esté disponible)
ciudad_nombre = {
    'Bogota': 'Bogotá',
    'Medellin': 'Medellín',
    'Valle de aburra': 'Valle de Aburrá'
}
ciudad_es = ciudad_nombre.get(locale_info, locale_info)

print("\nGenerating map of ALL flows...")
try:
    municipalities_gdf = gpd.read_file(file_path_shapefile)
    
    # Ensure CRS match
    if municipalities_gdf.crs != "EPSG:4326":
        municipalities_gdf = municipalities_gdf.to_crs("EPSG:4326")

    flows_df = pd.read_csv(FILE_4_FLOWS)
    geometry = [LineString([(lon_o, lat_o), (lon_d, lat_d)])
                for lon_o, lat_o, lon_d, lat_d in zip(flows_df['ORIGIN_CENTROID_LON'],
                                                      flows_df['ORIGIN_CENTROID_LAT'],
                                                      flows_df['DESTINATION_CENTROID_LON'],
                                                      flows_df['DESTINATION_CENTROID_LAT'])]
    flows_gdf = gpd.GeoDataFrame(flows_df, geometry=geometry, crs="EPSG:4326")
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    municipalities_gdf.plot(ax=ax, color='white', edgecolor='black', linewidth=0.7, alpha=0.5)
    flows_gdf.plot(
        ax=ax,
        column='FLOW_WEIGHT',
        norm=LogNorm(vmin=flows_gdf['FLOW_WEIGHT'].min(), vmax=flows_gdf['FLOW_WEIGHT'].max()),
        linewidth=np.log1p(flows_gdf['FLOW_WEIGHT']) / np.log1p(flows_df['FLOW_WEIGHT'].max()) * 8,
        legend=True,
        legend_kwds={'label': "Número de Viajes en el Flujo (Escala Logarítmica)", 'orientation': "horizontal"},
        cmap='viridis',
        alpha=0.6
    )
    ax.set_title(f'Flujos Representativos de Desplazamientos ({ciudad_es}) - Escala Logarítmica', fontsize=16)
    ax.set_axis_off()
    
    fig_file_name = f"4_flows_map_all_{locale_info}.png"
    fig_path = os.path.join(RESULTS, fig_file_name)
    plt.savefig(fig_path, dpi=300)
    print(f"\nFinal map of all flows saved to '{fig_file_name}'")
    # plt.show() # Commented out for smoother pipeline execution
    plt.close()

    # -------------------------------------------------------------------------- #
    # --- 8. VISUALIZE ONLY THE TOP-TIER FLOWS (NEW SECTION) ---
    # -------------------------------------------------------------------------- #
    print("\nGenerating map of TOP-TIER flows...")

    # Filter for the top flows using the percentile threshold
    flow_threshold = flows_df['FLOW_WEIGHT'].quantile(PERCENTILE_THRESHOLD)
    top_flows_gdf = flows_gdf[flows_gdf['FLOW_WEIGHT'] >= flow_threshold].copy()
    print(f"Visualizing the top {len(top_flows_gdf)} super-paths...")

    # Prepare and create the plot for the top flows
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    municipalities_gdf.plot(ax=ax, color='white', edgecolor='black', linewidth=0.7, alpha=0.5)

    # Plot only the top-tier flows
    top_flows_gdf.plot(
        ax=ax,
        column='FLOW_WEIGHT',
        linewidth=top_flows_gdf['FLOW_WEIGHT'] / top_flows_gdf['FLOW_WEIGHT'].max() * 12, # Make lines a bit thicker
        legend=True,
        legend_kwds={'label': "Número de Viajes en el Flujo", 'orientation': "horizontal"},
        cmap='viridis',
        alpha=0.9
    )
    ax.set_title(f'Top {100 - (PERCENTILE_THRESHOLD * 100):.0f}% de Flujos de Desplazamientos ({ciudad_es})', fontsize=16)
    ax.set_axis_off()
    
    fig_file_name_top = f"4_flows_map_top_{locale_info}.png"
    fig_path_top = os.path.join(RESULTS, fig_file_name_top)
    plt.savefig(fig_path_top, dpi=300)
    print(f"Map of top-tier flows saved to '{fig_file_name_top}'")
    # plt.show()
    plt.close()

except Exception as e:
    print(f"Warning: Visualization failed. Error: {e}")