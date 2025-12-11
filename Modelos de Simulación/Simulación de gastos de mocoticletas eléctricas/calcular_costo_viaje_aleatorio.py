import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import Point
from shapely.ops import transform
import random
import sys
import os
import math
from geopy.distance import geodesic
import requests
import json
import time
import folium
import matplotlib.pyplot as plt

# Agregar ruta para importar funciones del modelo
ruta_procesar = os.path.join(os.path.dirname(__file__), 'modelo_motocicleta_electrica')
if os.path.exists(ruta_procesar):
    sys.path.append(ruta_procesar)
    try:
        from procesar_rutas import consum, preprocesar_vectores
    except ImportError as e:
        print(f"Advertencia: No se pudo importar procesar_rutas: {e}")
        raise
else:
    raise FileNotFoundError(f"No se encontró la carpeta 'modelo_motocicleta_electrica'")

# Cargar shapefiles
print("Cargando shapefiles...")
zonas_sit = gpd.read_file("ZONAS SIT.shp")
zat = gpd.read_file("zat.shp")

# Cargar datos de canasta familiar
print("Cargando datos de canasta familiar...")
try:
    gasto_motos = pd.read_excel("ENPH_Rev.xlsx", sheet_name='Gasto_Motos')
    print("  ✓ Datos de canasta familiar cargados")
except Exception as e:
    print(f"  ⚠ Error al cargar canasta familiar: {e}")
    gasto_motos = None

def determinar_ciudad_municipio(municipio_nombre):
    """
    Determina a qué ciudad pertenece un municipio.
    Retorna 'Bogotá', 'MedellínAM' o None si no se puede determinar.
    """
    municipio_lower = str(municipio_nombre).lower().strip()
    
    # Municipios de Bogotá
    municipios_bogota = ['bogotá', 'bogota', 'bogota d.c.', 'bogotá d.c.', 'soacha']
    
    # Municipios de Medellín y Área Metropolitana
    municipios_medellin = [
        'medellin', 'medellín', 'envigado', 'bello', 'itagui', 'itagüí',
        'caldas', 'copacabana', 'barbosa', 'la estrella', 'girardota',
        'girardotá', 'sabaneta', 'rionegro', 'guarne', 'marinilla',
        'el retiro', 'la ceja', 'san vicente', 'don matias', 'don matías',
        'yarumal', 'angostura', 'santa rosa', 'santa rosa de osos'
    ]
    
    if any(mun in municipio_lower for mun in municipios_bogota):
        return 'Bogotá'
    elif any(mun in municipio_lower for mun in municipios_medellin):
        return 'MedellínAM'
    else:
        return None

def obtener_coordenadas_aleatorias_municipio(municipio_nombre, zonas_sit, zat):
    """
    Obtiene coordenadas aleatorias dentro de un municipio usando los shapefiles.
    Busca primero en ZONAS SIT (Medellín y área metropolitana) y luego en ZAT (Bogotá).
    """
    municipio_nombre = str(municipio_nombre).strip()
    
    # Determinar a qué ciudad pertenece el municipio
    ciudad = determinar_ciudad_municipio(municipio_nombre)
    
    # Normalizar nombre del municipio para búsqueda
    municipio_lower = municipio_nombre.lower()
    
    # Si es Bogotá, usar ZAT
    if ciudad == 'Bogotá':
        # Para Bogotá, usar ZAT
        if len(zat) > 0:
            # Seleccionar una zona ZAT aleatoria
            zona_aleatoria = zat.sample(n=1).iloc[0]
            geometria = zona_aleatoria.geometry
            
            # Obtener bounding box
            bounds = geometria.bounds  # (minx, miny, maxx, maxy)
            
            # Generar puntos aleatorios hasta encontrar uno dentro del polígono
            max_intentos = 100
            for _ in range(max_intentos):
                lat = random.uniform(bounds[1], bounds[3])  # miny, maxy
                lon = random.uniform(bounds[0], bounds[2])  # minx, maxx
                punto = Point(lon, lat)
                
                if geometria.contains(punto):
                    return lat, lon
            
            # Si no se encontró punto dentro, usar el centroide
            centroide = geometria.centroid
            return centroide.y, centroide.x
    
    # Si es MedellínAM, buscar en ZONAS SIT
    if ciudad == 'MedellínAM':
        # Buscar en ZONAS SIT (Medellín y área metropolitana)
        # Verificar si hay alguna columna con nombre de municipio
        if 'Municipio' in zonas_sit.columns:
            municipios_sit = zonas_sit[zonas_sit['Municipio'].astype(str).str.lower().str.contains(municipio_lower, na=False, regex=False)]
        else:
            # Si no hay columna de municipio, buscar en todas las zonas
            municipios_sit = zonas_sit
        
        if len(municipios_sit) > 0:
            # Seleccionar una zona aleatoria del municipio
            zona_aleatoria = municipios_sit.sample(n=1).iloc[0]
            geometria = zona_aleatoria.geometry
            
            # Obtener bounding box
            bounds = geometria.bounds
            
            # Generar puntos aleatorios hasta encontrar uno dentro del polígono
            max_intentos = 100
            for _ in range(max_intentos):
                lat = random.uniform(bounds[1], bounds[3])
                lon = random.uniform(bounds[0], bounds[2])
                punto = Point(lon, lat)
                
                if geometria.contains(punto):
                    return lat, lon
            
            # Si no se encontró, usar el centroide
            centroide = geometria.centroid
            return centroide.y, centroide.x
    
    # Si no se encuentra en los shapefiles, usar coordenadas aproximadas conocidas
    
    # Si no se encuentra en los shapefiles, usar coordenadas aproximadas conocidas
    # (esto solo debería pasar si el municipio no está en los shapefiles)
    coordenadas_aprox = {
        'medellin': (6.2442, -75.5812),
        'medellín': (6.2442, -75.5812),
        'bogotá': (4.7110, -74.0721),
        'bogota': (4.7110, -74.0721),
        'envigado': (6.1696, -75.5781),
        'bello': (6.3373, -75.5579),
        'itagui': (6.1846, -75.5994),
        'caldas': (6.0917, -75.6353),
        'copacabana': (6.3464, -75.5081),
        'barbosa': (6.4381, -75.3319),
        'la estrella': (6.1575, -75.6431),
        'girardota': (6.3778, -75.4481),
        'sabaneta': (6.1514, -75.6164),
        'soacha': (4.5794, -74.2169),
        'la ceja': (6.0267, -75.4281),  # La Ceja del Tambo - Antioquia
        'rionegro': (6.1417, -75.3731),
        'guarne': (6.2803, -75.4431),
        'marinilla': (6.1731, -75.3381),
        'el retiro': (6.0617, -75.5031),
        'san vicente': (6.2803, -75.3331)
    }
    
    for key, coords in coordenadas_aprox.items():
        if key in municipio_lower:
            # Agregar pequeña variación aleatoria
            lat = coords[0] + random.uniform(-0.05, 0.05)
            lon = coords[1] + random.uniform(-0.05, 0.05)
            return lat, lon
    
    # Coordenadas por defecto (centro de Colombia)
    print(f"  ⚠ No se encontró municipio '{municipio_nombre}', usando coordenadas por defecto")
    return 4.7110 + random.uniform(-0.1, 0.1), -74.0721 + random.uniform(-0.1, 0.1)

