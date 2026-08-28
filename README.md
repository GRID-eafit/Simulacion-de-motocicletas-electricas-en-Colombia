# Herramienta de simulación de motocicletas eléctricas en entornos urbanos

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

Proyecto: **Análisis de indicadores de impacto técnicos,económicos, sociales, ambientales, regulatorios y aspectos de seguridad vial asociados a la inclusión de motocicletas eléctricas o híbridas de bajo cilindraje en el sector transporte en Colombia.**

Plataforma web interactiva para simular motocicletas eléctricas en entornos urbanos colombianos.


Universidad EAFIT
Escuela de Ciencias Aplicadas e Ingeniería - Grupo de Investigación en Ingeniería de Diseño (GRID)
Escuela de Finanzas, Economía y Gobierno - Observatorio de Mercados y Empresas: Guía y Aplicaciones (OMEGA)
Banco Interamericano de Desarrollo (BID)

---

## Descripción

Esta plataforma permite analizar y simular el desempeño de motocicletas eléctricas en escenarios urbanos reales. Los usuarios pueden:

- Configurar y simular recorridos individuales o múltiples vehículos sobre mapas interactivos
- Analizar consumo energético, autonomía, estado de carga, potencia, emisiones y necesidades de recarga
- Comparar resultados de simulación con datos reales mediante el módulo de telemetría
- Optimizar rutas para flotillas considerando autonomía e intercambios de batería
- Estimar y comparar los costos de operación de motocicletas eléctricas y de combustión

La herramienta integra datos geoespaciales, servicios de ruteo, condiciones de tráfico, modelos físicos de consumo y componentes de optimización desarrollados por EAFIT para generar resultados técnicos, energéticos, ambientales y económicos.

---

## Características

- **Mapa interactivo** con soporte para Medellín, Bogotá y el Área Metropolitana del Valle de Aburrá (AMVA).
- **Simulación de múltiples motocicletas** y configuración de escenarios con diferentes rutas y condiciones de operación.
- **Cálculo de consumo energético punto a punto**, basado en modelos físicos y características del recorrido.
- **Indicadores de desempeño energético:** estado de carga (SoC), potencia, consumo, distancia, duración y emisiones equivalentes de CO₂.
- **Identificación automática de puntos y necesidades de recarga**, incluyendo el cálculo de energía y tiempo de carga requeridos.
- **Visualización de estaciones de carga** y recálculo de rutas cuando la autonomía disponible es insuficiente.
- **Análisis mediante gráficos e indicadores** para evaluar el comportamiento energético y comparar múltiples vehículos.
- **Módulo de telemetría** para visualizar y analizar recorridos reales a partir de archivos registrados.
- **Optimización de rutas para flotillas**, considerando autonomía, secuencia de visitas e intercambios de batería.
- **Modelo comparativo de costos** entre motocicletas eléctricas y de combustión, según las características territoriales y socioeconómicas del viaje.
- **Integración con condiciones de tráfico** para representar escenarios de operación más realistas.
- **Rutas reales** generadas mediante OpenRouteService (ORS) e integración de información geoespacial.
- Exportación e importación de datos mediante formatos JSON y GeoJSON.
- Documentación técnica integrada para facilitar la implementación, mantenimiento e integración mediante API.

---

## Tecnologías

### Frontend
- **React 18+** con Vite
- **Leaflet** para visualización de mapas
- **Axios** para comunicación HTTP
- **CSS Modules** / TailwindCSS (según configuración)

### Backend
- **Python 3.10+**
- **FastAPI** para API REST
- **Uvicorn** como servidor ASGI
- **OpenRouteService API** para generación de rutas
- **NumPy/Pandas** para procesamiento de datos
- Modelos físicos de consumo energético desarrollados por GRID

---

## Estructura del Proyecto

