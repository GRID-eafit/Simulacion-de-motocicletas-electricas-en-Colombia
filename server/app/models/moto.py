"""
Moto simulation domain class.

Simulates an electric (or hybrid) motorcycle moving along a pre-computed
route, tracking battery state-of-charge, power consumption, and charging
stops.
"""

import math
import numpy as np
from geopy.distance import geodesic


class Moto:
    def __init__(
        self,
        name: str,
        route_data: list,
        stations: dict,
        hybrid_cont: float,
        charger_power_kw: float = 3.5,
        price_per_kwh: float = 0.0,
    ):
        self.name = name
        self.route_data = route_data
        self.stations = stations
        self.positions = []

        # Battery capacity (kWh)
        self.capacidad_bateria = 2.5
        self.estado_bateria = self.capacidad_bateria

        self.en_carga = False
        self.historial_carga = [self.en_carga]

        # Energy threshold that triggers a charging stop
        self.umbral_energia = self.capacidad_bateria * 0.9
        self.energia_antes_de_recarga = None

        # Correction factors calibrated from real telemetry data
        self.factor_correccion = 0.959
        self.eficiencia_tren = 0.95

        # Route indices
        self.idx = 0       # current segment
        self.idx_ruta = 0  # index within the current segment

        # 0 = 100 % electric, 1 = 100 % combustion
        self.hybrid_cont = hybrid_cont

        # Instantaneous consumptions per step (kWh)
        self.pow_consumption = 0.0
        self.pcn_consumption = 0.0

        # Cumulative energy totals (kWh)
        self.total_electric_kwh = 0.0
        self.total_combustion_kwh = 0.0

        # Charger parameters
        self.charger_power_kw = float(charger_power_kw) if charger_power_kw is not None else 3.5
        self.price_per_kwh = float(price_per_kwh) if price_per_kwh is not None else 0.0

        # Charging accumulators
        self.total_energy_charged_kwh = 0.0
        self.total_charge_time_min = 0.0
        self.total_charge_cost = 0.0

        # Route totals
        self.distance = 0.0
        self.duration = 0.0

        # Histories
        self.puntos_recarga_realizados = []
        self.soc_history = []
        self.power = []

        # HEV model
        if hybrid_cont == 0:
            from HybridBikeConsumptionModel.parameters_electric import HEV
        else:
            from HybridBikeConsumptionModel.parameters_hybrid import HEV
        self.hev = HEV()

    # Navigation helpers

    def estacion_cercana(self, current_pos: list) -> int:
        """Return the index of the charging station closest to *current_pos*
        that also minimises the detour to the segment's final destination."""
        destiny = self.route_data[self.idx]["coords"][-1][:2]

        distancias = [
            geodesic(current_pos[::-1], coords[::-1]).meters
            + geodesic(coords[::-1], destiny[::-1]).meters
            for coords in self.stations["coords"]
        ]

        return distancias.index(min(distancias))

    def añadir_punto_carga(self, station_idx: int, current_pos: list) -> None:
        """Register the start of a charging stop.  Energy details are filled
        in later by :meth:`cargar`."""
        self.puntos_recarga_realizados.append({
            "station_name": self.stations["nombre"][station_idx],
            "station_coords": self.stations["coords"][station_idx],
            "start_coords": current_pos,
            "energy_charged": 0.0,
            "charge_time_h": 0.0,
            "charge_time_min": 0.0,
            "charger_power_kw": self.charger_power_kw,
            "price_per_kwh": self.price_per_kwh,
            "charge_cost": 0.0,
        })

    def cambiar_ruta(self, new_route: list) -> None:
        """Insert *new_route* into the plan at the current position,
        truncating the current segment."""
        self.route_data[self.idx]["coords"] = self.route_data[self.idx]["coords"][:self.idx_ruta + 1]
        self.route_data[self.idx]["speeds"] = self.route_data[self.idx]["speeds"][:self.idx_ruta + 1]
        self.route_data[self.idx]["slopes"] = self.route_data[self.idx]["slopes"][:self.idx_ruta + 1]

        self.route_data = self.route_data[:self.idx + 1] + new_route + self.route_data[self.idx + 1:]

        self.idx_ruta = 0
        self.idx += 1

    # Charging

    def cargar(self) -> None:
        """Simulate a full recharge at the last registered charging point."""
        energy_charged = self.capacidad_bateria - self.estado_bateria
        if energy_charged < 0:
            energy_charged = 0.0

        self.estado_bateria = self.capacidad_bateria

        charge_time_h = (energy_charged / self.charger_power_kw) if self.charger_power_kw > 0 else 0.0
        charge_time_min = charge_time_h * 60.0
        charge_cost = energy_charged * self.price_per_kwh

        last_cp = self.puntos_recarga_realizados[-1]
        last_cp["energy_charged"] = energy_charged
        last_cp["charge_time_h"] = charge_time_h
        last_cp["charge_time_min"] = charge_time_min
        last_cp["charger_power_kw"] = self.charger_power_kw
        last_cp["price_per_kwh"] = self.price_per_kwh
        last_cp["charge_cost"] = charge_cost

        self.total_energy_charged_kwh += energy_charged
        self.total_charge_time_min += charge_time_min
        self.total_charge_cost += charge_cost

        self.soc_history.append(self.estado_bateria)
        self.en_carga = False

    # Simulation step

    def consume_step(self) -> bool:
        """Compute forces, powers and energy consumption for one simulation
        step and update internal state.  Returns *False* when the current
        segment has been fully consumed."""
        hev = self.hev
        segment = self.route_data[self.idx]

        if self.idx_ruta >= len(segment["coords"]):
            return False

        vel = segment["speeds"][self.idx_ruta]
        theta = segment["slopes"][self.idx_ruta] * math.pi / 180

        rho = self.hev.Ambient.rho
        g = self.hev.Ambient.g
        rw = self.hev.Wheel.rw

        # Aerodynamic, rolling, gravitational and inertial forces
        faero = 0.5 * rho * hev.Chassis.a * hev.Chassis.cd * (vel ** 2)
        froll = g * hev.Chassis.m * hev.Chassis.crr * np.cos(theta)
        fg = g * hev.Chassis.m * np.sin(theta)

        v_prev = segment["speeds"][self.idx_ruta - 1] if self.idx_ruta > 0 else 0
        delta_v = vel - v_prev
        f_inertia = hev.Chassis.m * delta_v  # delta_t = 1 s

        fres = faero + froll + fg + f_inertia

        p_m = (fres * rw) * (vel / rw)

        # Electric share
        p_eb = p_m * (1 - self.hybrid_cont) / self.eficiencia_tren
        p_eb = max(p_eb * self.factor_correccion, 0.0)

        # Combustion share
        p_cn = max(p_m * self.hybrid_cont / 0.2, 0.0)

        # Time delta (hours)
        if self.idx_ruta == 0:
            if "ts" in segment and len(segment["ts"]) > 0:
                delta_t_horas = 1.0 / 3600.0
            else:
                delta_t = segment["times"][0] if segment["times"][0] > 0 else 1.0
                delta_t_horas = delta_t / 3600.0
        else:
            if "ts" in segment and len(segment["ts"]) > self.idx_ruta:
                if segment["ts"][self.idx_ruta] > segment["ts"][self.idx_ruta - 1]:
                    delta_t_ms = segment["ts"][self.idx_ruta] - segment["ts"][self.idx_ruta - 1]
                    delta_t_horas = delta_t_ms / 1000.0 / 3600.0
                else:
                    delta_t_horas = 1.0 / 3600.0
            else:
                delta_t = max(
                    segment["times"][self.idx_ruta] - segment["times"][self.idx_ruta - 1],
                    0.1,
                )
                delta_t_horas = delta_t / 3600.0

        # Instantaneous consumption
        potencia_kw = p_eb / 1000.0
        consumo_wh = potencia_kw * delta_t_horas * 1000

        self.pow_consumption = consumo_wh / 1000
        self.pcn_consumption = (p_cn / 1000.0) * delta_t_horas

        self.total_electric_kwh += self.pow_consumption
        self.total_combustion_kwh += self.pcn_consumption

        self.estado_bateria -= consumo_wh / 1000
        if self.estado_bateria < 0:
            self.estado_bateria = 0.0

        self.soc_history.append(self.estado_bateria)
        self.power.append(potencia_kw)
        self.positions.append(segment["coords"][self.idx_ruta])

        return True

    def avanzar_paso(self) -> int:
        """Advance one simulation step.

        Returns
        0
            End of route.
        1
            Continue normally.
        3
            Battery low – the caller must route the bike to a charging station.
        """
        if not self.consume_step():
            self.historial_carga.append(self.en_carga)
            self.duration += self.route_data[self.idx]["duration"]
            self.distance += self.route_data[self.idx]["distance"]

            self.idx += 1
            self.idx_ruta = 0

            if self.idx >= len(self.route_data):
                return 0

            if self.en_carga:
                self.cargar()

            return 1

        if self.estado_bateria < self.umbral_energia and not self.en_carga and not self.historial_carga[-1]:
            self.en_carga = True
            return 3

        self.idx_ruta += 1
        return 1
