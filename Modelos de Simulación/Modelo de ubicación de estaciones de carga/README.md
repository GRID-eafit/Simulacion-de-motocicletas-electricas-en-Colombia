# Guía Completa: Simulación de Estaciones de Carga con Clustering

## Descripción General

Este proyecto implementa un **pipeline completo de optimización de estaciones de carga para vehículos eléctricos ligeros (LEV)** utilizando técnicas avanzadas de clustering (DBSCAN), simulación física basada en rutas reales (OpenRouteService API), y optimización mediante Programación Lineal Entera Mixta (MILP).

El sistema procesa datos de origen-destino (O-D), agrupa viajes mediante clustering espacial, simula el consumo energético real de las rutas, y determina la ubicación y tecnología óptima de estaciones de carga.

---

## Características Principales

- **Procesamiento de datos O-D** con limpieza y validación geográfica
- **Clustering DBSCAN de dos etapas** para orígenes y destinos
- **Simulación física de consumo energético** usando OpenRouteService API
- **Optimización MILP** para ubicación y tecnología de estaciones
- **Soporte multi-territorio**: Medellín, Valle de Aburrá, Bogotá
- **Visualizaciones interactivas** (mapas HTML, gráficos)
- **Monitoreo en tiempo real** del pipeline completo

---

## Estructura del Proyecto

```
Scripts/
├── main_pipeline.py                    # Pipeline principal (ejecutar este)
├── AnalisisOD.py                        # Limpieza de datos O-D
├── Geographical_Zoning.py              # Filtrado geográfico
├── DBSCAN_Clustering.py                 # Clustering de orígenes/destinos
├── extract_cluster_info.py              # Extracción de info de clusters
├── Representative_flows_super_paths.py   # Agregación de flujos
├── Stratified_sampling.py               # Muestreo estratificado
├── real_path_simulation.py              # Simulación física (ORS API)
├── precompute_access_costs.py           # Cálculo de costos de acceso
├── Optimization_FCLP.py                 # Optimización MILP
├── extract_stations_info.py             # Extracción de info de estaciones
│
├── HybridBikeConsumptionModel/          # Modelo de consumo energético
│   ├── Modelo_moto.py
│   ├── functions.py
│   └── model.py
│
├── Archivos de apoyo/                   # Datos de entrada
│   ├── config.jsonc                     # Configuración principal
│   ├── Medellin/
│   │   └── med.csv                      # Datos O-D Medellín
│   ├── Valle de aburra/
│   │   └── amva.csv                     # Datos O-D Valle de Aburrá
│   ├── Bogota/
│   │   └── bog.csv                      # Datos O-D Bogotá
│   └── milp_input_data.json             # (Generado por simulación)
│   └── access_trip_costs.json           # (Generado por precompute)
│
├── Results/                             # Resultados del pipeline
│   ├── 1_cleaned_{territorio}.csv
│   ├── 2_zoned_{territorio}.csv
│   ├── 3_clustered_{territorio}.csv
│   ├── 4_flows_{territorio}.csv
│   ├── 5_final_sample_{territorio}.csv
│   ├── optimal_solution_{territorio}.csv
│   ├── optimal_locations_map_{territorio}.html
│   └── ...
│
└── Limites {Territorio}/                 # Shapefiles de límites
    └── {Territorio}_Urbano_y_Rural.shp
```

---

## Requisitos Previos

### 1. Software Necesario

- **Python 3.8+**
- **pip** (gestor de paquetes Python)

### 2. Dependencias Python

Instala las dependencias ejecutando:

```bash
pip install pandas geopandas scikit-learn numpy matplotlib shapely folium tqdm requests json5 pulp
```

O crea un archivo `requirements.txt` con:

```
pandas>=1.5.0
geopandas>=0.13.0
scikit-learn>=1.2.0
numpy>=1.23.0
matplotlib>=3.6.0
shapely>=2.0.0
folium>=0.14.0
tqdm>=4.65.0
requests>=2.28.0
json5>=0.9.0
pulp>=2.6.0
```

Luego ejecuta:

```bash
pip install -r requirements.txt
```

### 3. Archivos de Datos Necesarios

Asegúrate de tener los siguientes archivos en las ubicaciones correctas:

#### Datos O-D (Origen-Destino)
- `Archivos de apoyo/Medellin/med.csv`
- `Archivos de apoyo/Valle de aburra/amva.csv`
- `Archivos de apoyo/Bogota/bog.csv`

