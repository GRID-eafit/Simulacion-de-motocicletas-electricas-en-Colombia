# -*- coding: utf-8 -*-
"""
Created on Sun Jul 20 19:42:02 2025
Updated for Main Pipeline Integration (Direct Coordinate Pass-through)
"""
import pandas as pd
import os
import sys

#----------------------------------------UNIVERSAL CONFIGURATION-------------------------
# 1. Determine Territory (Listens to Main Pipeline)
locale_info = os.getenv('ANALYSIS_LOCALE', 'Medellin')

print(f"\n[CONFIG] Running AnalisisOD for: {locale_info}")

# 2. Define Dynamic Paths based on Territory
if locale_info == "Medellin":
    raw_csv_name = 'med.csv'
elif locale_info == "Valle de aburra":
    raw_csv_name = 'amva.csv'
elif locale_info == "Bogota":
    raw_csv_name = 'bog.csv'
else:
    print(f"Error: Unknown locale '{locale_info}'")
    sys.exit(1)

# 3. Standardized File Paths
script_dir = os.path.dirname(os.path.abspath(__file__))
data_folder = os.path.join(script_dir, 'Archivos de apoyo')
results_folder = os.path.join(script_dir, 'Results')

# Input File
file_path_EOD = os.path.join(data_folder, locale_info, raw_csv_name)

# Output File
FILE_1_CLEANED = os.path.join(results_folder, f"1_cleaned_{locale_info}.csv")

# Ensure Results folder exists
if not os.path.exists(results_folder):
    os.makedirs(results_folder)

#----------------------------------------------------------------------------------------

# --- 1. ROBUST LOADING FUNCTION ---
def load_robust_csv(filepath):
    if not os.path.exists(filepath):
        print(f"\nCRITICAL ERROR: Input file not found!")
        print(f"   Looking for: {os.path.abspath(filepath)}")
        sys.exit(1)

    encodings = ['utf-8', 'latin-1', 'cp1252']
    delimiters = [';', ','] 
    
    for enc in encodings:
        for sep in delimiters:
            try:
                # Read first row to check columns
                df_test = pd.read_csv(filepath, sep=sep, encoding=enc, nrows=2)
                if len(df_test.columns) > 1:
                    print(f"   [INFO] Successfully read with encoding='{enc}' and sep='{sep}'")
                    return pd.read_csv(filepath, sep=sep, encoding=enc)
            except Exception:
                continue
                
    print("\nERROR: Could not determine correct encoding or delimiter.")
    sys.exit(1)

# --- 2. LOAD AND NORMALIZE ---
print(f"Loading raw data from: {file_path_EOD}")
df = load_robust_csv(file_path_EOD)

# Force all columns to UPPERCASE and remove extra spaces
df.columns = df.columns.str.upper().str.strip()
print("   [INFO] Normalized all column headers to UPPERCASE.")

initial_rows = len(df)

# --- 3. COLUMN MAPPING ---
# We map the raw columns (UPPERCASE) to the standardized pipeline names
# Based on your log: O_LAT, O_LONG, D_LAT, D_LONG exist in the file.
column_mapping = {
    'MUNICIPIO_O': 'ORIGIN_MUNICIPIO',
    'COMUNA_O':    'ORIGIN_COMUNA',
    'HORA_O':      'ORIGIN_TIME',
    'O_LAT':       'o_lat',
    'O_LONG':      'o_long',
    'MUNICIPIO_D': 'DESTINATION_MUNICIPIO',
    'COMUNA_D':    'DESTINATION_COMUNA',
    'HORA_D':      'DESTINATION_TIME',
    'D_LAT':       'd_lat',
    'D_LONG':      'd_long',
    # Map transport mode if available, otherwise ignore
    'MODO_TTE':    'TRANSPORT_MODE_S1', 
    'MOTIVO_VIAJE': 'TRIP_PURPOSE'
}

# Check for missing critical columns
required_source_cols = ['O_LAT', 'O_LONG', 'D_LAT', 'D_LONG']
missing_critical = [col for col in required_source_cols if col not in df.columns]

if missing_critical:
    print(f"\nCRITICAL ERROR: The input file is missing coordinate columns.")
    print(f"   Missing: {missing_critical}")
    print(f"   Available: {list(df.columns)}")
    sys.exit(1)

# Rename columns
df_renamed = df.rename(columns=column_mapping)

# Keep only the columns we mapped (plus any others that matched the target names)
# This filters out extra columns we don't need
target_cols = list(column_mapping.values())
available_target_cols = [c for c in target_cols if c in df_renamed.columns]
df_final = df_renamed[available_target_cols].copy()

# --- 4. CLEANING ---
# Remove rows with missing coordinates
before_drop = len(df_final)
df_final.dropna(subset=['o_lat', 'o_long', 'd_lat', 'd_long'], inplace=True)
cleaned_rows = len(df_final)

# Ensure coordinates are numeric
for col in ['o_lat', 'o_long', 'd_lat', 'd_long']:
    df_final[col] = pd.to_numeric(df_final[col], errors='coerce')

# Drop again in case numeric conversion created NaNs (e.g. from strings like "None")
df_final.dropna(subset=['o_lat', 'o_long', 'd_lat', 'd_long'], inplace=True)
final_rows = len(df_final)

# --- 5. SAVE ---
try:
    df_final.to_csv(FILE_1_CLEANED, index=False, encoding='utf-8')
except PermissionError:
    print(f"\nERROR: Could not write to '{FILE_1_CLEANED}'.")
    print("   Is the file open in Excel? Please close it and try again.")
    sys.exit(1)

#--------------------------------- Results ------------------------------------

print("\n--- Data Cleaning Summary ---")
print(f"Initial number of rows: {initial_rows}")
print(f"Rows with valid coordinates: {final_rows}")
print(f"Percentage of data removed: {((initial_rows - final_rows) / initial_rows) * 100:.2f}%\n")

print(f"--- Final Output ---")
print(f"Successfully saved {len(df_final)} commute paths to:")
print(f" -> {os.path.abspath(FILE_1_CLEANED)}")
print("Here's a preview of your final data:")
print(df_final.head())