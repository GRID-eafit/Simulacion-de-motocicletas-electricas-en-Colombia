# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 14:30:30 2025
"""
import os
import json
import pickle
import folium
from folium import Element
import webbrowser

def create_summary_map_from_cache(routes_to_load):
    """
    Loads route data from cache files and generates a single interactive
    map showing all processed routes with selectable animations.
    """
    print("Loading route geometries from cache to generate summary map...")
    
    all_route_geometries = []
    # Loop through the routes defined in routes.json
    for route_task in routes_to_load:
        start_point = route_task['start']
        end_point = route_task['end']
        
        # Reconstruct the cache filename for each route
        script_dir = os.path.dirname(os.path.abspath(__file__))
        cache_filename = f"route_cache_{start_point['lat']}_{start_point['lon']}_to_{end_point['lat']}_{end_point['lon']}.pkl"
        cache_folder = os.path.join(script_dir, "Route Cache")
        full_path_cache = os.path.join(cache_folder, cache_filename)
        if os.path.exists(full_path_cache):
            with open(full_path_cache, 'rb') as f:
                # Load the detailed route data from the pickle file
                route_data = pickle.load(f)
                all_route_geometries.append(route_data)
        else:
            print(f"Warning: Cache file not found for a route, it will be skipped on the map: {cache_filename}")

    if not all_route_geometries:
        print("No cached route data found to generate a map.")
        return

    # --- Map Creation Logic (from your provided function) ---
    print("Generating final interactive summary map...")
    start_location = [all_route_geometries[0][0]["latitude"], all_route_geometries[0][0]["longitude"]]
    m = folium.Map(location=start_location, zoom_start=11)
    map_name = m.get_name()

    colors = ['blue', 'red', 'green', 'purple', 'orange', 'darkred', 'darkblue', 'lightgreen', 'cadetblue', 'darkpurple']
    for i, route_data in enumerate(all_route_geometries):
        coords = [(p["latitude"], p["longitude"]) for p in route_data]
        color = colors[i % len(colors)]
        line = folium.PolyLine(locations=coords, color=color, weight=5, opacity=0.8)
        popup_html = f'<button onclick="window.startOrRestartAnimation({i})">Animate Route {i+1}</button>'
        line.add_child(folium.Popup(popup_html))
        line.add_to(m)

    js_all_routes = json.dumps([
        [[p["latitude"], p["longitude"], p["slope_pct"]] for p in route_data]
        for route_data in all_route_geometries
    ])
    
    # Embed the advanced JavaScript and CSS
    js_code = f"""
    <style>
      .folium-popup-content button {{
        padding: 8px 12px; font-size: 14px; font-weight: bold;
        background-color: #fff; border: 1px solid #ccc;
        border-radius: 5px; cursor: pointer;
      }}
    </style>
    <script>
        setTimeout(function() {{
            const all_routes = {js_all_routes};
            if (!all_routes || all_routes.length === 0) return;

            let animationTimeoutId = null;
            let frame_index = 0;
            let current_points = [];

            var marker = L.circleMarker([0,0], {{
                radius: 8, color: 'black', weight: 1, fillOpacity: 1
            }}).addTo({map_name});

            function getColor(slope) {{
                if (slope > 5) return 'red';
                if (slope < -5) return 'blue';
                return 'green';
            }}
            
            function runAnimationFrame() {{
                if (frame_index >= current_points.length) {{
                    clearTimeout(animationTimeoutId);
                    return;
                }}
                const point = current_points[frame_index];
                const color = getColor(point[2]);
                marker.setLatLng([point[0], point[1]]);
                marker.setStyle({{fillColor: color}});
                frame_index++;
                animationTimeoutId = setTimeout(runAnimationFrame, 50);
            }}

            window.startOrRestartAnimation = function(routeIndex) {{
                if (animationTimeoutId) clearTimeout(animationTimeoutId);
                current_points = all_routes[routeIndex];
                if (!current_points || current_points.length === 0) return;
                marker.setLatLng([current_points[0][0], current_points[0][1]]);
                frame_index = 0;
                runAnimationFrame();
            }};
        }}, 100);
    </script>
    """
    m.get_root().html.add_child(Element(js_code))

    script_dir = os.path.dirname(os.path.abspath(__file__))
    file_name = "summary_animated_map.html"
    output_folder = os.path.join(script_dir, "Results")
    full_path = os.path.join(output_folder, file_name)
    m.save(full_path)
    print(f"Final interactive summary map saved to: {full_path}")
    webbrowser.open('file://' + os.path.realpath(full_path))


if __name__ == '__main__':
    try:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        Support_folder = os.path.join(script_dir, "Archivos de apoyo")
        os.makedirs(Support_folder, exist_ok=True)
        file_name = "routes.json"
        routes_path = os.path.join(Support_folder, file_name)
        with open(routes_path, 'r') as f:
            routes = json.load(f)
        create_summary_map_from_cache(routes)
    except FileNotFoundError:
        print("ERROR: 'routes.json' file not found. Cannot determine which routes to map.")