# -*- coding: utf-8 -*-
"""
Script auxiliar para ejecutar la extracción de información
para múltiples territorios.
"""

import subprocess
import sys
import os

territories = ["Bogota", "Valle de aburra"]

print("="*70)
print("   EJECUTANDO EXTRACCIÓN DE INFORMACIÓN")
print("="*70)

for territory in territories:
    print(f"\n{'='*70}")
    print(f"   Procesando: {territory}")
    print(f"{'='*70}\n")
    
    # Ejecutar extract_cluster_info.py
    print(f"1. Extrayendo información de clusters para {territory}...")
    try:
        result = subprocess.run(
            [sys.executable, "extract_cluster_info.py", territory],
            check=True,
            capture_output=False
        )
        print(f"   Clusters extraídos exitosamente\n")
    except subprocess.CalledProcessError as e:
        print(f"   Error al extraer clusters: {e}\n")
        continue
    
    # Ejecutar extract_stations_info.py
    print(f"2. Extrayendo información de estaciones para {territory}...")
    try:
        result = subprocess.run(
            [sys.executable, "extract_stations_info.py", territory],
            check=True,
            capture_output=False
        )
        print(f"   Estaciones extraídas exitosamente\n")
    except subprocess.CalledProcessError as e:
        print(f"   Error al extraer estaciones: {e}\n")
        continue

print("\n" + "="*70)
print("   EXTRACCIÓN COMPLETA")
print("="*70)


