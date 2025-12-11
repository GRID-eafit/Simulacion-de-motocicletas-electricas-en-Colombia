# -*- coding: utf-8 -*-
"""
Script para generar un mapa HTML interactivo con todas las estaciones
de carga para los 3 casos de estudio.
"""

import pandas as pd
import folium
from folium import plugins
import os

# Configuración
script_dir = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(script_dir, "Results")
results_folder = RESULTS

# Territorios y sus centros aproximados
territories_config = {
    "Bogota": {
        "name": "Bogotá",
        "center": [4.6097, -74.0817],
        "zoom": 11
    },
    "Medellin": {
        "name": "Medellín",
        "center": [6.2476, -75.5658],
        "zoom": 12
    },
    "Valle de aburra": {
        "name": "Valle de Aburrá",
        "center": [6.2442, -75.5812],
        "zoom": 11
    }
}

# Configuración de tecnologías
tech_config = {
    "Standard_Charger": {
        "name": "Cargador Estándar",
        "color": "blue",
        "icon": "plug"
    },
    "High_Capacity_Charger": {
        "name": "Cargador Alta Capacidad",
        "color": "green",
        "icon": "bolt"
    },
    "Battery_Swapping_Station": {
        "name": "Intercambio de Baterías",
        "color": "purple",
        "icon": "battery-full"
    }
}

def create_stations_map():
    """Crea un mapa interactivo con todas las estaciones."""
    
    # Calcular centro general (promedio de todos los territorios)
    all_lats = []
    all_lons = []
    all_stations = []
    
    # Cargar datos de cada territorio
    for territory_key, territory_info in territories_config.items():
        file_path = os.path.join(results_folder, f"optimal_solution_{territory_key}.csv")
        
        if os.path.exists(file_path):
            df = pd.read_csv(file_path)
            
            for _, row in df.iterrows():
                station_id = f"ST-{territory_key[:3].upper()}-{int(row['Cell_Row']):03d}-{int(row['Cell_Col']):03d}"
                all_lats.append(row['Latitude'])
                all_lons.append(row['Longitude'])
                
                tech_info = tech_config.get(row['Technology'], {
                    "name": row['Technology'],
                    "color": "gray",
                    "icon": "question"
                })
                
                all_stations.append({
                    'territory': territory_info['name'],
                    'station_id': station_id,
                    'technology': tech_info['name'],
                    'tech_key': row['Technology'],
                    'latitude': row['Latitude'],
                    'longitude': row['Longitude'],
                    'cell_row': int(row['Cell_Row']),
                    'cell_col': int(row['Cell_Col'])
                })
    
    # Calcular centro del mapa
    if all_lats and all_lons:
        center_lat = sum(all_lats) / len(all_lats)
        center_lon = sum(all_lons) / len(all_lons)
    else:
        center_lat, center_lon = 5.0, -74.0  # Centro aproximado de Colombia
    
    # Crear mapa base
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=6,
        tiles='OpenStreetMap'
    )
    
    # Agregar capas de mapas alternativos
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)
    
    # Crear grupos de marcadores por territorio
    feature_groups = {}
    for territory_name in territories_config.values():
        feature_groups[territory_name['name']] = folium.FeatureGroup(name=territory_name['name']).add_to(m)
    
    # Agregar marcadores
    for station in all_stations:
        tech_info = tech_config.get(station['tech_key'], {
            "name": station['technology'],
            "color": "gray",
            "icon": "question"
        })
        
        # Crear popup con información
        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 5px 0; color: #333;">{station['station_id']}</h4>
            <hr style="margin: 5px 0;">
            <p style="margin: 3px 0;"><b>Caso de Estudio:</b> {station['territory']}</p>
            <p style="margin: 3px 0;"><b>Tecnología:</b> {tech_info['name']}</p>
            <p style="margin: 3px 0;"><b>Latitud:</b> {station['latitude']:.6f}°</p>
            <p style="margin: 3px 0;"><b>Longitud:</b> {station['longitude']:.6f}°</p>
            <p style="margin: 3px 0;"><b>Celda:</b> ({station['cell_row']}, {station['cell_col']})</p>
        </div>
        """
        
        # Crear marcador
        marker = folium.Marker(
            location=[station['latitude'], station['longitude']],
            popup=folium.Popup(popup_html, max_width=300),
            tooltip=f"{station['station_id']} - {tech_info['name']}",
            icon=folium.Icon(
                color=tech_info['color'],
                icon=tech_info['icon'],
                prefix='fa'
            )
        )
        
        # Agregar al grupo correspondiente
        marker.add_to(feature_groups[station['territory']])
    
    # Agregar control de capas
    folium.LayerControl(collapsed=False).add_to(m)
    
    # Agregar leyenda
    legend_html = '''
    <div style="position: fixed; 
                bottom: 50px; right: 50px; width: 250px; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:14px; padding: 15px; border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
    <h4 style="margin-top: 0; margin-bottom: 10px; color: #333;">Leyenda</h4>
    <hr style="margin: 5px 0;">
    <p style="margin: 5px 0;"><b>Tecnologías:</b></p>
    <p style="margin: 3px 0;">
        <i class="fa fa-plug" style="color: blue; margin-right: 5px;"></i>
        Cargador Estándar
    </p>
    <p style="margin: 3px 0;">
        <i class="fa fa-bolt" style="color: green; margin-right: 5px;"></i>
        Cargador Alta Capacidad
    </p>
    <p style="margin: 3px 0;">
        <i class="fa fa-battery-full" style="color: purple; margin-right: 5px;"></i>
        Intercambio de Baterías
    </p>
    <hr style="margin: 10px 0;">
    <p style="margin: 5px 0;"><b>Total:</b> ''' + str(len(all_stations)) + ''' estaciones</p>
    <p style="margin: 3px 0; font-size: 12px; color: #666;">
        Usa los controles en la esquina superior derecha para mostrar/ocultar territorios
    </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Agregar título
    title_html = '''
    <div style="position: fixed; 
                top: 10px; left: 50px; width: auto; height: auto; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:16px; padding: 10px 15px; border-radius: 5px;
                box-shadow: 0 2px 5px rgba(0,0,0,0.3);">
    <h3 style="margin: 0; color: #333;">Estaciones de Carga Optimizadas</h3>
    <p style="margin: 5px 0 0 0; font-size: 12px; color: #666;">
        Casos de Estudio: Bogotá, Medellín y Valle de Aburrá
    </p>
    </div>
    '''
    m.get_root().html.add_child(folium.Element(title_html))
    
    # Guardar mapa
    output_file = os.path.join(results_folder, "estaciones_mapa.html")
    m.save(output_file)
    
    print(f"Mapa HTML generado: {output_file}")
    print(f"  Total de estaciones: {len(all_stations)}")
    
    # Mostrar resumen
    print("\nResumen por territorio:")
    for territory_name in territories_config.values():
        count = len([s for s in all_stations if s['territory'] == territory_name['name']])
        print(f"  - {territory_name['name']}: {count} estaciones")
    
    return output_file

if __name__ == "__main__":
    print("="*70)
    print("   GENERANDO MAPA INTERACTIVO DE ESTACIONES")
    print("="*70)
    print()
    
    output_file = create_stations_map()
    
    print("\n" + "="*70)
    print("PROCESO COMPLETADO")
    print("="*70)
    print(f"\nArchivo generado: {output_file}")
    print("\nAbre el archivo en tu navegador para ver el mapa interactivo.")



