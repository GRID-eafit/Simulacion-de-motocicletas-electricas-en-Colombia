"""
app/services/fleet_service.py
------------------------------
Fleet routing service using the Gurobi optimizer.

Exposes :func:`procesar_ruteo` which takes a list of lat/lon coordinates
(with the depot repeated at the end) and returns an ordered sequence of
arc pairs representing the optimal vehicle route with charging swaps.
"""

import math
import os
from typing import List, Tuple

import numpy as np
from gurobipy import GRB, Model, quicksum
import gurobipy as gp

from app.core.config import settings
from app.utils.geo import haversine_km


# ---------------------------------------------------------------------------
# Gurobi environment – built from settings to avoid reading env vars twice
# ---------------------------------------------------------------------------

_gurobi_env = gp.Env(params={
    "WLSACCESSID": settings.WLSACCESSID,
    "WLSSECRET": settings.WLSSECRET,
    "LICENSEID": settings.LICENSEID,
})


# ---------------------------------------------------------------------------
# Distance matrix
# ---------------------------------------------------------------------------

def _matriz_distancias(coords: list) -> np.ndarray:
    """Return a zero-initialised distance matrix (placeholder for ORS calls)."""
    N = len(coords)
    return np.zeros((N, N), dtype=float)


# ---------------------------------------------------------------------------
# Data preparation
# ---------------------------------------------------------------------------

def _prepare_data(coords: list) -> dict:
    """Build all data structures needed by the Gurobi model.

    Parameters
    ----------
    coords:
        List of [lat, lon] pairs.  The depot is the first element and is
        duplicated at the end by the caller to form the closed tour.
    """
    n = len(coords) - 2  # number of customers (excluding depot start/end)
    V = range(1, n + 1)  # customer nodes

    Z = [0] + list(V) + [n + 1]  # full node list: depot_start, …, depot_end

    n_vehicles = 1
    n_customers = n + 1
    V_prime = list(range(1, n_customers))
    V_2 = list(range(n_customers + 1))
    Tmax = 24.0

    capa = 100
    Emax = 100
    Emin = 1
    conso = 2.5     # kWh/km average
    rr = 2          # charging rate (kW/min)
    speed = 44.22   # km/h urban average
    TOJ = 0.0

    N = n + 2

    _matriz_distancias(coords)  # (placeholder)

    cij = np.zeros((N, N), dtype=float)
    for i in range(N):
        for j in range(N):
            if i == j:
                continue
            cij[i][j] = round(
                haversine_km(coords[i][0], coords[i][1], coords[j][0], coords[j][1]),
                2,
            ) * 100

    tij = np.round((cij / speed) + 1, 2)

    np.random.seed(42)
    d = {i: np.random.randint(10, 25) if i in V else 0 for i in Z}

    inicio, fin = 0, 500
    valores_intermedios_si = np.random.uniform(0.1, 0.4, len(Z) - 1)
    valores_intermedios_li = np.random.uniform(0.0001, 2, len(Z) - 1)
    valores_intermedios_ei = np.random.uniform(300, 500, len(Z) - 1)

    si = np.round(np.array([inicio, *valores_intermedios_si, inicio]), 2)
    li = np.round(np.array([inicio, *valores_intermedios_li, inicio]), 2)
    ei = np.round(np.array([fin, *valores_intermedios_ei, fin]), 2)

    return {
        "n": n,
        "n_vehicles": n_vehicles,
        "V": V_2,
        "n_customers": n_customers,
        "V_prime": V_prime,
        "capa": capa,
        "Emax": Emax,
        "Emin": Emin,
        "conso": conso,
        "rr": rr,
        "tij": tij,
        "si": si,
        "d": d,
        "ei": ei,
        "li": li,
        "Tmax": Tmax,
    }


# ---------------------------------------------------------------------------
# Optimisation model
# ---------------------------------------------------------------------------

