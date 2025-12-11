# -*- coding: utf-8 -*-
"""
Script para procesar información de clusters y estaciones
para Bogotá y Valle de Aburrá directamente.
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import sys
import json
import json5

# Configuración
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS
data_folder = os.path.join(script_dir, 'Archivos de apoyo')

territories = ["Bogota", "Valle de aburra"]

# Importar funciones necesarias de extract_cluster_info.py
def get_color_from_colormap(cluster_id, cluster_index, total_clusters, colormap_name, is_noise=False):
    if is_noise:
        return (128, 128, 128), "#808080"
    if total_clusters > 1:
        normalized = cluster_index / (total_clusters - 1)
    elif total_clusters == 1:
        normalized = 0.5
    else:
        normalized = 0.5
    cmap = plt.get_cmap(colormap_name)
    rgba = cmap(normalized)
    r, g, b = int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    return (r, g, b), hex_color

def get_color_description(colormap_name):
    descriptions = {
        'viridis': "Escala de colores de amarillo-verde a púrpura-azul. Clusters más oscuros (púrpura/azul) representan valores más altos en la escala, clusters más claros (amarillo/verde) representan valores más bajos.",
        'plasma': "Escala de colores de púrpura a rosa a amarillo. Clusters más oscuros (púrpura) representan valores más bajos, clusters más claros (amarillo) representan valores más altos.",
        'gray': "Color gris uniforme. Representa puntos de ruido (noise) que no pertenecen a ningún cluster."
    }
    return descriptions.get(colormap_name, "Colormap estándar de matplotlib.")

def calculate_cluster_info(df, cluster_col, coord_lat_col, coord_lon_col, cluster_type):
    cluster_info_list = []
    unique_clusters = sorted([c for c in df[cluster_col].unique() if c != -1])
    total_clusters = len(unique_clusters)
    colormap_name = 'viridis' if cluster_type == 'origin' else 'plasma'
    
    for idx, cluster_id in enumerate(unique_clusters):
        cluster_data = df[df[cluster_col] == cluster_id]
        centroid_lat = cluster_data[coord_lat_col].mean()
        centroid_lon = cluster_data[coord_lon_col].mean()
        num_trips = len(cluster_data)
        rgb, hex_color = get_color_from_colormap(cluster_id, idx, total_clusters, colormap_name, is_noise=False)
        cluster_info_list.append({
            'cluster_id': cluster_id,
            'centroid_lat': centroid_lat,
            'centroid_lon': centroid_lon,
            'num_trips': num_trips,
            'color_rgb': f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
            'color_hex': hex_color,
            'colormap': colormap_name,
            'cluster_type': cluster_type
        })
    
    noise_data = df[df[cluster_col] == -1]
    if len(noise_data) > 0:
        noise_lat = noise_data[coord_lat_col].mean()
        noise_lon = noise_data[coord_lon_col].mean()
        rgb, hex_color = get_color_from_colormap(-1, 0, total_clusters, colormap_name, is_noise=True)
        cluster_info_list.append({
            'cluster_id': -1,
            'centroid_lat': noise_lat,
            'centroid_lon': noise_lon,
            'num_trips': len(noise_data),
            'color_rgb': f"rgb({rgb[0]}, {rgb[1]}, {rgb[2]})",
            'color_hex': hex_color,
            'colormap': 'gray',
            'cluster_type': cluster_type
        })
    
    return pd.DataFrame(cluster_info_list)

def calculate_coverage_stats(df, origin_cluster_col, dest_cluster_col):
    total_trips = len(df)
    trips_with_origin_cluster = len(df[df[origin_cluster_col] != -1])
    trips_origin_noise = len(df[df[origin_cluster_col] == -1])
    origin_coverage_pct = (trips_with_origin_cluster / total_trips * 100) if total_trips > 0 else 0
    trips_with_dest_cluster = len(df[df[dest_cluster_col] != -1])
    trips_dest_noise = len(df[df[dest_cluster_col] == -1])
    dest_coverage_pct = (trips_with_dest_cluster / total_trips * 100) if total_trips > 0 else 0
    trips_both_clustered = len(df[(df[origin_cluster_col] != -1) & (df[dest_cluster_col] != -1)])
    both_coverage_pct = (trips_both_clustered / total_trips * 100) if total_trips > 0 else 0
    num_origin_clusters = len([c for c in df[origin_cluster_col].unique() if c != -1])
    num_dest_clusters = len([c for c in df[dest_cluster_col].unique() if c != -1])
    
    return {
        'total_trips': total_trips,
        'trips_with_origin_cluster': trips_with_origin_cluster,
        'trips_origin_noise': trips_origin_noise,
        'origin_coverage_percentage': round(origin_coverage_pct, 2),
        'trips_with_dest_cluster': trips_with_dest_cluster,
        'trips_dest_noise': trips_dest_noise,
        'dest_coverage_percentage': round(dest_coverage_pct, 2),
        'trips_both_clustered': trips_both_clustered,
        'both_coverage_percentage': round(both_coverage_pct, 2),
        'num_origin_clusters': num_origin_clusters,
        'num_dest_clusters': num_dest_clusters
    }

if __name__ == "__main__":
    print("="*70)
    print("   PROCESANDO INFORMACIÓN DE CLUSTERS Y ESTACIONES")
    print("="*70)

    for territory in territories:
        print(f"\n{'='*70}")
        print(f"   Procesando: {territory}")
        print(f"{'='*70}\n")
        
        # Procesar clusters
        FILE_3_CLUSTERED = os.path.join(results_folder, f"3_clustered_{territory}.csv")
        if os.path.exists(FILE_3_CLUSTERED):
            print(f"1. Procesando clusters para {territory}...")
            try:
                df = pd.read_csv(FILE_3_CLUSTERED)
                origins_info = calculate_cluster_info(df, 'ORIGIN_CLUSTER', 'o_lat', 'o_long', 'origin')
                destinations_info = calculate_cluster_info(df, 'DESTINATION_CLUSTER', 'd_lat', 'd_long', 'destination')
                coverage_stats = calculate_coverage_stats(df, 'ORIGIN_CLUSTER', 'DESTINATION_CLUSTER')
                
                # Guardar resultados
                origins_info.to_csv(os.path.join(results_folder, f"cluster_origins_info_{territory}.csv"), index=False)
                destinations_info.to_csv(os.path.join(results_folder, f"cluster_destinations_info_{territory}.csv"), index=False)
                
                output_data = {
                    'territory': territory,
                    'coverage_statistics': coverage_stats,
                    'origin_clusters': origins_info.to_dict('records'),
                    'destination_clusters': destinations_info.to_dict('records'),
                    'color_meaning': {
                        'origin_colormap': {'name': 'viridis', 'description': get_color_description('viridis')},
                        'destination_colormap': {'name': 'plasma', 'description': get_color_description('plasma')},
                        'noise_color': {'name': 'gray', 'rgb': 'rgb(128, 128, 128)', 'hex': '#808080', 'description': get_color_description('gray')}
                    }
                }
                
                with open(os.path.join(results_folder, f"cluster_info_{territory}.json"), 'w', encoding='utf-8') as f:
                    json.dump(output_data, f, indent=2, ensure_ascii=False)
                
                print(f"   Clusters procesados: {len(origins_info)} orígenes, {len(destinations_info)} destinos")
                print(f"   Cobertura orígenes: {coverage_stats['origin_coverage_percentage']}%")
                print(f"   Cobertura destinos: {coverage_stats['dest_coverage_percentage']}%")
            except Exception as e:
                print(f"   Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   Archivo de clusters no encontrado: {FILE_3_CLUSTERED}")
        
        # Procesar estaciones
        FILE_OPTIMAL = os.path.join(results_folder, f"optimal_solution_{territory}.csv")
        if os.path.exists(FILE_OPTIMAL):
            print(f"\n2. Procesando estaciones para {territory}...")
            try:
                df_stations = pd.read_csv(FILE_OPTIMAL)
                
                # Cargar configuración de tecnologías
                CONFIG_FILE = os.path.join(data_folder, 'config.jsonc')
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        config = json5.load(f)
                    tech_cfg = config.get('optimization_settings', {}).get('technologies', {})
                else:
                    tech_cfg = {}
                
                # Procesar estaciones (simplificado - solo guardar CSV con información básica)
                stations_data = []
                for _, row in df_stations.iterrows():
                    stations_data.append({
                        'station_id': f"ST_{int(row['Cell_Row'])}_{int(row['Cell_Col'])}",
                        'cell_row': int(row['Cell_Row']),
                        'cell_col': int(row['Cell_Col']),
                        'latitude': row['Latitude'],
                        'longitude': row['Longitude'],
                        'technology': row['Technology']
                    })
                
                stations_df = pd.DataFrame(stations_data)
                stations_df.to_csv(os.path.join(results_folder, f"stations_detailed_{territory}.csv"), index=False)
                
                print(f"   Estaciones procesadas: {len(stations_df)} estaciones")
            except Exception as e:
                print(f"   Error: {e}")
                import traceback
                traceback.print_exc()
        else:
            print(f"   Archivo de estaciones no encontrado: {FILE_OPTIMAL}")

    print("\n" + "="*70)
    print("   PROCESAMIENTO COMPLETA")
    print("="*70)

