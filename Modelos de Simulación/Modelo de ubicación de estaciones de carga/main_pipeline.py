# -*- coding: utf-8 -*-
"""
Master Pipeline Orchestrator (Advanced)
Integrates Data Preparation and Optimization Phases with Real-Time Monitoring.

Features:
- Real-time output streaming.
- Regex-based result extraction (Key Performance Indicators).
- Step timing and progress tracking.
"""
import subprocess
import sys
import os
import time
import re
import threading

# --- CONFIGURATION: KEY METRICS TO EXTRACT ---
# This dictionary defines what text to look for in the output of each script
# and what label to give it in the final summary.
STEP_METRICS = {
    "AnalisisOD.py": {
        "Initial Rows": r"Initial number of rows: (\d+)",
        "Cleaned Rows": r"Number of rows after cleaning: (\d+)",
        "Data Removed": r"Percentage of data removed: ([\d\.]+)%"
    },
    "Geographical_Zoning.py": {
        "Valid Trips (In Zone)": r"Found (\d+) trips that start and end",
        "Invalid Trips": r"(\d+) trips were invalid"
    },
    "DBSCAN_Clustering.py": {
        "Clustered Trips": r"Loaded (\d+) commute paths",
        "Origin Clusters": r"Final Origin cluster labels created", # Boolean check
        "Dest Clusters": r"Final Destination cluster labels created" # Boolean check
    },
    "extract_cluster_info.py": {
        "Origin Clusters Found": r"(\d+) clusters de orígenes identificados",
        "Dest Clusters Found": r"(\d+) clusters de destinos identificados",
        "Origin Coverage": r"ORÍGENES:.*?Cobertura: ([\d\.]+)%",
        "Dest Coverage": r"DESTINOS:.*?Cobertura: ([\d\.]+)%"
    },
    "Representative_flows_super_paths.py": {
        "Total Flows": r"Distilled .* down to (\d+) representative flows"
    },
    "Stratified_sampling.py": {
        "Final Sample Size": r"Created a final .* sample of (\d+) paths"
    },
    "real_path_simulation.py": {
        "Paths Loaded": r"Successfully loaded (\d+) paths",
        "Successful Sims": r"Simulation complete", # We will count occurrences of this
        "API Errors": r"API failure count" # We will count occurrences
    },
    "precompute_access_costs.py": {
        "Potential Stations": r"Found (\d+) potential locations",
        "Access Costs Calc": r"A complete set of access trip costs \((\d+) entries\)"
    },
    "Optimization_FCLP.py": {
        "Objective Value": r"Optimal Solution .*: \$([\d,]+\.\d+)",
        "Stations Built": r"Number of Stations Built: (\d+)",
        "Total Cost": r"Total Cost: \$([\d,]+\.\d+)",
        "Coverage": r"Demand Covered: \d+ \(([\d\.]+)%\)"
    },
    "extract_stations_info.py": {
        "Total Stations": r"Total de estaciones: (\d+)",
        "Total Cost": r"Costo total: \$([\d,]+\.\d+)"
    }
}

def get_user_selection():
    """Prompts the user to select the analysis territory."""
    print(f"\n{'='*70}")
    print("   EV INFRASTRUCTURE OPTIMIZATION - MAIN PIPELINE")
    print(f"{'='*70}")
    print("Please select the territory for analysis:")
    print("1. Medellin")
    print("2. Valle de Aburra")
    print("3. Bogota")
    print(f"{'='*70}")
    
    while True:
        choice = input("Enter number (1-3): ").strip()
        if choice == '1': return "Medellin"
        elif choice == '2': return "Valle de aburra"
        elif choice == '3': return "Bogota"
        else: print("Invalid selection.")

def format_time(seconds):
    """Formats seconds into MM:SS"""
    m, s = divmod(seconds, 60)
    return f"{int(m):02d}:{int(s):02d}"

