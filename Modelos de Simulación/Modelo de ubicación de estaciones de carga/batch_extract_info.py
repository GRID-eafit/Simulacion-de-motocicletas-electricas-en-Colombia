# -*- coding: utf-8 -*-
"""
Script para ejecutar la extracción de información de clusters y estaciones
para Bogotá y Valle de Aburrá.
"""

import sys
import os

# Agregar el directorio actual al path
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# Importar las funciones principales de los scripts
from extract_cluster_info import main as extract_clusters_main
from extract_stations_info import main as extract_stations_main

territories = ["Bogota", "Valle de aburra"]

print("="*70)
print("   EJECUTANDO EXTRACCIÓN DE INFORMACIÓN")
print("="*70)

for territory in territories:
    print(f"\n{'='*70}")
    print(f"   Procesando: {territory}")
    print(f"{'='*70}\n")
    
    # Configurar el territorio
    os.environ['ANALYSIS_LOCALE'] = territory
    
    # Ejecutar extract_cluster_info.py
    print(f"1. Extrayendo información de clusters para {territory}...")
    try:
        # Modificar sys.argv para simular el argumento
        original_argv = sys.argv[:]
        sys.argv = ['extract_cluster_info.py', territory]
        extract_clusters_main()
        sys.argv = original_argv
        print(f"   Clusters extraídos exitosamente\n")
    except Exception as e:
        print(f"   Error al extraer clusters: {e}\n")
        import traceback
        traceback.print_exc()
        sys.argv = original_argv
        continue
    
    # Ejecutar extract_stations_info.py
    print(f"2. Extrayendo información de estaciones para {territory}...")
    try:
        # Modificar sys.argv para simular el argumento
        original_argv = sys.argv[:]
        sys.argv = ['extract_stations_info.py', territory]
        extract_stations_main()
        sys.argv = original_argv
        print(f"   Estaciones extraídas exitosamente\n")
    except Exception as e:
        print(f"   Error al extraer estaciones: {e}\n")
        import traceback
        traceback.print_exc()
        sys.argv = original_argv
        continue

print("\n" + "="*70)
print("   EXTRACCIÓN COMPLETA")
print("="*70)