```

/
├── client/                              # Frontend React
│   ├── src/
│   │   ├── components/                  # Componentes reutilizables
│   │   ├── pages/                       # Vistas principales
│   │   ├── services/                    # Servicios API
│   │   └── App.jsx                      # Componente principal
│   ├── public/
│   ├── package.json
│   └── vite.config.js
│
├── server/                              # Backend FastAPI
│   ├── main.py                          # Punto de entrada del servidor
│   ├── consume.py                       # Motor de simulación energética
│   ├── moto.py                          # Lógica del vehículo eléctrico
│   ├── petitions.py                     # Integración con OpenRouteService y Azure
│   ├── resources/                       # Datos de estaciones y ejemplos
│   ├── utils.py                         # Métodos auxiliares
│   ├── HybridBikeConsumptionModel/      # Parámetros de las motocicletas
│   ├── requirements.txt
│   └── .env.example
│
├── Modelos de Simulación/
│   ├── Modelo de costos
│   ├── Modelo de crecimiento vehicular de Gompertz
│   ├── Modelo de ubicación de estaciones de carga
│   ├── Simulación de gastos de motocicletas eléctricas
│
├── Informe - Herramienta de simulación _ Contrato BID #RG-T4200-P007, ATN_OC-19711-RG _ Universidad EAFIT
│
├── README.md
│
└── LICENSE

````

---

## Requisitos Previos

Asegúrate de tener instalado:

- **Node.js** ≥ 18.x ([Descargar](https://nodejs.org/))
- **Python** ≥ 3.10 ([Descargar](https://www.python.org/downloads/))
- **pip** (gestor de paquetes de Python)
- **git** para clonar el repositorio
- **(Opcional)** `virtualenv` o `venv` para entornos virtuales

---

## Instalación

### 1. Clonar el repositorio

```bash
git clone https://github.com/niosto/electric-bikes-routes-simulation
cd repositorio
````

### 2. Configurar el Backend

```bash
cd server

# Crear entorno virtual (recomendado)
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En macOS/Linux:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar el Frontend

```bash
cd client