#### Shapefiles de Límites
Se debe descomprimir los archivos 'Limites Bogota DC.zip', 'Limites Valle de Aburra.zip' y 'Limites Medellin.zip'
- `Limites Medellin/Medellin_Urbano_y_Rural.shp` (y archivos relacionados: .dbf, .prj, .shx)
- `Limites Valle de Aburra/Valle_De_Aburra_Urbano_y_Rural.shp`
- `Limites Bogota DC/Bogota_Urbano_y_Rural.shp`

#### Archivo de Configuración
- `Archivos de apoyo/config.jsonc` (ver sección de configuración)

### 4. API Key de OpenRouteService

Necesitas una API key de OpenRouteService para la simulación de rutas. Obtén una en: https://openrouteservice.org/

---

## Configuración

### Archivo `config.jsonc`

El archivo de configuración contiene todos los parámetros del modelo. Ubicación: `Archivos de apoyo/config.jsonc`

#### Configuración de Simulación

```jsonc
{
  "simulation_settings": {
    "ors_api_key": "TU_API_KEY_AQUI",  // IMPORTANTE: Reemplazar con tu API key
    "vehicle_model_to_use": "hybrid",   // "electric" o "hybrid"
    "hybrid_contribution": 0.0,
    "speed_profile": {
      "cruising_speed": 45,              // km/h
      "accel_points": 15,
      "decel_points": 10,
      "uphill_sensitivity": 0.5,
      "downhill_sensitivity": 0.8,
      "num_stops": 3,
      "stop_duration": 20,              // segundos
      "max_slope_effect": 15
    },
    "clustering_settings": {
      "origins": {
        "stage_1": { "eps": 400, "min_samples": 15 },  // Clustering inicial
        "stage_2": { "eps": 150, "min_samples": 10 }  // Refinamiento
      },
      "destinations": {
        "stage_1": { "eps": 400, "min_samples": 15 },
        "stage_2": { "eps": 150, "min_samples": 10 }
      }
    },
    "vehicle_models": {
      "electric": {
        "chassis": {"m": 225, "a": 0.6, "cd": 0.7, "crr": 0.01},
        "wheel": {"rw": 0.2667},
        "ambient": {"rho": 1.21, "g": 9.8}
      },
      "hybrid": {
        "chassis": {"m": 200, "a": 0.6, "cd": 0.7, "crr": 0.01},
        "wheel": {"rw": 0.2667},
        "ambient": {"rho": 1.21, "g": 9.8}
      }
    }
  }
}
```

#### Configuración de Optimización

```jsonc
{
  "optimization_settings": {
    "grid_settings": {
      "geodata_shapefile_path": "Medellin_Urbano_y_Rural.shp",
      "grid_size_km": 1.0  // Tamaño de celda de la malla (km)
    },
    "battery_settings": {
      "total_capacity_wh": 5400,        // Capacidad total de batería (Wh)
      "starting_soc_pct": 100,          // Estado de carga inicial (%)
      "low_soc_threshold_pct": 20        // Umbral mínimo de reserva (%)
    },
    "technologies": {
      "Standard_Charger": {
        "cost": 80000,
        "annual_op_cost": 8000,
        "service_capacity_routes_per_day": 40,
        "resource_units_required": 4,
        "color": "blue",
        "icon": "fa-plug"
      },
      "High_Capacity_Charger": {
        "cost": 150000,
        "annual_op_cost": 15000,
        "service_capacity_routes_per_day": 90,
        "resource_units_required": 8,
        "color": "green",
        "icon": "fa-bolt"
      },
      "Battery_Swapping_Station": {
        "cost": 300000,
        "annual_op_cost": 30000,
        "service_capacity_routes_per_day": 200,
        "resource_units_required": 20,
        "color": "purple",
        "icon": "fa-battery-full"
      }
    },
    "parameters": {
      "lifespan_years": 10,
      "total_budget": 2000000,           // Presupuesto total (COP)
      "exact_stations_to_build": 10,     // Número exacto de estaciones
      "total_resource_units_available": 80,
      "coverage_radius_km": 1,           // Radio de cobertura (km)
      "enforce_closest_assignment": true
    },
    "objective_function": {
      "type": "weighted_utility",
      "utility_weights": {
        "coverage": 1.0,
        "travel_distance": 0.2
      },
      "profit_parameters": {
        "revenue_per_charge_session": 5.0,
        "days_per_year": 365
      }
    },
    "zonal_constraints": {
      "enabled": false,
      "zone_id_column": "mpio_ccdgo",
      "max_stations_per_zone": {
        "MEDELLÍN": 5,
        "BELLO": 1,
        "ITAGÜÍ": 1,
        "ENVIGADO": 1,
        "SABANETA": 1,
        "DEFAULT": 5
      }
    }
  }
}
```

