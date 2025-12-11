# Significado de los Colores de los Clusters

## Resumen General

Los colores en los mapas de clusters **NO representan una característica específica de los datos** (como densidad, importancia, o cantidad de viajes). En su lugar, son una **escala visual continua** asignada automáticamente por el algoritmo de visualización para distinguir diferentes clusters.

---

## Clusters de ORÍGENES (Colormap: VIRIDIS)

### Escala de Colores
- **Amarillo-Verde claro** → Clusters con IDs más bajos (primeros en la lista ordenada)
- **Verde** → Clusters intermedios
- **Azul** → Clusters intermedios-altos
- **Púrpura-Azul oscuro** → Clusters con IDs más altos (últimos en la lista ordenada)

### Características
- **Colormap**: `viridis`
- **Rango**: De amarillo-verde claro (valores bajos) a púrpura-azul oscuro (valores altos)
- **Propósito**: Distinguir visualmente diferentes clusters de orígenes
- **Nota importante**: El color NO indica importancia, densidad o cantidad de viajes. Solo es una etiqueta visual para diferenciar clusters.

### Ejemplo Visual
```
Cluster ID 0  → Color: Púrpura oscuro (#440154) - Primer cluster identificado
Cluster ID 1  → Color: Púrpura (#460e61)
Cluster ID 2  → Color: Púrpura claro (#481c6e)
...
Cluster ID N  → Color: Amarillo-verde claro - Último cluster identificado
```

---

## Clusters de DESTINOS (Colormap: PLASMA)

### Escala de Colores
- **Púrpura oscuro** → Clusters con IDs más bajos (primeros en la lista ordenada)
- **Rosa** → Clusters intermedios
- **Amarillo claro** → Clusters con IDs más altos (últimos en la lista ordenada)

### Características
- **Colormap**: `plasma`
- **Rango**: De púrpura oscuro (valores bajos) a amarillo claro (valores altos)
- **Propósito**: Distinguir visualmente diferentes clusters de destinos
- **Nota importante**: El color NO indica importancia, densidad o cantidad de viajes. Solo es una etiqueta visual para diferenciar clusters.

### Ejemplo Visual
```
Cluster ID 0  → Color: Púrpura oscuro - Primer cluster identificado
Cluster ID 1  → Color: Púrpura
Cluster ID 2  → Color: Rosa púrpura
...
Cluster ID N  → Color: Amarillo claro - Último cluster identificado
```

---

## Puntos de RUIDO (NOISE) - Color GRIS

### Características
- **Color**: Gris uniforme (#808080)
- **Significado**: Puntos que **NO pertenecen a ningún cluster**
- **Causa**: Estos puntos están demasiado dispersos o aislados para formar un cluster según los parámetros del algoritmo DBSCAN
- **Visualización**: Se muestran con marcadores más pequeños y transparencia (alpha=0.5)

### ¿Por qué aparecen puntos de ruido?
- Los puntos están muy dispersos geográficamente
- No hay suficientes puntos cercanos para formar un cluster (según `min_samples`)
- Están fuera del radio de agrupación (`eps`) de otros puntos

---

## ¿Qué SÍ Indican los Colores?

### ✅ Lo que SÍ representan:
1. **Diferenciación visual**: Cada color único identifica un cluster diferente
2. **Orden de identificación**: Los colores se asignan según el orden en que se identificaron los clusters
3. **Agrupación geográfica**: Todos los puntos del mismo color pertenecen al mismo cluster (misma zona geográfica)

### ❌ Lo que NO representan:
1. **Importancia**: Un cluster púrpura NO es más importante que uno amarillo
2. **Densidad**: El color NO indica cuántos viajes tiene el cluster
3. **Calidad**: El color NO indica si es un "buen" o "mal" cluster
4. **Prioridad**: El color NO indica prioridad para ubicar estaciones

---

## Información Real de los Clusters

Para obtener información **real** sobre los clusters, consulta:

1. **Número de viajes** (`num_trips`): Indica cuántos viajes pertenecen a cada cluster
2. **Coordenadas del centroide**: Ubicación geográfica promedio del cluster
3. **ID del cluster**: Identificador único del cluster
4. **Estadísticas de cobertura**: Porcentaje de viajes que están en clusters vs. ruido

---

## Ejemplo Práctico

### Cluster de Origen (Viridis)
- **Cluster ID 0**: Color púrpura oscuro (#440154)
  - Centroide: Lat 6.259, Lon -75.580
  - Viajes: 3,125
  - **Interpretación**: Es el cluster más grande (más viajes), pero el color púrpura solo indica que fue el primero identificado, no su importancia.

### Cluster de Destino (Plasma)
- **Cluster ID 0**: Color púrpura oscuro
  - Centroide: Lat 6.250, Lon -75.570
  - Viajes: 2,800
  - **Interpretación**: Cluster importante por cantidad de viajes, pero el color solo indica orden de identificación.

---

## Recomendaciones para Interpretación

1. **No uses el color para priorizar**: Usa el número de viajes (`num_trips`) para identificar clusters importantes
2. **Consulta las estadísticas**: Revisa los archivos JSON/CSV generados para información detallada
3. **Usa el color como etiqueta**: El color es útil para identificar visualmente qué puntos pertenecen al mismo cluster en el mapa
4. **Considera el ruido**: Los puntos grises (ruido) pueden ser importantes si representan una proporción significativa de viajes

---

## Archivos de Referencia

Para información detallada sobre cada cluster, consulta:
- `cluster_info_{territorio}.json` - Información completa en JSON
- `cluster_origins_info_{territorio}.csv` - Tabla de clusters de orígenes
- `cluster_destinations_info_{territorio}.csv` - Tabla de clusters de destinos
- `cluster_report_{territorio}.txt` - Reporte en texto plano

---

**Nota Final**: Los colores son una herramienta de visualización, no un indicador de valor o importancia. Para análisis real, consulta las métricas numéricas de cada cluster.

