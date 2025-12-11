import numpy as np
import math

def bike_model_particle(hybrid_cont, speeds, slopes, vehicle_params):
    """
    Modelo optimizado de consumo de motocicleta eléctrica/híbrida.
    
    Este modelo está basado en parámetros optimizados mediante análisis de telemetría real
    obtenidos del archivo telemetry.py ubicado en la carpeta "Puntos de rutas".
    
    Los parámetros optimizados fueron calibrados usando datos reales de motocicletas eléctricas
    en condiciones de operación urbana, garantizando precisión en el cálculo de consumo energético.
    
    Args:
        hybrid_cont: Contribución híbrida (0 = eléctrico puro, 1 = combustión pura)
        speeds: Lista de velocidades en km/h
        slopes: Lista de pendientes en grados
        vehicle_params: Diccionario con parámetros del vehículo desde config.jsonc
                       Si no se proporciona, se usan los valores optimizados por defecto
    
    Returns:
        State_bater: Estado final de la batería en Wh
        combus: Lista de consumo de combustible en galones por punto
        combus2: Lista de consumo de combustible en Wh por punto
        E_TOTAL: Lista de consumo total de energía en Wh por punto
    
    Referencia:
        Parámetros optimizados obtenidos de: Puntos de rutas/telemetry.py
        Implementación original: calcular_potencia_por_punto()
    """
    # Parámetros optimizados del modelo (basados en telemetry.py)
    # Estos valores fueron obtenidos mediante optimización con datos de telemetría real
    # Fuente: Puntos de rutas/telemetry.py - función calcular_potencia_por_punto()
    params_optimizados = {
        'm': 140.0,           # Masa optimizada (kg) - validada con telemetría
        'cd': 0.3,            # Coeficiente de arrastre optimizado
        'a': 0.74,            # Área frontal optimizada (m²)
        'crr': 0.01,          # Coeficiente de rodamiento optimizado
        'factor_correccion': 1.617,  # Factor de corrección optimizado (calibrado)
        'eficiencia_tren': 0.85      # Eficiencia del tren motriz optimizada
    }
    
    # Usar parámetros del vehículo si están disponibles, sino usar los optimizados
    if vehicle_params:
        m = vehicle_params.get('chassis', {}).get('m', params_optimizados['m'])
        cd = vehicle_params.get('chassis', {}).get('cd', params_optimizados['cd'])
        a = vehicle_params.get('chassis', {}).get('a', params_optimizados['a'])
        crr = vehicle_params.get('chassis', {}).get('crr', params_optimizados['crr'])
        rho = vehicle_params.get('ambient', {}).get('rho', 1.225)
        g = vehicle_params.get('ambient', {}).get('g', 9.81)
        rw = vehicle_params.get('wheel', {}).get('rw', 0.3)
    else:
        m = params_optimizados['m']
        cd = params_optimizados['cd']
        a = params_optimizados['a']
        crr = params_optimizados['crr']
        rho = 1.225
        g = 9.81
        rw = 0.3
    
    # Usar parámetros optimizados para eficiencia y factor de corrección
    eficiencia_tren = params_optimizados['eficiencia_tren']
    factor_correccion = params_optimizados['factor_correccion']
    
    last_vel = 0
    State_bater = 3700  # Estado inicial de batería en Wh
    Energy = []
    combus = []
    combus2 = []
    E_TOTAL = []

    for i in range(len(speeds)):
        vel = speeds[i] / 3.6  # Convertir km/h a m/s
        theta = slopes[i] * math.pi / 180  # Convertir grados a radianes
        
        # Cálculo de fuerzas (modelo optimizado)
        faero = 0.5 * rho * a * cd * (vel ** 2)
        froll = g * m * crr * np.cos(theta)
        fg = g * m * np.sin(theta)
        
        # Fuerza de inercia
        delta_v = vel - last_vel
        f_inertia = m * delta_v / 1  # dt = 1 segundo implícito
        
        # Fuerza resultante total
        fres = faero + froll + fg + f_inertia
        
        # Potencia mecánica requerida
        p_m = (fres * rw) * (vel / rw)
        
        # Potencia eléctrica (con eficiencia optimizada y factor de corrección)
        p_eb = p_m * (1 - hybrid_cont) / eficiencia_tren
        p_eb = p_eb * factor_correccion  # Aplicar factor de corrección optimizado
        
        if p_eb < 0:
            p_eb = 0
        
        # Potencia de combustión
        p_cn = p_m * hybrid_cont / 0.2
        if p_cn <= 0:
            p_cn = 0

        last_vel = vel
        
        # Convertir potencia a consumo de energía (Wh por segundo)
        # Dividir por 3600 para convertir de W a Wh/s
        pow_consumption = p_eb / 3600  # Consumo eléctrico en Wh/s
        pcn_consumption = p_cn / 3600   # Consumo de combustión en Wh/s
        
        # Actualizar estado de batería
        result1 = State_bater - pow_consumption
        if result1 < 0:
            result1 = 0
        
        # Conversión de energía de combustible a galones
        # Poder calorífico de gasolina (valor calibrado del modelo original)
        poder_calorifico_wh_galon = 36718.50158230244
        result2 = pcn_consumption / poder_calorifico_wh_galon
        
        Energy.append(result1)
        combus.append(result2)
        combus2.append(pcn_consumption)
        E_TOTAL.append(pow_consumption + pcn_consumption)
        State_bater = result1

    return State_bater, combus, combus2, E_TOTAL