# Instalar dependencias
npm install
```

---

## Configuración

### Variables de Entorno

Crea un archivo `.env` dentro de la carpeta `server/` con las siguientes claves:

```env
AZURE_TOKEN=tu_token_de_azure
ORS_TOKEN=tu_token_de_openrouteservice
```

> **Nota**: Ambas claves son obligatorias para la funcionalidad completa del backend.

**¿Dónde obtener los tokens?**

* **ORS_TOKEN**: Regístrate en [OpenRouteService](https://openrouteservice.org/dev/#/signup) para obtener una API key gratuita
* **AZURE_TOKEN**: Contacta al equipo de GRID o revisa la documentación interna

---

### Variables de Entorno (Frontend)

El frontend está construido con **Vite**, por lo que todas las variables de entorno utilizadas en el cliente deben comenzar con el prefijo `VITE_`.

#### 1. Crear archivo `.env` en `client/`

Crea un archivo llamado `.env` dentro de la carpeta `client/`:

**Ruta:**

```
client/.env
```

**Contenido (ejemplo en desarrollo local):**

```env
VITE_API_URL=la_url_base
```

Esta variable define la URL base del backend a la cual el frontend enviará las solicitudes HTTP.

#### 2. Reiniciar el servidor de Vite

Después de crear o modificar el archivo `.env`, es obligatorio reiniciar el frontend para que Vite cargue las variables:

```bash
# detener el servidor (Ctrl + C) y luego:
npm run dev
```

#### 3. Error común

Si aparece el error:

```
RAW_BASE is undefined
can't access property "replace"
```

significa que la variable `VITE_API_URL` no está definida correctamente o que el servidor de Vite no fue reiniciado después de crear el `.env`.

---

## Uso

### Iniciar el Backend

```bash
cd server
python -m uvicorn main:app --reload --port 8000
```

El backend estará disponible en:

* **API**: [http://localhost:8000](http://localhost:8000)
* **Documentación automática (Swagger)**: [http://localhost:8000/docs](http://localhost:8000/docs)
* **Documentación alternativa (ReDoc)**: [http://localhost:8000/redoc](http://localhost:8000/redoc)

### Iniciar el Frontend

```bash
cd client
npm run dev
```

El frontend estará disponible en:

* **Aplicación**: [http://localhost:5173](http://localhost:5173)

---

## Flujo de la Aplicación

La aplicación se organiza en diferentes módulos que permiten simular, analizar y optimizar el desempeño de motocicletas eléctricas.

1. **Acceso y selección del módulo**

El usuario inicia sesión y accede a los diferentes componentes de la plataforma:

* Simulación de recorridos y comportamiento energético
* Telemetría para el análisis de datos reales
* Optimización de flotilla para la planificación de circuitos
* Modelo de costos para comparar motocicletas eléctricas y de combustión
* Documentación técnica para consulta e integración con la API

2. **Configuración del escenario**

Dependiendo del módulo seleccionado, el usuario configura los parámetros necesarios. En el módulo de simulación puede definir:

* Ciudad o área de estudio (Medellín, Bogotá o AMVA)
* Número de motocicletas
* Puntos del recorrido directamente sobre el mapa
* Ubicación de estaciones de carga
* Condiciones de tráfico

En los demás módulos, puede cargar datos de telemetría, definir puntos de visita para una flotilla o seleccionar el origen y destino de un viaje para el análisis de costos.

3. **Solicitud al backend**

El frontend envía la configuración y los datos requeridos al backend mediante solicitudes HTTP y una arquitectura API REST, utilizando el formato JSON.

4. **Procesamiento**

Según el módulo seleccionado, el backend realiza:

* Consulta y generación de rutas mediante OpenRouteService y servicios geoespaciales
* Análisis de distancias, pendientes, velocidades y condiciones de tráfico
* Ejecución del modelo físico de consumo energético
* Cálculo del estado de carga, potencia, consumo, autonomía y emisiones equivalentes
* Identificación de necesidades y puntos de recarga
* Optimización de secuencias de visita para flotillas
* Estimación y comparación de costos entre tecnologías eléctricas y de combustión
* Procesamiento y análisis de datos reales de telemetría

5. **Respuesta**

El backend devuelve, según el módulo ejecutado:

* Geometrías y rutas en formato JSON o GeoJSON
* Métricas de desempeño energético y ambiental
* Indicadores de consumo, autonomía, potencia y estado de carga
* Información sobre eventos y necesidades de recarga
* Resultados de optimización de rutas y secuencias de visita
* Comparativas de costos y ahorro potencial
* Datos procesados para la visualización de telemetría

6. **Visualización y análisis**

Finalmente, el frontend presenta los resultados mediante:

* Mapas interactivos con rutas, puntos de interés y estaciones de carga
* Paneles informativos con indicadores clave
* Gráficos de potencia, velocidad, consumo, energía acumulada y estado de carga
* Comparaciones entre motocicletas y escenarios
* Visualización de resultados de optimización de flotillas
* Análisis comparativos de costos entre motocicletas eléctricas y de combustión

**Nota:** Para obtener una descripción más detallada sobre la arquitectura, funcionalidades, módulos, modelos implementados, flujo de operación y resultados de la plataforma, se recomienda consultar el documento “Informe - Herramienta de simulación | Contrato BID #RG-T4200-P007, ATN_OC-19711-RG | Universidad EAFIT”, el cual constituye el documento técnico de referencia para la implementación, operación y mantenimiento de la herramienta.

---

## API Endpoints

### `GET /health`

Verifica el estado del servidor y la disponibilidad del token ORS.

**Respuesta:**

```json
{
  "status": "healthy",
  "ors_available": true
}
```

### `GET /estaciones`

Devuelve las estaciones de carga disponibles por ciudad.

**Query params:**

* `ciudad`: `medellin` | `bogota` | `amva`

**Respuesta:**

```json
{
  "ciudad": "medellin",
  "estaciones": [...]
}
```

### `POST /routes`

Ejecuta la simulación de consumo energético.

**Body:**

```json
{
  "ciudad": "medellin",
  "num_motos": 1,
  "puntos": [[lat1, lon1], [lat2, lon2], ...],
  "perfil": "balanced",
  "usar_trafico": false
}
```

**Respuesta:**

```json
{
  "ruta": {...},
  "consumo": {...},
  "recargas": [...],
  "metricas": {...}
}
```

### `POST /routes/geojson`

Versión alternativa que recibe rutas completas en formato GeoJSON.

---

## Créditos

**Proyecto desarrollado por:**

* **Universidad EAFIT**

**En colaboración con:**

* **Banco Interamericano de Desarrollo (BID)**

**Autores:**

* Ana María Ortega Álvarez
* Felipe Mendoza Giraldo
* Gustavo Adolfo García Cruz
* John Jairo García Rendón
* José Fernando Martínez Cadavid
* José Miguel Arias Mejía
* Juan Manuel Aristizábal Tamayo
* Juan Pablo González Alzate
* Santiago Bernal del Río

  **Monitores:**
  - Nicolás Ospina Torres
  - Alejandro Garcés Ramírez

**Coordinador:**
Gilberto Osorio Gómez

---

## Licencia

---
