# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 08:05:39 2025
Updated for Main Pipeline Integration (Config-Driven Parameters)
"""

import pandas as pd
import geopandas as gpd
from sklearn.cluster import DBSCAN
from sklearn.neighbors import NearestNeighbors
import numpy as np
import matplotlib.pyplot as plt
import os
import sys
import json5 # Required to read the config

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running DBSCAN_Clustering for: {locale_info}")

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
results_folder = RESULTS

# Input Files
CONFIG_FILE = os.path.join(data_folder, 'config.jsonc')
file_path_shapefile = os.path.join(shapefile_folder, shapefile_name)
FILE_2_ZONED = os.path.join(results_folder, f"2_zoned_{locale_info}.csv")

# Output Files
FILE_3_CLUSTERED = os.path.join(results_folder, f"3_clustered_{locale_info}.csv")
OD_MATRIX_FILE = os.path.join(results_folder, f"od_matrix_{locale_info}.csv")

# Ensure Results folder exists
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

# --- LOAD CONFIGURATION ---
print(f"Loading clustering parameters from: {CONFIG_FILE}")
if not os.path.exists(CONFIG_FILE):
    print("CRITICAL ERROR: config.jsonc not found.")
    sys.exit(1)

with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
    full_config = json5.load(f)

# Extract clustering settings with defaults if missing
cluster_cfg = full_config.get('clustering_settings', {})

# Map config structure to script logic
DBSCAN_PARAMS = {
    "Stage 1 Origins":      cluster_cfg.get('origins', {}).get('stage_1', {"eps": 400, "min_samples": 15}),
    "Stage 2 Origins":      cluster_cfg.get('origins', {}).get('stage_2', {"eps": 150, "min_samples": 10}),
    "Stage 1 Destinations": cluster_cfg.get('destinations', {}).get('stage_1', {"eps": 400, "min_samples": 15}),
    "Stage 2 Destinations": cluster_cfg.get('destinations', {}).get('stage_2', {"eps": 150, "min_samples": 10})
}

print("   [INFO] Parameters loaded:")
for k, v in DBSCAN_PARAMS.items():
    print(f"     - {k}: eps={v['eps']}, min_samples={v['min_samples']}")

#----------------------------------------------------------------------------------------

def run_dbscan_automated(coords_data, context_name):
    """
    Runs DBSCAN using parameters loaded from config.jsonc.
    """
    params = DBSCAN_PARAMS.get(context_name, {"eps": 300, "min_samples": 10})
    eps = params['eps']
    min_samples = params['min_samples']
    
    print(f"   -> Running DBSCAN for {context_name} with eps={eps}m, min_samples={min_samples}...")
    
    # Generate K-Distance graph for reference (saved, not shown)
    try:
        neighbors = NearestNeighbors(n_neighbors=min_samples)
        neighbors_fit = neighbors.fit(coords_data)
        distances, _ = neighbors_fit.kneighbors(coords_data)
        sorted_distances = np.sort(distances[:, min_samples-1])
        
        plt.figure(figsize=(10, 6))
        plt.plot(sorted_distances)
        # Traducir nombres de contexto al español
        context_spanish = {
            "Stage 1 Origins": "Etapa 1 Orígenes",
            "Stage 2 Origins": "Etapa 2 Orígenes",
            "Stage 1 Destinations": "Etapa 1 Destinos",
            "Stage 2 Destinations": "Etapa 2 Destinos"
        }
        context_name_es = context_spanish.get(context_name, context_name)
        plt.title(f"Gráfico K-Distancia: {context_name_es} (eps={eps}m)", fontsize=12)
        plt.ylabel("Distancia (m)")
        plt.xlabel("Puntos ordenados")
        plt.grid(True)
        
        # Save plot instead of blocking execution
        safe_name = context_name.replace(" ", "_").replace("(", "").replace(")", "")
        plot_path = os.path.join(results_folder, f"debug_kdist_{safe_name}_{locale_info}.png")
        plt.savefig(plot_path)
        plt.close()
    except Exception as e:
        print(f"   [WARN] Could not generate debug plot: {e}")

    return eps, min_samples

# --- 1. Load Data ---
print("Loading zoned and filtered commute data...")
if not os.path.exists(FILE_2_ZONED):
    print(f"CRITICAL ERROR: Input file '{FILE_2_ZONED}' not found.")
    print("Please run 'Geographical_Zoning.py' first.")
    sys.exit(1)

commute_df = pd.read_csv(FILE_2_ZONED)
commute_df.dropna(subset=['o_lat', 'o_long', 'd_lat', 'd_long'], inplace=True)
print(f"Loaded {len(commute_df)} commute paths.")

# --- 2. Prepare and Transform Coordinates ---
print("Preparing and projecting coordinates to a meter-based system...")
# Project Origin coordinates
gdf_origins = gpd.GeoDataFrame(
    commute_df, geometry=gpd.points_from_xy(commute_df.o_long, commute_df.o_lat), crs="EPSG:4326"
)
# EPSG:32618 is UTM Zone 18N (Suitable for Colombia)
gdf_origins_proj = gdf_origins.to_crs(epsg=32618)
origin_coords_proj = np.array(list(zip(gdf_origins_proj.geometry.x, gdf_origins_proj.geometry.y)))

# Project Destination coordinates
gdf_dests = gpd.GeoDataFrame(
    commute_df, geometry=gpd.points_from_xy(commute_df.d_long, commute_df.d_lat), crs="EPSG:4326"
)
gdf_dests_proj = gdf_dests.to_crs(epsg=32618)
destination_coords_proj = np.array(list(zip(gdf_dests_proj.geometry.x, gdf_dests_proj.geometry.y)))

# =====================================================================================
# --- HIERARCHICAL CLUSTERING FOR ORIGINS ---
# =====================================================================================

# --- 3. Stage 1: Initial DBSCAN for Origins ---
print("\n--- ORIGINS: STAGE 1 ---")
eps_1_o, min_samples_1_o = run_dbscan_automated(origin_coords_proj, "Stage 1 Origins")
dbscan_origin_1 = DBSCAN(eps=eps_1_o, min_samples=min_samples_1_o)
origin_clusters_1 = dbscan_origin_1.fit_predict(origin_coords_proj)
commute_df['ORIGIN_CLUSTER_TMP'] = origin_clusters_1

if len(commute_df[commute_df['ORIGIN_CLUSTER_TMP'] != -1]) > 0:
    super_cluster_id_o = commute_df[commute_df['ORIGIN_CLUSTER_TMP'] != -1]['ORIGIN_CLUSTER_TMP'].value_counts().idxmax()
    print(f"Identified Origin super cluster with ID: {super_cluster_id_o}")

    # --- 4. Isolate Origin Super Cluster ---
    super_cluster_df_o = commute_df[commute_df['ORIGIN_CLUSTER_TMP'] == super_cluster_id_o].copy()

    # --- 5. Stage 2: Re-Cluster Origin Super Cluster ---
    print("\n--- ORIGINS: STAGE 2 ---")
    sc_coords_proj_o = origin_coords_proj[commute_df['ORIGIN_CLUSTER_TMP'] == super_cluster_id_o]

    eps_2_o, min_samples_2_o = run_dbscan_automated(sc_coords_proj_o, "Stage 2 Origins")

    dbscan_origin_2 = DBSCAN(eps=eps_2_o, min_samples=min_samples_2_o)
    origin_clusters_2 = dbscan_origin_2.fit_predict(sc_coords_proj_o)
    super_cluster_df_o['SUB_CLUSTER'] = origin_clusters_2

    # --- 6. Combine Origin Cluster Labels ---
    super_cluster_df_o['SUB_CLUSTER_FINAL'] = super_cluster_df_o['SUB_CLUSTER'].apply(
        lambda x: super_cluster_id_o if x == -1 else x + 100
    )
    commute_df = commute_df.merge(
        super_cluster_df_o[['SUB_CLUSTER_FINAL']], left_index=True, right_index=True, how='left'
    )
    commute_df['ORIGIN_CLUSTER'] = commute_df['SUB_CLUSTER_FINAL'].fillna(commute_df['ORIGIN_CLUSTER_TMP']).astype(int)
    commute_df.drop(columns=['ORIGIN_CLUSTER_TMP', 'SUB_CLUSTER_FINAL'], inplace=True)
else:
    commute_df['ORIGIN_CLUSTER'] = commute_df['ORIGIN_CLUSTER_TMP']
    commute_df.drop(columns=['ORIGIN_CLUSTER_TMP'], inplace=True)

print("Final Origin cluster labels created.")


# =====================================================================================
# --- HIERARCHICAL CLUSTERING FOR DESTINATIONS ---
# =====================================================================================

# --- 7. Stage 1: Initial DBSCAN for Destinations ---
print("\n--- DESTINATIONS: STAGE 1 ---")
eps_1_d, min_samples_1_d = run_dbscan_automated(destination_coords_proj, "Stage 1 Destinations")
dbscan_dest_1 = DBSCAN(eps=eps_1_d, min_samples=min_samples_1_d)
dest_clusters_1 = dbscan_dest_1.fit_predict(destination_coords_proj)
commute_df['DEST_CLUSTER_TMP'] = dest_clusters_1

if len(commute_df[commute_df['DEST_CLUSTER_TMP'] != -1]) > 0:
    super_cluster_id_d = commute_df[commute_df['DEST_CLUSTER_TMP'] != -1]['DEST_CLUSTER_TMP'].value_counts().idxmax()
    print(f"Identified Destination super cluster with ID: {super_cluster_id_d}")

    # --- 8. Isolate Destination Super Cluster ---
    super_cluster_df_d = commute_df[commute_df['DEST_CLUSTER_TMP'] == super_cluster_id_d].copy()
    
    # --- 9. Stage 2: Re-Cluster Destination Super Cluster ---
    print("\n--- DESTINATIONS: STAGE 2 ---")
    sc_coords_proj_d = destination_coords_proj[commute_df['DEST_CLUSTER_TMP'] == super_cluster_id_d]

    eps_2_d, min_samples_2_d = run_dbscan_automated(sc_coords_proj_d, "Stage 2 Destinations")

    dbscan_dest_2 = DBSCAN(eps=eps_2_d, min_samples=min_samples_2_d)
    dest_clusters_2 = dbscan_dest_2.fit_predict(sc_coords_proj_d)
    super_cluster_df_d['SUB_CLUSTER'] = dest_clusters_2

    # --- 10. Combine Destination Cluster Labels ---
    super_cluster_df_d['SUB_CLUSTER_FINAL'] = super_cluster_df_d['SUB_CLUSTER'].apply(
        lambda x: super_cluster_id_d if x == -1 else x + 200 # Using 200 to avoid collision with origin sub-clusters
    )
    commute_df = commute_df.merge(
        super_cluster_df_d[['SUB_CLUSTER_FINAL']], left_index=True, right_index=True, how='left'
    )
    commute_df['DESTINATION_CLUSTER'] = commute_df['SUB_CLUSTER_FINAL'].fillna(commute_df['DEST_CLUSTER_TMP']).astype(int)
    commute_df.drop(columns=['DEST_CLUSTER_TMP', 'SUB_CLUSTER_FINAL'], inplace=True)
else:
    commute_df['DESTINATION_CLUSTER'] = commute_df['DEST_CLUSTER_TMP']
    commute_df.drop(columns=['DEST_CLUSTER_TMP'], inplace=True)
    
print("Final Destination cluster labels created.")

# --- 11. Visualize and Save ---
# Traducir nombre de ciudad al español (antes del try para que esté disponible)
ciudad_nombre = {
    'Bogota': 'Bogotá',
    'Medellin': 'Medellín',
    'Valle de aburra': 'Valle de Aburrá'
}
ciudad_es = ciudad_nombre.get(locale_info, locale_info)

try:
    municipalities_gdf = gpd.read_file(file_path_shapefile)

    # Plot Origin Clusters
    results_gdf_o = gpd.GeoDataFrame(
        commute_df, geometry=gpd.points_from_xy(commute_df.o_long, commute_df.o_lat), crs="EPSG:4326"
    ).to_crs(municipalities_gdf.crs)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    municipalities_gdf.plot(ax=ax, color='white', edgecolor='black', linewidth=0.9)
    results_gdf_o[results_gdf_o['ORIGIN_CLUSTER'] != -1].plot(ax=ax, column='ORIGIN_CLUSTER', categorical=True, markersize=30, cmap='viridis')
    results_gdf_o[results_gdf_o['ORIGIN_CLUSTER'] == -1].plot(ax=ax, color='gray', markersize=15, alpha=0.5)
    ax.set_title(f'Clusters Jerárquicos Finales de Orígenes ({ciudad_es})', fontsize=16)
    ax.set_axis_off()
    
    # Save plot
    plot_path_o = os.path.join(results_folder, f"3_clusters_origins_{locale_info}.png")
    plt.savefig(plot_path_o)
    print(f"Origin cluster map saved to {plot_path_o}")
    plt.close() # Close to prevent blocking

    # Plot Destination Clusters
    results_gdf_d = gpd.GeoDataFrame(
        commute_df, geometry=gpd.points_from_xy(commute_df.d_long, commute_df.d_lat), crs="EPSG:4326"
    ).to_crs(municipalities_gdf.crs)
    
    fig, ax = plt.subplots(1, 1, figsize=(12, 16))
    municipalities_gdf.plot(ax=ax, color='white', edgecolor='black', linewidth=0.9)
    results_gdf_d[results_gdf_d['DESTINATION_CLUSTER'] != -1].plot(ax=ax, column='DESTINATION_CLUSTER', categorical=True, markersize=30, cmap='plasma')
    results_gdf_d[results_gdf_d['DESTINATION_CLUSTER'] == -1].plot(ax=ax, color='gray', markersize=15, alpha=0.5)
    # Usar la misma traducción de ciudad
    ax.set_title(f'Clusters Jerárquicos Finales de Destinos ({ciudad_es})', fontsize=16)
    ax.set_axis_off()
    
    # Save plot
    plot_path_d = os.path.join(results_folder, f"3_clusters_destinations_{locale_info}.png")
    plt.savefig(plot_path_d)
    print(f"Destination cluster map saved to {plot_path_d}")
    plt.close()

except Exception as e:
    print(f"Warning: Visualization failed. Error: {e}")


# --- 12. Save the Final Clustered Data ---
commute_df.to_csv(FILE_3_CLUSTERED, index=False)
print(f"\nSuccessfully saved data with final cluster IDs to '{FILE_3_CLUSTERED}'")

# --- 13. Create and Save the Origin-Destination (O-D) Matrix ---
print("\nCreating the Origin-Destination (O-D) Matrix...")

# Group by the origin and destination clusters and count the number of trips in each group
od_matrix = commute_df.groupby(['ORIGIN_CLUSTER', 'DESTINATION_CLUSTER']).size()

# Convert the grouped Series into a 2D matrix format, filling non-existent pairs with 0
od_matrix = od_matrix.unstack(fill_value=0)

# Save the matrix to a CSV file
od_matrix.to_csv(OD_MATRIX_FILE)

print(f"Successfully saved the O-D Matrix to '{OD_MATRIX_FILE}'")
print("\nHere is a preview of your O-D Matrix:")
print(od_matrix.head())

print("\n--- Data processing pipeline complete! ---")