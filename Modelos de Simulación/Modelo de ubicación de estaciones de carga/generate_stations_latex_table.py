# -*- coding: utf-8 -*-
"""
Script para generar una tabla LaTeX con las coordenadas de todas las estaciones
de carga para los 3 casos de estudio.
"""

import pandas as pd
import os

# Configuración
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS

# Territorios
territories = {
    "Bogota": "Bogotá",
    "Medellin": "Medellín",
    "Valle de aburra": "Valle de Aburrá"
}

# Traducción de tecnologías
tech_translation = {
    "Standard_Charger": "Cargador Estándar",
    "High_Capacity_Charger": "Cargador Alta Capacidad",
    "Battery_Swapping_Station": "Intercambio de Baterías"
}

def generate_latex_table():
    """Genera la tabla LaTeX con todas las estaciones."""
    
    all_stations = []
    
    # Cargar datos de cada territorio
    for territory_key, territory_name in territories.items():
        file_path = os.path.join(results_folder, f"optimal_solution_{territory_key}.csv")
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            for idx, row in df.iterrows():
                station_id = f"ST-{territory_key[:3].upper()}-{int(row['Cell_Row']):03d}-{int(row['Cell_Col']):03d}"
                all_stations.append({
                    'territory': territory_name,
                    'station_id': station_id,
                    'technology': tech_translation.get(row['Technology'], row['Technology']),
                    'latitude': row['Latitude'],
                    'longitude': row['Longitude'],
                    'cell_row': int(row['Cell_Row']),
                    'cell_col': int(row['Cell_Col'])
                })
        else:
            print(f"Archivo no encontrado: {file_path}")
    
    # Ordenar por territorio y luego por coordenadas
    all_stations.sort(key=lambda x: (x['territory'], x['latitude'], x['longitude']))
    
    # Generar LaTeX
    latex_content = """\\documentclass[12pt]{article}
\\usepackage[utf8]{inputenc}
\\usepackage[spanish]{babel}
\\usepackage{geometry}
\\usepackage{longtable}
\\usepackage{booktabs}
\\usepackage{array}
\\usepackage{xcolor}
\\usepackage{colortbl}

\\geometry{a4paper, margin=2cm}

\\title{Coordenadas de Estaciones de Carga\\\\(Casos de Estudio: Bogotá, Medellín y Valle de Aburrá)}
\\author{Sistema de Optimización de Infraestructura de Carga}
\\date{\\today}

\\begin{document}

\\maketitle

\\section{Resumen}
Este documento presenta las coordenadas geográficas (latitud y longitud) de todas las estaciones de carga optimizadas para los tres casos de estudio: Bogotá, Medellín y Valle de Aburrá.

\\begin{table}[h]
\\centering
\\caption{Resumen de Estaciones por Caso de Estudio}
\\begin{tabular}{lcc}
\\toprule
\\textbf{Caso de Estudio} & \\textbf{Número de Estaciones} & \\textbf{Tecnologías} \\\\
\\midrule
"""
    
    # Agregar resumen por territorio
    for territory_name in territories.values():
        territory_stations = [s for s in all_stations if s['territory'] == territory_name]
        tech_counts = {}
        for station in territory_stations:
            tech = station['technology']
            tech_counts[tech] = tech_counts.get(tech, 0) + 1
        
        tech_list = ", ".join([f"{tech}: {count}" for tech, count in sorted(tech_counts.items())])
        latex_content += f"{territory_name} & {len(territory_stations)} & {tech_list} \\\\\n"
    
    latex_content += """\\bottomrule
\\end{tabular}
\\end{table}

\\section{Coordenadas Detalladas de Estaciones}

\\begin{longtable}{p{2cm}p{3cm}p{4cm}cc}
\\caption{Coordenadas de todas las estaciones de carga optimizadas}\\\\
\\toprule
\\textbf{Caso de Estudio} & \\textbf{ID Estación} & \\textbf{Tecnología} & \\textbf{Latitud (°)} & \\textbf{Longitud (°)} \\\\
\\midrule
\\endfirsthead

\\multicolumn{5}{c}{{\\tablename\\ \\thetable{} -- continuación de la página anterior}} \\\\
\\toprule
\\textbf{Caso de Estudio} & \\textbf{ID Estación} & \\textbf{Tecnología} & \\textbf{Latitud (°)} & \\textbf{Longitud (°)} \\\\
\\midrule
\\endhead

\\midrule
\\multicolumn{5}{r}{{Continúa en la página siguiente}} \\\\
\\endfoot

\\bottomrule
\\endlastfoot

"""
    
    # Agregar filas de datos
    for station in all_stations:
        # Formatear coordenadas con 6 decimales
        lat_str = f"{station['latitude']:.6f}"
        lon_str = f"{station['longitude']:.6f}"
        
        # Escapar caracteres especiales de LaTeX
        territory_escaped = station['territory'].replace('á', '\\\'{a}').replace('é', '\\\'{e}').replace('í', '\\\'{i}').replace('ó', '\\\'{o}').replace('ú', '\\\'{u}')
        tech_escaped = station['technology'].replace('á', '\\\'{a}').replace('é', '\\\'{e}').replace('í', '\\\'{i}').replace('ó', '\\\'{o}').replace('ú', '\\\'{u}')
        
        latex_content += f"{territory_escaped} & {station['station_id']} & {tech_escaped} & {lat_str} & {lon_str} \\\\\n"
    
    latex_content += """\\end{longtable}

\\section{Notas}
\\begin{itemize}
    \\item Las coordenadas están en el sistema de referencia WGS84 (EPSG:4326).
    \\item La latitud es positiva hacia el norte (valores positivos indican hemisferio norte).
    \\item La longitud es negativa hacia el oeste (valores negativos indican hemisferio oeste para Colombia).
    \\item Las tecnologías disponibles son:
    \\begin{itemize}
        \\item \\textbf{Cargador Estándar}: Cargador convencional con capacidad moderada.
        \\item \\textbf{Cargador Alta Capacidad}: Cargador rápido con mayor capacidad de servicio.
        \\item \\textbf{Intercambio de Baterías}: Estación que permite el intercambio rápido de baterías.
    \\end{itemize}
\\end{itemize}

\\end{document}
"""
    
    # Guardar archivo LaTeX
    output_file = os.path.join(results_folder, "estaciones_coordenadas.tex")
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(latex_content)
    
    print(f"Tabla LaTeX generada: {output_file}")
    print(f"  Total de estaciones: {len(all_stations)}")
    
    # Mostrar resumen
    print("\nResumen por territorio:")
    for territory_name in territories.values():
        count = len([s for s in all_stations if s['territory'] == territory_name])
        print(f"  - {territory_name}: {count} estaciones")
    
    return output_file

if __name__ == "__main__":
    print("="*70)
    print("   GENERANDO TABLA LaTeX DE COORDENADAS DE ESTACIONES")
    print("="*70)
    print()
    
    output_file = generate_latex_table()
    
    print("\n" + "="*70)
    print("PROCESO COMPLETADO")
    print("="*70)
    print(f"\nArchivo generado: {output_file}")
    print("\nPara compilar el documento LaTeX, ejecuta:")
    print("  pdflatex estaciones_coordenadas.tex")


