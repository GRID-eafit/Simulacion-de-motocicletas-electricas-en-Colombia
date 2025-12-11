================================================================================
    ACCESO A TODOS LOS RESULTADOS - PROYECTO DELFÍN 2025
================================================================================

ARCHIVOS PRINCIPALES
================================================================================

1. INFORME LATEX COMPLETO
   - informe_resultados_simulacion.tex
   → Compilar con: pdflatex informe_resultados_simulacion.tex (2 veces)

2. MAPAS INTERACTIVOS HTML
   - optimal_locations_map_Bogota.html
   - optimal_locations_map_Medellin.html
   - optimal_locations_map_Valle de aburra.html
   → Abrir con cualquier navegador web

3. TABLAS DE RESULTADOS
   - tabla_resultados_optimizacion.tex
   - tabla_resultados_optimizacion_completa.tex

4. SOLUCIONES ÓPTIMAS (CSV)
   - optimal_solution_Bogota.csv
   - optimal_solution_Medellin.csv
   - optimal_solution_Valle de aburra.csv

RESUMEN DE RESULTADOS
================================================================================

BOGOTÁ:
  - Total estaciones: 9
  - Standard Charger: 6
  - High Capacity Charger: 2
  - Battery Swapping Station: 1
  - Diversidad tecnológica: Sí

MEDELLÍN:
  - Total estaciones: 9
  - Standard Charger: 8
  - High Capacity Charger: 1
  - Diversidad tecnológica: Sí

VALLE DE ABURRÁ:
  - Total estaciones: 10
  - Standard Charger: 10
  - Diversidad tecnológica: No

TOTAL GENERAL:
  - Total estaciones: 28
  - Standard Charger: 24
  - High Capacity Charger: 3
  - Battery Swapping Station: 1

ARCHIVOS POR ETAPA DEL PIPELINE
================================================================================

ETAPA 1 - LIMPIEZA:
  1_cleaned_Bogota.csv
  1_cleaned_Medellin.csv
  1_cleaned_Valle de aburra.csv

ETAPA 2 - ZONIFICACIÓN:
  2_zoned_*.csv
  2_zoned_map_*.png

ETAPA 3 - CLUSTERING:
  3_clustered_*.csv
  3_clusters_origins_*.png
  3_clusters_destinations_*.png
  od_matrix_*.csv

ETAPA 4 - FLUJOS:
  4_flows_*.csv
  4_flows_map_all_*.png
  4_flows_map_top_*.png

ETAPA 5 - MUESTREO:
  5_final_sample_*.csv
  5_hotspots_map_*.png
  5_stratified_sample_map_*.png

ETAPA 6 - OPTIMIZACIÓN:
  optimal_solution_*.csv
  optimal_locations_map_*.html

CÓMO USAR
================================================================================

OPCIÓN 1: Script Python Interactivo
  python acceder_todos_resultados.py
  → Menú interactivo para acceder a todos los archivos

OPCIÓN 2: Índice Markdown
  Abrir: INDICE_RESULTADOS.md
  → Lista completa de todos los archivos con descripciones

OPCIÓN 3: Este archivo
  README_ACCESO.txt
  → Referencia rápida de archivos principales

COMPILAR INFORME LATEX
================================================================================

Windows:
  pdflatex informe_resultados_simulacion.tex
  pdflatex informe_resultados_simulacion.tex

Linux/Mac:
  pdflatex informe_resultados_simulacion.tex
  pdflatex informe_resultados_simulacion.tex

NOTAS
================================================================================

- Todos los archivos están en la carpeta Results/
- Los mapas HTML son interactivos (zoom, pan, información detallada)
- Los gráficos PNG tienen alta resolución para impresión
- Los CSV pueden abrirse con Excel, Python, R, etc.
- El informe LaTeX requiere paquetes estándar (booktabs, graphicx, etc.)

================================================================================
Proyecto Delfín 2025 - Todos los derechos reservados
================================================================================