---

## Ejecución del Pipeline

### Método 1: Pipeline Automático (Recomendado)

El método más sencillo es ejecutar el pipeline completo usando `main_pipeline.py`:

```bash
python main_pipeline.py
```

El script te pedirá seleccionar el territorio:
1. **Medellin**
2. **Valle de Aburra**
3. **Bogota**

El pipeline ejecutará automáticamente todos los pasos en orden y mostrará el progreso en tiempo real.

### Método 2: Ejecución Manual Paso a Paso

Si prefieres ejecutar cada paso manualmente o necesitas depurar un paso específico:

#### Paso 1: Limpieza de Datos O-D
```bash
set ANALYSIS_LOCALE=Medellin  # Windows
# o
export ANALYSIS_LOCALE=Medellin  # Linux/Mac

python AnalisisOD.py
```
**Salida**: `Results/1_cleaned_{territorio}.csv`

#### Paso 2: Filtrado Geográfico
```bash
python Geographical_Zoning.py
```
**Salida**: `Results/2_zoned_{territorio}.csv`

#### Paso 3: Clustering DBSCAN
```bash
python DBSCAN_Clustering.py
```
**Salida**: `Results/3_clustered_{territorio}.csv`

#### Paso 4: Extracción de Información de Clusters
```bash
python extract_cluster_info.py
```
**Salida**: 
- `Results/cluster_info_{territorio}.json`
- `Results/cluster_origins_info_{territorio}.csv`
- `Results/cluster_destinations_info_{territorio}.csv`
- `Results/cluster_report_{territorio}.txt`

#### Paso 5: Agregación de Flujos Representativos
```bash
python Representative_flows_super_paths.py
```
**Salida**: `Results/4_flows_{territorio}.csv`

#### Paso 6: Muestreo Estratificado
```bash
python Stratified_sampling.py
```
**Salida**: `Results/5_final_sample_{territorio}.csv`

#### Paso 7: Simulación Física de Rutas
```bash
python real_path_simulation.py
```
**Salida**: `Archivos de apoyo/milp_input_data.json`

**Nota**: Este paso puede tardar mucho tiempo ya que hace llamadas a la API de OpenRouteService. El script incluye caché de rutas para evitar llamadas duplicadas.

#### Paso 8: Cálculo de Costos de Acceso
```bash
python precompute_access_costs.py
```
**Salida**: `Archivos de apoyo/access_trip_costs.json`

#### Paso 9: Optimización MILP
```bash
python Optimization_FCLP.py
```
**Salida**: 
- `Results/optimal_solution_{territorio}.csv`
- `Results/optimal_locations_map_{territorio}.html`

#### Paso 10: Extracción de Información de Estaciones
```bash
python extract_stations_info.py
```
**Salida**: 
- `Results/stations_info_{territorio}.json`
- `Results/stations_detailed_{territorio}.csv`
- `Results/stations_report_{territorio}.txt`

---

## Descripción Detallada de Cada Script

### 1. `AnalisisOD.py`
**Propósito**: Limpia y prepara los datos de origen-destino.

**Funciones**:
- Carga datos CSV de encuestas O-D
- Elimina filas con coordenadas inválidas
- Valida rangos geográficos (latitud/longitud)
- Elimina duplicados
- Calcula estadísticas de limpieza

**Entrada**: `Archivos de apoyo/{Territorio}/{territorio}.csv`
**Salida**: `Results/1_cleaned_{territorio}.csv`

---

### 2. `Geographical_Zoning.py`
**Propósito**: Filtra viajes que están dentro de los límites geográficos del territorio.

**Funciones**:
- Carga shapefile de límites
- Filtra viajes que inician y terminan dentro del área
- Elimina viajes que cruzan límites
- Genera visualización de viajes válidos

**Entrada**: 
- `Results/1_cleaned_{territorio}.csv`
- `Limites {Territorio}/{Territorio}_Urbano_y_Rural.shp`

**Salida**: `Results/2_zoned_{territorio}.csv`

---

### 3. `DBSCAN_Clustering.py`
**Propósito**: Agrupa orígenes y destinos usando clustering DBSCAN de dos etapas.

**Funciones**:
- **Etapa 1**: Clustering amplio (eps=400m, min_samples=15)
- **Etapa 2**: Refinamiento de super-clusters (eps=150m, min_samples=10)
- Asigna etiquetas de cluster a cada viaje
- Genera visualizaciones de clusters