def obtener_ruta_osrm(origin_lat, origin_lon, dest_lat, dest_lon):
    """
    Obtiene la ruta real por carretera más corta usando OSRM (Open Source Routing Machine).
    Retorna la ruta con coordenadas, distancia y duración reales.
    OSRM optimiza por tiempo por defecto, pero podemos obtener alternativas y elegir la más corta.
    """
    # URL del servicio público de OSRM
    # Formato: /route/v1/{profile}/{coordinates}?overview=full&geometries=geojson
    # profile puede ser: driving, walking, cycling
    base_url = "http://router.project-osrm.org/route/v1"
    profile = "driving"  # Usar 'driving' para motocicletas
    
    # Formato de coordenadas: lon,lat;lon,lat
    coordinates = f"{origin_lon},{origin_lat};{dest_lon},{dest_lat}"
    
    # Solicitar alternativas para obtener múltiples rutas y elegir la más corta
    # alternatives=true permite obtener hasta 3 rutas alternativas
    url = f"{base_url}/{profile}/{coordinates}?overview=full&geometries=geojson&steps=true&alternatives=true"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if data.get('code') == 'Ok' and len(data.get('routes', [])) > 0:
            # Obtener todas las rutas disponibles (principal + alternativas)
            rutas = data['routes']
            
            # Seleccionar la ruta más corta (menor distancia)
            ruta_mas_corta = min(rutas, key=lambda r: r['distance'])
            
            geometry = ruta_mas_corta['geometry']
            
            # Extraer coordenadas de la geometría GeoJSON
            # GeoJSON usa formato [lon, lat]
            coordenadas_ruta = []
            if geometry['type'] == 'LineString':
                for coord in geometry['coordinates']:
                    coordenadas_ruta.append([coord[1], coord[0]])  # Convertir a [lat, lon]
            
            # Distancia en metros, convertir a km
            distancia_metros = ruta_mas_corta['distance']
            distancia_km = distancia_metros / 1000.0
            
            # Duración en segundos
            duracion_segundos = ruta_mas_corta['duration']
            
            # Información adicional si hay múltiples rutas
            if len(rutas) > 1:
                distancias = [r['distance'] / 1000.0 for r in rutas]
                print(f"  ℹ {len(rutas)} rutas encontradas, seleccionada la más corta: {distancia_km:.2f} km (alternativas: {', '.join([f'{d:.2f}' for d in distancias[1:]])} km)")
            
            return {
                'coordenadas': coordenadas_ruta,
                'distancia_km': distancia_km,
                'duracion_segundos': duracion_segundos,
                'exito': True
            }
        else:
            print(f"  ⚠ OSRM no encontró ruta, usando método simple")
            return {'exito': False}
            
    except Exception as e:
        print(f"  ⚠ Error al obtener ruta de OSRM: {e}")
        print(f"  ⚠ Usando método de distancia geodésica como respaldo")
        return {'exito': False}

def obtener_ruta_simple(origin_lat, origin_lon, dest_lat, dest_lon, num_puntos=50):
    """
    Genera una ruta entre origen y destino.
    Primero intenta usar OSRM para obtener ruta real por carretera.
    Si falla, usa interpolación simple con distancia geodésica.
    """
    # Intentar obtener ruta real con OSRM
    ruta_osrm = obtener_ruta_osrm(origin_lat, origin_lon, dest_lat, dest_lon)
    
    if ruta_osrm.get('exito', False):
        # Usar ruta real de OSRM
        coordenadas_ruta = ruta_osrm['coordenadas']
        distancia_total = ruta_osrm['distancia_km']
        duracion_segundos = ruta_osrm['duracion_segundos']
        
        # Si hay muchas coordenadas, muestrear para reducir puntos
        if len(coordenadas_ruta) > num_puntos:
            indices = np.linspace(0, len(coordenadas_ruta) - 1, num_puntos, dtype=int)
            coordenadas_ruta = [coordenadas_ruta[i] for i in indices]
        
        # Extraer lats, lons y estimar altitud
        lats = [coord[0] for coord in coordenadas_ruta]
        lons = [coord[1] for coord in coordenadas_ruta]
        
        # Estimar altitud (en producción usar servicio de elevación)
        altitud_promedio = 1500  # Altitud promedio en Medellín/Bogotá
        alts = [altitud_promedio] * len(lats)
        
        # Calcular velocidades basadas en duración real
        tiempo_total_segundos = duracion_segundos
        velocidad_promedio = (distancia_total * 1000) / tiempo_total_segundos * 3.6  # m/s a km/h
        
        tiempos = np.linspace(0, tiempo_total_segundos, len(lats))
        velocidades = []
        for i, t in enumerate(tiempos):
            # Perfil de velocidad realista
            if t < tiempo_total_segundos * 0.1:
                v = velocidad_promedio * (t / (tiempo_total_segundos * 0.1))
            elif t > tiempo_total_segundos * 0.9:
                v = velocidad_promedio * ((tiempo_total_segundos - t) / (tiempo_total_segundos * 0.1))
            else:
                v = velocidad_promedio
            velocidades.append(max(0, min(v, 80)))  # Limitar a 80 km/h
        
        # Calcular pendientes
        pendientes = []
        for i in range(len(lats)):
            if i == 0:
                pendientes.append(0.0)
            else:
                distancia_horizontal = geodesic((lats[i-1], lons[i-1]), (lats[i], lons[i])).meters
                if distancia_horizontal > 0:
                    delta_alt = alts[i] - alts[i-1]
                    pendiente_rad = math.atan(delta_alt / distancia_horizontal)
                    pendiente_deg = math.degrees(pendiente_rad)
                else:
                    pendiente_deg = 0.0
                pendientes.append(pendiente_deg)
        
        return {
            'coords': [[lats[i], lons[i], alts[i]] for i in range(len(lats))],
            'velocidades_kmh': velocidades,
            'pendientes': pendientes,
            'tiempos': tiempos.tolist(),
            'distancia_km': distancia_total,
            'duracion_segundos': duracion_segundos,
            'usando_osrm': True
        }
    
    else:
        # Método de respaldo: interpolación simple con distancia geodésica
        distancia_total = geodesic((origin_lat, origin_lon), (dest_lat, dest_lon)).kilometers
        
        lats = np.linspace(origin_lat, dest_lat, num_puntos)
        lons = np.linspace(origin_lon, dest_lon, num_puntos)
        
        altitud_inicial = 1500
        altitud_final = 1500
        alts = np.linspace(altitud_inicial, altitud_final, num_puntos)
        
        velocidad_promedio = 35  # km/h
        tiempo_total_horas = distancia_total / velocidad_promedio
        tiempo_total_segundos = tiempo_total_horas * 3600
        
        tiempos = np.linspace(0, tiempo_total_segundos, num_puntos)
        velocidades = []
        for i, t in enumerate(tiempos):
            if t < tiempo_total_segundos * 0.1:
                v = velocidad_promedio * (t / (tiempo_total_segundos * 0.1))
            elif t > tiempo_total_segundos * 0.9:
                v = velocidad_promedio * ((tiempo_total_segundos - t) / (tiempo_total_segundos * 0.1))
            else:
                v = velocidad_promedio
            velocidades.append(max(0, min(v, 60)))
        
        pendientes = []
        for i in range(num_puntos):
            if i == 0:
                pendientes.append(0.0)
            else:
                distancia_horizontal = geodesic((lats[i-1], lons[i-1]), (lats[i], lons[i])).meters
                if distancia_horizontal > 0:
                    delta_alt = alts[i] - alts[i-1]
                    pendiente_rad = math.atan(delta_alt / distancia_horizontal)
                    pendiente_deg = math.degrees(pendiente_rad)
                else:
                    pendiente_deg = 0.0
                pendientes.append(pendiente_deg)
        
        return {
            'coords': [[lats[i], lons[i], alts[i]] for i in range(num_puntos)],
            'velocidades_kmh': velocidades,
            'pendientes': pendientes,
            'tiempos': tiempos.tolist(),
            'distancia_km': distancia_total,
            'duracion_segundos': tiempo_total_segundos,
            'usando_osrm': False
        }

