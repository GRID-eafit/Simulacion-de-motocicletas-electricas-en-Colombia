import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.linear_model import LinearRegression

# Ruta del archivo
file_path = 'Consolidado datos.xlsx'

# Cargar todas las hojas del Excel como diccionario de DataFrames
excel_data = pd.read_excel(file_path, sheet_name=None)

# Mostrar nombres de las hojas
sheet_names = list(excel_data.keys())

# Mostrar contenido de cada hoja
df0 = None
df1 = None
for name, df in excel_data.items():
    print(f"\n--- Hoja: {name} ---")
    print(df.head())
    if "1941" in name:
        df0 = df
    elif df1 is None:
        df1 = df

# Si solo hay una hoja, usar la misma para ambos
if df0 is not None and df1 is None:
    df1 = df0
elif df0 is None and df1 is not None:
    df0 = df1

sheet_names

#df0 = df0.drop(columns=["Unnamed: 8", "Unnamed: 9", "Unnamed: 10", "Unnamed: 11", "Unnamed: 12"])

df_motos_0 = df0[df0["CLASE"] == "MOTOCICLETA"]
df_motos_1 = df1[df1["CLASE"] == "MOTOCICLETA"]

# Combustibles a eliminar
combustibles_excluir = ["GAS GASOL", "GASO ELEC", "HIDROGENO", None, "", np.nan]

# Filtrar excluyendo esos combustibles
df_motos_0 = df_motos_0[~df_motos_0["COMBUSTIBLE"].isin(combustibles_excluir)]
df_motos_1 = df_motos_1[~df_motos_1["COMBUSTIBLE"].isin(combustibles_excluir)]

df_motos = pd.concat([df_motos_0, df_motos_1], ignore_index=True)

# Agrupar por año y sumar las cantidades
df_motos_agrupado = df_motos.groupby("AÑO_MATRICULA", as_index=False)["CANTIDAD"].sum()
df_motos_agrupado = df_motos_agrupado.sort_values("AÑO_MATRICULA")

# Crear DataFrame filtrado desde 2020 para la primera gráfica
df_motos_agrupado_2020_primera = df_motos_agrupado[df_motos_agrupado["AÑO_MATRICULA"] >= 2020]

# Graficar desde 2020
plt.figure(figsize=(10,5))
plt.plot(df_motos_agrupado_2020_primera["AÑO_MATRICULA"], df_motos_agrupado_2020_primera["CANTIDAD"], marker='o')
plt.title("Cantidad de Motocicletas por Año (Desde 2020)")
plt.xlabel("Año de Matrícula")
plt.ylabel("Cantidad")
plt.grid(True)
plt.show()


# Crear un rango completo de años desde el mínimo al máximo
all_years = pd.Series(range(df_motos_agrupado["AÑO_MATRICULA"].min(),
                            df_motos_agrupado["AÑO_MATRICULA"].max() + 1))

# Reindexar y llenar NaN con 0
df_motos_agrupado = (
    df_motos_agrupado
    .set_index("AÑO_MATRICULA")
    .reindex(all_years)
    .rename_axis("AÑO_MATRICULA")
    .fillna({"CANTIDAD": 0})
    .reset_index()
)

# Calcular acumulado
df_motos_agrupado["ACUMULADO"] = df_motos_agrupado["CANTIDAD"].cumsum()

# Crear DataFrame filtrado desde 2020
df_motos_agrupado_2020 = df_motos_agrupado[df_motos_agrupado["AÑO_MATRICULA"] >= 2020]

# Graficar acumulado desde 2020
plt.figure(figsize=(10,5))
plt.plot(df_motos_agrupado_2020["AÑO_MATRICULA"], df_motos_agrupado_2020["ACUMULADO"], marker='o', color='orange')
plt.title("Acumulado de Motocicletas por Año (Desde 2020)")
plt.xlabel("Año de Matrícula")
plt.ylabel("Cantidad Acumulada")
plt.grid(True)
plt.show()

# =============================================================================
# NUEVA GRÁFICA: MOTOS A GASOLINA vs MOTOS ELÉCTRICAS (2020-2024)
# =============================================================================

# Filtrar motos a gasolina desde 2020
df_motos_gasolina_0 = df0[(df0["CLASE"] == "MOTOCICLETA") & (df0["COMBUSTIBLE"] == "GASOLINA")]
df_motos_gasolina_1 = df1[(df1["CLASE"] == "MOTOCICLETA") & (df1["COMBUSTIBLE"] == "GASOLINA")]