def _solve_evrp(data: dict, Tlim: float = 200) -> Tuple[list, list]:
    """Solve the Electric Vehicle Routing Problem with Battery Swap.

    Returns
    -------
    used_swap:
        List of arc pairs that involve a depot-side charging swap.
    used:
        List of regular arc pairs.
    """
    n_vehicles = data["n_vehicles"]
    n_customers = data["n_customers"]
    V_prime = data["V_prime"]
    capa = data["capa"]
    E_max = data["Emax"]
    E_min = data["Emin"]
    conso = data["conso"]
    rr = data["rr"]
    t_ij = data["tij"]
    S_i = data["si"]
    d = data["d"]
    ei = data["ei"]
    li = data["li"]
    Tmax = data["Tmax"]
    V = data["V"]
    n = data["n"]

    m = Model("EVRP_BatterySwap", env=_gurobi_env)

    X = m.addVars(((i, j) for i in V for j in V if i != j), vtype=GRB.BINARY, name="X")
    Xp = m.addVars(((i, j) for i in V_prime for j in V_prime if i != j), vtype=GRB.BINARY, name="Xp")
    E = m.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="E")
    R = m.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="R")
    tau = m.addVars(((i, j) for i in V_prime for j in V_prime if i != j), lb=0.0, vtype=GRB.CONTINUOUS, name="tau")
    l = m.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, ub=capa, vtype=GRB.CONTINUOUS, name="l")
    Tj = m.addVars(V, lb=0.0, vtype=GRB.CONTINUOUS, name="Tj")
    u = m.addVars(((i, j) for i in V for j in V if i != j), lb=0.0, ub=n_customers, vtype=GRB.CONTINUOUS, name="u")

    arcs_vp_list = [(i, j) for i in V_prime for j in V_prime if i != j]

    # Objective
    m.setObjective(
        quicksum((t_ij[i, j] + S_i[i]) * X[i, j] for i in V for j in V if i != j and i != n_customers)
        + quicksum(tau[i, j] for i in V_prime for j in V_prime if i != j)
        + quicksum((t_ij[i, 0] + t_ij[0, j] + S_i[i]) * Xp[i, j] for i in V_prime for j in V_prime if i != j and i != n_customers),
        GRB.MINIMIZE,
    )

    # --- Routing constraints ---
    m.addConstr(quicksum(X[0, j] for j in V_prime) == n_vehicles)
    m.addConstrs(
        quicksum(X[i, j] for j in V if j != i and j != 0)
        + quicksum(Xp[i, j] for j in V_prime if j != i) == 1
        for i in V_prime
    )
    m.addConstr(quicksum(X[j, 0] + X[n_customers, j] for j in V_prime) == 0)

    for i in V_prime:
        m.addConstr(
            quicksum(X[j, i] for j in V if j != i)
            - quicksum(X[i, j] for j in V if j != i)
            + quicksum(Xp[j, i] for j in V_prime if j != i)
            - quicksum(Xp[i, j] for j in V_prime if j != i) == 0
        )

    m.addConstr(X[0, n_customers] + X[n_customers, 0] == 0)

    # Sub-tour elimination (GG)
    for i in V:
        for j in V:
            if i != j:
                if i in V_prime and j in V_prime:
                    m.addConstr(u[i, j] <= n_customers * (X[i, j] + Xp[i, j]))
                    m.addConstr(u[i, j] >= (X[i, j] + Xp[i, j]))
                else:
                    m.addConstr(u[i, j] <= n_customers * X[i, j])
                    m.addConstr(u[i, j] >= X[i, j])
        if i != 0 and i != n_customers:
            m.addConstr(
                quicksum(u[i, j] for j in V if j != i)
                - quicksum(u[j, i] for j in V if j != i) == 1
            )

    # Load constraints
    for i in V:
        for j in V:
            if i != j:
                if i == 0 or j == n + 1 or i == n + 1 or j == 0:
                    m.addConstr(l[i, j] <= capa * X[i, j])
                else:
                    m.addConstr(l[i, j] <= capa * (X[i, j] + Xp[i, j]))
                m.addConstr(l[i, j] >= d[j] * X[i, j])
                if i in V_prime and j in V_prime:
                    m.addConstr(l[i, j] >= d[j] * Xp[i, j])

    for i in V_prime:
        m.addConstr(
            quicksum(l[j, i] for j in V if j != i and j != n_customers)
            - quicksum(l[i, j] for j in V if j != i and j != 0)
            <= d[i] + capa * quicksum(Xp[i, j] for j in V_prime if i != j)
        )
        m.addConstr(
            quicksum(l[j, i] for j in V if j != i and j != n_customers)
            - quicksum(l[i, j] for j in V if j != i and j != 0)
            >= d[i] - capa * quicksum(Xp[i, j] for j in V_prime if i != j)
        )

    # Time constraints
    for j in V_prime:
        m.addConstr(Tj[0] >= t_ij[0, j])

    Mt = max(
        (t_ij[i, j] + S_i[i])
        for i in V for j in V if i != j
    ) * n_customers + 100

    for i in V:
        for j in V:
            if i != j:
                m.addConstr(Tj[j] >= Tj[i] + S_i[i] + t_ij[i, j] - Mt * (1 - X[i, j]))

    for i in V_prime:
        for j in V_prime:
            if i != j:
                m.addConstr(
                    Tj[j] >= Tj[i] + S_i[i] + t_ij[i, 0] + t_ij[0, j] + tau[i, j]
                    - Mt * (1 - Xp[i, j])
                )

    # Time windows
    for j in V_prime:
        m.addConstr(Tj[j] >= li[j])
        m.addConstr(Tj[j] <= ei[j])

    # Energy constraints
    for i in V_prime:
        m.addConstr(
            quicksum(E[i, j] for j in V if j != i)
            == quicksum(E[j, i] for j in V if j != i)
            + quicksum(R[i, j] for j in V_prime if j != i)
            - quicksum(conso * t_ij[i, j] * X[i, j] for j in V if j != i)
            - quicksum(conso * (t_ij[i, n + 1] + t_ij[0, j]) * Xp[i, j] for j in V_prime if j != i and i in V_prime)
        )

    for i in V_prime:
        for j in V_prime:
            if i != j:
                m.addConstr(R[i, j] == rr * tau[i, j])

    for i in V:
        for j in V:
            if i != j:
                if i in V_prime and j in V_prime:
                    m.addConstr(E[i, j] <= E_max * (X[i, j] + Xp[i, j]))
                    m.addConstr(E[i, j] >= E_min * (X[i, j] + Xp[i, j]))
                    m.addConstr(
                        quicksum(E[h, i] for h in V if h != i) - conso * t_ij[i, n + 1]
                        >= E_min - E_max * (1 - Xp[i, j])
                    )
                    m.addConstr(
                        quicksum(E[h, i] for h in V if h != i) - conso * t_ij[i, n + 1] + R[i, j]
                        <= E_max
                    )
                else:
                    m.addConstr(E[i, j] <= E_max * X[i, j])
                    m.addConstr(E[i, j] >= E_min * X[i, j])

    for i, j in arcs_vp_list:
        m.addConstr(R[i, j] <= E_max * Xp[i, j])
        m.addConstr(
            R[i, j] <= E_max - quicksum(E[k, i_dest] for k, i_dest in arcs_vp_list if i_dest == i)
            + conso * t_ij[i, 0] * Xp[i, j]
            + E_max * (1 - Xp[i, j])
        )

    for i in V_prime:
        m.addConstr(E[0, i] == (E_max - conso * t_ij[0, i]) * X[0, i])

    m.Params.OutputFlag = 1
    m.setParam(GRB.Param.TimeLimit, Tlim)
    m.optimize()

    if m.Status in (GRB.OPTIMAL, GRB.TIME_LIMIT, GRB.SUBOPTIMAL):
        used = [(i, j) for i in V for j in V if i != j and X[i, j].X > 0.5]
        used_swap = [(i, j) for i in V_prime for j in V_prime if i != j and Xp[i, j].X > 0.5]
        return used_swap, used
    else:
        raise RuntimeError(f"Gurobi ended with status {m.Status}")


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def procesar_ruteo(coords: list) -> list:
    """Return the ordered sequence of arc pairs for the optimal fleet route.

    Parameters
    ----------
    coords:
        List of [lat, lon] pairs.  The depot must appear first.
        The caller is responsible for appending ``coords[0]`` at the end
        to close the tour before calling this function.

    Returns
    -------
    list of [origin_idx, destination_idx] pairs, where ``0`` represents
    the depot and charging swaps are encoded as two consecutive arcs
    passing through the depot.
    """
    data = _prepare_data(coords)
    used_swap, used = _solve_evrp(data)

    carga = {i[0] for i in used_swap}
    viajes = used + used_swap
    dic = {v[0]: v[1] for v in viajes}

    n = 0
    recorrido = []
    while n in dic:
        if n in carga:
            recorrido.append([n, 0])
            recorrido.append([0, dic[n]])
        else:
            recorrido.append([n, dic[n]])
        n = dic[n]

    return recorrido
