# -*- coding: utf-8 -*-
"""
Script para extraer información de estaciones optimizadas:
- Coordenadas de cada estación
- Tecnología y color asignado
- Significado de cada tecnología
- Estadísticas de cobertura y distribución
"""

import pandas as pd
import json5
import os
import sys
import json

# --- CONFIGURACIÓN ---
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS
data_folder = os.path.join(script_dir, 'Archivos de apoyo')

# Archivos de entrada
FILE_OPTIMAL_SOLUTION = os.path.join(results_folder, f"optimal_solution_{locale_info}.csv")
CONFIG_FILE = os.path.join(data_folder, 'config.jsonc')

# Archivos de salida
OUTPUT_JSON = os.path.join(results_folder, f"stations_info_{locale_info}.json")
OUTPUT_CSV = os.path.join(results_folder, f"stations_detailed_{locale_info}.csv")
OUTPUT_REPORT = os.path.join(results_folder, f"stations_report_{locale_info}.txt")

def get_technology_info(tech_name, tech_cfg):
    """
    Obtiene información completa de una tecnología.
    
    Returns:
        Diccionario con información de la tecnología
    """
    if tech_name not in tech_cfg:
        return {
            'name': tech_name,
            'description': 'Tecnología no definida en configuración',
            'color': 'gray',
            'color_hex': '#808080',
            'icon': 'fa-question',
            'cost': 0,
            'annual_op_cost': 0,
            'service_capacity': 0,
            'resource_units': 0
        }
    
    tech = tech_cfg[tech_name]
    
    # Mapeo de colores comunes a hexadecimal
    color_map = {
        'blue': '#0000FF',
        'green': '#00FF00',
        'purple': '#800080',
        'red': '#FF0000',
        'orange': '#FFA500',
        'yellow': '#FFFF00',
        'gray': '#808080',
        'black': '#000000'
    }
    
    color_name = tech.get('color', 'gray')
    color_hex = color_map.get(color_name.lower(), '#808080')
    
    # Descripciones de tecnologías
    descriptions = {
        'Standard_Charger': 'Cargador estándar: Tecnología de carga convencional con capacidad moderada. Ideal para ubicaciones con demanda media.',
        'High_Capacity_Charger': 'Cargador de alta capacidad: Tecnología de carga rápida con mayor capacidad de servicio. Ideal para ubicaciones con alta demanda.',
        'Battery_Swapping_Station': 'Estación de intercambio de baterías: Permite el intercambio rápido de baterías descargadas por baterías cargadas. Tecnología de mayor capacidad y costo.'
    }
    
    return {
        'name': tech_name,
        'description': descriptions.get(tech_name, f'Tecnología: {tech_name}'),
        'color': color_name,
        'color_hex': color_hex,
        'color_rgb': hex_to_rgb(color_hex),
        'icon': tech.get('icon', 'fa-plug'),
        'cost': tech.get('cost', 0),
        'annual_op_cost': tech.get('annual_op_cost', 0),
        'service_capacity': tech.get('service_capacity_routes_per_day', 0),
        'resource_units': tech.get('resource_units_required', 0)
    }