# Combinar datos de motos a gasolina
df_motos_gasolina = pd.concat([df_motos_gasolina_0, df_motos_gasolina_1], ignore_index=True)

# Agrupar por año y sumar las cantidades de motos a gasolina
df_motos_gasolina_agrupado = df_motos_gasolina.groupby("AÑO_MATRICULA", as_index=False)["CANTIDAD"].sum()
df_motos_gasolina_agrupado = df_motos_gasolina_agrupado.sort_values("AÑO_MATRICULA")

# Filtrar motos eléctricas desde 2020
df_motos_electricas_0 = df0[(df0["CLASE"] == "MOTOCICLETA") & (df0["COMBUSTIBLE"] == "ELECTRICO")]
df_motos_electricas_1 = df1[(df1["CLASE"] == "MOTOCICLETA") & (df1["COMBUSTIBLE"] == "ELECTRICO")]

# Combinar datos de motos eléctricas
df_motos_electricas = pd.concat([df_motos_electricas_0, df_motos_electricas_1], ignore_index=True)

# Agrupar por año y sumar las cantidades de motos eléctricas
df_motos_electricas_agrupado = df_motos_electricas.groupby("AÑO_MATRICULA", as_index=False)["CANTIDAD"].sum()
df_motos_electricas_agrupado = df_motos_electricas_agrupado.sort_values("AÑO_MATRICULA")

# Filtrar desde 2020
df_motos_gasolina_2020 = df_motos_gasolina_agrupado[df_motos_gasolina_agrupado["AÑO_MATRICULA"] >= 2020]
df_motos_electricas_2020 = df_motos_electricas_agrupado[df_motos_electricas_agrupado["AÑO_MATRICULA"] >= 2020]

# Crear rango completo de años desde 2020 hasta 2024
years_2020_2024 = pd.Series(range(2020, 2025))

# Reindexar y llenar NaN con 0 para motos a gasolina
df_motos_gasolina_2020_completo = (
    df_motos_gasolina_2020
    .set_index("AÑO_MATRICULA")
    .reindex(years_2020_2024)
    .rename_axis("AÑO_MATRICULA")
    .fillna({"CANTIDAD": 0})
    .reset_index()
)

# Reindexar y llenar NaN con 0 para motos eléctricas
df_motos_electricas_2020_completo = (
    df_motos_electricas_2020
    .set_index("AÑO_MATRICULA")
    .reindex(years_2020_2024)
    .rename_axis("AÑO_MATRICULA")
    .fillna({"CANTIDAD": 0})
    .reset_index()
)

# =============================================================================
# GRÁFICAS SEPARADAS: MOTOS A GASOLINA vs MOTOS ELÉCTRICAS (2020-2024)
# =============================================================================

# Calcular acumulados
df_motos_gasolina_2020_completo["ACUMULADO"] = df_motos_gasolina_2020_completo["CANTIDAD"].cumsum()
df_motos_electricas_2020_completo["ACUMULADO"] = df_motos_electricas_2020_completo["CANTIDAD"].cumsum()

# GRÁFICA 1: Motos a Gasolina (2020-2024)
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(df_motos_gasolina_2020_completo["AÑO_MATRICULA"], df_motos_gasolina_2020_completo["CANTIDAD"], 
         'ro-', label='Motos a Gasolina', linewidth=3, markersize=10)
