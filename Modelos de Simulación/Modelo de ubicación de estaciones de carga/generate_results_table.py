# -*- coding: utf-8 -*-
"""
Script para generar tabla de resultados en LaTeX
Analiza las soluciones óptimas de estaciones de carga para las tres ciudades
"""

import pandas as pd
import os

# Rutas de los archivos de resultados
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS_FOLDER = os.path.join(script_dir, "Results")
cities = ["Bogota", "Medellin", "Valle de aburra"]

# Diccionario para almacenar resultados
results_summary = {}

print("Analizando resultados de optimización...\n")

for city in cities:
    csv_file = os.path.join(RESULTS_FOLDER, f"optimal_solution_{city}.csv")
    
    if not os.path.exists(csv_file):
        print(f"Archivo no encontrado: {csv_file}")
        continue
    
    # Leer datos
    df = pd.read_csv(csv_file)
    
    # Calcular estadísticas
    total_stations = len(df)
    tech_counts = df['Technology'].value_counts().to_dict()
    standard_count = tech_counts.get('Standard_Charger', 0)
    high_capacity_count = tech_counts.get('High_Capacity_Charger', 0)
    
    # Calcular área de cobertura aproximada (basado en las coordenadas)
    lat_range = df['Latitude'].max() - df['Latitude'].min()
    lon_range = df['Longitude'].max() - df['Longitude'].min()
    
    # Almacenar resultados
    results_summary[city] = {
        'Total Estaciones': total_stations,
        'Standard Charger': standard_count,
        'High Capacity Charger': high_capacity_count,
        'Rango Latitud (grados)': f"{lat_range:.4f}",
        'Rango Longitud (grados)': f"{lon_range:.4f}"
    }
    
    print(f"{city}:")
    print(f"   - Total estaciones: {total_stations}")
    print(f"   - Standard Charger: {standard_count}")
    print(f"   - High Capacity Charger: {high_capacity_count}")
    print()

# Generar tabla LaTeX
latex_table = """\\begin{table}[htbp]
\\centering
\\caption{Resultados de Optimización de Ubicaciones de Estaciones de Carga}
\\label{tab:optimizacion_estaciones}
\\begin{tabular}{lcccc}
\\toprule
\\textbf{Ciudad} & \\textbf{Total Estaciones} & \\textbf{Standard Charger} & \\textbf{High Capacity} & \\textbf{Diversidad Tecnológica} \\\\
\\midrule
"""

# Agregar filas de datos
for city in cities:
    if city in results_summary:
        data = results_summary[city]
        total = data['Total Estaciones']
        standard = data['Standard Charger']
        high_cap = data['High Capacity Charger']
        
        # Calcular diversidad (0 = solo un tipo, 1 = ambos tipos)
        if total > 0:
            diversity = "Sí" if high_cap > 0 and standard > 0 else "No"
        else:
            diversity = "N/A"
        
        # Formatear nombre de ciudad
        city_name = city.replace(" de ", " de ").title()
        if city == "Valle de aburra":
            city_name = "Valle de Aburrá"
        
        latex_table += f"{city_name} & {total} & {standard} & {high_cap} & {diversity} \\\\\n"

latex_table += """\\bottomrule
\\end{tabular}
\\begin{flushleft}
\\footnotesize
\\textit{Nota:} Los resultados se obtuvieron mediante optimización MILP (Mixed Integer Linear Programming) 
basada en clustering DBSCAN de orígenes y destinos. La diversidad tecnológica indica si se utilizaron 
ambos tipos de cargadores en la solución óptima.
\\end{flushleft}
\\end{table}
"""

# Guardar tabla LaTeX
output_file = os.path.join(RESULTS_FOLDER, "tabla_resultados_optimizacion.tex")
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(latex_table)

print(f"Tabla LaTeX generada: {output_file}\n")
print("="*70)
print("TABLA GENERADA:")
print("="*70)
print(latex_table)