def calcular_consumo_y_costos_viaje(origin_lat, origin_lon, dest_lat, dest_lon, 
                                   municipio_origen, municipio_destino, 
                                   estrato, motivo_viaje):
    """
    Calcula el consumo y costos para motocicleta eléctrica y a combustión
    incluyendo información del viaje (IDA Y VUELTA).
    """
    print("\n" + "="*70)
    print("=== CÁLCULO DE CONSUMO Y COSTOS DEL VIAJE (IDA Y VUELTA) ===")
    print(f"Municipio Origen: {municipio_origen}")
    print(f"Municipio Destino: {municipio_destino}")
    print(f"Estrato: {estrato}")
    print(f"Motivo de Viaje: {motivo_viaje}")
    print(f"Coordenadas Origen: ({origin_lat:.6f}, {origin_lon:.6f})")
    print(f"Coordenadas Destino: ({dest_lat:.6f}, {dest_lon:.6f})")
    
    # ========== CALCULAR TRAYECTO DE IDA ==========
    print("\n--- TRAYECTO DE IDA ---")
    print("Obteniendo ruta...")
    ruta_ida = obtener_ruta_simple(origin_lat, origin_lon, dest_lat, dest_lon, num_puntos=100)
    if ruta_ida.get('usando_osrm', False):
        print(f"Distancia ida (ruta real por carretera): {ruta_ida['distancia_km']:.2f} km")
        print(f"Duración estimada: {ruta_ida['duracion_segundos']/60:.1f} minutos")
    else:
        print(f"Distancia ida (geodésica - aproximada): {ruta_ida['distancia_km']:.2f} km")
    
    # Preprocesar vectores (ida)
    velocidades_interp_ida, pendientes_interp_ida, tiempos_interp_ida, coordenadas_interp_ida = preprocesar_vectores(
        ruta_ida['velocidades_kmh'],
        ruta_ida['pendientes'],
        ruta_ida['tiempos'],
        ruta_ida['coords'],
        puntos_intermedios=2
    )
    
    # Calcular consumo para motocicleta ELÉCTRICA (ida)
    consumo_electrico_kwh_ida, _, _, _, _, _, _ = consum(
        velocidades_interp_ida, 
        pendientes_interp_ida, 
        tiempos_interp_ida, 
        hybrid_cont=0,
        distancia_km=ruta_ida['distancia_km']
    )
    
    # Calcular consumo para motocicleta A COMBUSTIÓN (ida)
    _, consumo_combustion_kwh_ida, consumo_galones_ida, _, _, _, _ = consum(
        velocidades_interp_ida, 
        pendientes_interp_ida, 
        tiempos_interp_ida, 
        hybrid_cont=1,
        distancia_km=ruta_ida['distancia_km']
    )
    
    # ========== CALCULAR TRAYECTO DE VUELTA ==========
    print("\n--- TRAYECTO DE VUELTA ---")
    print("Obteniendo ruta...")
    # Pequeña pausa para no saturar el servicio OSRM
    time.sleep(0.5)
    ruta_vuelta = obtener_ruta_simple(dest_lat, dest_lon, origin_lat, origin_lon, num_puntos=100)
    if ruta_vuelta.get('usando_osrm', False):
        print(f"Distancia vuelta (ruta real por carretera): {ruta_vuelta['distancia_km']:.2f} km")
        print(f"Duración estimada: {ruta_vuelta['duracion_segundos']/60:.1f} minutos")
    else:
        print(f"Distancia vuelta (geodésica - aproximada): {ruta_vuelta['distancia_km']:.2f} km")
    
    # Preprocesar vectores (vuelta)
    velocidades_interp_vuelta, pendientes_interp_vuelta, tiempos_interp_vuelta, coordenadas_interp_vuelta = preprocesar_vectores(
        ruta_vuelta['velocidades_kmh'],
        ruta_vuelta['pendientes'],
        ruta_vuelta['tiempos'],
        ruta_vuelta['coords'],
        puntos_intermedios=2
    )
    
    # Calcular consumo para motocicleta ELÉCTRICA (vuelta)
    consumo_electrico_kwh_vuelta, _, _, _, _, _, _ = consum(
        velocidades_interp_vuelta, 
        pendientes_interp_vuelta, 
        tiempos_interp_vuelta, 
        hybrid_cont=0,
        distancia_km=ruta_vuelta['distancia_km']
    )
    
    # Calcular consumo para motocicleta A COMBUSTIÓN (vuelta)
    _, consumo_combustion_kwh_vuelta, consumo_galones_vuelta, _, _, _, _ = consum(
        velocidades_interp_vuelta, 
        pendientes_interp_vuelta, 
        tiempos_interp_vuelta, 
        hybrid_cont=1,
        distancia_km=ruta_vuelta['distancia_km']
    )
    
    # ========== SUMAR CONSUMOS (IDA + VUELTA) ==========
    consumo_electrico_kwh_total = consumo_electrico_kwh_ida + consumo_electrico_kwh_vuelta
    consumo_galones_total = consumo_galones_ida + consumo_galones_vuelta
    distancia_total = ruta_ida['distancia_km'] + ruta_vuelta['distancia_km']
    
    # Precios
    precio_gasolina_min = 16200  # COP por galón
    precio_gasolina_max = 16400  # COP por galón
    precio_kwh_min = 780  # COP por kWh
    precio_kwh_max = 1200  # COP por kWh
    
    # Calcular costos totales
    costo_electrico_min = consumo_electrico_kwh_total * precio_kwh_min
    costo_electrico_max = consumo_electrico_kwh_total * precio_kwh_max
    costo_combustion_min = consumo_galones_total * precio_gasolina_min
    costo_combustion_max = consumo_galones_total * precio_gasolina_max
    
    # Mostrar resultados
    print("\n" + "="*70)
    print("RESULTADOS DEL TRAyecto (IDA Y VUELTA)")
    print("="*70)
    print(f"\n--- INFORMACIÓN DEL VIAJE ---")
    print(f"Municipio Origen: {municipio_origen}")
    print(f"Municipio Destino: {municipio_destino}")
    print(f"Estrato: {estrato}")
    print(f"Motivo de Viaje: {motivo_viaje}")
    print(f"Distancia total: {distancia_total:.2f} km")
    print(f"  - Ida: {ruta_ida['distancia_km']:.2f} km")
    print(f"  - Vuelta: {ruta_vuelta['distancia_km']:.2f} km")
    
    print("\n--- MOTOCICLETA ELÉCTRICA ---")
    print(f"Consumo eléctrico (ida): {consumo_electrico_kwh_ida:.4f} kWh")
    print(f"Consumo eléctrico (vuelta): {consumo_electrico_kwh_vuelta:.4f} kWh")
    print(f"Consumo eléctrico TOTAL: {consumo_electrico_kwh_total:.4f} kWh")
    print(f"Costo (precio mínimo ${precio_kwh_min:,} COP/kWh): ${costo_electrico_min:,.2f} COP")
    print(f"Costo (precio máximo ${precio_kwh_max:,} COP/kWh): ${costo_electrico_max:,.2f} COP")
    print(f"Costo promedio: ${(costo_electrico_min + costo_electrico_max)/2:,.2f} COP")
    
    print("\n--- MOTOCICLETA A COMBUSTIÓN ---")
    print(f"Consumo de gasolina (ida): {consumo_galones_ida:.6f} galones")
    print(f"Consumo de gasolina (vuelta): {consumo_galones_vuelta:.6f} galones")
    print(f"Consumo de gasolina TOTAL: {consumo_galones_total:.6f} galones")
    print(f"Costo (precio mínimo ${precio_gasolina_min:,} COP/galón): ${costo_combustion_min:,.2f} COP")
    print(f"Costo (precio máximo ${precio_gasolina_max:,} COP/galón): ${costo_combustion_max:,.2f} COP")
    print(f"Costo promedio: ${(costo_combustion_min + costo_combustion_max)/2:,.2f} COP")
    
    print("\n--- COMPARACIÓN ---")
    ahorro_min = costo_combustion_min - costo_electrico_max
    ahorro_max = costo_combustion_max - costo_electrico_min
    print(f"Ahorro estimado (eléctrica vs combustión):")
    print(f"  Mínimo: ${ahorro_min:,.2f} COP")
    print(f"  Máximo: ${ahorro_max:,.2f} COP")
    print(f"  Promedio: ${(ahorro_min + ahorro_max)/2:,.2f} COP")
    
    porcentaje_ahorro_min = (ahorro_min / costo_combustion_min) * 100 if costo_combustion_min > 0 else 0
    porcentaje_ahorro_max = (ahorro_max / costo_combustion_max) * 100 if costo_combustion_max > 0 else 0
    print(f"  Porcentaje de ahorro: {porcentaje_ahorro_min:.1f}% - {porcentaje_ahorro_max:.1f}%")
    
    # ========== CALCULAR PORCENTAJE RESPECTO A CANASTA FAMILIAR ==========
    print("\n--- ANÁLISIS RESPECTO A CANASTA FAMILIAR ---")
    
    # Determinar ciudad basada en municipios (deben ser de la misma ciudad)
    ciudad_origen = determinar_ciudad_municipio(municipio_origen)
    ciudad_destino = determinar_ciudad_municipio(municipio_destino)
    
    ciudad = None
    if ciudad_origen == ciudad_destino and ciudad_origen is not None:
        ciudad = ciudad_origen
    elif ciudad_origen is not None:
        ciudad = ciudad_origen
        print(f"  ⚠ Advertencia: Origen ({municipio_origen}) y destino ({municipio_destino}) son de ciudades diferentes")
    elif ciudad_destino is not None:
        ciudad = ciudad_destino
        print(f"  ⚠ Advertencia: Origen ({municipio_origen}) y destino ({municipio_destino}) son de ciudades diferentes")
    
    # Limpiar estrato (puede venir como "ESTRATO 1", "1", etc.)
    estrato_limpio = str(estrato).replace('ESTRATO', '').replace(' ', '').strip()
    
    gasto_mensual_combustion_min = None
    gasto_mensual_combustion_max = None
    gasto_total_canasta = None
    porcentaje_canasta_min = None
    porcentaje_canasta_max = None
    
    if gasto_motos is not None and ciudad and estrato_limpio:
        try:
            # Buscar el gasto_total para el estrato y ciudad correspondiente
            filtro = (gasto_motos['Estrato'].astype(str).str.strip() == estrato_limpio) & \
                     (gasto_motos['Ciudad'].astype(str).str.strip() == ciudad)
            
            datos_estrato = gasto_motos[filtro]
            
            if len(datos_estrato) > 0:
                gasto_total_canasta = datos_estrato.iloc[0]['gasto_total']
                
                # Calcular gasto mensual de combustible (gasto diario * 30 días)
                # El gasto diario es el costo del viaje ida y vuelta
                gasto_diario_combustion_min = costo_combustion_min
                gasto_diario_combustion_max = costo_combustion_max
                
                gasto_mensual_combustion_min = gasto_diario_combustion_min * 30
                gasto_mensual_combustion_max = gasto_diario_combustion_max * 30
                
                # Calcular porcentaje respecto a la canasta familiar
                if gasto_total_canasta > 0:
                    porcentaje_canasta_min = (gasto_mensual_combustion_min / gasto_total_canasta) * 100
                    porcentaje_canasta_max = (gasto_mensual_combustion_max / gasto_total_canasta) * 100
                    
                    print(f"Ciudad: {ciudad}")
                    print(f"Estrato: {estrato_limpio}")
                    print(f"Canasta familiar (gasto_total): ${gasto_total_canasta:,.2f} COP/mes")
                    print(f"\nGasto diario en combustible (ida y vuelta):")
                    print(f"  Mínimo: ${gasto_diario_combustion_min:,.2f} COP")
                    print(f"  Máximo: ${gasto_diario_combustion_max:,.2f} COP")
                    print(f"\nGasto mensual en combustible (30 días):")
                    print(f"  Mínimo: ${gasto_mensual_combustion_min:,.2f} COP")
                    print(f"  Máximo: ${gasto_mensual_combustion_max:,.2f} COP")
                    print(f"\nPorcentaje del gasto mensual respecto a la canasta familiar:")
                    print(f"  Mínimo: {porcentaje_canasta_min:.2f}%")
                    print(f"  Máximo: {porcentaje_canasta_max:.2f}%")
                    print(f"  Promedio: {(porcentaje_canasta_min + porcentaje_canasta_max)/2:.2f}%")
                else:
                    print(f"  ⚠ No se pudo calcular: gasto_total es cero o inválido")
            else:
                print(f"  ⚠ No se encontraron datos para Estrato {estrato_limpio} en {ciudad}")
        except Exception as e:
            print(f"  ⚠ Error al calcular porcentaje de canasta familiar: {e}")
    else:
        if not ciudad:
            print(f"  ⚠ No se pudo determinar la ciudad para los municipios: {municipio_origen}, {municipio_destino}")
        if not estrato_limpio or estrato_limpio == '':
            print(f"  ⚠ Estrato inválido: {estrato}")
    
    return {
        'municipio_origen': municipio_origen,
        'municipio_destino': municipio_destino,
        'estrato': estrato,
        'motivo_viaje': motivo_viaje,
        'distancia_km': distancia_total,
        'distancia_ida_km': ruta_ida['distancia_km'],
        'distancia_vuelta_km': ruta_vuelta['distancia_km'],
        'consumo_electrico_kwh': consumo_electrico_kwh_total,
        'consumo_electrico_kwh_ida': consumo_electrico_kwh_ida,
        'consumo_electrico_kwh_vuelta': consumo_electrico_kwh_vuelta,
        'consumo_galones': consumo_galones_total,
        'consumo_galones_ida': consumo_galones_ida,
        'consumo_galones_vuelta': consumo_galones_vuelta,
        'costo_electrico_min': costo_electrico_min,
        'costo_electrico_max': costo_electrico_max,
        'costo_combustion_min': costo_combustion_min,
        'costo_combustion_max': costo_combustion_max,
        'coordenadas_origen': (origin_lat, origin_lon),
        'coordenadas_destino': (dest_lat, dest_lon),
        'gasto_total_canasta': gasto_total_canasta,
        'gasto_mensual_combustion_min': gasto_mensual_combustion_min,
        'gasto_mensual_combustion_max': gasto_mensual_combustion_max,
        'porcentaje_canasta_min': porcentaje_canasta_min,
        'porcentaje_canasta_max': porcentaje_canasta_max,
        'ciudad': ciudad,
        'ruta_ida': ruta_ida,
        'ruta_vuelta': ruta_vuelta
    }

