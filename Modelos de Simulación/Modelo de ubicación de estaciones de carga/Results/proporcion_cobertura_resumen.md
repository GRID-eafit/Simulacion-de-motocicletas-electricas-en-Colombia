# Proporción de Cobertura de Clusters por Caso de Estudio

## Resumen Ejecutivo

Este documento presenta las proporciones de cobertura de clusters (agrupaciones geográficas) para los tres casos de estudio: **Bogotá**, **Medellín** y **Valle de Aburrá**.

---

## 📊 MEDELLÍN

### Estadísticas Generales
- **Total de viajes**: 4,253
- **Clusters de orígenes identificados**: 27
- **Clusters de destinos identificados**: 34

### Cobertura de Orígenes
- **Viajes con cluster**: 3,735 viajes
- **Proporción de cobertura**: **87.82%**
- **Viajes sin cluster (ruido)**: 518 viajes (12.18%)

### Cobertura de Destinos
- **Viajes con cluster**: 3,742 viajes
- **Proporción de cobertura**: **87.98%**
- **Viajes sin cluster (ruido)**: 511 viajes (12.02%)

### Cobertura Completa (Origen y Destino)
- **Viajes con ambos clusters**: 3,370 viajes
- **Proporción de cobertura completa**: **79.24%**
- **Viajes sin cobertura completa**: 883 viajes (20.76%)

---

## 📊 BOGOTÁ

*Nota: Los datos detallados se calcularán al ejecutar el script `extract_cluster_info.py` para Bogotá.*

Para obtener las estadísticas completas de Bogotá, ejecuta:
```bash
python extract_cluster_info.py Bogota
```

---

## 📊 VALLE DE ABURRÁ

*Nota: Los datos detallados se calcularán al ejecutar el script `extract_cluster_info.py` para Valle de Aburrá.*

Para obtener las estadísticas completas de Valle de Aburrá, ejecuta:
```bash
python extract_cluster_info.py "Valle de aburra"
```

---

## 📈 Interpretación de las Métricas

### ¿Qué significa "Cobertura de Orígenes"?
- Indica el porcentaje de viajes cuyo **punto de origen** fue agrupado exitosamente en un cluster.
- Un valor alto (ej: >85%) indica que la mayoría de los orígenes están geográficamente concentrados.

### ¿Qué significa "Cobertura de Destinos"?
- Indica el porcentaje de viajes cuyo **punto de destino** fue agrupado exitosamente en un cluster.
- Un valor alto (ej: >85%) indica que la mayoría de los destinos están geográficamente concentrados.

### ¿Qué significa "Cobertura Completa"?
- Indica el porcentaje de viajes donde **tanto el origen como el destino** fueron agrupados en clusters.
- Esta es la métrica más estricta y útil para planificación, ya que representa viajes completamente "clustereados".

### ¿Qué son los "Viajes de Ruido"?
- Son viajes cuyos puntos (origen o destino) están demasiado dispersos o aislados para formar parte de un cluster.
- Pueden representar viajes atípicos, rutas poco comunes, o puntos geográficamente aislados.

---

## 🔍 Cómo Calcular las Estadísticas

Para calcular las estadísticas de cobertura para todos los casos de estudio, ejecuta:

```bash
# Opción 1: Script individual por territorio
python extract_cluster_info.py Bogota
python extract_cluster_info.py Medellin
python extract_cluster_info.py "Valle de aburra"

# Opción 2: Script que procesa todos los territorios
python process_territories.py
```

Los resultados se guardarán en:
- `Results/cluster_info_{territorio}.json`
- `Results/cluster_report_{territorio}.txt`

---

## 📋 Archivos de Referencia

- **Medellín**: `Results/cluster_info_Medellin.json`
- **Bogotá**: Se generará al ejecutar el script
- **Valle de Aburrá**: Se generará al ejecutar el script

---

**Última actualización**: Basado en los datos disponibles de Medellín. Los datos de Bogotá y Valle de Aburrá se calcularán al ejecutar los scripts correspondientes.



