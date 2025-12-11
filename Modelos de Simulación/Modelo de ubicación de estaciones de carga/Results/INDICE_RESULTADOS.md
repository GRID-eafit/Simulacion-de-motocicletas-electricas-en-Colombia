# Índice Completo de Resultados - Proyecto Delfín 2025

## Archivos Principales

### Informe LaTeX Completo
- **`informe_resultados_simulacion.tex`** - Documento LaTeX completo con todos los resultados y gráficos
- **`tabla_resultados_optimizacion.tex`** - Tabla de resultados de optimización
- **`tabla_resultados_optimizacion_completa.tex`** - Tablas completas (3 tablas)

### Mapas Interactivos HTML
- **`optimal_locations_map_Bogota.html`** - Mapa interactivo de estaciones en Bogotá
- **`optimal_locations_map_Medellin.html`** - Mapa interactivo de estaciones en Medellín
- **`optimal_locations_map_Valle de aburra.html`** - Mapa interactivo de estaciones en Valle de Aburrá

## Resultados por Ciudad

### Bogotá
#### Datos CSV
- `1_cleaned_Bogota.csv` - Datos limpios iniciales
- `2_zoned_Bogota.csv` - Datos después de zonificación
- `3_clustered_Bogota.csv` - Datos con clusters identificados
- `4_flows_Bogota.csv` - Flujos de demanda agregados
- `5_final_sample_Bogota.csv` - Muestra estratificada final
- `od_matrix_Bogota.csv` - Matriz origen-destino
- `optimal_solution_Bogota.csv` - Solución óptima de estaciones

#### Gráficos PNG
- `2_zoned_map_Bogota.png` - Mapa de zonificación
- `3_clusters_origins_Bogota.png` - Clusters de orígenes
- `3_clusters_destinations_Bogota.png` - Clusters de destinos
- `4_flows_map_all_Bogota.png` - Todos los flujos de demanda
- `4_flows_map_top_Bogota.png` - Flujos principales
- `5_hotspots_map_Bogota.png` - Mapa de hotspots
- `5_stratified_sample_map_Bogota.png` - Mapa de muestreo estratificado
- `debug_kdist_Stage_1_Origins_Bogota.png` - Gráfico K-distance (Orígenes Etapa 1)
- `debug_kdist_Stage_2_Origins_Bogota.png` - Gráfico K-distance (Orígenes Etapa 2)
- `debug_kdist_Stage_1_Destinations_Bogota.png` - Gráfico K-distance (Destinos Etapa 1)
- `debug_kdist_Stage_2_Destinations_Bogota.png` - Gráfico K-distance (Destinos Etapa 2)

### Medellín
#### Datos CSV
- `1_cleaned_Medellin.csv` - Datos limpios iniciales
- `2_zoned_Medellin.csv` - Datos después de zonificación
- `3_clustered_Medellin.csv` - Datos con clusters identificados
- `4_flows_Medellin.csv` - Flujos de demanda agregados
- `5_final_sample_Medellin.csv` - Muestra estratificada final
- `od_matrix_Medellin.csv` - Matriz origen-destino
- `optimal_solution_Medellin.csv` - Solución óptima de estaciones

#### Gráficos PNG
- `2_zoned_map_Medellin.png` - Mapa de zonificación
- `3_clusters_origins_Medellin.png` - Clusters de orígenes
- `3_clusters_destinations_Medellin.png` - Clusters de destinos
- `4_flows_map_all_Medellin.png` - Todos los flujos de demanda
- `4_flows_map_top_Medellin.png` - Flujos principales
- `5_hotspots_map_Medellin.png` - Mapa de hotspots
- `5_stratified_sample_map_Medellin.png` - Mapa de muestreo estratificado
- `debug_kdist_Stage_1_Origins_Medellin.png` - Gráfico K-distance (Orígenes Etapa 1)
- `debug_kdist_Stage_2_Origins_Medellin.png` - Gráfico K-distance (Orígenes Etapa 2)
- `debug_kdist_Stage_1_Destinations_Medellin.png` - Gráfico K-distance (Destinos Etapa 1)
- `debug_kdist_Stage_2_Destinations_Medellin.png` - Gráfico K-distance (Destinos Etapa 2)

