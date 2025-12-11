import json
import numpy as np
import matplotlib.pyplot as plt
import math
from geopy.distance import geodesic
from scipy.optimize import minimize
import folium

# Paleta de colores EAFIT
COLOR_AZUL = (0/255, 75/255, 133/255)  # EAFIT Blue RGB(0, 75, 133)
COLOR_AMARILLO = (255/255, 200/255, 0/255)  # Amarillo complementario
COLOR_ROJO = (200/255, 0/255, 0/255)  # Rojo en tono similar
COLOR_NEGRO = (0/255, 0/255, 0/255)  # Negro
COLOR_GRIS = (128/255, 128/255, 128/255)  # Gris medio

def cargar_datos(archivo):
    with open(archivo, 'r') as f:
        return json.load(f)

def identificar_rutas(data):
    rutas = []
    ruta_actual = []
    for punto in data:
        if punto.get("id") == 1 and len(ruta_actual) > 0:
            rutas.append(ruta_actual)
            ruta_actual = []
        ruta_actual.append(punto)
    if len(ruta_actual) > 0:
        rutas.append(ruta_actual)
    return rutas

def extraer_datos_ruta(ruta):
    iA, lat, lon, alt, spdKmh, ts = [], [], [], [], [], []
    for punto in ruta:
        iA.append(punto.get("iA", 0))
        ts.append(punto.get("ts", 0))
        gps = punto.get("gps", {})
        if isinstance(gps, dict) and "fix" not in gps:
            lat.append(gps.get("lat", 0))
            lon.append(gps.get("lon", 0))
            alt.append(gps.get("alt", 0))
            spdKmh.append(gps.get("spdKmh", 0))
        else:
            lat.append(0)
            lon.append(0)
            alt.append(0)
            spdKmh.append(0)
    return np.array(iA), np.array(lat), np.array(lon), np.array(alt), np.array(spdKmh), np.array(ts)

def calcular_soc(potencia, ts, energia_inicial=2000.0):
    soc = []
    energia_actual = energia_inicial
    for i in range(len(potencia)):
        if i > 0 and ts[i] > ts[i-1]:
            delta_t = (ts[i] - ts[i-1]) / 1000.0 / 3600.0
        else:
            delta_t = 1.0 / 3600.0
        consumo_wh = potencia[i] * delta_t
        energia_actual -= consumo_wh
        if energia_actual < 0:
            energia_actual = 0.0
        soc.append(energia_actual)
    return np.array(soc)

def calcular_pendientes_desde_altitud(lat, lon, alt):
    pendientes = [0.0]
    for i in range(1, len(alt)):
        if lat[i] != 0 and lon[i] != 0 and lat[i-1] != 0 and lon[i-1] != 0:
            distancia_horizontal = geodesic((lat[i-1], lon[i-1]), (lat[i], lon[i])).meters
            if distancia_horizontal > 0:
                delta_alt = alt[i] - alt[i-1]
                pendiente_rad = math.atan(delta_alt / distancia_horizontal)
                pendiente_deg = math.degrees(pendiente_rad)
            else:
                pendiente_deg = 0.0
        else:
            pendiente_deg = 0.0
        pendientes.append(pendiente_deg)
    return np.array(pendientes)

def calcular_tiempos_desde_ts(ts):
    tiempos = []
    tiempo_acumulado = 0.0
    for i in range(len(ts)):
        if i == 0:
            tiempos.append(0.0)
        else:
            if ts[i] > ts[i-1]:
                delta_t = (ts[i] - ts[i-1]) / 1000.0
            else:
                delta_t = 1.0
            tiempo_acumulado += delta_t
            tiempos.append(tiempo_acumulado)
    return np.array(tiempos)

def preprocesar_vectores(velocidades, pendientes, tiempos, coordenadas, puntos_intermedios=10):
    n_original = len(velocidades)
    n_nuevo = n_original + (n_original - 1) * puntos_intermedios
    
    x_original = np.arange(n_original)
    x_nuevo = np.linspace(0, n_original - 1, n_nuevo)
    
    velocidades_interp = np.interp(x_nuevo, x_original, velocidades).tolist()
    pendientes_interp = np.interp(x_nuevo, x_original, pendientes).tolist()
    tiempos_interp = np.interp(x_nuevo, x_original, tiempos).tolist()
    
    coords_interp = []
    for i in range(3):
        valores = [coord[i] for coord in coordenadas]
        valores_interp = np.interp(x_nuevo, x_original, valores)
        coords_interp.append(valores_interp.tolist())
    
    coordenadas_interp = [[coords_interp[0][i], coords_interp[1][i], coords_interp[2][i]] for i in range(n_nuevo)]
    
    return velocidades_interp, pendientes_interp, tiempos_interp, coordenadas_interp