**Parámetros** (en `config.jsonc`):
```jsonc
"clustering_settings": {
  "origins": {
    "stage_1": { "eps": 400, "min_samples": 15 },
    "stage_2": { "eps": 150, "min_samples": 10 }
  },
  "destinations": {
    "stage_1": { "eps": 400, "min_samples": 15 },
    "stage_2": { "eps": 150, "min_samples": 10 }
  }
}
```

**Entrada**: `Results/2_zoned_{territorio}.csv`
**Salida**: `Results/3_clustered_{territorio}.csv`

---

### 4. `extract_cluster_info.py`
**Propósito**: Extrae información detallada de los clusters generados.

**Funciones**:
- Calcula centroides de clusters
- Calcula cobertura (porcentaje de viajes agrupados)
- Genera reportes en JSON, CSV y TXT
- Asigna colores a clusters para visualización

**Entrada**: `Results/3_clustered_{territorio}.csv`
**Salida**: 
- `Results/cluster_info_{territorio}.json`
- `Results/cluster_origins_info_{territorio}.csv`
- `Results/cluster_destinations_info_{territorio}.csv`
- `Results/cluster_report_{territorio}.txt`

---

### 5. `Representative_flows_super_paths.py`
**Propósito**: Agrega viajes similares en flujos representativos.

**Funciones**:
- Agrupa viajes con mismo origen y destino cluster
- Calcula flujos agregados (número de viajes por flujo)
- Genera visualizaciones de flujos

**Entrada**: `Results/3_clustered_{territorio}.csv`
**Salida**: `Results/4_flows_{territorio}.csv`

---

### 6. `Stratified_sampling.py`
**Propósito**: Selecciona una muestra representativa de 500 rutas para simulación.

**Funciones**:
- Muestreo estratificado por flujos
- Asegura representatividad de clusters importantes
- Balancea muestreo entre orígenes y destinos

**Tamaño de muestra**: 500 rutas (configurable en el script)

**Entrada**: 
- `Results/3_clustered_{territorio}.csv`
- `Results/4_flows_{territorio}.csv`

**Salida**: `Results/5_final_sample_{territorio}.csv`

---

### 7. `real_path_simulation.py`
**Propósito**: Simula el consumo energético real de cada ruta usando OpenRouteService API.

**Funciones**:
- Obtiene ruta real de OpenRouteService
- Obtiene perfil de elevación
- Calcula consumo energético usando modelo físico
- Guarda resultados en JSON

**Modelo de Consumo**:
- Usa `HybridBikeConsumptionModel/Modelo_moto.py`
- Considera: pendiente, velocidad, aceleración, resistencia del aire, fricción

**Caché**: Las rutas se guardan en `Route Cache/` para evitar llamadas duplicadas.

**Entrada**: `Results/5_final_sample_{territorio}.csv`
**Salida**: `Archivos de apoyo/milp_input_data.json`

**Tiempo estimado**: 1-3 horas (depende del número de rutas y límites de API)

---

### 8. `precompute_access_costs.py`
**Propósito**: Pre-calcula el costo energético de viajes de acceso (destino → estación de carga).

**Funciones**:
- Genera malla de celdas candidatas para estaciones
- Calcula costo energético de cada viaje de acceso
- Almacena resultados en JSON para optimización rápida

**Entrada**: 
- `Archivos de apoyo/milp_input_data.json`
- `Limites {Territorio}/{Territorio}_Urbano_y_Rural.shp`

**Salida**: `Archivos de apoyo/access_trip_costs.json`

---

### 9. `Optimization_FCLP.py`
**Propósito**: Resuelve el problema de optimización MILP para ubicar estaciones.

**Modelo de Optimización**:
- **Variables de decisión**:
  - `x[j,t]`: ¿Se construye estación de tecnología `t` en celda `j`?
  - `y[i,j]`: ¿La ruta `i` se asigna a la estación en celda `j`?

- **Restricciones**:
  - Presupuesto total
  - Número de estaciones
  - Unidades de recursos disponibles
  - Cobertura (radio máximo)
  - Factibilidad energética (batería suficiente)
  - Restricciones zonales (opcional)

- **Función objetivo**: Maximizar utilidad ponderada (cobertura + distancia de viaje)

**Solver**: PuLP (usa CBC por defecto)

**Entrada**: 
- `Archivos de apoyo/milp_input_data.json`
- `Archivos de apoyo/access_trip_costs.json`
- `Archivos de apoyo/config.jsonc`
- `Limites {Territorio}/{Territorio}_Urbano_y_Rural.shp`

**Salida**: 
- `Results/optimal_solution_{territorio}.csv`
- `Results/optimal_locations_map_{territorio}.html` (mapa interactivo)

---

### 10. `extract_stations_info.py`
**Propósito**: Extrae información detallada de las estaciones optimizadas.

