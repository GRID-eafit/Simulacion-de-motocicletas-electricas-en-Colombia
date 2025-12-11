# Simulador de Consumo para Motocicletas Eléctricas en Entornos Urbanos

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688.svg)](https://fastapi.tiangolo.com/)

Plataforma web interactiva para simular el consumo energético de motocicletas eléctricas en entornos urbanos colombianos.

Desarrollado por el **Semillero GRID** de la Universidad EAFIT, en colaboración con el **Banco Interamericano de Desarrollo (BID)**.

---

## Descripción

Esta plataforma permite a los usuarios simular el comportamiento energético de motocicletas eléctricas en rutas urbanas reales. Los usuarios pueden:

- Seleccionar rutas sobre un mapa interactivo
- Definir parámetros de simulación (número de vehículos, tipo de perfil, etc.)
- Visualizar indicadores de consumo, autonomía y comportamiento energético
- Identificar puntos óptimos de recarga

La herramienta utiliza datos geoespaciales, ruteo externo mediante **OpenRouteService (ORS)** y modelos físicos de consumo desarrollados por GRID para generar resultados precisos y realistas.

---

## Características

-  **Mapa interactivo** con soporte para Medellín, Bogotá y AMVA
-  **Cálculo de consumo energético** punto a punto basado en modelos físicos
-  **Indicadores en tiempo real**: SOC, potencia consumida, distancia, tiempo estimado
-  **Identificación automática** de estaciones de carga disponibles
-  **Recálculo inteligente** cuando la batería está por agotarse
-  **Visualización de métricas** de desempeño y eficiencia
-  **Integración con tráfico** (en desarrollo)
-  **Rutas reales** generadas con OpenRouteService

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
├── docs/                                # Documentación adicional
├── README.md
└── LICENSE
```

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
```

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

- **ORS_TOKEN**: Regístrate en [OpenRouteService](https://openrouteservice.org/dev/#/signup) para obtener una API key gratuita
- **AZURE_TOKEN**: Contacta al equipo de GRID o revisa la documentación interna

---

## Uso

### Iniciar el Backend

```bash
cd server
python -m uvicorn main:app --reload --port 8000
```

El backend estará disponible en:
- **API**: http://localhost:8000
- **Documentación automática (Swagger)**: http://localhost:8000/docs
- **Documentación alternativa (ReDoc)**: http://localhost:8000/redoc

### Iniciar el Frontend

```bash
cd client
npm run dev
```

El frontend estará disponible en:
- **Aplicación**: http://localhost:5173

---

## Flujo de la Aplicación

1. **Selección de parámetros**: El usuario ingresa al frontend y configura:
   - Ciudad (Medellín, Bogotá o AMVA)
   - Número de motocicletas
   - Puntos del recorrido en el mapa
   - Tipo de perfil de conducción
   - Uso de tráfico en tiempo real 

2. **Solicitud al backend**: El frontend envía la configuración mediante HTTP POST

3. **Procesamiento**:
   - Consulta de rutas optimizadas en OpenRouteService y Azure Maps
   - Análisis de pendientes, distancias y velocidades
   - Ejecución del modelo físico de consumo energético
   - Cálculo de indicadores y puntos de recarga óptimos

4. **Respuesta**: El backend devuelve:
   - Geometría de la ruta en formato GeoJSON
   - Métricas de desempeño energético
   - Puntos de recarga recomendados
   - Indicadores de autonomía

5. **Visualización**: El frontend muestra los resultados en:
   - Mapa interactivo con la ruta trazada
   - Paneles informativos con métricas
   - Gráficos de consumo y SOC

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
- `ciudad`: `medellin` | `bogota` | `amva`

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

## Indicadores Calculados

- **SOC (State of Charge)**: Nivel de carga de la batería en porcentaje
- **Potencia consumida**: Energía utilizada en cada segmento (kW)
- **Distancia recorrida**: Kilometraje total y parcial
- **Tiempo estimado**: Duración del trayecto
- **Puntos de recarga**: Ubicaciones óptimas para recargar
- **Autonomía restante**: Distancia que se puede recorrer con la carga actual
- **Eficiencia energética**: Consumo promedio por kilómetro
---

## Créditos

**Proyecto desarrollado por:**
- **Universidad EAFIT**

**En colaboración con:**
- **Banco Interamericano de Desarrollo (BID)**

**Autores:**
- Ana María Ortega Álvarez
- Felipe Mendoza Giraldo
- Gustavo Adolfo García Cruz
- John Jairo García Rendón
- José Fernando Martínez Cadavid
- José Miguel Arias Mejía
- Juan Manuel Aristizábal Tamayo
- Juan Pablo González Alzate
- Santiago Bernal del Río

   **Monitores:**  
      - Nicolás Ospina Torres  
      - Alejandro Garcés Ramírez  
  
**Coordinador:**
Gilberto Osorio Gómez

---

## Licencia


---