def calcular_potencia_por_punto(speeds, slopes, hybrid_cont, params=None):
    if params is None:
        params = {
            'm': 140,
            'cd': 0.3,
            'a': 0.74,
            'crr': 0.01,
            'factor_correccion': 1.617,
            'eficiencia_tren': 0.85
        }
    
    rho = 1.225
    g = 9.81
    rw = 0.3
    
    potencia_por_punto = []
    potencia_combustion_por_punto = []
    last_vel = 0
    
    for i in range(len(speeds)):
        vel = speeds[i] / 3.6
        theta = slopes[i] * math.pi / 180
        faero = 0.5 * rho * params['a'] * params['cd'] * (vel ** 2)
        froll = g * params['m'] * params['crr'] * np.cos(theta)
        fg = g * params['m'] * np.sin(theta)
        delta_v = vel - last_vel
        f_inertia = params['m'] * delta_v / 1
        fres = faero + froll + fg + f_inertia
        p_e = vel * fres
        p_m = (fres * rw) * (vel / rw)
        p_eb = p_m * (1 - hybrid_cont) / params['eficiencia_tren']
        p_eb = p_eb * params['factor_correccion']
        if p_eb < 0:
            p_eb = 0
        
        # Potencia de combustión
        p_cn = p_m * hybrid_cont / 0.2
        #factor_correccion_combustion = 1.8
        #p_cn = p_cn * factor_correccion_combustion
        if p_cn <= 0:
            p_cn = 0

        last_vel = vel
        potencia_kw = p_eb / 1000
        potencia_por_punto.append(potencia_kw)
        potencia_combustion_por_punto.append(p_cn / 1000)
    
    return potencia_por_punto, potencia_combustion_por_punto

def calcular_consumo_y_emisiones(potencia_electrica_w, potencia_combustion_kw, tiempos, speeds):
    """
    Calcula el consumo total y las emisiones equivalentes de ciclo de vida
    """
    # Calcular consumo eléctrico total (kWh)
    consumo_electrico_total = 0
    consumo_combustion_total = 0
    
    for i in range(len(potencia_electrica_w)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i-1], 0.1)
        
        tiempo_horas = delta_t / 3600
        consumo_electrico_total += (potencia_electrica_w[i] / 1000) * tiempo_horas
        consumo_combustion_total += potencia_combustion_kw[i] * tiempo_horas
    
    # Calcular distancia total (km)
    distancia_total = 0
    for i in range(len(speeds)):
        if i == 0:
            delta_t = tiempos[0] if tiempos[0] > 0 else 1.0
        else:
            delta_t = max(tiempos[i] - tiempos[i-1], 0.1)
        vel_ms = speeds[i] / 3.6
        distancia_total += vel_ms * delta_t
    distancia_km = distancia_total / 1000
    
    # Factores de emisión equivalentes de ciclo de vida (gCO₂/km)
    factor_emision_electrico_gco2_km = 35  # Motocicleta eléctrica
    factor_emision_combustion_gco2_km = 70  # Motocicleta a combustión
    
    # Emisiones equivalentes de ciclo de vida (kg CO₂)
    emisiones_electrico_kg = (factor_emision_electrico_gco2_km * distancia_km) / 1000
    emisiones_combustion_kg = (factor_emision_combustion_gco2_km * distancia_km) / 1000
    
    # Conversión de energía de combustible a galones
    poder_calorifico_gasolina_kwh_galon = 33.7
    consumo_galones = consumo_combustion_total / poder_calorifico_gasolina_kwh_galon
    
    return {
        'consumo_electrico_kwh': consumo_electrico_total,
        'consumo_combustion_kwh': consumo_combustion_total,
        'consumo_galones': consumo_galones,
        'distancia_km': distancia_km,
        'emisiones_electrico_kg': emisiones_electrico_kg,
        'emisiones_combustion_kg': emisiones_combustion_kg,
        'factor_emision_electrico': factor_emision_electrico_gco2_km,
        'factor_emision_combustion': factor_emision_combustion_gco2_km
    }

