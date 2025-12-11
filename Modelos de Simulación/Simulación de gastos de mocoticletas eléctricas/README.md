# Simulación de Costos de Viajes en Motocicleta

Este paquete contiene todo lo necesario para ejecutar la simulación de cálculo de costos de viajes en motocicleta (eléctrica vs. combustión) con análisis de impacto en la canasta familiar.

## Descripción

La simulación selecciona aleatoriamente un viaje de motocicleta de la base de datos de la Encuesta de Movilidad (EOD 2017), calcula coordenadas aleatorias dentro de los municipios de origen y destino, obtiene rutas reales usando OSRM, y calcula:

- Consumo energético (kWh para eléctrica, galones para combustión)
- Costos del viaje (ida y vuelta)
- Impacto en la canasta familiar (% del gasto mensual)
- Características de la moto durante el recorrido
- Mapa HTML interactivo de la ruta

## Estructura de Archivos

```
simulacion_costos_motos/
├── calcular_costo_viaje_aleatorio.py  # Script principal
├── modelo_motocicleta_electrica/      # Modelo de consumo de motocicletas
│   ├── procesar_rutas.py              # Funciones de cálculo de consumo
│   └── HybridBikeConsumptionModel/    # Parámetros del modelo
├── ZONAS SIT.*                         # Shapefiles de Medellín y Área Metropolitana
├── zat.*                               # Shapefiles de Bogotá
├── ENPH_Rev.xlsx                       # Datos de canasta familiar
├── viajes_motos_procesados.csv        # Base de datos de viajes en moto
├── requirements.txt                    # Dependencias de Python
└── README.md                           # Este archivo
```

## Instalación

### 1. Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### 2. Instalar Dependencias

```bash
pip install -r requirements.txt
```

**Nota para macOS/Linux:** Si tienes problemas instalando `geopandas` o `fiona`, es posible que necesites instalar las dependencias del sistema primero:

**macOS:**
```bash
brew install gdal
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get install gdal-bin libgdal-dev
```

## Uso

### Ejecución Básica

Simplemente ejecuta el script principal:

```bash
python calcular_costo_viaje_aleatorio.py
```

### ¿Qué hace el script?

1. **Carga los datos necesarios:**
   - Shapefiles de zonas geográficas (ZONAS SIT para Medellín, ZAT para Bogotá)
   - Base de datos de viajes en motocicleta procesados
   - Datos de canasta familiar por estrato y ciudad

2. **Selecciona un viaje aleatorio:**
   - Filtra viajes con estrato válido
   - Asegura que origen y destino sean de la misma ciudad (Bogotá o MedellínAM)
   - Selecciona un viaje aleatorio

3. **Obtiene coordenadas:**
   - Genera coordenadas aleatorias dentro del municipio de origen
   - Genera coordenadas aleatorias dentro del municipio de destino

4. **Calcula la ruta:**
   - Usa OSRM (Open Source Routing Machine) para obtener rutas reales por carretera
   - Calcula distancia y duración para ida y vuelta

5. **Calcula consumo y costos:**
   - Consumo eléctrico (kWh) para motocicleta eléctrica
   - Consumo de gasolina (galones) para motocicleta a combustión
   - Costos con rangos de precios:
     - Gasolina: $16,200 - $16,400 COP/galón
     - Electricidad: $780 - $1,200 COP/kWh

6. **Analiza impacto en canasta familiar:**
   - Calcula gasto mensual (gasto diario × 30 días)
   - Calcula porcentaje respecto al gasto_total de la canasta familiar

7. **Genera visualizaciones:**
   - Mapa HTML interactivo (`ruta_viaje_mapa.html`)
   - Gráfica de características de la moto (`grafica_caracteristicas_moto.png`)

## Archivos de Salida

Después de ejecutar el script, se generarán:

- **`ruta_viaje_mapa.html`**: Mapa interactivo con las rutas de ida y vuelta, marcadores de origen/destino, y panel de información del viaje.

- **`grafica_caracteristicas_moto.png`**: Gráfica con 6 paneles mostrando:
  - Velocidad durante el recorrido
  - Potencia eléctrica requerida
  - Pendiente del terreno
  - Perfil de elevación
  - Fuerzas que actúan sobre la moto
  - Estadísticas del recorrido

## Configuración

### Precios de Combustible y Electricidad

Los precios están definidos en el script (líneas ~460-463):

```python
precio_gasolina_min = 16200  # COP por galón
precio_gasolina_max = 16400  # COP por galón
precio_kwh_min = 780  # COP por kWh
precio_kwh_max = 1200  # COP por kWh
```

Puedes modificar estos valores según necesites.

### Servicio de Routing (OSRM)

El script usa el servicio público de OSRM (`http://router.project-osrm.org`). Si necesitas usar un servidor propio, modifica la función `obtener_ruta_osrm()` (línea ~190).

## Datos Requeridos

### Archivos Necesarios

1. **`viajes_motos_procesados.csv`**: Base de datos de viajes en motocicleta con columnas:
   - `Ciudad_Municipio`
   - `ESTRATO`
   - `Municipio_Origen`
   - `Municipio_Destino`
   - `Motivo_Viaje`

2. **`ENPH_Rev.xlsx`**: Archivo Excel con hoja `Gasto_Motos` que contiene:
   - `Ciudad`
   - `Estrato`
   - `gasto_total` (canasta familiar)

3. **Shapefiles**: Archivos `.shp`, `.shx`, `.dbf`, `.prj` (y opcionales `.cpg`, `.qix`, `.xml`) para:
   - `ZONAS SIT`: Zonas de Medellín y Área Metropolitana
   - `zat`: Zonas de Bogotá

## Solución de Problemas

### Error: "No se encontró la carpeta 'modelo_motocicleta_electrica'"

Asegúrate de que la carpeta `modelo_motocicleta_electrica` esté en el mismo directorio que el script.

### Error: "No se pudo importar procesar_rutas"

Verifica que el archivo `modelo_motocicleta_electrica/procesar_rutas.py` exista y tenga las funciones `consum` y `preprocesar_vectores`.

### Error al cargar shapefiles

Asegúrate de que todos los archivos del shapefile estén presentes (`.shp`, `.shx`, `.dbf`, `.prj`).

### Error de conexión con OSRM

El script tiene un mecanismo de respaldo que usa distancia geodésica si OSRM no está disponible. Si el problema persiste, verifica tu conexión a internet.

## Notas

- El script selecciona viajes aleatorios, por lo que cada ejecución puede dar resultados diferentes.
- Los cálculos de consumo están basados en un modelo físico de motocicleta con parámetros específicos (masa, coeficiente de arrastre, etc.).
- Las rutas se obtienen de OSRM, que proporciona rutas reales por carretera cuando está disponible.

## Soporte

Para problemas o preguntas, revisa los comentarios en el código o consulta la documentación de las librerías utilizadas.

## Licencia

Este código es parte de un proyecto de investigación sobre consumo energético en motocicletas.

