# -*- coding: utf-8 -*-
"""
Script para extraer información de clusters:
- Coordenadas de los clusters (centroides)
- Colores asignados y su significado
- Proporción de cobertura respecto a viajes y clusters
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import os
import sys
import json

# --- CONFIGURACIÓN ---
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS

# Archivos de entrada
FILE_3_CLUSTERED = os.path.join(results_folder, f"3_clustered_{locale_info}.csv")

# Archivos de salida
OUTPUT_JSON = os.path.join(results_folder, f"cluster_info_{locale_info}.json")
OUTPUT_CSV_ORIGINS = os.path.join(results_folder, f"cluster_origins_info_{locale_info}.csv")
OUTPUT_CSV_DESTINATIONS = os.path.join(results_folder, f"cluster_destinations_info_{locale_info}.csv")
OUTPUT_REPORT = os.path.join(results_folder, f"cluster_report_{locale_info}.txt")

def get_color_from_colormap(cluster_id, cluster_index, total_clusters, colormap_name, is_noise=False):
    """
    Obtiene el color RGB de un cluster basado en el colormap usado.
    
    Args:
        cluster_id: ID del cluster (o -1 para ruido)
        cluster_index: Índice del cluster en la lista ordenada (0-based)
        total_clusters: Número total de clusters (sin contar ruido)
        colormap_name: Nombre del colormap ('viridis' o 'plasma')
        is_noise: Si es True, retorna gris
    
    Returns:
        Tupla (R, G, B) en valores 0-255 y código hexadecimal
    """
    if is_noise:
        return (128, 128, 128), "#808080"  # Gris para ruido
    
    # Normalizar el índice del cluster al rango [0, 1] para el colormap
    # Usamos el índice (posición en lista ordenada) en lugar del ID para distribución uniforme
    if total_clusters > 1:
        normalized = cluster_index / (total_clusters - 1)
    elif total_clusters == 1:
        normalized = 0.5
    else:
        normalized = 0.5
    
    # Obtener colormap
    cmap = plt.get_cmap(colormap_name)
    rgba = cmap(normalized)
    
    # Convertir a RGB 0-255
    r, g, b = int(rgba[0] * 255), int(rgba[1] * 255), int(rgba[2] * 255)
    hex_color = f"#{r:02x}{g:02x}{b:02x}"
    
    return (r, g, b), hex_color

def get_color_description(colormap_name):
    """Retorna descripción del significado del colormap."""
    descriptions = {
        'viridis': "Escala de colores de amarillo-verde a púrpura-azul. Clusters más oscuros (púrpura/azul) representan valores más altos en la escala, clusters más claros (amarillo/verde) representan valores más bajos.",
        'plasma': "Escala de colores de púrpura a rosa a amarillo. Clusters más oscuros (púrpura) representan valores más bajos, clusters más claros (amarillo) representan valores más altos.",
        'gray': "Color gris uniforme. Representa puntos de ruido (noise) que no pertenecen a ningún cluster."
    }
    return descriptions.get(colormap_name, "Colormap estándar de matplotlib.")

def calculate_cluster_info(df, cluster_col, coord_lat_col, coord_lon_col, cluster_type):
    """
    Calcula información de clusters: centroides, colores, estadísticas.
    
    Args:
        df: DataFrame con datos de viajes
        cluster_col: Nombre de la columna con IDs de cluster
        coord_lat_col: Nombre de la columna con latitud
        coord_lon_col: Nombre de la columna con longitud
        cluster_type: 'origin' o 'destination'
    
    Returns:
        DataFrame con información de clusters
    """
    cluster_info_list = []
    
    # Obtener todos los clusters únicos (excluyendo ruido temporalmente)
    unique_clusters = sorted([c for c in df[cluster_col].unique() if c != -1])
    total_clusters = len(unique_clusters)
    
    # Colormap según tipo
    colormap_name = 'viridis' if cluster_type == 'origin' else 'plasma'
    
    # Procesar cada cluster
    for idx, cluster_id in enumerate(unique_clusters):
        cluster_data = df[df[cluster_col] == cluster_id]
        
        # Calcular centroide
        centroid_lat = cluster_data[coord_lat_col].mean()
        centroid_lon = cluster_data[coord_lon_col].mean()
        
        # Estadísticas
        num_trips = len(cluster_data)
        
        # Obtener color (usar índice para distribución uniforme en colormap)
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
    
    # Procesar ruido (cluster_id = -1)
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
    """
    Calcula estadísticas de cobertura.
    
    Returns:
        Diccionario con estadísticas
    """
    total_trips = len(df)
    
    # Orígenes
    trips_with_origin_cluster = len(df[df[origin_cluster_col] != -1])
    trips_origin_noise = len(df[df[origin_cluster_col] == -1])
    origin_coverage_pct = (trips_with_origin_cluster / total_trips * 100) if total_trips > 0 else 0
    
    # Destinos
    trips_with_dest_cluster = len(df[df[dest_cluster_col] != -1])
    trips_dest_noise = len(df[df[dest_cluster_col] == -1])
    dest_coverage_pct = (trips_with_dest_cluster / total_trips * 100) if total_trips > 0 else 0
    
    # Ambos
    trips_both_clustered = len(df[(df[origin_cluster_col] != -1) & (df[dest_cluster_col] != -1)])
    both_coverage_pct = (trips_both_clustered / total_trips * 100) if total_trips > 0 else 0
    
    # Número de clusters
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

def main():
    # Permitir pasar el territorio como argumento de línea de comandos
    global locale_info
    if len(sys.argv) > 1:
        locale_info = sys.argv[1]
        os.environ['ANALYSIS_LOCALE'] = locale_info
    
    print(f"\n{'='*70}")
    print(f"   EXTRACCIÓN DE INFORMACIÓN DE CLUSTERS")
    print(f"   Territorio: {locale_info}")
    print(f"{'='*70}\n")
    
    # Verificar que existe el archivo
    if not os.path.exists(FILE_3_CLUSTERED):
        print(f"ERROR: Archivo '{FILE_3_CLUSTERED}' no encontrado.")
        print("   Por favor ejecuta primero 'DBSCAN_Clustering.py' o el pipeline completo.")
        sys.exit(1)
    
    # Cargar datos
    print("Cargando datos de clusters...")
    df = pd.read_csv(FILE_3_CLUSTERED)
    print(f" Cargados {len(df)} viajes")
    
    # Verificar columnas necesarias
    required_cols = ['ORIGIN_CLUSTER', 'DESTINATION_CLUSTER', 'o_lat', 'o_long', 'd_lat', 'd_long']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Faltan columnas: {missing_cols}")
        sys.exit(1)
    
    # Calcular información de clusters de orígenes
    print("\nCalculando información de clusters de ORÍGENES...")
    origins_info = calculate_cluster_info(df, 'ORIGIN_CLUSTER', 'o_lat', 'o_long', 'origin')
    print(f" {len(origins_info)} clusters de orígenes identificados")
    
    # Calcular información de clusters de destinos
    print("Calculando información de clusters de DESTINOS...")
    destinations_info = calculate_cluster_info(df, 'DESTINATION_CLUSTER', 'd_lat', 'd_long', 'destination')
    print(f" {len(destinations_info)} clusters de destinos identificados")
    
    # Calcular estadísticas de cobertura
    print("Calculando estadísticas de cobertura...")
    coverage_stats = calculate_coverage_stats(df, 'ORIGIN_CLUSTER', 'DESTINATION_CLUSTER')
    
    # Guardar CSVs
    print("\nGuardando archivos CSV...")
    origins_info.to_csv(OUTPUT_CSV_ORIGINS, index=False)
    print(f"  {OUTPUT_CSV_ORIGINS}")
    destinations_info.to_csv(OUTPUT_CSV_DESTINATIONS, index=False)
    print(f" {OUTPUT_CSV_DESTINATIONS}")
    
    # Preparar datos para JSON
    output_data = {
        'territory': locale_info,
        'coverage_statistics': coverage_stats,
        'origin_clusters': origins_info.to_dict('records'),
        'destination_clusters': destinations_info.to_dict('records'),
        'color_meaning': {
            'origin_colormap': {
                'name': 'viridis',
                'description': get_color_description('viridis')
            },
            'destination_colormap': {
                'name': 'plasma',
                'description': get_color_description('plasma')
            },
            'noise_color': {
                'name': 'gray',
                'rgb': 'rgb(128, 128, 128)',
                'hex': '#808080',
                'description': get_color_description('gray')
            }
        }
    }
    
    # Guardar JSON
    print("Guardando archivo JSON...")
    with open(OUTPUT_JSON, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)
    print(f" {OUTPUT_JSON}")
    
    # Generar reporte en texto
    print("Generando reporte en texto...")
    with open(OUTPUT_REPORT, 'w', encoding='utf-8') as f:
        f.write("="*70 + "\n")
        f.write(f"   REPORTE DE CLUSTERS - {locale_info.upper()}\n")
        f.write("="*70 + "\n\n")
        
        # Estadísticas de cobertura
        f.write("ESTADÍSTICAS DE COBERTURA\n")
        f.write("-"*70 + "\n")
        f.write(f"Total de viajes: {coverage_stats['total_trips']:,}\n\n")
        
        f.write("ORÍGENES:\n")
        f.write(f"  - Viajes con cluster: {coverage_stats['trips_with_origin_cluster']:,} ")
        f.write(f"({coverage_stats['origin_coverage_percentage']}%)\n")
        f.write(f"  - Viajes sin cluster (ruido): {coverage_stats['trips_origin_noise']:,} ")
        f.write(f"({100 - coverage_stats['origin_coverage_percentage']:.2f}%)\n")
        f.write(f"  - Número de clusters: {coverage_stats['num_origin_clusters']}\n\n")
        
        f.write("DESTINOS:\n")
        f.write(f"  - Viajes con cluster: {coverage_stats['trips_with_dest_cluster']:,} ")
        f.write(f"({coverage_stats['dest_coverage_percentage']}%)\n")
        f.write(f"  - Viajes sin cluster (ruido): {coverage_stats['trips_dest_noise']:,} ")
        f.write(f"({100 - coverage_stats['dest_coverage_percentage']:.2f}%)\n")
        f.write(f"  - Número de clusters: {coverage_stats['num_dest_clusters']}\n\n")
        
        f.write("AMBOS (ORIGEN Y DESTINO):\n")
        f.write(f"  - Viajes con ambos clusters: {coverage_stats['trips_both_clustered']:,} ")
        f.write(f"({coverage_stats['both_coverage_percentage']}%)\n\n")
        
        # Significado de colores
        f.write("="*70 + "\n")
        f.write("SIGNIFICADO DE COLORES\n")
        f.write("-"*70 + "\n\n")
        f.write("CLUSTERS DE ORÍGENES (Colormap: VIRIDIS):\n")
        f.write(f"  {output_data['color_meaning']['origin_colormap']['description']}\n\n")
        f.write("CLUSTERS DE DESTINOS (Colormap: PLASMA):\n")
        f.write(f"  {output_data['color_meaning']['destination_colormap']['description']}\n\n")
        f.write("PUNTOS DE RUIDO (NOISE):\n")
        f.write(f"  {output_data['color_meaning']['noise_color']['description']}\n")
        f.write(f"  Color: {output_data['color_meaning']['noise_color']['rgb']} ")
        f.write(f"({output_data['color_meaning']['noise_color']['hex']})\n\n")
        
        # Clusters de orígenes
        f.write("="*70 + "\n")
        f.write("CLUSTERS DE ORÍGENES\n")
        f.write("-"*70 + "\n")
        f.write(f"{'ID':<8} {'Latitud':<12} {'Longitud':<12} {'Viajes':<10} {'Color HEX':<10}\n")
        f.write("-"*70 + "\n")
        for _, row in origins_info.iterrows():
            cluster_id = "Ruido" if row['cluster_id'] == -1 else str(int(row['cluster_id']))
            f.write(f"{cluster_id:<8} {row['centroid_lat']:<12.6f} {row['centroid_lon']:<12.6f} ")
            f.write(f"{int(row['num_trips']):<10} {row['color_hex']:<10}\n")
        
        # Clusters de destinos
        f.write("\n" + "="*70 + "\n")
        f.write("CLUSTERS DE DESTINOS\n")
        f.write("-"*70 + "\n")
        f.write(f"{'ID':<8} {'Latitud':<12} {'Longitud':<12} {'Viajes':<10} {'Color HEX':<10}\n")
        f.write("-"*70 + "\n")
        for _, row in destinations_info.iterrows():
            cluster_id = "Ruido" if row['cluster_id'] == -1 else str(int(row['cluster_id']))
            f.write(f"{cluster_id:<8} {row['centroid_lat']:<12.6f} {row['centroid_lon']:<12.6f} ")
            f.write(f"{int(row['num_trips']):<10} {row['color_hex']:<10}\n")
    
    print(f"{OUTPUT_REPORT}")
    
    # Mostrar resumen en consola
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    print(f"\nTotal de viajes: {coverage_stats['total_trips']:,}")
    print(f"\nORÍGENES:")
    print(f"  - Cobertura: {coverage_stats['origin_coverage_percentage']}% "
          f"({coverage_stats['trips_with_origin_cluster']:,} viajes)")
    print(f"  - Clusters identificados: {coverage_stats['num_origin_clusters']}")
    print(f"\nDESTINOS:")
    print(f"  - Cobertura: {coverage_stats['dest_coverage_percentage']}% "
          f"({coverage_stats['trips_with_dest_cluster']:,} viajes)")
    print(f"  - Clusters identificados: {coverage_stats['num_dest_clusters']}")
    print(f"\nAMBOS:")
    print(f"  - Cobertura completa: {coverage_stats['both_coverage_percentage']}% "
          f"({coverage_stats['trips_both_clustered']:,} viajes)")
    
    print(f"\n{'='*70}")
    print(" EXTRACCIÓN COMPLETA")
    print(f"{'='*70}")
    print(f"\nArchivos generados:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_CSV_ORIGINS}")
    print(f"  - {OUTPUT_CSV_DESTINATIONS}")
    print(f"  - {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()

