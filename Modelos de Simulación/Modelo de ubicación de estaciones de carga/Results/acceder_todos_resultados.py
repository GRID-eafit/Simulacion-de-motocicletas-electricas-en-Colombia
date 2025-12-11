#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script para acceder y visualizar todos los resultados del proyecto
Proyecto Delfín 2025
"""

import os
import webbrowser
import subprocess
import sys
from pathlib import Path

# Colores para terminal
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text:^70}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.ENDC}\n")

def print_section(text):
    print(f"\n{Colors.OKCYAN}{Colors.BOLD}{text}{Colors.ENDC}")
    print(f"{Colors.OKCYAN}{'-'*70}{Colors.ENDC}")

def list_files(directory, pattern, description):
    """Lista archivos que coinciden con un patrón"""
    files = list(Path(directory).glob(pattern))
    if files:
        print(f"\n{Colors.OKGREEN}{description}:{Colors.ENDC}")
        for f in sorted(files):
            print(f"  • {f.name}")
        return files
    else:
        print(f"{Colors.WARNING}No se encontraron archivos para: {description}{Colors.ENDC}")
        return []

def open_file(filepath):
    """Abre un archivo con el programa predeterminado"""
    try:
        if sys.platform == "win32":
            os.startfile(filepath)
        elif sys.platform == "darwin":
            subprocess.run(["open", filepath])
        else:
            subprocess.run(["xdg-open", filepath])
        return True
    except Exception as e:
        print(f"{Colors.FAIL}Error al abrir archivo: {e}{Colors.ENDC}")
        return False

def main():
    results_dir = Path(__file__).parent
    
    print_header("ACCESO A TODOS LOS RESULTADOS - PROYECTO DELFÍN 2025")
    
    print(f"{Colors.BOLD}Directorio de resultados:{Colors.ENDC} {results_dir}")
    
    # 1. Mapas Interactivos HTML
    print_section("1. MAPAS INTERACTIVOS HTML")
    html_files = list_files(results_dir, "optimal_locations_map_*.html", "Mapas interactivos")
    
    # 2. Informe LaTeX
    print_section("2. INFORME LATEX")
    tex_files = list_files(results_dir, "*.tex", "Archivos LaTeX")
    
    # 3. Soluciones Óptimas CSV
    print_section("3. SOLUCIONES ÓPTIMAS (CSV)")
    csv_optimal = list_files(results_dir, "optimal_solution_*.csv", "Soluciones óptimas")
    
    # 4. Gráficos por Ciudad
    cities = ["Bogota", "Medellin", "Valle de aburra"]
    for city in cities:
        print_section(f"4. GRÁFICOS - {city.upper()}")
        # Clusters
        list_files(results_dir, f"3_clusters_*_{city}.png", "Clusters")
        # Flujos
        list_files(results_dir, f"4_flows_map_*_{city}.png", "Flujos de demanda")
        # Hotspots y muestreo
        list_files(results_dir, f"5_*_{city}.png", "Hotspots y muestreo")
    
    # 5. Menú Interactivo
    print_header("MENÚ DE ACCESO RÁPIDO")
    
    while True:
        print(f"\n{Colors.BOLD}Opciones:{Colors.ENDC}")
        print("  1. Abrir mapas interactivos HTML")
        print("  2. Ver soluciones óptimas (CSV)")
        print("  3. Compilar informe LaTeX")
        print("  4. Abrir carpeta de resultados")
        print("  5. Ver índice completo")
        print("  6. Salir")
        
        choice = input(f"\n{Colors.OKCYAN}Selecciona una opción (1-6): {Colors.ENDC}").strip()
        
        if choice == "1":
            print_section("ABRIENDO MAPAS INTERACTIVOS")
            for html_file in html_files:
                print(f"Abriendo: {html_file.name}")
                webbrowser.open(f"file://{html_file.absolute()}")
                input("Presiona Enter para continuar...")
        
        elif choice == "2":
            print_section("SOLUCIONES ÓPTIMAS")
            for i, csv_file in enumerate(csv_optimal, 1):
                print(f"{i}. {csv_file.name}")
            sel = input(f"\n{Colors.OKCYAN}Selecciona un archivo (número) o 'todos': {Colors.ENDC}").strip()
            if sel.lower() == "todos":
                for csv_file in csv_optimal:
                    open_file(csv_file)
            elif sel.isdigit() and 1 <= int(sel) <= len(csv_optimal):
                open_file(csv_optimal[int(sel)-1])
        
        elif choice == "3":
            print_section("COMPILANDO INFORME LATEX")
            tex_file = results_dir / "informe_resultados_simulacion.tex"
            if tex_file.exists():
                print(f"Compilando: {tex_file.name}")
                try:
                    subprocess.run(["pdflatex", str(tex_file)], cwd=results_dir, check=True)
                    print(f"{Colors.OKGREEN}Primera compilación completada{Colors.ENDC}")
                    subprocess.run(["pdflatex", str(tex_file)], cwd=results_dir, check=True)
                    print(f"{Colors.OKGREEN}Segunda compilación completada{Colors.ENDC}")
                    print(f"{Colors.OKGREEN}PDF generado exitosamente{Colors.ENDC}")
                except subprocess.CalledProcessError:
                    print(f"{Colors.FAIL}Error al compilar. Asegúrate de tener pdflatex instalado.{Colors.ENDC}")
                except FileNotFoundError:
                    print(f"{Colors.FAIL}pdflatex no encontrado. Instala TeX Live o MiKTeX.{Colors.ENDC}")
            else:
                print(f"{Colors.WARNING}Archivo LaTeX no encontrado{Colors.ENDC}")
        
        elif choice == "4":
            print_section("ABRIENDO CARPETA DE RESULTADOS")
            open_file(results_dir)
        
        elif choice == "5":
            print_section("ÍNDICE COMPLETO")
            index_file = results_dir / "INDICE_RESULTADOS.md"
            if index_file.exists():
                open_file(index_file)
            else:
                print(f"{Colors.WARNING}Archivo de índice no encontrado{Colors.ENDC}")
        
        elif choice == "6":
            print(f"\n{Colors.OKGREEN}¡Hasta luego!{Colors.ENDC}\n")
            break
        
        else:
            print(f"{Colors.WARNING}Opción no válida{Colors.ENDC}")

if __name__ == "__main__":
    main()


