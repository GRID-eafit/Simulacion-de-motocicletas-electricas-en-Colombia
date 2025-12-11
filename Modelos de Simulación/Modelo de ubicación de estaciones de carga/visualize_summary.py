# -*- coding: utf-8 -*-
"""
Created on Mon Jun 30 13:59:55 2025
"""

import json5 as json
import matplotlib.pyplot as plt
import numpy as np
import os

def plot_summary_results():
    """
    Loads the aggregated simulation data from milp_input_data.json
    and creates bar charts to visualize and compare the routes.
    """
    script_dir = os.path.dirname(os.path.abspath(__file__))
    input_filename = "milp_input_data.json"
    input_folder = os.path.join(script_dir, "Archivos de apoyo")
    full_path = os.path.join(input_folder, input_filename)
    
    try:
        with open(full_path, 'r') as f:
            data = json.load(f)
        print(f"Successfully loaded summary data from '{input_filename}'.")
    except FileNotFoundError:
        print(f"ERROR: '{input_filename}' not found. Please run real_path_simulation.py first.")
        return

    if not data:
        print("No data to visualize.")
        return

    # Prepare data for plotting
    route_labels = [f"Route {d['route_index']}" for d in data]
    distances = [d['distance_km'] for d in data]
    durations = [d['duration_minutes'] for d in data]
    electric_wh = [d['electric_wh_consumed'] for d in data]
    fuel_gal = [d['fuel_gallons_consumed'] for d in data]
    
    # Create a 2x2 grid of plots
    fig, axs = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle('Resumen de Resultados de Simulación para Todas las Rutas', fontsize=16)

    # Plot 1: Distance
    axs[0, 0].bar(route_labels, distances, color='skyblue')
    axs[0, 0].set_title('Distancia por Ruta')
    axs[0, 0].set_ylabel('Distancia (km)')
    
    # Plot 2: Duration
    axs[0, 1].bar(route_labels, durations, color='lightcoral')
    axs[0, 1].set_title('Duración por Ruta')
    axs[0, 1].set_ylabel('Duración (minutos)')
    
    # Plot 3: Electric Energy Consumed
    axs[1, 0].bar(route_labels, electric_wh, color='limegreen')
    axs[1, 0].set_title('Energía Eléctrica Consumida')
    axs[1, 0].set_ylabel('Energía (Wh)')
    
    # Plot 4: Fuel Consumed
    axs[1, 1].bar(route_labels, fuel_gal, color='sandybrown')
    axs[1, 1].set_title('Combustible Consumido')
    axs[1, 1].set_ylabel('Combustible (galones)')
    
    # Improve layout for all subplots
    for ax in axs.flat:
        ax.tick_params(axis='x', labelrotation=45)
        ax.grid(True, linestyle='--', alpha=0.6)
        
    plt.tight_layout(rect=[0, 0.03, 1, 0.95])
    plt.show()

if __name__ == '__main__':
    plot_summary_results()