def run_step_with_monitoring(script_name, step_desc, step_num, total_steps):
    """
    Runs a script, streams output, and extracts key metrics.
    """
    print(f"\n{'-'*70}")
    print(f"STEP {step_num}/{total_steps}: {step_desc}")
    print(f"Running: {script_name}")
    print(f"{'-'*70}")
    
    if not os.path.exists(script_name):
        print(f"ERROR: Script '{script_name}' not found.")
        sys.exit(1)

    start_time = time.time()
    metrics_def = STEP_METRICS.get(script_name, {})
    extracted_results = {key: "N/A" for key in metrics_def}
    
    # Special counters for things that appear multiple times (like API calls)
    counters = {"Successful Sims": 0, "API Errors": 0}

    # Start Subprocess
    # bufsize=1 means line buffered, universal_newlines=True handles text encoding
    process = subprocess.Popen(
        [sys.executable, script_name],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        universal_newlines=True,
        bufsize=1
    )

    # Real-time Output Processing
    while True:
        line = process.stdout.readline()
        if not line and process.poll() is not None:
            break
        
        if line:
            # 1. Print the line to console (so user sees tqdm bars and logs)
            sys.stdout.write(line)
            sys.stdout.flush()

            # 2. Scan for Metrics
            for key, regex in metrics_def.items():
                # Handle counters separately
                if key in counters:
                    if re.search(regex, line):
                        counters[key] += 1
                        extracted_results[key] = counters[key]
                else:
                    # Handle standard value extraction
                    match = re.search(regex, line)
                    if match:
                        # If regex has a group (), use it. Else just mark "Yes"
                        if match.groups():
                            extracted_results[key] = match.group(1)
                        else:
                            extracted_results[key] = "Done"

    # Wait for finish
    return_code = process.poll()
    elapsed = time.time() - start_time

    if return_code == 0:
        print(f"\nCOMPLETED: {step_desc}")
        print(f"   Time Elapsed: {format_time(elapsed)}")
        
        # Print Summary Box for this Step
        if extracted_results:
            print(f"   {'+' + '-'*40 + '+'}")
            print(f"   | {'KEY RESULTS':<38} |")
            print(f"   {'+' + '-'*40 + '+'}")
            for k, v in extracted_results.items():
                print(f"   | {k:<25} : {str(v):<10} |")
            print(f"   {'+' + '-'*40 + '+'}")
    else:
        print(f"\nFAILURE: {script_name} failed (Exit Code {return_code}).")
        sys.exit(1)

def main():
    # 1. Setup
    selected_city = get_user_selection()
    os.environ['ANALYSIS_LOCALE'] = selected_city
    
    steps = [
        ("AnalisisOD.py", "Data Cleaning & Coordinates"),
        ("Geographical_Zoning.py", "Geographic Filtering"),
        ("DBSCAN_Clustering.py", "Clustering (Origins/Destinations)"),
        ("extract_cluster_info.py", "Extract Cluster Information & Coverage"),
        ("Representative_flows_super_paths.py", "Flow Aggregation"),
        ("Stratified_sampling.py", "Stratified Sampling"),
        ("real_path_simulation.py", "Physics Simulation (ORS API)"),
        ("precompute_access_costs.py", "Access Cost Calculation"),
        ("Optimization_FCLP.py", "Final Optimization (MILP)"),
        ("extract_stations_info.py", "Extract Stations Information & Coordinates")
    ]
    
    total_steps = len(steps)
    pipeline_start = time.time()

    print(f"\n[SYSTEM] Environment set to: {selected_city}")
    print(f"[SYSTEM] Starting Pipeline with {total_steps} steps...")

    # 2. Execution Loop
    for i, (script, desc) in enumerate(steps, 1):
        run_step_with_monitoring(script, desc, i, total_steps)

    # 3. Final Summary
    total_elapsed = time.time() - pipeline_start
    print(f"\n{'='*70}")
    print(f"PIPELINE COMPLETE FOR {selected_city.upper()}")
    print(f"   Total Execution Time: {format_time(total_elapsed)}")
    print(f"   Results saved in: ./Results")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()