def main():
    """Función principal que selecciona un viaje aleatorio y calcula costos."""
    print("="*70)
    print("CALCULADORA DE COSTOS DE VIAJES EN MOTOCICLETA")
    print("="*70)
    
    # Cargar archivo de viajes procesados
    print("\n1. Cargando archivo de viajes procesados...")
    try:
        df_viajes = pd.read_csv('viajes_motos_procesados.csv', sep=';', encoding='utf-8-sig')
        print(f"   ✓ Archivo cargado: {len(df_viajes):,} viajes")
    except Exception as e:
        print(f"   ✗ Error al cargar archivo: {e}")
        return
    
    # Filtrar solo filas con estrato válido (no "No aplica")
    print("\n2. Filtrando viajes con estrato válido...")
    df_filtrado = df_viajes[df_viajes['ESTRATO'].astype(str).str.strip() != 'No aplica'].copy()
    df_filtrado = df_filtrado[df_filtrado['ESTRATO'].astype(str).str.strip() != '']
    print(f"   ✓ Viajes con estrato válido: {len(df_filtrado):,}")
    
    if len(df_filtrado) == 0:
        print("   ✗ No hay viajes con estrato válido")
        return
    
    # Filtrar viajes donde origen y destino sean de la misma ciudad
    print("\n3. Filtrando viajes con origen y destino de la misma ciudad...")
    def misma_ciudad(row):
        ciudad_origen = determinar_ciudad_municipio(row['Municipio_Origen'])
        ciudad_destino = determinar_ciudad_municipio(row['Municipio_Destino'])
        return ciudad_origen == ciudad_destino and ciudad_origen is not None
    
    df_misma_ciudad = df_filtrado[df_filtrado.apply(misma_ciudad, axis=1)].copy()
    print(f"   ✓ Viajes con misma ciudad: {len(df_misma_ciudad):,}")
    
    if len(df_misma_ciudad) == 0:
        print("   ✗ No hay viajes donde origen y destino sean de la misma ciudad")
        print("   ⚠ Intentando con todos los viajes filtrados...")
        df_misma_ciudad = df_filtrado.copy()
    
    # Seleccionar una fila aleatoria
    print("\n4. Seleccionando viaje aleatorio...")
    fila_aleatoria = df_misma_ciudad.sample(n=1).iloc[0]
    
    municipio_origen = str(fila_aleatoria['Municipio_Origen']).strip()
    municipio_destino = str(fila_aleatoria['Municipio_Destino']).strip()
    estrato = str(fila_aleatoria['ESTRATO']).strip()
    motivo_viaje = str(fila_aleatoria['Motivo_Viaje']).strip()
    ciudad_municipio = str(fila_aleatoria['Ciudad_Municipio']).strip()
    
    # Verificar que origen y destino sean de la misma ciudad
    ciudad_origen = determinar_ciudad_municipio(municipio_origen)
    ciudad_destino = determinar_ciudad_municipio(municipio_destino)
    
    if ciudad_origen != ciudad_destino or ciudad_origen is None:
        print(f"   ✗ ERROR: Origen y destino no son de la misma ciudad")
        print(f"     - Origen: {municipio_origen} ({ciudad_origen})")
        print(f"     - Destino: {municipio_destino} ({ciudad_destino})")
        print(f"   ⚠ Seleccionando otro viaje...")
        # Intentar de nuevo con un filtro más estricto
        df_misma_ciudad = df_filtrado[df_filtrado.apply(misma_ciudad, axis=1)].copy()
        if len(df_misma_ciudad) > 0:
            fila_aleatoria = df_misma_ciudad.sample(n=1).iloc[0]
            municipio_origen = str(fila_aleatoria['Municipio_Origen']).strip()
            municipio_destino = str(fila_aleatoria['Municipio_Destino']).strip()
            estrato = str(fila_aleatoria['ESTRATO']).strip()
            motivo_viaje = str(fila_aleatoria['Motivo_Viaje']).strip()
            ciudad_origen = determinar_ciudad_municipio(municipio_origen)
            ciudad_destino = determinar_ciudad_municipio(municipio_destino)
        else:
            print("   ✗ No se encontraron viajes válidos")
            return
    
    print(f"   ✓ Viaje seleccionado:")
    print(f"     - Municipio Origen: {municipio_origen} ({ciudad_origen})")
    print(f"     - Municipio Destino: {municipio_destino} ({ciudad_destino})")
    print(f"     - Estrato: {estrato}")
    print(f"     - Motivo: {motivo_viaje}")
    
    # Obtener coordenadas aleatorias dentro de los municipios
    print("\n5. Obteniendo coordenadas aleatorias dentro de los municipios...")
    print(f"   Obteniendo coordenadas para {municipio_origen}...")
    origin_lat, origin_lon = obtener_coordenadas_aleatorias_municipio(
        municipio_origen, zonas_sit, zat
    )
    print(f"   ✓ Coordenadas origen: ({origin_lat:.6f}, {origin_lon:.6f})")
    
    print(f"   Obteniendo coordenadas para {municipio_destino}...")
    dest_lat, dest_lon = obtener_coordenadas_aleatorias_municipio(
        municipio_destino, zonas_sit, zat
    )
    print(f"   ✓ Coordenadas destino: ({dest_lat:.6f}, {dest_lon:.6f})")
    
    # Calcular consumo y costos
    print("\n6. Calculando consumo y costos...")
    resultados = calcular_consumo_y_costos_viaje(
        origin_lat, origin_lon, dest_lat, dest_lon,
        municipio_origen, municipio_destino, estrato, motivo_viaje
    )
    
    # Generar mapa HTML con la ruta
    print("\n7. Generando mapa HTML de la ruta...")
    generar_mapa_ruta_viaje(
        resultados['ruta_ida'],
        resultados['ruta_vuelta'],
        municipio_origen,
        municipio_destino,
        resultados,
        nombre_archivo='ruta_viaje_mapa.html'
    )
    print("   ✓ Mapa HTML generado: ruta_viaje_mapa.html")
    
    # Generar gráfica de características de la moto
    print("\n8. Generando gráfica de características de la moto...")
    generar_grafica_caracteristicas_moto(
        resultados['ruta_ida'],
        resultados['ruta_vuelta'],
        municipio_origen,
        municipio_destino,
        nombre_archivo='grafica_caracteristicas_moto.png'
    )
    
    print("\n" + "="*70)
    print("PROCESO COMPLETADO")
    print("="*70)
    
    return resultados