def hex_to_rgb(hex_color):
    """Convierte color hexadecimal a RGB."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def calculate_station_statistics(df, tech_cfg):
    """
    Calcula estadísticas de las estaciones.
    
    Returns:
        Diccionario con estadísticas
    """
    total_stations = len(df)
    
    # Estadísticas por tecnología
    tech_stats = {}
    for tech_name in df['Technology'].unique():
        tech_df = df[df['Technology'] == tech_name]
        tech_info = get_technology_info(tech_name, tech_cfg)
        tech_stats[tech_name] = {
            'count': len(tech_df),
            'percentage': round(len(tech_df) / total_stations * 100, 2) if total_stations > 0 else 0,
            'total_cost': tech_info['cost'] * len(tech_df),
            'total_annual_op_cost': tech_info['annual_op_cost'] * len(tech_df),
            'total_service_capacity': tech_info['service_capacity'] * len(tech_df),
            'total_resource_units': tech_info['resource_units'] * len(tech_df),
            'color': tech_info['color'],
            'color_hex': tech_info['color_hex']
        }
    
    # Costos totales
    total_cost = sum(tech_stats[t]['total_cost'] for t in tech_stats)
    total_annual_op_cost = sum(tech_stats[t]['total_annual_op_cost'] for t in tech_stats)
    total_service_capacity = sum(tech_stats[t]['total_service_capacity'] for t in tech_stats)
    total_resource_units = sum(tech_stats[t]['total_resource_units'] for t in tech_stats)
    
    # Distribución geográfica
    lat_range = {
        'min': df['Latitude'].min(),
        'max': df['Latitude'].max(),
        'mean': df['Latitude'].mean()
    }
    lon_range = {
        'min': df['Longitude'].min(),
        'max': df['Longitude'].max(),
        'mean': df['Longitude'].mean()
    }
    
    return {
        'total_stations': total_stations,
        'technology_distribution': tech_stats,
        'total_cost': total_cost,
        'total_annual_op_cost': total_annual_op_cost,
        'total_service_capacity': total_service_capacity,
        'total_resource_units': total_resource_units,
        'geographic_distribution': {
            'latitude': lat_range,
            'longitude': lon_range
        }
    }

def main():
    # Permitir pasar el territorio como argumento de línea de comandos
    global locale_info
    if len(sys.argv) > 1:
        locale_info = sys.argv[1]
        os.environ['ANALYSIS_LOCALE'] = locale_info
    
    print(f"\n{'='*70}")
    print(f"   EXTRACCIÓN DE INFORMACIÓN DE ESTACIONES OPTIMIZADAS")
    print(f"   Territorio: {locale_info}")
    print(f"{'='*70}\n")
    
    # Verificar que existe el archivo de solución óptima
    if not os.path.exists(FILE_OPTIMAL_SOLUTION):
        print(f"ERROR: Archivo '{FILE_OPTIMAL_SOLUTION}' no encontrado.")
        print("   Por favor ejecuta primero 'Optimization_FCLP.py' o el pipeline completo.")
        sys.exit(1)
    
    # Cargar configuración para obtener información de tecnologías
    if not os.path.exists(CONFIG_FILE):
        print(f"ADVERTENCIA: Archivo de configuración '{CONFIG_FILE}' no encontrado.")
        print("   Se usará información básica sin detalles de tecnologías.")
        tech_cfg = {}
    else:
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            config = json5.load(f)
        tech_cfg = config.get('optimization_settings', {}).get('technologies', {})
    
    # Cargar datos de estaciones
    print("Cargando datos de estaciones optimizadas...")
    df = pd.read_csv(FILE_OPTIMAL_SOLUTION)
    print(f"  Cargadas {len(df)} estaciones")
    
    # Verificar columnas necesarias
    required_cols = ['Cell_Row', 'Cell_Col', 'Technology', 'Latitude', 'Longitude']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        print(f"ERROR: Faltan columnas: {missing_cols}")
        sys.exit(1)
    
    # Agregar información detallada de tecnologías
    print("Procesando información de tecnologías...")
    stations_data = []
    for _, row in df.iterrows():
        tech_info = get_technology_info(row['Technology'], tech_cfg)
        station_data = {
            'station_id': f"ST_{int(row['Cell_Row'])}_{int(row['Cell_Col'])}",
            'cell_row': int(row['Cell_Row']),
            'cell_col': int(row['Cell_Col']),
            'latitude': row['Latitude'],
            'longitude': row['Longitude'],
            'technology': row['Technology'],
            'technology_name': tech_info['name'],
            'technology_description': tech_info['description'],
            'color': tech_info['color'],
            'color_hex': tech_info['color_hex'],
            'color_rgb': f"rgb({tech_info['color_rgb'][0]}, {tech_info['color_rgb'][1]}, {tech_info['color_rgb'][2]})",
            'icon': tech_info['icon'],
            'cost': tech_info['cost'],
            'annual_op_cost': tech_info['annual_op_cost'],
            'service_capacity': tech_info['service_capacity'],
            'resource_units': tech_info['resource_units']
        }
        stations_data.append(station_data)
    
    stations_df = pd.DataFrame(stations_data)
    
    # Calcular estadísticas
    print("Calculando estadísticas...")
    stats = calculate_station_statistics(df, tech_cfg)
    
    # Guardar CSV detallado
    print("\nGuardando archivo CSV detallado...")
    stations_df.to_csv(OUTPUT_CSV, index=False)
    print(f" {OUTPUT_CSV}")
    
    # Preparar datos para JSON
    output_data = {
        'territory': locale_info,
        'statistics': stats,
        'stations': stations_data,
        'technology_legend': {
            tech_name: get_technology_info(tech_name, tech_cfg) 
            for tech_name in tech_cfg.keys()
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
        f.write(f"   REPORTE DE ESTACIONES OPTIMIZADAS - {locale_info.upper()}\n")
        f.write("="*70 + "\n\n")
        
        # Estadísticas generales
        f.write("ESTADÍSTICAS GENERALES\n")
        f.write("-"*70 + "\n")
        f.write(f"Total de estaciones: {stats['total_stations']}\n")
        f.write(f"Costo total de inversión: ${stats['total_cost']:,.2f}\n")
        f.write(f"Costo operativo anual total: ${stats['total_annual_op_cost']:,.2f}\n")
        f.write(f"Capacidad de servicio total: {stats['total_service_capacity']} rutas/día\n")
        f.write(f"Unidades de recurso totales: {stats['total_resource_units']}\n\n")
        
        # Distribución por tecnología
        f.write("="*70 + "\n")
        f.write("DISTRIBUCIÓN POR TECNOLOGÍA\n")
        f.write("-"*70 + "\n")
        for tech_name, tech_stat in stats['technology_distribution'].items():
            tech_info = get_technology_info(tech_name, tech_cfg)
            f.write(f"\n{tech_info['name']}:\n")
            f.write(f"  Descripción: {tech_info['description']}\n")
            f.write(f"  Cantidad: {tech_stat['count']} ({tech_stat['percentage']}%)\n")
            f.write(f"  Color: {tech_stat['color']} ({tech_stat['color_hex']})\n")
            f.write(f"  Icono: {tech_info['icon']}\n")
            f.write(f"  Costo unitario: ${tech_info['cost']:,.2f}\n")
            f.write(f"  Costo operativo anual unitario: ${tech_info['annual_op_cost']:,.2f}\n")
            f.write(f"  Capacidad de servicio: {tech_info['service_capacity']} rutas/día\n")
            f.write(f"  Unidades de recurso: {tech_info['resource_units']}\n")
            f.write(f"  Costo total: ${tech_stat['total_cost']:,.2f}\n")
            f.write(f"  Costo operativo anual total: ${tech_stat['total_annual_op_cost']:,.2f}\n")
            f.write(f"  Capacidad total: {tech_stat['total_service_capacity']} rutas/día\n")
        
        # Distribución geográfica
        f.write("\n" + "="*70 + "\n")
        f.write("DISTRIBUCIÓN GEOGRÁFICA\n")
        f.write("-"*70 + "\n")
        f.write(f"Latitud:\n")
        f.write(f"  Mínima: {stats['geographic_distribution']['latitude']['min']:.6f}\n")
        f.write(f"  Máxima: {stats['geographic_distribution']['latitude']['max']:.6f}\n")
        f.write(f"  Promedio: {stats['geographic_distribution']['latitude']['mean']:.6f}\n")
        f.write(f"Longitud:\n")
        f.write(f"  Mínima: {stats['geographic_distribution']['longitude']['min']:.6f}\n")
        f.write(f"  Máxima: {stats['geographic_distribution']['longitude']['max']:.6f}\n")
        f.write(f"  Promedio: {stats['geographic_distribution']['longitude']['mean']:.6f}\n")
        
        # Lista de estaciones
        f.write("\n" + "="*70 + "\n")
        f.write("LISTA DE ESTACIONES\n")
        f.write("-"*70 + "\n")
        f.write(f"{'ID':<15} {'Latitud':<12} {'Longitud':<12} {'Tecnología':<25} {'Color':<10}\n")
        f.write("-"*70 + "\n")
        for station in stations_data:
            f.write(f"{station['station_id']:<15} {station['latitude']:<12.6f} {station['longitude']:<12.6f} ")
            f.write(f"{station['technology']:<25} {station['color_hex']:<10}\n")
    
    print(f" {OUTPUT_REPORT}")
    
    # Mostrar resumen en consola
    print("\n" + "="*70)
    print("RESUMEN DE RESULTADOS")
    print("="*70)
    print(f"\nTotal de estaciones: {stats['total_stations']}")
    print(f"Costo total: ${stats['total_cost']:,.2f}")
    print(f"\nDistribución por tecnología:")
    for tech_name, tech_stat in stats['technology_distribution'].items():
        tech_info = get_technology_info(tech_name, tech_cfg)
        print(f"  - {tech_info['name']}: {tech_stat['count']} estaciones ({tech_stat['percentage']}%)")
        print(f"    Color: {tech_stat['color']} ({tech_stat['color_hex']})")
    
    print(f"\n{'='*70}")
    print("EXTRACCIÓN COMPLETA")
    print(f"{'='*70}")
    print(f"\nArchivos generados:")
    print(f"  - {OUTPUT_JSON}")
    print(f"  - {OUTPUT_CSV}")
    print(f"  - {OUTPUT_REPORT}")

if __name__ == "__main__":
    main()