def main():
    data = cargar_datos("datos-telemetry.json")
    rutas = identificar_rutas(data)
    ruta_mas_larga = max(rutas, key=len)
    
    iA, lat, lon, alt, spdKmh, ts = extraer_datos_ruta(ruta_mas_larga)
    potencia = iA * 48
    soc = calcular_soc(potencia, ts, energia_inicial=2000.0)
    tiempos = calcular_tiempos_desde_ts(ts)
    
    # Grupo 1a: Corriente y Potencia (2 gráficas)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].plot(tiempos, iA, color=COLOR_AZUL, linewidth=1.5)
    axes[0].set_title("Corriente (iA)")
    axes[0].set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("iA (A)")
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(tiempos, potencia, color=COLOR_ROJO, linewidth=1.5)
    axes[1].set_title("Potencia (iA × 48V)")
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("Potencia (W)")
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("telemetria_corriente_potencia.png", dpi=150)
    plt.close()
    
    # Grupo 1b: SOC (1 gráfica)
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    ax.plot(tiempos, soc, color=COLOR_AZUL, linewidth=1.5)
    ax.set_title("SOC (desde 2.0 kWh)")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("SOC (Wh)")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("telemetria_soc.png", dpi=150)
    plt.close()
    
    # Grupo 2a: Latitud y Longitud (2 gráficas)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].plot(tiempos, lat, color=COLOR_AZUL, linewidth=1.5)
    axes[0].set_title("Latitud")
    axes[0].set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("Latitud")
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(tiempos, lon, color=COLOR_AMARILLO, linewidth=1.5)
    axes[1].set_title("Longitud")
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("Longitud")
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("telemetria_latitud_longitud.png", dpi=150)
    plt.close()
    
    # Grupo 2b: Altitud y Trayectoria GPS (2 gráficas)
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    
    axes[0].plot(tiempos, alt, color=COLOR_ROJO, linewidth=1.5)
    axes[0].set_title("Altitud")
    axes[0].set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("Altitud (m)")
    axes[0].grid(True, alpha=0.3)
    
    axes[1].plot(lon, lat, color=COLOR_AZUL, linewidth=1.5, alpha=0.7)
    axes[1].set_title("Trayectoria GPS")
    axes[1].set_xlabel("Longitud")
    axes[1].set_ylabel("Latitud")
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("telemetria_altitud_trayectoria.png", dpi=150)
    plt.close()
    
    # Grupo 3: Parámetros de movimiento (1 gráfica)
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    ax.plot(tiempos, spdKmh, color=COLOR_AZUL, linewidth=1.5)
    ax.set_title("Velocidad")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Velocidad (km/h)")
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("telemetria_velocidad.png", dpi=150)
    plt.close()
    
    print(f"Ruta más larga: {len(ruta_mas_larga)} puntos")
    print(f"Potencia: min={np.min(potencia):.2f}W, max={np.max(potencia):.2f}W, media={np.mean(potencia):.2f}W")
    print(f"SOC final: {soc[-1]:.2f} Wh")