plt.title('Cantidad Anual de Motocicletas a Gasolina (2020-2024)', fontsize=14, fontweight='bold')
plt.xlabel('Año', fontsize=12)
plt.ylabel('Cantidad de Motocicletas', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.xticks(years_2020_2024)

plt.subplot(2, 1, 2)
plt.plot(df_motos_gasolina_2020_completo["AÑO_MATRICULA"], df_motos_gasolina_2020_completo["ACUMULADO"], 
         'ro-', label='Motos a Gasolina (Acumulado)', linewidth=3, markersize=10)
plt.title('Acumulado de Motocicletas a Gasolina (2020-2024)', fontsize=14, fontweight='bold')
plt.xlabel('Año', fontsize=12)
plt.ylabel('Cantidad Acumulada', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.xticks(years_2020_2024)

plt.tight_layout()
plt.show()

# GRÁFICA 2: Motos Eléctricas (2020-2024)
plt.figure(figsize=(10, 6))
plt.subplot(2, 1, 1)
plt.plot(df_motos_electricas_2020_completo["AÑO_MATRICULA"], df_motos_electricas_2020_completo["CANTIDAD"], 
         'go-', label='Motos Eléctricas', linewidth=3, markersize=10)
plt.title('Cantidad Anual de Motocicletas Eléctricas (2020-2024)', fontsize=14, fontweight='bold')
plt.xlabel('Año', fontsize=12)
plt.ylabel('Cantidad de Motocicletas', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.xticks(years_2020_2024)

plt.subplot(2, 1, 2)
plt.plot(df_motos_electricas_2020_completo["AÑO_MATRICULA"], df_motos_electricas_2020_completo["ACUMULADO"], 
         'go-', label='Motos Eléctricas (Acumulado)', linewidth=3, markersize=10)
plt.title('Acumulado de Motocicletas Eléctricas (2020-2024)', fontsize=14, fontweight='bold')
plt.xlabel('Año', fontsize=12)
plt.ylabel('Cantidad Acumulada', fontsize=12)
plt.grid(True, alpha=0.3)
plt.legend(fontsize=11)
plt.xticks(years_2020_2024)

plt.tight_layout()
plt.show()


# =============================================================================
# GRÁFICA 4: MODELO GOMPERTZ PARA GASOLINA Y ELÉCTRICAS (2020-2024)
# =============================================================================

# Preparar datos para el modelo Gompertz
# Usar datos acumulados desde 2020
motos_gasolina_acum = df_motos_gasolina_2020_completo["ACUMULADO"].values
motos_electricas_acum = df_motos_electricas_2020_completo["ACUMULADO"].values
years_gompertz = df_motos_gasolina_2020_completo["AÑO_MATRICULA"].values

# Ajustar modelo Gompertz para motos a gasolina
def gompertz_gasolina(x, a, b, c):
    """Modelo Gompertz para motos a gasolina: V = a * exp(-b * exp(-c * x))"""
    return a * np.exp(-b * np.exp(-c * x))

# Ajustar modelo Gompertz para motos eléctricas  
def gompertz_electricas(x, a, b, c):
    """Modelo Gompertz para motos eléctricas: V = a * exp(-b * exp(-c * x))"""
    return a * np.exp(-b * np.exp(-c * x))


motos_tot = np.array(list(df_motos_agrupado["ACUMULADO"]), dtype=float)
pib_1985_2024 = [
    169, 227, 288, 375, 474,
    737, 936, 1171, 1510, 1913,
    2347, 2749, 3264, 3702, 3928,
    5318, 5669, 6064, 6633, 7390,
    8005, 8922, 9895, 10876, 11319,
    12140, 13662, 14558, 15444, 16344,
    17078, 18137, 19037, 20046, 21122,
    22137, 23150, 23844, 24559, 25296
]
years_1985_2024 = list(range(1985, 2025))
years_1941_1984 = list(range(1941, 1985))
growth_rate = 0.035  # crecimiento anual promedio

# Partimos del valor de 1985 e iteramos hacia atrás
pib_1941_1984 = []
value = pib_1985_2024[0]  # valor 1985
for i in range(len(years_1941_1984)):
    # Retrocedemos en el tiempo
    val = value / ((1 + growth_rate) ** (1985 - years_1941_1984[i]))
    pib_1941_1984.append(round(val, 1))


years = np.arange(1941, 2025)  
pib_pc = np.array(pib_1941_1984 + pib_1985_2024, dtype=float)
# quick check
assert len(years) == len(pib_pc) == len(motos_tot)

# DataFrame (opcional)
df_3 = pd.DataFrame({'Año': years, 'Motos': motos_tot, 'PIB_pc_1000COP': pib_pc})
print(df_3.tail(), '\n')

# -------------------------------------------------------------
# 3. Nivel de saturación γ  (≥ máx(V))
# -------------------------------------------------------------
gamma = motos_tot.max() * 1.30           # 30 % por encima del valor 2024
# γ ≈ 16,1 millones de motos

# -------------------------------------------------------------
# 4. Linealización para estimar α y β
# -------------------------------------------------------------
Y = np.log( np.log( gamma / motos_tot ) )   # ln[ ln(γ / V) ]
X = pib_pc.reshape(-1, 1)                   # predictor (PIB pc)

lin = LinearRegression().fit(X, Y)
beta      = lin.coef_[0]
ln_neg_al = lin.intercept_
alpha     = -np.exp(ln_neg_al)              # α < 0

print(f'Parámetros Gompertz estimados:')
print(f'  α = {alpha: .6f}')
print(f'  β = {beta: .8f}')
print(f'  γ = {gamma:,.0f}\n')

# -------------------------------------------------------------
# 5. Función Gompertz y proyección 2025-2035
# -------------------------------------------------------------
def gompertz(pib, a, b, g):
    """V = γ · exp[ α · exp( β · PIB ) ]"""
    return g * np.exp( a * np.exp( b * pib ) )

# Escenario simple: PIB pc (×1000 COP) crece 50 % de 2024 a 2035
years_fut = np.arange(2024, 2040)                        # 11 años
pib_fut   = np.linspace(pib_pc[-1], pib_pc[-1]*1.5, len(years_fut))

# Ajuste histórico + proyección
V_hat_hist = gompertz(pib_pc,  alpha, beta, gamma)
V_hat_fut  = gompertz(pib_fut, alpha, beta, gamma)

# -------------------------------------------------------------
# 6. Gráfica desde 2020
# -------------------------------------------------------------
# Filtrar datos desde 2020
years_2020 = years[years >= 2020]
motos_tot_2020 = motos_tot[years >= 2020]
V_hat_hist_2020 = V_hat_hist[years >= 2020]

plt.figure(figsize=(8,5))
plt.scatter(years_2020, motos_tot_2020, label='Datos reales', color='black')
plt.plot(years_2020, V_hat_hist_2020,      label='Ajuste Gompertz', color='royalblue')
plt.plot(years_fut, V_hat_fut, '--', label='Proyección 2025-2035', color='firebrick')
plt.xlabel('Año')
plt.ylabel('Motocicletas (unidades)')
plt.title('Parque de motocicletas en Colombia – Modelo Gompertz (Desde 2020)')
plt.grid(True);  plt.legend()
plt.tight_layout();  plt.show()

# -------------------------------------------------------------
# 7. Tabla de proyección
# -------------------------------------------------------------
proy = pd.DataFrame({
    'Año':              years_fut,
    'PIB_pc_escenario': np.round(pib_fut, 1),
    'Motos_Gompertz':   np.round(V_hat_fut).astype(int)
})
print('Proyección 2025-2035:\n')
print(proy)

years_model = np.concatenate([years, years_fut[1:]])     # une histórico + proyección
gompertz_full = np.concatenate([V_hat_hist, V_hat_fut[1:]])

plt.figure(figsize=(8,5))
plt.plot(years_model, gompertz_full, 'o-', color='purple', label='Modelo Gompertz')
plt.xlabel('Año')
plt.ylabel('Motocicletas (unidades)')
plt.title('Modelo Gompertz – toda la serie (1941–2039)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

# -------------------------------------------------------------
# 6b. Gráfica completa del modelo Gompertz en un solo color
# -------------------------------------------------------------
from matplotlib.ticker import MaxNLocator   # <= importa el locator de enteros

years_model   = np.concatenate([years, years_fut[1:]])
gompertz_full = np.concatenate([V_hat_hist, V_hat_fut[1:]])

plt.figure(figsize=(8,5))
plt.plot(years_model, gompertz_full, 'o-', color='purple', label='Modelo Gompertz')
plt.xlabel('Año')
plt.ylabel('Motocicletas (unidades)')
plt.title('Modelo Gompertz – toda la serie (1941–2039)')
plt.grid(True)
plt.legend()

ax = plt.gca()
ax.xaxis.set_major_locator(MaxNLocator(integer=True))   # <= fuerza ticks enteros
# (Opcional: para todos los años, aunque se verá muy cargado)
# ax.set_xticks(np.arange(years_model.min(), years_model.max() + 1))

plt.tight_layout()
plt.show()


# -------------------------------------------------------------
# Serie del modelo Gompertz desde 2020
# -------------------------------------------------------------
serie_2020 = pd.DataFrame({
    "Año": np.concatenate([years_2020, years_fut[1:]]),   # 2020–2024 + 2025–2039
    "Motos_Gompertz": np.concatenate([V_hat_hist_2020, V_hat_fut[1:]])
})

print(serie_2020)


plt.figure(figsize=(8,5))
plt.plot(serie_2020["Año"],
         serie_2020["Motos_Gompertz"],
         'o-', color='purple', label='Modelo Gompertz (2020–2039)')
plt.axvline(2024, color='gray', linestyle='--', linewidth=1, label='Fin datos históricos')
plt.title('Serie del Modelo Gompertz desde 2020')
plt.xlabel('Año')
plt.ylabel('Motocicletas (unidades)')
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()

a=0


