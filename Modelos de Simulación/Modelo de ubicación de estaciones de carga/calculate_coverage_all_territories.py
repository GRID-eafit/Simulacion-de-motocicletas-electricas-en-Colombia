# -*- coding: utf-8 -*-
"""
Script para calcular y mostrar las proporciones de cobertura
para los 3 casos de estudio.
"""

import pandas as pd
import os
import json

script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS

territories = {
    "Bogota": "Bogotá",
    "Medellin": "Medellín",
    "Valle de aburra": "Valle de Aburrá"
}

def calculate_coverage_stats(df, origin_cluster_col, dest_cluster_col):
    """Calcula estadísticas de cobertura."""
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

print("="*80)
print("   PROPORCIÓN DE COBERTURA DE CLUSTERS POR CASO DE ESTUDIO")
print("="*80)
print()

all_results = {}

for territory_key, territory_name in territories.items():
    file_path = os.path.join(results_folder, f"3_clustered_{territory_key}.csv")
    
    if os.path.exists(file_path):
        df = pd.read_csv(file_path)
        stats = calculate_coverage_stats(df, 'ORIGIN_CLUSTER', 'DESTINATION_CLUSTER')
        all_results[territory_name] = stats
        
        print(f"{'='*80}")
        print(f"  {territory_name.upper()}")
        print(f"{'='*80}")
        print(f"\nTotal de viajes: {stats['total_trips']:,}")
        print(f"\nCOBERTURA DE ORÍGENES:")
        print(f"   • Viajes con cluster: {stats['trips_with_origin_cluster']:,} ({stats['origin_coverage_percentage']}%)")
        print(f"   • Viajes sin cluster (ruido): {stats['trips_origin_noise']:,} ({100 - stats['origin_coverage_percentage']:.2f}%)")
        print(f"   • Número de clusters: {stats['num_origin_clusters']}")
        
        print(f"\nCOBERTURA DE DESTINOS:")
        print(f"   • Viajes con cluster: {stats['trips_with_dest_cluster']:,} ({stats['dest_coverage_percentage']}%)")
        print(f"   • Viajes sin cluster (ruido): {stats['trips_dest_noise']:,} ({100 - stats['dest_coverage_percentage']:.2f}%)")
        print(f"   • Número de clusters: {stats['num_dest_clusters']}")
        
        print(f"\nCOBERTURA COMPLETA (ORIGEN Y DESTINO):")
        print(f"   • Viajes con ambos clusters: {stats['trips_both_clustered']:,} ({stats['both_coverage_percentage']}%)")
        print(f"   • Viajes sin cobertura completa: {stats['total_trips'] - stats['trips_both_clustered']:,} ({100 - stats['both_coverage_percentage']:.2f}%)")
        print()
    else:
        print(f"Archivo no encontrado: {file_path}\n")

# Resumen comparativo
print("\n" + "="*80)
print("  RESUMEN COMPARATIVO")
print("="*80)
print(f"\n{'Caso de Estudio':<20} {'Total Viajes':<15} {'Cob. Orígenes':<15} {'Cob. Destinos':<15} {'Cob. Completa':<15}")
print("-"*80)

for territory_name, stats in all_results.items():
    print(f"{territory_name:<20} {stats['total_trips']:<15,} {stats['origin_coverage_percentage']:<14}% {stats['dest_coverage_percentage']:<14}% {stats['both_coverage_percentage']:<14}%")

# Guardar resumen en JSON
summary_file = os.path.join(results_folder, "coverage_summary_all_territories.json")
with open(summary_file, 'w', encoding='utf-8') as f:
    json.dump(all_results, f, indent=2, ensure_ascii=False)

print(f"\nResumen guardado en: {summary_file}")
print("\n" + "="*80)



