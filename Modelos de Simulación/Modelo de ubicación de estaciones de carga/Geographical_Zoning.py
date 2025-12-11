# -*- coding: utf-8 -*-
"""
Created on Mon Jul 21 08:05:39 2025
Updated for Main Pipeline Integration
"""

import pandas as pd
import geopandas as gpd
import os
import sys
import matplotlib.pyplot as plt

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running Geographical_Zoning for: {locale_info}")

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
FILE_1_CLEANED = os.path.join(RESULTS, f"1_cleaned_{locale_info}.csv")

# Output File (Standardized Name for Pipeline)
FILE_2_ZONED = os.path.join(RESULTS, f"2_zoned_{locale_info}.csv")

# Ensure Results folder exists
if not os.path.exists(RESULTS):
    os.makedirs(RESULTS)
#----------------------------------------------------------------------------------------

# --- 1. Load Your Data ---
print("Loading data...")

# Check if input file exists
if not os.path.exists(FILE_1_CLEANED):
    print(f"CRITICAL ERROR: Input file '{FILE_1_CLEANED}' not found.")
    print("Please run 'AnalisisOD.py' first.")
    sys.exit(1)

# Load the municipality shapefile
try:
    municipalities_gdf = gpd.read_file(file_path_shapefile)
    print(f"Shapefile loaded: {shapefile_name}")
    print("Shapefile columns are:", municipalities_gdf.columns)
except Exception as e:
    print(f"Error loading shapefile: {e}")
    sys.exit(1)

# Load your commute data (Output from Step 1)
# Note: Removed encoding='latin-1' as Step 1 saves in default UTF-8
commute_df = pd.read_csv(FILE_1_CLEANED)

# Drop any rows that might have missing coordinates from the previous step
commute_df.dropna(subset=['o_lat', 'o_long', 'd_lat', 'd_long'], inplace=True)
total_initial_trips = len(commute_df)

# --- 2. Create GeoDataFrames for Commute Points ---
print("Preparing geographic points...")
# Create a GeoDataFrame for the ORIGIN points
origins_gdf = gpd.GeoDataFrame(
    commute_df,
    geometry=gpd.points_from_xy(commute_df.o_long, commute_df.o_lat),
    crs="EPSG:4326"  # Standard latitude/longitude CRS
)

# Create a GeoDataFrame for the DESTINATION points
destinations_gdf = gpd.GeoDataFrame(
    commute_df,
    geometry=gpd.points_from_xy(commute_df.d_long, commute_df.d_lat),
    crs="EPSG:4326"
)

# --- 3. Identify Valid Trips ---
print("Identifying trips that are fully within the study area...")

# Ensure shapefile is in the same CRS as points (EPSG:4326)
if municipalities_gdf.crs != "EPSG:4326":
    print(f"Reprojecting shapefile from {municipalities_gdf.crs} to EPSG:4326")
    municipalities_gdf = municipalities_gdf.to_crs("EPSG:4326")

# Perform an 'inner' sjoin to find which origins fall within the shapefile.
# The result 'origins_inside' will only contain points that are inside a polygon.
origins_inside = gpd.sjoin(origins_gdf, municipalities_gdf, how="inner", predicate='within')

# Do the same for destinations.
destinations_inside = gpd.sjoin(destinations_gdf, municipalities_gdf, how="inner", predicate='within')

# Now, find the trips that appear in BOTH lists.
# We get the unique index of each successful join and find their intersection.
valid_origin_indices = set(origins_inside.index)
valid_destination_indices = set(destinations_inside.index)

valid_trip_indices = list(valid_origin_indices.intersection(valid_destination_indices))
valid_trip_count = len(valid_trip_indices)
invalid_trip_count = total_initial_trips - valid_trip_count
print(f"Found {len(valid_trip_indices)} trips that start and end within the mapped area.")


# --- 4. Filter The Original Data ---
print("Filtering the original dataframes to keep only valid trips...")
# Use the list of valid indices to filter your main dataframes.
commute_df_filtered = commute_df.loc[valid_trip_indices]
origins_gdf_filtered = origins_gdf.loc[valid_trip_indices]
destinations_gdf_filtered = destinations_gdf.loc[valid_trip_indices]


# --- 4.5. Visualize the CLEAN Data ---
# Traducir nombre de ciudad al español (antes del try para que esté disponible)
ciudad_nombre = {
    'Bogota': 'Bogotá',
    'Medellin': 'Medellín',
    'Valle de aburra': 'Valle de Aburrá'
}
ciudad_es = ciudad_nombre.get(locale_info, locale_info)

print("Creating a map of the filtered commute points...")
try:
    fig, ax = plt.subplots(1, 1, figsize=(15, 15))

    # Plot the base map
    municipalities_gdf.plot(ax=ax, color='lightgray', edgecolor='black', linewidth=0.5)

    # Plot the FILTERED origin points
    origins_gdf_filtered.plot(ax=ax, marker='o', color='blue', markersize=5, alpha=0.7, label='Orígenes')

    # Plot the FILTERED destination points
    destinations_gdf_filtered.plot(ax=ax, marker='x', color='red', markersize=5, alpha=0.7, label='Destinos')
    ax.set_title(f'Orígenes y Destinos de Desplazamientos Filtrados ({ciudad_es})', fontsize=16)
    ax.set_xlabel('Longitud')
    ax.set_ylabel('Latitud')
    ax.legend(['Orígenes', 'Destinos'])
    ax.grid(True)
    
    # Save the plot instead of just showing it, useful for pipeline runs
    plot_path = os.path.join(RESULTS, f"2_zoned_map_{locale_info}.png")
    plt.savefig(plot_path)
    print(f"Map saved to {plot_path}")
    
    # Only show if running interactively (optional)
    # plt.show() 
    plt.close() # Close figure to free memory
    print("Map generation complete.")
except Exception as e:
    print(f"Warning: Could not generate map. Error: {e}")


# --- 5. Save the Final Enriched File ---
commute_df_filtered.to_csv(FILE_2_ZONED, index=False)

print("\n--- Geographic Zoning Complete! ---")
print(f"Found {valid_trip_count} trips that start and end within the mapped area.")
print(f"--> This means {invalid_trip_count} trips were invalid and have been removed.")
print(f"Successfully saved {len(commute_df_filtered)} filtered commute paths to '{FILE_2_ZONED}'")
print("\nHere is a preview of your clean data:")
print(commute_df_filtered.head())