# Proporción de Cobertura de Clusters - Todos los Casos de Estudio

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

*Para obtener las estadísticas completas de Bogotá, ejecuta:*
```bash
python extract_cluster_info.py Bogota
```

O desde el directorio de Scripts:
```bash
cd "C:\Users\jpgonzala1\Desktop\P delfin V3.0\Proyecto Investigación Delfin 2025\Scripts"
python extract_cluster_info.py Bogota
```

Los resultados se guardarán en `Results/cluster_info_Bogota.json`

---

## 📊 VALLE DE ABURRÁ

*Para obtener las estadísticas completas de Valle de Aburrá, ejecuta:*
```bash
python extract_cluster_info.py "Valle de aburra"
```

O desde el directorio de Scripts:
```bash
cd "C:\Users\jpgonzala1\Desktop\P delfin V3.0\Proyecto Investigación Delfin 2025\Scripts"
python extract_cluster_info.py "Valle de aburra"
```

Los resultados se guardarán en `Results/cluster_info_Valle de aburra.json`

---

## 📈 Interpretación de las Métricas

### Cobertura de Orígenes
- **Definición**: Porcentaje de viajes cuyo punto de origen fue agrupado en un cluster
- **Interpretación**: 
  - >85% = Excelente cobertura (la mayoría de orígenes están concentrados)
  - 70-85% = Buena cobertura
  - <70% = Cobertura baja (muchos orígenes dispersos)

### Cobertura de Destinos
- **Definición**: Porcentaje de viajes cuyo punto de destino fue agrupado en un cluster
- **Interpretación**: Similar a cobertura de orígenes

### Cobertura Completa
- **Definición**: Porcentaje de viajes donde tanto origen como destino están en clusters
- **Interpretación**: 
  - >75% = Excelente (la mayoría de viajes están completamente clustereados)
  - 60-75% = Buena
  - <60% = Baja (muchos viajes con al menos un punto sin cluster)

### Viajes de Ruido
- **Definición**: Viajes cuyos puntos están demasiado dispersos para formar clusters
- **Causas posibles**:
  - Puntos geográficamente aislados
  - Rutas poco comunes
  - Parámetros de clustering muy estrictos

---

## 🔧 Cómo Calcular Todas las Estadísticas

### Opción 1: Script Individual
```bash
python extract_cluster_info.py Bogota
python extract_cluster_info.py Medellin
python extract_cluster_info.py "Valle de aburra"
```

### Opción 2: Script que Procesa Todos
```bash
python process_territories.py
```

### Opción 3: Script de Resumen
```bash
python calculate_coverage_all_territories.py
```

---

## 📋 Archivos Generados

Después de ejecutar los scripts, encontrarás:

### Para cada territorio:
- `cluster_info_{territorio}.json` - Información completa en JSON
- `cluster_origins_info_{territorio}.csv` - Tabla de clusters de orígenes
- `cluster_destinations_info_{territorio}.csv` - Tabla de clusters de destinos
- `cluster_report_{territorio}.txt` - Reporte en texto plano

### Resumen general:
- `coverage_summary_all_territories.json` - Resumen comparativo (se genera con `calculate_coverage_all_territories.py`)

---

## 📊 Ejemplo de Resultados (Medellín)

```
Total de viajes: 4,253

COBERTURA DE ORÍGENES:
   • Viajes con cluster: 3,735 (87.82%)
   • Viajes sin cluster (ruido): 518 (12.18%)
   • Número de clusters: 27

COBERTURA DE DESTINOS:
   • Viajes con cluster: 3,742 (87.98%)
   • Viajes sin cluster (ruido): 511 (12.02%)
   • Número de clusters: 34

COBERTURA COMPLETA (ORIGEN Y DESTINO):
   • Viajes con ambos clusters: 3,370 (79.24%)
   • Viajes sin cobertura completa: 883 (20.76%)
```

---

**Nota**: Los datos de Bogotá y Valle de Aburrá se calcularán al ejecutar los scripts correspondientes. El archivo `cluster_info_Medellin.json` ya contiene las estadísticas completas de Medellín.