def generar_mapa_ruta(lat_interp, lon_interp, alt_interp, spdKmh_interp, potencia_modelo_w, 
                      resultados_emisiones, nombre_archivo="ruta_mapa.html"):
    """
    Genera un mapa HTML interactivo con Folium mostrando la ruta realizada
    """
    # Filtrar puntos válidos
    puntos_validos = [(lat, lon, alt, vel, pot) for lat, lon, alt, vel, pot 
                     in zip(lat_interp, lon_interp, alt_interp, spdKmh_interp, potencia_modelo_w)
                     if lat != 0 and lon != 0]
    
    if not puntos_validos:
        print("No hay puntos GPS válidos para generar el mapa")
        return
    
    lat_validos = [p[0] for p in puntos_validos]
    lon_validos = [p[1] for p in puntos_validos]
    alt_validos = [p[2] for p in puntos_validos]
    vel_validos = [p[3] for p in puntos_validos]
    pot_validos = [p[4] for p in puntos_validos]
    
    # Calcular centro del mapa
    lat_centro = np.mean(lat_validos)
    lon_centro = np.mean(lon_validos)
    
    # Crear mapa base
    mapa = folium.Map(
        location=[lat_centro, lon_centro],
        zoom_start=13,
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
    
    # Función para convertir RGB a hexadecimal
    def rgb_to_hex(rgb):
        return '#{:02x}{:02x}{:02x}'.format(int(rgb[0]*255), int(rgb[1]*255), int(rgb[2]*255))
    
    # Colores en formato hexadecimal para Folium
    COLOR_AZUL_HEX = rgb_to_hex(COLOR_AZUL)  # #004B85
    COLOR_AMARILLO_HEX = rgb_to_hex(COLOR_AMARILLO)  # #FFC800
    COLOR_ROJO_HEX = rgb_to_hex(COLOR_ROJO)  # #C80000
    
    # Función para determinar color según velocidad
    def color_velocidad(vel):
        if vel < 40:
            return COLOR_AZUL_HEX
        elif vel < 80:
            return COLOR_AMARILLO_HEX
        else:
            return COLOR_ROJO_HEX
    
    # Crear línea de la ruta con colores según velocidad
    puntos_ruta = [[lat, lon] for lat, lon in zip(lat_validos, lon_validos)]
    
    # Agregar línea de la ruta segmentada por velocidad
    for i in range(len(puntos_ruta) - 1):
        color = color_velocidad(vel_validos[i])
        folium.PolyLine(
            locations=[puntos_ruta[i], puntos_ruta[i+1]],
            color=color,
            weight=6,
            opacity=0.7,
            popup=f"Vel: {vel_validos[i]:.1f} km/h"
        ).add_to(mapa)
    
    # Agregar marcador de inicio
    folium.Marker(
        location=[lat_validos[0], lon_validos[0]],
        popup=folium.Popup(
            f"<b>Inicio</b><br>"
            f"Velocidad: {vel_validos[0]:.1f} km/h<br>"
            f"Altitud: {alt_validos[0]:.1f} m<br>"
            f"Potencia: {pot_validos[0]:.1f} W",
            max_width=200
        ),
        icon=folium.Icon(color='blue', icon='play')  # Usa azul estándar de Folium
    ).add_to(mapa)
    
    # Agregar marcador de fin
    folium.Marker(
        location=[lat_validos[-1], lon_validos[-1]],
        popup=folium.Popup(
            f"<b>Fin</b><br>"
            f"Velocidad: {vel_validos[-1]:.1f} km/h<br>"
            f"Altitud: {alt_validos[-1]:.1f} m<br>"
            f"Potencia: {pot_validos[-1]:.1f} W",
            max_width=200
        ),
        icon=folium.Icon(color='red', icon='stop')
    ).add_to(mapa)
    
    # Agregar algunos puntos intermedios con información detallada
    num_marcadores = min(10, len(puntos_validos))
    indices_marcadores = np.linspace(0, len(puntos_validos) - 1, num_marcadores, dtype=int)
    
    for idx in indices_marcadores[1:-1]:  # Excluir inicio y fin
        folium.CircleMarker(
            location=[lat_validos[idx], lon_validos[idx]],
            radius=5,
            popup=folium.Popup(
                f"<b>Punto {idx}</b><br>"
                f"Velocidad: {vel_validos[idx]:.1f} km/h<br>"
                f"Altitud: {alt_validos[idx]:.1f} m<br>"
                f"Potencia: {pot_validos[idx]:.1f} W",
                max_width=200
            ),
            color=color_velocidad(vel_validos[idx]),
            fill=True,
            fillColor=color_velocidad(vel_validos[idx]),
            fillOpacity=0.6
        ).add_to(mapa)
    
    # Agregar leyenda de colores
    legend_html = f'''
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 220px; height: 130px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 10px">
    <p><b>Velocidad (km/h)</b></p>
    <p><span style="color:{COLOR_AZUL_HEX}; font-size:16px;">●</span> Velocidad &lt; 40 km/h</p>
    <p><span style="color:{COLOR_AMARILLO_HEX}; font-size:16px;">●</span> 40 km/h ≤ Velocidad &lt; 80 km/h</p>
    <p><span style="color:{COLOR_ROJO_HEX}; font-size:16px;">●</span> Velocidad ≥ 80 km/h</p>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(legend_html))
    
    # Agregar información de la ruta en un panel
    info_html = f'''
    <div style="position: fixed; 
                top: 10px; right: 10px; width: 250px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>Información de la Ruta</h4>
    <p><b>Distancia:</b> {resultados_emisiones['distancia_km']:.2f} km</p>
    <p><b>Consumo Eléctrico:</b> {resultados_emisiones['consumo_electrico_kwh']:.3f} kWh</p>
    <p><b>Emisiones Eléctrica:</b> {resultados_emisiones['emisiones_electrico_kg']:.3f} kg CO₂</p>
    <p><b>Emisiones Combustión:</b> {resultados_emisiones['emisiones_combustion_kg']:.3f} kg CO₂</p>
    <p><b>Reducción:</b> {((resultados_emisiones['emisiones_combustion_kg'] - resultados_emisiones['emisiones_electrico_kg']) / resultados_emisiones['emisiones_combustion_kg'] * 100):.1f}%</p>
    </div>
    '''
    mapa.get_root().html.add_child(folium.Element(info_html))
    
    # Guardar mapa
    mapa.save(nombre_archivo)
    print(f"\nMapa HTML generado: {nombre_archivo}")

def error_modelo(params, speeds, slopes, ts, potencia_real, soc_real):
    params_dict = {
        'm': params[0],
        'cd': params[1],
        'a': params[2],
        'crr': params[3],
        'factor_correccion': params[4],
        'eficiencia_tren': params[5]
    }
    
    # Asegurar que ts sea un array numpy
    ts = np.array(ts) if not isinstance(ts, np.ndarray) else ts
    potencia_real = np.array(potencia_real) if not isinstance(potencia_real, np.ndarray) else potencia_real
    soc_real = np.array(soc_real) if not isinstance(soc_real, np.ndarray) else soc_real
    
    potencia_modelo_kw, _ = calcular_potencia_por_punto(speeds, slopes, hybrid_cont=0, params=params_dict)
    potencia_modelo_w = np.array(potencia_modelo_kw) * 1000
    soc_modelo = calcular_soc(potencia_modelo_w, ts, energia_inicial=2000.0)
    
    error_potencia = np.mean((potencia_modelo_w - potencia_real) ** 2)
    error_soc = np.mean((soc_modelo - soc_real) ** 2)
    
    return error_potencia + error_soc

def modelo_motocicleta_electrica():
    data = cargar_datos("datos-telemetry.json")
    rutas = identificar_rutas(data)
    ruta_mas_larga = max(rutas, key=len)
    
    iA, lat, lon, alt, spdKmh, ts = extraer_datos_ruta(ruta_mas_larga)
    potencia_real = iA * 48
    soc_real = calcular_soc(potencia_real, ts, energia_inicial=2000.0)
    
    pendientes = calcular_pendientes_desde_altitud(lat, lon, alt)
    tiempos = calcular_tiempos_desde_ts(ts)
    coordenadas = [[lat[i], lon[i], alt[i]] for i in range(len(lat))]
    
    # Interpolar vectores para mayor detalle
    print("\n=== Preprocesando vectores con interpolación ===")
    spdKmh_interp, pendientes_interp, tiempos_interp, coordenadas_interp = preprocesar_vectores(
        spdKmh.tolist(), 
        pendientes.tolist(), 
        tiempos.tolist(), 
        coordenadas, 
        puntos_intermedios=2
    )
    
    # Interpolar también los datos reales para comparación
    n_original = len(potencia_real)
    n_nuevo = len(spdKmh_interp)
    x_original = np.arange(n_original)
    x_nuevo = np.linspace(0, n_original - 1, n_nuevo)
    potencia_real_interp = np.interp(x_nuevo, x_original, potencia_real)
    
    # Interpolar ts para el cálculo de SOC
    ts_interp = np.interp(x_nuevo, x_original, ts)
    soc_real_interp = calcular_soc(potencia_real_interp, ts_interp, energia_inicial=2000.0)
    
    print(f"Puntos originales: {n_original}")
    print(f"Puntos interpolados: {n_nuevo}")
    
    print("\n=== Optimizando parámetros del modelo ===")
    params_iniciales = np.array([140.0, 0.3, 0.74, 0.01, 1.617, 0.85])
    bounds = [
        (50, 200),      # m
        (0.1, 1.0),     # cd
        (0.3, 1.5),     # a
        (0.005, 0.05),  # crr
        (0.5, 3.0),     # factor_correccion
        (0.6, 0.95)     # eficiencia_tren
    ]
    
    resultado = minimize(
        error_modelo,
        params_iniciales,
        args=(spdKmh_interp, pendientes_interp, ts_interp, potencia_real_interp, soc_real_interp),
        method='L-BFGS-B',
        bounds=bounds,
        options={'maxiter': 100}
    )
    
    params_optimizados = {
        'm': resultado.x[0],
        'cd': resultado.x[1],
        'a': resultado.x[2],
        'crr': resultado.x[3],
        'factor_correccion': resultado.x[4],
        'eficiencia_tren': resultado.x[5]
    }
    
    print(f"Parámetros optimizados:")
    print(f"  Masa (m): {params_optimizados['m']:.2f} kg")
    print(f"  Coef. arrastre (cd): {params_optimizados['cd']:.3f}")
    print(f"  Área frontal (a): {params_optimizados['a']:.3f} m²")
    print(f"  Coef. rodamiento (crr): {params_optimizados['crr']:.4f}")
    print(f"  Factor corrección: {params_optimizados['factor_correccion']:.3f}")
    print(f"  Eficiencia tren: {params_optimizados['eficiencia_tren']:.3f}")
    
    # Calcular modelo con datos interpolados (eléctrico y combustión)
    potencia_modelo_kw, potencia_combustion_kw = calcular_potencia_por_punto(
        spdKmh_interp, pendientes_interp, hybrid_cont=0, params=params_optimizados
    )
    potencia_modelo_w = np.array(potencia_modelo_kw) * 1000
    soc_modelo = calcular_soc(potencia_modelo_w, ts_interp, energia_inicial=2000.0)
    
    # Calcular potencia de combustión (simulando moto a combustión)
    _, potencia_combustion_kw_full = calcular_potencia_por_punto(
        spdKmh_interp, pendientes_interp, hybrid_cont=1, params=params_optimizados
    )
    potencia_combustion_w = np.array(potencia_combustion_kw_full) * 1000
    
    # Calcular consumo y emisiones equivalentes de ciclo de vida
    tiempos_interp_array = np.array(tiempos_interp)
    resultados_emisiones = calcular_consumo_y_emisiones(
        potencia_modelo_w, potencia_combustion_kw_full, tiempos_interp_array, spdKmh_interp
    )
    
    # Extraer coordenadas interpoladas para la ruta
    lat_interp = [coord[0] for coord in coordenadas_interp]
    lon_interp = [coord[1] for coord in coordenadas_interp]
    alt_interp = [coord[2] for coord in coordenadas_interp]
    
    # Grupo 1: Validación del modelo (2 gráficas)
    fig, axes = plt.subplots(1, 2, figsize=(16, 5))
    
    axes[0].plot(tiempos_interp_array, potencia_real_interp, color=COLOR_ROJO, linewidth=1.5, label="Telemetría", alpha=0.7)
    axes[0].plot(tiempos_interp_array, potencia_modelo_w, color=COLOR_AZUL, linewidth=1.5, label="Modelo Eléctrico", alpha=0.7)
    axes[0].set_title("Potencia: Modelo vs Telemetría")
    axes[0].set_xlabel("Tiempo (s)")
    axes[0].set_ylabel("Potencia (W)")
    axes[0].grid(True, alpha=0.3)
    axes[0].legend()
    
    axes[1].plot(tiempos_interp_array, soc_real_interp, color=COLOR_ROJO, linewidth=1.5, label="SOC Telemetría", alpha=0.7)
    axes[1].plot(tiempos_interp_array, soc_modelo, color=COLOR_AZUL, linewidth=1.5, label="SOC Modelo", alpha=0.7)
    axes[1].set_title("SOC: Modelo vs Telemetría (desde 2.0 kWh)")
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("SOC (Wh)")
    axes[1].grid(True, alpha=0.3)
    axes[1].legend()
    
    plt.tight_layout()
    plt.savefig("modelo_validacion.png", dpi=150)
    plt.close()
    
    # Grupo 2: Comparación de tecnologías (1 gráfica)
    fig, ax = plt.subplots(1, 1, figsize=(10, 5))
    
    ax.plot(tiempos_interp_array, potencia_modelo_w, color=COLOR_AZUL, linewidth=1.5, label="Eléctrica", alpha=0.7)
    ax.plot(tiempos_interp_array, potencia_combustion_w, color=COLOR_AMARILLO, linewidth=1.5, label="Combustión", alpha=0.7)
    ax.set_title("Potencia: Eléctrica vs Combustión")
    ax.set_xlabel("Tiempo (s)")
    ax.set_ylabel("Potencia (W)")
    ax.grid(True, alpha=0.3)
    ax.legend()
    
    plt.tight_layout()
    plt.savefig("modelo_comparacion_tecnologias.png", dpi=150)
    plt.close()
    
    # Grupo 3: Análisis espacial y temporal (2 gráficas)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    
    # Gráfica de la ruta GPS con colores según velocidad
    if len(lat_interp) > 0 and len(lon_interp) > 0 and any(lat_interp) and any(lon_interp):
        # Filtrar puntos válidos (no ceros)
        puntos_validos = [(lat, lon, vel) for lat, lon, vel in zip(lat_interp, lon_interp, spdKmh_interp) 
                         if lat != 0 and lon != 0]
        if puntos_validos:
            lat_validos = [p[0] for p in puntos_validos]
            lon_validos = [p[1] for p in puntos_validos]
            vel_validos = [p[2] for p in puntos_validos]
            
            # Función para determinar color según velocidad
            def color_velocidad_plot(vel):
                if vel < 40:
                    return COLOR_AZUL
                elif vel < 80:
                    return COLOR_AMARILLO
                else:
                    return COLOR_ROJO
            
            colores_plot = [color_velocidad_plot(vel) for vel in vel_validos]
            scatter = axes[0].scatter(lon_validos, lat_validos, c=colores_plot, 
                                    s=10, alpha=0.6, edgecolors='none')
            axes[0].plot(lon_validos, lat_validos, color=COLOR_GRIS, linewidth=0.5, alpha=0.3, zorder=0)
            axes[0].set_title("Ruta GPS (colores según velocidad)")
            axes[0].set_xlabel("Longitud")
            axes[0].set_ylabel("Latitud")
            axes[0].grid(True, alpha=0.3)
            
            # Agregar leyenda personalizada para los rangos de velocidad
            from matplotlib.patches import Patch
            legend_elements = [
                Patch(facecolor=COLOR_AZUL, alpha=0.6, label='Velocidad < 40 km/h'),
                Patch(facecolor=COLOR_AMARILLO, alpha=0.6, label='40 km/h ≤ Velocidad < 80 km/h'),
                Patch(facecolor=COLOR_ROJO, alpha=0.6, label='Velocidad ≥ 80 km/h')
            ]
            axes[0].legend(handles=legend_elements, loc='upper right', fontsize=9)
        else:
            axes[0].text(0.5, 0.5, 'No hay datos GPS válidos', 
                      ha='center', va='center', transform=axes[0].transAxes)
            axes[0].set_title("Ruta GPS")
    else:
        axes[0].text(0.5, 0.5, 'No hay datos GPS disponibles', 
                  ha='center', va='center', transform=axes[0].transAxes)
        axes[0].set_title("Ruta GPS")
    
    # Gráfica de velocidad vs tiempo
    axes[1].plot(tiempos_interp_array, spdKmh_interp, color=COLOR_AZUL, linewidth=1.5)
    axes[1].set_title("Velocidad vs Tiempo")
    axes[1].set_xlabel("Tiempo (s)")
    axes[1].set_ylabel("Velocidad (km/h)")
    axes[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig("modelo_analisis_espacial.png", dpi=150)
    plt.close()
    
    # Grupo 4: Análisis de emisiones (1 gráfica)
    fig, ax = plt.subplots(1, 1, figsize=(8, 6))
    
    tipos = ['Eléctrica', 'Combustión']
    emisiones = [resultados_emisiones['emisiones_electrico_kg'], resultados_emisiones['emisiones_combustion_kg']]
    colores = [COLOR_AZUL, COLOR_AMARILLO]
    bars = ax.bar(tipos, emisiones, color=colores, alpha=0.7, edgecolor=COLOR_NEGRO, linewidth=1.5)
    ax.set_title("Emisiones Equivalentes de Ciclo de Vida")
    ax.set_ylabel("CO₂ (kg)")
    ax.grid(True, alpha=0.3, axis='y')
    # Agregar valores en las barras
    for bar, emision in zip(bars, emisiones):
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{emision:.3f} kg',
                ha='center', va='bottom', fontweight='bold')
    
    plt.tight_layout()
    plt.savefig("modelo_emisiones.png", dpi=150)
    plt.close()
    
    error_potencia_medio = np.mean(np.abs(potencia_modelo_w - potencia_real_interp))
    error_soc_medio = np.mean(np.abs(soc_modelo - soc_real_interp))
    correlacion_potencia = np.corrcoef(potencia_modelo_w, potencia_real_interp)[0, 1]
    correlacion_soc = np.corrcoef(soc_modelo, soc_real_interp)[0, 1]
    
    # Calcular errores porcentuales
    potencia_real_no_cero = np.where(potencia_real_interp != 0, potencia_real_interp, 1)
    error_porcentual_potencia = np.mean(np.abs((potencia_modelo_w - potencia_real_interp) / potencia_real_no_cero)) * 100
    
    soc_real_no_cero = np.where(soc_real_interp != 0, soc_real_interp, 1)
    error_porcentual_soc = np.mean(np.abs((soc_modelo - soc_real_interp) / soc_real_no_cero)) * 100
    
    error_porcentual_potencia_final = np.abs((potencia_modelo_w[-1] - potencia_real_interp[-1]) / potencia_real_no_cero[-1]) * 100 if potencia_real_no_cero[-1] != 0 else 0
    error_porcentual_soc_final = np.abs((soc_modelo[-1] - soc_real_interp[-1]) / soc_real_no_cero[-1]) * 100 if soc_real_no_cero[-1] != 0 else 0
    
    print(f"\n=== Resultados del Modelo ===")
    print(f"Puntos originales: {len(ruta_mas_larga)}")
    print(f"Puntos interpolados: {n_nuevo}")
    print(f"Potencia modelo: min={np.min(potencia_modelo_w):.2f}W, max={np.max(potencia_modelo_w):.2f}W, media={np.mean(potencia_modelo_w):.2f}W")
    print(f"Potencia real: min={np.min(potencia_real_interp):.2f}W, max={np.max(potencia_real_interp):.2f}W, media={np.mean(potencia_real_interp):.2f}W")
    print(f"Error medio potencia: {error_potencia_medio:.2f} W")
    print(f"Error porcentual medio potencia: {error_porcentual_potencia:.2f}%")
    print(f"Correlación potencia: {correlacion_potencia:.4f}")
    print(f"SOC modelo final: {soc_modelo[-1]:.2f} Wh")
    print(f"SOC real final: {soc_real_interp[-1]:.2f} Wh")
    print(f"Error medio SOC: {error_soc_medio:.2f} Wh")
    print(f"Error porcentual medio SOC: {error_porcentual_soc:.2f}%")
    print(f"Error porcentual SOC final: {error_porcentual_soc_final:.2f}%")
    print(f"Correlación SOC: {correlacion_soc:.4f}")
    
    print(f"\n=== Comparación Eléctrica vs Combustión ===")
    print(f"Distancia total: {resultados_emisiones['distancia_km']:.2f} km")
    print(f"\nConsumo Energético:")
    print(f"  Eléctrica: {resultados_emisiones['consumo_electrico_kwh']:.3f} kWh")
    print(f"  Combustión: {resultados_emisiones['consumo_combustion_kwh']:.3f} kWh")
    print(f"  Combustión equivalente: {resultados_emisiones['consumo_galones']:.3f} galones")
    print(f"\nEmisiones Equivalentes de Ciclo de Vida:")
    print(f"  Factor emisión eléctrica: {resultados_emisiones['factor_emision_electrico']} gCO₂/km")
    print(f"  Factor emisión combustión: {resultados_emisiones['factor_emision_combustion']} gCO₂/km")
    print(f"  Emisiones eléctrica: {resultados_emisiones['emisiones_electrico_kg']:.3f} kg CO₂")
    print(f"  Emisiones combustión: {resultados_emisiones['emisiones_combustion_kg']:.3f} kg CO₂")
    reduccion_porcentual = ((resultados_emisiones['emisiones_combustion_kg'] - resultados_emisiones['emisiones_electrico_kg']) / 
                           resultados_emisiones['emisiones_combustion_kg']) * 100
    print(f"  Reducción de emisiones: {reduccion_porcentual:.1f}%")
    
    # Generar mapa HTML con la ruta
    print("\n=== Generando mapa HTML de la ruta ===")
    generar_mapa_ruta(lat_interp, lon_interp, alt_interp, spdKmh_interp, potencia_modelo_w, 
                     resultados_emisiones, nombre_archivo="ruta_mapa.html")

if __name__ == "__main__":
    main()
    print("\n" + "="*50)
    modelo_motocicleta_electrica()