**Funciones**:
- Extrae coordenadas de cada estación
- Identifica tecnología asignada
- Calcula estadísticas de cobertura
- Genera reportes en JSON, CSV y TXT

**Entrada**: 
- `Results/optimal_solution_{territorio}.csv`
- `Archivos de apoyo/config.jsonc`

**Salida**: 
- `Results/stations_info_{territorio}.json`
- `Results/stations_detailed_{territorio}.csv`
- `Results/stations_report_{territorio}.txt`

---

## Scripts Auxiliares y de Visualización

### Scripts de Visualización

#### `visualize_route_map.py`
Genera un mapa HTML interactivo con las 500 rutas seleccionadas.

```bash
python visualize_route_map.py
```

#### `visualize_summary.py`
Genera gráficas analizando consumo de combustible, tiempo de trayecto y distancia.

```bash
python visualize_summary.py
```

#### `gridvizualization.py`
Visualiza la malla de celdas sobre el territorio.

```bash
python gridvizualization.py
```

#### `generate_stations_map.py`
Genera mapas de estaciones optimizadas.

```bash
python generate_stations_map.py
```

### Scripts de Análisis

#### `generate_results_table.py`
Genera tablas de resultados en formato LaTeX o CSV.

```bash
python generate_results_table.py
```

#### `generate_stations_latex_table.py`
Genera tablas LaTeX de estaciones.

```bash
python generate_stations_latex_table.py
```

#### `calculate_coverage_all_territories.py`
Calcula cobertura para todos los territorios.

```bash
python calculate_coverage_all_territories.py
```

---

## Solución de Problemas

### Error: "Config file not found"
**Solución**: Verifica que `Archivos de apoyo/config.jsonc` existe y está en la ubicación correcta.

### Error: "API key not found"
**Solución**: Agrega tu API key de OpenRouteService en `config.jsonc`:
```jsonc
"ors_api_key": "TU_API_KEY_AQUI"
```

### Error: "Input file not found"
**Solución**: Asegúrate de ejecutar los scripts en orden. Cada script depende de la salida del anterior.

### Error: "Shapefile not found"
**Solución**: Verifica que los shapefiles están en las carpetas correctas:
- `Limites Medellin/Medellin_Urbano_y_Rural.shp`
- `Limites Valle de Aburra/Valle_De_Aburra_Urbano_y_Rural.shp`
- `Limites Bogota DC/Bogota_Urbano_y_Rural.shp`

### Error: "Module not found"
**Solución**: Instala las dependencias:
```bash
pip install -r requirements.txt
```

### La simulación tarda mucho tiempo
**Normal**: La simulación de rutas puede tardar 1-3 horas. El script usa caché para evitar llamadas duplicadas.

### Error de límites de API
**Solución**: OpenRouteService tiene límites de llamadas. Considera:
- Usar una API key con mayor límite
- Esperar entre ejecuciones
- Reducir el tamaño de muestra en `Stratified_sampling.py`

---

## Notas Importantes

1. **Orden de Ejecución**: Los scripts deben ejecutarse en orden. El pipeline automático (`main_pipeline.py`) maneja esto automáticamente.

2. **Variables de Entorno**: Al ejecutar scripts manualmente, asegúrate de configurar `ANALYSIS_LOCALE`:
   ```bash
   set ANALYSIS_LOCALE=Medellin  # Windows
   export ANALYSIS_LOCALE=Medellin  # Linux/Mac
   ```

3. **Caché de Rutas**: Las rutas simuladas se guardan en `Route Cache/` para evitar llamadas duplicadas a la API.

4. **Resultados Intermedios**: Todos los resultados intermedios se guardan en `Results/` con nombres estandarizados.

5. **Configuración**: Todos los parámetros importantes están en `config.jsonc`. Modifica este archivo para ajustar el modelo.

6. **Resultados**: Si se desea consultar resultados previos, en la carpeta 'Results' se pueden encontrar archivos .zip que permiten ver como mapa interactivo las rutas de cada ciudad.

---

## Referencias

- **OpenRouteService**: https://openrouteservice.org/
- **PuLP (Optimización)**: https://github.com/coin-or/pulp
- **DBSCAN Clustering**: https://scikit-learn.org/stable/modules/clustering.html#dbscan
- **Geopandas**: https://geopandas.org/

---

## Licencia

Este proyecto es parte de un proyecto de investigación académica.

---

## Soporte

Para problemas o preguntas, revisa:
1. Los mensajes de error en la consola
2. Los archivos de log en `Results/`
3. La documentación de cada script (comentarios en el código)

---

---

**Fin del documento**