def generar_mapa_ruta_viaje(ruta_ida, ruta_vuelta, municipio_origen, municipio_destino, 
                           resultados, nombre_archivo='ruta_viaje_mapa.html'):
    """
    Genera un mapa HTML interactivo con Folium mostrando las rutas de ida y vuelta.
    """
    # Obtener coordenadas de ambas rutas
    coords_ida = ruta_ida['coords']
    coords_vuelta = ruta_vuelta['coords']
    
    # Filtrar coordenadas válidas
    coords_ida_validas = [[c[0], c[1]] for c in coords_ida if c[0] != 0 and c[1] != 0]
    coords_vuelta_validas = [[c[0], c[1]] for c in coords_vuelta if c[0] != 0 and c[1] != 0]
    
    if not coords_ida_validas or not coords_vuelta_validas:
        print("  ⚠ No hay coordenadas válidas para generar el mapa")
        return
    
    # Calcular centro del mapa
    todas_coords = coords_ida_validas + coords_vuelta_validas
    lat_centro = np.mean([c[0] for c in todas_coords])
    lon_centro = np.mean([c[1] for c in todas_coords])
    
    # Crear mapa base
    mapa = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=12,
        tiles='OpenStreetMap'
    )
    
    # Agregar capa de satélite
    folium.TileLayer(
        tiles='https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
        attr='Esri',
        name='Satélite',
        overlay=False,
        control=True
    ).add_to(mapa)
    
    # Agregar ruta de IDA (color azul)
    folium.PolyLine(
        locations=coords_ida_validas,
        color='blue',
        weight=5,
        opacity=0.7,
        popup='Ruta de Ida',
        tooltip=f'Ida: {ruta_ida["distancia_km"]:.2f} km'
    ).add_to(mapa)
    
    # Agregar ruta de VUELTA (color rojo)
    folium.PolyLine(
        locations=coords_vuelta_validas,
        color='red',
        weight=5,
        opacity=0.7,
        popup='Ruta de Vuelta',
        tooltip=f'Vuelta: {ruta_vuelta["distancia_km"]:.2f} km'
    ).add_to(mapa)
    
    # Marcador de inicio (origen)
    folium.Marker(
        location=coords_ida_validas[0],
        popup=folium.Popup(
            f"<b>Origen: {municipio_origen}</b><br>"
            f"Distancia ida: {ruta_ida['distancia_km']:.2f} km<br>"
            f"Distancia vuelta: {ruta_vuelta['distancia_km']:.2f} km",
            max_width=250
        ),
        icon=folium.Icon(color='green', icon='play', prefix='fa')
    ).add_to(mapa)
    
    # Marcador de destino
    folium.Marker(
        location=coords_ida_validas[-1],
        popup=folium.Popup(
            f"<b>Destino: {municipio_destino}</b><br>"
            f"Distancia ida: {ruta_ida['distancia_km']:.2f} km<br>"
            f"Distancia vuelta: {ruta_vuelta['distancia_km']:.2f} km",
            max_width=250
        ),
        icon=folium.Icon(color='red', icon='stop', prefix='fa')
    ).add_to(mapa)
    
    # Agregar leyenda
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Leyenda de Rutas</b></p>
    <p><span style="color:blue; font-size:16px;">━━━</span> Ruta de Ida ({ruta_ida['distancia_km']:.2f} km)</p>
    <p><span style="color:red; font-size:16px;">━━━</span> Ruta de Vuelta ({ruta_vuelta['distancia_km']:.2f} km)</p>
    <p><span style="color:green; font-size:16px;">●</span> Origen: {municipio_origen}</p>
    <p><span style="color:red; font-size:16px;">●</span> Destino: {municipio_destino}</p>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(legend_html))
    
    # Agregar panel de información del viaje
    info_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 300px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>Información del Viaje</h4>
    <p><b>Origen:</b> {municipio_origen}</p>
    <p><b>Destino:</b> {municipio_destino}</p>
    <p><b>Estrato:</b> {resultados['estrato']}</p>
    <p><b>Motivo:</b> {resultados['motivo_viaje']}</p>
    <hr>
    <p><b>Distancia Total:</b> {resultados['distancia_km']:.2f} km</p>
    <p><b>Consumo Eléctrico:</b> {resultados['consumo_electrico_kwh']:.4f} kWh</p>
    <p><b>Consumo Gasolina:</b> {resultados['consumo_galones']:.6f} galones</p>
    <p><b>Costo Eléctrico:</b> ${resultados['costo_electrico_min']:,.0f} - ${resultados['costo_electrico_max']:,.0f} COP</p>
    <p><b>Costo Combustión:</b> ${resultados['costo_combustion_min']:,.0f} - ${resultados['costo_combustion_max']:,.0f} COP</p>
    '''
    
    if resultados.get('porcentaje_canasta_min') is not None:
        info_html += f'''
    <hr>
    <p><b>% Canasta Familiar:</b> {resultados['porcentaje_canasta_min']:.2f}% - {resultados['porcentaje_canasta_max']:.2f}%</p>
    '''
    
    info_html += '</div>'
    mapa.get_root().html.add_child(folium.Element(info_html))
    
    # Guardar mapa
    mapa.save(nombre_archivo)
    return mapa

def calcular_caracteristicas_moto_por_punto(speeds, slopes, tiempos, coordenadas, hybrid_cont=0):
    """
    Calcula las características de la moto (fuerzas, potencia) para cada punto del recorrido.
    """
    # Parámetros de la moto
    m = 140  # kg (masa total)
    cd = 0.3  # coeficiente de arrastre
    a = 0.74  # m² (área frontal)
    crr = 0.01  # coeficiente de rodamiento
    rho = 1.225  # kg/m³ (densidad del aire)
    g = 9.81  # m/s² (gravedad)
    rw = 0.3  # m (radio de la rueda)
    eficiencia_tren = 0.85
    factor_correccion = 1.617
    
    # Listas para almacenar resultados
    distancias = []
    velocidades_ms = []
    potencias_electricas_kw = []
    potencias_combustion_kw = []
    fuerzas_aerodinamica = []
    fuerzas_rodamiento = []
    fuerzas_gravitacional = []
    fuerzas_inercia = []
    fuerzas_resistencia_total = []
    altitudes = []
    
    distancia_acumulada = 0
    last_vel = 0
    
    for i in range(len(speeds)):
        # Calcular distancia acumulada
        if i > 0:
            lat_ant = coordenadas[i-1][0]
            lon_ant = coordenadas[i-1][1]
            lat_act = coordenadas[i][0]
            lon_act = coordenadas[i][1]
            if lat_ant != 0 and lon_ant != 0 and lat_act != 0 and lon_act != 0:
                dist_segmento = geodesic((lat_ant, lon_ant), (lat_act, lon_act)).kilometers
                distancia_acumulada += dist_segmento
        
        distancias.append(distancia_acumulada)
        
        # Velocidad en m/s
        vel_ms = speeds[i] / 3.6
        velocidades_ms.append(vel_ms)
        
        # Ángulo de pendiente
        theta = slopes[i] * math.pi / 180
        
        # Calcular fuerzas
        faero = 0.5 * rho * a * cd * (vel_ms ** 2)
        froll = g * m * crr * np.cos(theta)
        fg = g * m * np.sin(theta)
        delta_v = vel_ms - last_vel
        f_inertia = m * delta_v / 1  # Asumiendo dt = 1 segundo
        
        fres = faero + froll + fg + f_inertia
        
        # Potencia mecánica
        p_m = (fres * rw) * (vel_ms / rw)
        
        # Potencia eléctrica
        p_eb = p_m * (1 - hybrid_cont) / eficiencia_tren
        p_eb = p_eb * factor_correccion
        if p_eb < 0:
            p_eb = 0
        potencias_electricas_kw.append(p_eb / 1000)
        
        # Potencia de combustión
        p_cn = p_m * hybrid_cont / 0.2
        factor_correccion_combustion = 1.8
        p_cn = p_cn * factor_correccion_combustion
        if p_cn <= 0:
            p_cn = 0
        potencias_combustion_kw.append(p_cn / 1000)
        
        # Guardar fuerzas
        fuerzas_aerodinamica.append(faero)
        fuerzas_rodamiento.append(froll)
        fuerzas_gravitacional.append(fg)
        fuerzas_inercia.append(f_inertia)
        fuerzas_resistencia_total.append(fres)
        
        # Altitud
        altitudes.append(coordenadas[i][2] if len(coordenadas[i]) > 2 else 1500)
        
        last_vel = vel_ms
    
    return {
        'distancias': distancias,
        'velocidades_ms': velocidades_ms,
        'velocidades_kmh': speeds,
        'potencias_electricas_kw': potencias_electricas_kw,
        'potencias_combustion_kw': potencias_combustion_kw,
        'fuerzas_aerodinamica': fuerzas_aerodinamica,
        'fuerzas_rodamiento': fuerzas_rodamiento,
        'fuerzas_gravitacional': fuerzas_gravitacional,
        'fuerzas_inercia': fuerzas_inercia,
        'fuerzas_resistencia_total': fuerzas_resistencia_total,
        'pendientes': slopes,
        'altitudes': altitudes,
        'tiempos': tiempos
    }

def generar_grafica_caracteristicas_moto(ruta_ida, ruta_vuelta, municipio_origen, municipio_destino,
                                        nombre_archivo='grafica_caracteristicas_moto.png'):
    """
    Genera una gráfica con las características de la moto durante el recorrido.
    """
    # Calcular características para ida (eléctrica)
    caracteristicas_ida = calcular_caracteristicas_moto_por_punto(
        ruta_ida['velocidades_kmh'],
        ruta_ida['pendientes'],
        ruta_ida['tiempos'],
        ruta_ida['coords'],
        hybrid_cont=0
    )
    
    # Calcular características para vuelta (eléctrica)
    caracteristicas_vuelta = calcular_caracteristicas_moto_por_punto(
        ruta_vuelta['velocidades_kmh'],
        ruta_vuelta['pendientes'],
        ruta_vuelta['tiempos'],
        ruta_vuelta['coords'],
        hybrid_cont=0
    )
    
    # Ajustar distancias de vuelta para continuar desde donde terminó ida
    distancia_final_ida = caracteristicas_ida['distancias'][-1] if caracteristicas_ida['distancias'] else 0
    distancias_vuelta_ajustadas = [d + distancia_final_ida for d in caracteristicas_vuelta['distancias']]
    
    # Combinar datos de ida y vuelta
    distancias_total = caracteristicas_ida['distancias'] + distancias_vuelta_ajustadas
    velocidades_total = caracteristicas_ida['velocidades_kmh'] + caracteristicas_vuelta['velocidades_kmh']
    potencias_total = caracteristicas_ida['potencias_electricas_kw'] + caracteristicas_vuelta['potencias_electricas_kw']
    pendientes_total = caracteristicas_ida['pendientes'] + caracteristicas_vuelta['pendientes']
    altitudes_total = caracteristicas_ida['altitudes'] + caracteristicas_vuelta['altitudes']
    fuerzas_aero_total = caracteristicas_ida['fuerzas_aerodinamica'] + caracteristicas_vuelta['fuerzas_aerodinamica']
    fuerzas_roll_total = caracteristicas_ida['fuerzas_rodamiento'] + caracteristicas_vuelta['fuerzas_rodamiento']
    fuerzas_grav_total = caracteristicas_ida['fuerzas_gravitacional'] + caracteristicas_vuelta['fuerzas_gravitacional']
    fuerzas_inercia_total = caracteristicas_ida['fuerzas_inercia'] + caracteristicas_vuelta['fuerzas_inercia']
    
    # Crear figura con subplots
    fig, axes = plt.subplots(3, 2, figsize=(16, 12))
    fig.suptitle(f'Características de la Motocicleta durante el Recorrido\n{municipio_origen} → {municipio_destino} (Ida y Vuelta)', 
                 fontsize=16, fontweight='bold')
    
    # Encontrar punto de transición entre ida y vuelta
    punto_transicion = len(caracteristicas_ida['distancias'])
    
    # 1. Velocidad vs Distancia
    ax1 = axes[0, 0]
    ax1.plot(distancias_total, velocidades_total, 'b-', linewidth=2, label='Velocidad')
    ax1.axvline(x=distancia_final_ida, color='r', linestyle='--', linewidth=1, alpha=0.7, label='Fin Ida / Inicio Vuelta')
    ax1.set_xlabel('Distancia (km)', fontsize=11)
    ax1.set_ylabel('Velocidad (km/h)', fontsize=11)
    ax1.set_title('Velocidad durante el Recorrido', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend()
    
    # 2. Potencia Eléctrica vs Distancia
    ax2 = axes[0, 1]
    ax2.plot(distancias_total, potencias_total, 'g-', linewidth=2, label='Potencia Eléctrica')
    ax2.axvline(x=distancia_final_ida, color='r', linestyle='--', linewidth=1, alpha=0.7)
    ax2.set_xlabel('Distancia (km)', fontsize=11)
    ax2.set_ylabel('Potencia (kW)', fontsize=11)
    ax2.set_title('Potencia Eléctrica Requerida', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend()
    
    # 3. Pendiente vs Distancia
    ax3 = axes[1, 0]
    ax3.plot(distancias_total, pendientes_total, 'orange', linewidth=2, label='Pendiente')
    ax3.axvline(x=distancia_final_ida, color='r', linestyle='--', linewidth=1, alpha=0.7)
    ax3.axhline(y=0, color='k', linestyle='-', linewidth=0.5, alpha=0.3)
    ax3.set_xlabel('Distancia (km)', fontsize=11)
    ax3.set_ylabel('Pendiente (grados)', fontsize=11)
    ax3.set_title('Pendiente del Terreno', fontsize=12, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend()
    
    # 4. Altitud vs Distancia
    ax4 = axes[1, 1]
    ax4.plot(distancias_total, altitudes_total, 'purple', linewidth=2, label='Altitud')
    ax4.axvline(x=distancia_final_ida, color='r', linestyle='--', linewidth=1, alpha=0.7)
    ax4.set_xlabel('Distancia (km)', fontsize=11)
    ax4.set_ylabel('Altitud (m)', fontsize=11)
    ax4.set_title('Perfil de Elevación', fontsize=12, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.legend()
    
    # 5. Fuerzas vs Distancia
    ax5 = axes[2, 0]
    ax5.plot(distancias_total, fuerzas_aero_total, 'b-', linewidth=1.5, label='Aerodinámica', alpha=0.7)
    ax5.plot(distancias_total, fuerzas_roll_total, 'g-', linewidth=1.5, label='Rodamiento', alpha=0.7)
    ax5.plot(distancias_total, [abs(f) for f in fuerzas_grav_total], 'orange', linewidth=1.5, label='Gravitacional (abs)', alpha=0.7)
    ax5.plot(distancias_total, [abs(f) for f in fuerzas_inercia_total], 'r-', linewidth=1.5, label='Inercia (abs)', alpha=0.7)
    ax5.axvline(x=distancia_final_ida, color='r', linestyle='--', linewidth=1, alpha=0.7)
    ax5.set_xlabel('Distancia (km)', fontsize=11)
    ax5.set_ylabel('Fuerza (N)', fontsize=11)
    ax5.set_title('Fuerzas que Actúan sobre la Motocicleta', fontsize=12, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.legend(fontsize=9)
    
    # 6. Resumen de estadísticas
    ax6 = axes[2, 1]
    ax6.axis('off')
    
    # Calcular estadísticas
    vel_promedio = np.mean(velocidades_total)
    vel_max = np.max(velocidades_total)
    pot_promedio = np.mean(potencias_total)
    pot_max = np.max(potencias_total)
    pendiente_max = np.max([abs(p) for p in pendientes_total])
    alt_min = np.min(altitudes_total)
    alt_max = np.max(altitudes_total)
    distancia_total_km = distancias_total[-1] if distancias_total else 0
    
    stats_text = f"""
    ESTADÍSTICAS DEL RECORRIDO
    
    Distancia Total: {distancia_total_km:.2f} km
    
    VELOCIDAD:
    • Promedio: {vel_promedio:.1f} km/h
    • Máxima: {vel_max:.1f} km/h
    
    POTENCIA ELÉCTRICA:
    • Promedio: {pot_promedio:.2f} kW
    • Máxima: {pot_max:.2f} kW
    
    TERRENO:
    • Pendiente máxima: {pendiente_max:.2f}°
    • Altitud mínima: {alt_min:.0f} m
    • Altitud máxima: {alt_max:.0f} m
    • Desnivel: {alt_max - alt_min:.0f} m
    
    FUERZAS PROMEDIO:
    • Aerodinámica: {np.mean(fuerzas_aero_total):.1f} N
    • Rodamiento: {np.mean(fuerzas_roll_total):.1f} N
    • Gravitacional: {np.mean([abs(f) for f in fuerzas_grav_total]):.1f} N
    • Inercia: {np.mean([abs(f) for f in fuerzas_inercia_total]):.1f} N
    """
    
    ax6.text(0.1, 0.5, stats_text, fontsize=10, verticalalignment='center',
             family='monospace', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    plt.tight_layout()
    plt.savefig(nombre_archivo, dpi=300, bbox_inches='tight')
    plt.close()
    
    print(f"   ✓ Gráfica de características generada: {nombre_archivo}")
    return fig

if __name__ == "__main__":
    resultados = main()

