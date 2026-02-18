from gurobipy import *
import gurobipy as gp
import numpy as np
import os
import math
from typing import List, Tuple
import math
from geopy.distance import geodesic
from typing import Dict, Iterable, Tuple
import pandas as pd
import ast 
from petitions import _fetch_ors_route

options = {
    "WLSACCESSID": os.getenv("WLSACCESSID", ""),
    "WLSSECRET": os.getenv("WLSSECRET", ""),
    "LICENSEID": (int)(os.getenv("LICENSEID", ""))
}

env = gp.Env(params=options)

def matriz_distancias(coords):
    n = len(coords) - 2
    N = n + 2
    cij = np.zeros((N, N), dtype=float)
    for i in range(N):
        for j in range(N):
            if i == j:
                #rs_route([1,3],[2,4])
                continue
    return cij

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c

def moto3(n_vehicles, n_customers, V_prime, capa, E_max, E_min, conso, rr, t_ij, S_i, d, ei, li, Tmax, V, Tlim, n) -> None:

    moto3 = Model("EVRP_BatterySwap")

    X = moto3.addVars(((i, j) for i in V for j in V if i != j), vtype=GRB.BINARY, name="X")
    Xp = moto3.addVars(((i, j) for i in V_prime for j in V_prime if i != j), vtype=GRB.BINARY, name="Xp")
    E = moto3.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="E")
    R = moto3.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="R")
    tau = moto3.addVars(((i, j) for i in V_prime for j in V_prime if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="tau")
    l = moto3.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, ub = capa, vtype=GRB.CONTINUOUS, name="l")
    #T = moto3.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="T")
    Tj = moto3.addVars(V, lb=0.0, vtype=GRB.CONTINUOUS, name="Tj")
    u = moto3.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, ub = n_customers, vtype=GRB.CONTINUOUS, name="u")

    j1 = moto3.addVar(lb=0.0, vtype=GRB.CONTINUOUS)
    j2 = moto3.addVar(lb=0.0, vtype=GRB.CONTINUOUS)
    j3 = moto3.addVar(lb=0.0, vtype=GRB.CONTINUOUS)
    j4 = moto3.addVar(lb=0.0, vtype=GRB.CONTINUOUS)
    j5 = moto3.addVar(lb=0.0, vtype=GRB.CONTINUOUS)

    arcs_vp_list = [(i, j) for i in V_prime for j in V_prime if i != j]

    moto3.setObjective(
        quicksum((t_ij[i, j] + S_i[i]) * X[i, j] for i in V for j in V if i != j and i != n_customers)
        + quicksum(tau[i, j] for i in V_prime for j in V_prime if i != j) 
        + quicksum((t_ij[i, 0]+ t_ij[0, j] + S_i[i]) * Xp[i,j] for i in V_prime for j in V_prime if i != j and i != n_customers),
        GRB.MINIMIZE,
    )

    moto3.addConstr(j1== quicksum((t_ij[i, j]) * X[i, j] for i in V for j in V if i != j and i != n_customers))
    moto3.addConstr(j2== quicksum((S_i[i]) * X[i, j] for i in V for j in V if i != j and i != n_customers))
    moto3.addConstr(j3 == quicksum(tau[i, j] for i in V_prime for j in V_prime if i != j))
    moto3.addConstr(j4 == quicksum((t_ij[i, 0]+ t_ij[0, j]) * Xp[i,j] for i in V_prime for j in V_prime if i != j and i != n_customers))
    moto3.addConstr(j5 == quicksum((S_i[i]) * Xp[i,j] for i in V_prime for j in V_prime if i != j and i != n_customers))
    ### ROUTING

    moto3.addConstr(
        quicksum(X[0, j] for j in V_prime) == n_vehicles)

    moto3.addConstrs(quicksum(X[i, j] for j in V if j != i and j!=0) + quicksum(Xp[i, j] for j in V_prime if j != i) == 1  for i in V_prime)

    moto3.addConstr(quicksum(X[j, 0] + X[n_customers , j]  for j in V_prime) == 0)

    for i in V_prime :
        moto3.addConstr(quicksum(X[j, i] for j in V if j != i) - quicksum(X[i, j] for j in V if j != i) + quicksum(Xp[j, i] for j in V_prime if j != i) - quicksum(Xp[i, j] for j in V_prime if j != i) == 0)

    moto3.addConstr(X[0,n_customers] + X[n_customers,0] == 0)


    #### GG - Sub-tour elimination
    
    for i in V:
        for j in V:
            if i != j:
                if i in V_prime and j in V_prime:
                    moto3.addConstr(u[i, j] <= n_customers * (X[i, j]+Xp[i, j]))
                    moto3.addConstr(u[i, j] >= (X[i, j]+Xp[i, j]))
                else:
                    moto3.addConstr(u[i, j] <= n_customers * X[i, j])
                    moto3.addConstr(u[i, j] >= X[i, j])
        if i != 0 and i!= n_customers:
            moto3.addConstr(quicksum(u[i, j] for j in V if j != i) - quicksum(u[j, i] for j in V if j != i) == 1)
    

    #### CARGA

    for i in V:
        for j in V:
            if i != j:
                if i==0 or j == n+1 or i == n+1 or j == 0:
                    moto3.addConstr(l[i, j] <= capa * X[i, j], name=f"capacidad_arc_{i}_{j}")
                else:
                    moto3.addConstr(l[i, j] <= capa * (X[i, j]+Xp[i, j]), name=f"capacidad_arc_{i}_{j}")
                moto3.addConstr(l[i, j] >= d[j] * X[i, j], name=f"capacidad_arc_{i}_{j}")
                if i in V_prime and j in V_prime:
                    moto3.addConstr(l[i, j] >= d[j] * Xp[i ,j], name=f"capacidad_arc_{i}_{j}")

    for i in V_prime:
        moto3.addConstr(quicksum(l[j, i] for j in V if j != i and j!=n_customers) - quicksum(l[i, j] for j in V if j != i and j!=0) <= d[i] + capa*quicksum(Xp[i,j] for j in V_prime if i!=j),name=f"balance_carga_1_{i}")
        moto3.addConstr(quicksum(l[j, i] for j in V if j != i and j!=n_customers) - quicksum(l[i, j] for j in V if j != i and j!=0) >= d[i] - capa*quicksum(Xp[i,j] for j in V_prime if i!=j),name=f"balance_carga_2_{i}")


    #### TIEMPO

    #moto3.addConstr(Tj[0] == 0.0)
    for j in V_prime:
        moto3.addConstr(Tj[0] >= t_ij[0, j], name="t_depot_start")

    Mt = 0
    for i in V:
        for j in V:
            if i != j and t_ij[i, j]+S_i[i] > Mt:
                Mt = t_ij[i, j] + S_i[i]
    Mt = Mt * n_customers + 100

    for i in V:
        for j in V:
            if i != j:
                moto3.addConstr(
                    Tj[j] >= Tj[i] + S_i[i] + t_ij[i, j] - Mt * (1 - X[i, j]),
                    name=f"timeprop_X_{i}_{j}"
                )

    for i in V_prime:
        for j in V_prime:
            if i != j:
                moto3.addConstr(
                    Tj[j] >= Tj[i] + S_i[i] + t_ij[i, 0] + t_ij[0, j] + tau[i, j]
                            - Mt* (1 - Xp[i, j]),
                    name=f"timeprop_Xp_{i}_{j}"
                )

    #### VENTANAS TIEMPO
    for j in V_prime:  # ventanas solo en clientes
        moto3.addConstr(Tj[j] >= li[j], name=f"tw_early_{j}")
        moto3.addConstr(Tj[j] <= ei[j], name=f"tw_late_{j}")
        

    #### ENERGIA

    for i in V_prime:
        moto3.addConstr(quicksum(E[i, j] for j in V if j != i) == quicksum(E[j, i] for j in V if j != i) + quicksum(R[i, j] for j in V_prime if j != i)
                    - quicksum(conso * t_ij[i, j] * X[i, j] for j in V if j != i) 
                    - quicksum(conso * (t_ij[i, n+1] + t_ij[0, j]) * Xp[i, j] for j in V_prime if j != i and i in V_prime))
        
    # 5) R_ij = rr * tau_ij
    for i in V_prime:
        for j in V_prime:
            if i != j:
                moto3.addConstr(R[i, j] == rr * tau[i, j], name=f"recarga_tiempo_{i}_{j}")

    for i in V:
        for j in V:
            if i != j:
                if i in V_prime and j in V_prime:
                    moto3.addConstr(E[i, j] <= E_max * (X[i, j]+Xp[i,j]), name=f"recarga_tiempo_{i}_{j}")
                    moto3.addConstr(E[i, j] >= E_min * (X[i, j]+Xp[i,j]), name=f"recarga_tiempo_{i}_{j}")

                    moto3.addConstr(quicksum(E[h, i] for h in V if h != i) - conso * t_ij[i, n+1] >= E_min - E_max * (1 - Xp[i, j]), name=f"opcion_2_recarga_{i}_{j}")
                    moto3.addConstr(quicksum(E[h, i] for h in V if h != i) - conso * t_ij[i, n+1] + R[i,j] <= E_max, name=f"opcion_2_recarga_2_{i}_{j}")
                else:
                    moto3.addConstr(E[i, j] <= E_max * X[i, j], name=f"recarga_tiempo_{i}_{j}")
                    moto3.addConstr(E[i, j] >= E_min * X[i, j], name=f"recarga_tiempo_{i}_{j}")
                
    for i, j in arcs_vp_list:
        moto3.addConstr(R[i, j] <= E_max * Xp[i, j], name=f"R_cero_si_no_arco_{i}_{j}")
    
    for i, j in arcs_vp_list:
        moto3.addConstr(R[i, j] <= E_max - quicksum(E[k, i_dest] for k, i_dest in arcs_vp_list if i_dest == i)
            + conso * t_ij[i, 0] * Xp[i, j]
            + E_max * (1 - Xp[i, j]),
            name=f"restriccion_recarga_{i}_{j}"
        )

    for i in V_prime:
        moto3.addConstr(E[0, i] == (E_max - conso * t_ij[0, i]) * X[0, i])
                  
    moto3.Params.OutputFlag = 1
    moto3.setParam(GRB.Param.TimeLimit,Tlim)
    moto3.optimize()

    if moto3.Status in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        print(f"Status: {moto3.Status}, Obj: {moto3.ObjVal:.4f}")
        used = [(i, j) for i in V for j in V if i != j and X[i, j].X > 0.5]
        used_swap = [(i, j) for i in V_prime for j in V_prime if i != j and Xp[i, j].X > 0.5]
        print("Arcos X usados:", used)
        print("Arcos X' usados (i->0->j):", used_swap)
        print("")
        print(f"X \t\t u \t l \t T \t E \t R \t tau")
        print("")
        i=0
        while i < n_customers:
            for j in V:
                if i != j and X[i, j].X > 0.5:
                    print(f"X[{i},{j}] = {X[i, j].X} \t {u[i,j].X:.1f} \t {l[i,j].X:.1f} \t {Tj[j].X:.1f} \t {E[i,j].X:.1f} \t {R[i,j].X:.1f}")
                    i=j
                    break
            for j in V_prime:
                if i != j and i in V_prime and Xp[i, j].X > 0.5:
                    print("")
                    print(f"Xp[{i},{j}] = {Xp[i, j].X} \t {u[i,j].X:.1f} \t {l[i,j].X:.1f} \t {Tj[j].X:.1f} \t {E[i,j].X:.1f} \t {R[i,j].X:.1f} \t {tau[i,j].X:.1f}")
                    print("")
                    i = j
                    break
        print("")
        print(j1.X,j2.X,j3.X,j4.X,j5.X)
        return used_swap, used
        
    else:
        print(f"Modelo terminó con estado {moto3.Status}")
    
    print("")