### Valle de Aburrá
#### Datos CSV
- `1_cleaned_Valle de aburra.csv` - Datos limpios iniciales
- `2_zoned_Valle de aburra.csv` - Datos después de zonificación
- `3_clustered_Valle de aburra.csv` - Datos con clusters identificados
- `4_flows_Valle de aburra.csv` - Flujos de demanda agregados
- `5_final_sample_Valle de aburra.csv` - Muestra estratificada final
- `od_matrix_Valle de aburra.csv` - Matriz origen-destino
- `optimal_solution_Valle de aburra.csv` - Solución óptima de estaciones

#### Gráficos PNG
- `2_zoned_map_Valle de aburra.png` - Mapa de zonificación
- `3_clusters_origins_Valle de aburra.png` - Clusters de orígenes
- `3_clusters_destinations_Valle de aburra.png` - Clusters de destinos
- `4_flows_map_all_Valle de aburra.png` - Todos los flujos de demanda
- `4_flows_map_top_Valle de aburra.png` - Flujos principales
- `5_hotspots_map_Valle de aburra.png` - Mapa de hotspots
- `5_stratified_sample_map_Valle de aburra.png` - Mapa de muestreo estratificado
- `debug_kdist_Stage_1_Origins_Valle de aburra.png` - Gráfico K-distance (Orígenes Etapa 1)
- `debug_kdist_Stage_2_Origins_Valle de aburra.png` - Gráfico K-distance (Orígenes Etapa 2)
- `debug_kdist_Stage_1_Destinations_Valle de aburra.png` - Gráfico K-distance (Destinos Etapa 1)
- `debug_kdist_Stage_2_Destinations_Valle de aburra.png` - Gráfico K-distance (Destinos Etapa 2)

## Cómo Usar

### Compilar el Informe LaTeX
```bash
cd Results
pdflatex informe_resultados_simulacion.tex
pdflatex informe_resultados_simulacion.tex  # Segunda pasada para referencias
```

### Ver Mapas Interactivos
Abre los archivos HTML en tu navegador web:
- `optimal_locations_map_Bogota.html`
- `optimal_locations_map_Medellin.html`
- `optimal_locations_map_Valle de aburra.html`

### Ver Gráficos
Todos los gráficos están en formato PNG y pueden abrirse con cualquier visor de imágenes.

### Analizar Datos CSV
Los archivos CSV pueden abrirse con:
- Excel
- Python (pandas)
- R
- Cualquier editor de texto

## Resumen de Resultados

### Bogotá
- **Total de estaciones:** 9
- **Standard Charger:** 6
- **High Capacity Charger:** 2
- **Battery Swapping Station:** 1
- **Diversidad tecnológica:** Sí

### Medellín
- **Total de estaciones:** 9
- **Standard Charger:** 8
- **High Capacity Charger:** 1
- **Diversidad tecnológica:** Sí

### Valle de Aburrá
- **Total de estaciones:** 10
- **Standard Charger:** 10
- **Diversidad tecnológica:** No

### Total General
- **Total de estaciones:** 28
- **Standard Charger:** 24
- **High Capacity Charger:** 3
- **Battery Swapping Station:** 1

## Notas

- Todos los archivos están en la carpeta `Results/`
- Los mapas HTML son interactivos y permiten hacer zoom y ver detalles
- Los gráficos PNG tienen alta resolución para impresión
- Los CSV contienen todos los datos procesados en cada etapa

## Estructura del Pipeline

1. **Limpieza de datos** → `1_cleaned_*.csv`
2. **Zonificación** → `2_zoned_*.csv` + `2_zoned_map_*.png`
3. **Clustering** → `3_clustered_*.csv` + `3_clusters_*.png`
4. **Flujos** → `4_flows_*.csv` + `4_flows_map_*.png`
5. **Muestreo** → `5_final_sample_*.csv` + `5_*.png`
6. **Optimización** → `optimal_solution_*.csv` + `optimal_locations_map_*.html`

---
*Generado automáticamente - Proyecto Delfín 2025*