def data(coords):
    import pandas as pd
    import time

    n = len(coords) - 2 # número de clientes (Restando el deposito al inicio y al final)
    R = range(n)  # número de viajes permitidos (reducido)
    V = range(1, n + 1)  # clientes

    Z = [0] + list(V) + [n + 1]  # nodos: 0=depot inicio, n+1=depot final

    n_vehicles = 1
    n_customers = n + 1
    V_prime = list(range(1, n_customers))
    V_2 = list(range(n_customers + 1))
    Tmax = 24.0  
        
    
    capa = 100  # capacidad del EV (aumentada)
    Emax = 100  # batería máxima (kWh) (aumentada)
    Emin = 1  # batería mínima
    conso = 2.5  # consumo por km PROMEDIO (reducido)
    rr = 2   #1 / 360  # tasa de recarga (kW/min)
    speed = 44.22  # km/h promedio urbano
    TOJ = 0.0  

    N = n + 2


    ci = matriz_distancias(coords)


    cij = np.zeros((N, N), dtype=float)
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            cij[i][j] = round(haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1]),2) * 100
            
    tij = np.round((cij / speed) + 1, 2)


    np.random.seed(42)

    #si = np.random.uniform(0, 0.4, len(Z))
    d = {i: np.random.randint(10, 25) if i in V else 0 for i in Z}
  
    inicio = 0
    fin = 500

    valores_intermedios_si = np.random.uniform(0.1, 0.4, len(Z)-1)
    valores_intermedios_li = np.random.uniform(0.0001, 2, len(Z)-1)
    valores_intermedios_ei = np.random.uniform(300, 500, len(Z)-1)


    # Construir el vector completo
    si = np.array([inicio, *valores_intermedios_si, inicio])
    li = np.array([inicio, *valores_intermedios_li, inicio])
    ei = np.array([fin, *valores_intermedios_ei, fin])

    si = np.round(si, decimals=2)
    li = np.round(li, decimals=2)
    ei = np.round(ei, decimals=2)

 
    return n, n_vehicles, R, V, n_customers, V_prime, Z, capa, Emax, Emin,  conso, rr, speed, TOJ, coords, cij, tij, si, d, ei, li, Tmax, V_2 

def procesar_ruteo(coords):
    # En las coordenadas se asume que el depósito aún no es la coordenada final
    n, n_vehicles, R_1, V, n_customers, V_prime, Z, capa, Emax, Emin,  conso, rr, speed, TOJ, coords, cij, t_ij, si, d, ei, li, Tmax, V_2 = data(coords)
    
    Tlim = 200

    used_swap, used = moto3(n_vehicles, n_customers, V_prime, capa, Emax, Emin, conso, rr, t_ij, si, d, ei, li, Tmax, V_2, Tlim, n)

    # Algoritmo para traducir las rutas
    dic = {}
    carga = set()
    viajes = used + used_swap

    for i in used_swap:
        carga.add(i[0])

    for i in range(len(viajes)):
        dic[viajes[i][0]] = viajes[i][1]

    n = 0
    recorrido = []
    while n in dic:
        if n in carga:
            recorrido.append([n,0])
            recorrido.append([0,dic[n]])
            n = dic[n]
            continue
        recorrido.append([n,dic[n]])
        n = dic[n]

    return recorrido