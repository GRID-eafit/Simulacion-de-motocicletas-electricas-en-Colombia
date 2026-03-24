"""
Wrapper around the standalone trip-cost simulation model.

The model lives in ``server/Modelos de Simulación/Modelo costos/`` and is
loaded lazily on first use to keep startup time low.
"""

import logging
import os
import sys
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_model_module = None
_load_error = None


def _load_model():
    global _model_module, _load_error

    if _model_module:
        return _model_module

    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Navigate up three levels: services → app → server → project root
    project_root = os.path.join(current_dir, "..", "..")
    model_path = os.path.normpath(os.path.join(project_root, "Modelos de Simulación", "Modelo costos"))

    if not os.path.exists(model_path):
        _load_error = FileNotFoundError(f"Model directory not found at: {model_path}")
        logger.error(str(_load_error))
        raise _load_error

    old_cwd = os.getcwd()
    try:
        os.chdir(model_path)

        if model_path not in sys.path:
            sys.path.insert(0, model_path)

        logger.info(f"Loading costs model from: {model_path}")
        import calcular_costo_viaje_aleatorio as model

        _model_module = model
        logger.info("Costs model loaded successfully.")
        return model

    except Exception as exc:
        _load_error = exc
        logger.error(f"Failed to load costs model: {exc}")
        raise exc
    finally:
        os.chdir(old_cwd)


def compute_custom_trip(
    origin_lat: float,
    origin_lng: float,
    dest_lat: float,
    dest_lng: float,
    municipio_origen: Optional[str] = None,
    municipio_destino: Optional[str] = None,
    estrato: Optional[str] = None,
    motivo_viaje: Optional[str] = None,
) -> Dict[str, Any]:
    """Compute trip costs using the simulation model.

    Missing parameters (municipality, estrato, purpose) are inferred from
    the model's internal CSV dataset when not supplied by the caller.
    """
    try:
        model = _load_model()
    except Exception as exc:
        return {"error": "Model initialisation failed", "details": str(exc), "fallback": True}

    try:
        # Infer municipalities from geographic coordinates if not provided
        if not municipio_origen or not municipio_destino:
            try:
                mun_o, _ = model.inferir_info_geo(origin_lat, origin_lng)
                mun_d, _ = model.inferir_info_geo(dest_lat, dest_lng)
                if not municipio_origen and mun_o:
                    municipio_origen = mun_o
                if not municipio_destino and mun_d:
                    municipio_destino = mun_d
                logger.info(f"Inferred municipalities: {municipio_origen} → {municipio_destino}")
            except AttributeError:
                logger.warning("inferir_info_geo not found in model.")
            except Exception as inf_exc:
                logger.warning(f"Municipality inference failed: {inf_exc}")

        # Infer estrato / motivo from the CSV dataset if not provided
        if not estrato or not motivo_viaje:
            try:
                csv_estrato, csv_motivo = model.seleccionar_datos_viaje_desde_coordenadas(
                    origin_lat, origin_lng, dest_lat, dest_lng
                )
                if not estrato:
                    estrato = csv_estrato
                if not motivo_viaje:
                    motivo_viaje = csv_motivo
                logger.info(f"Selected from CSV: Estrato={estrato}, Motivo={motivo_viaje}")
            except AttributeError:
                logger.warning("seleccionar_datos_viaje_desde_coordenadas not found in model.")
            except Exception as sel_exc:
                logger.warning(f"CSV data selection failed: {sel_exc}")

        # Sensible defaults
        municipio_origen = municipio_origen or "Medellín"
        municipio_destino = municipio_destino or "Medellín"
        estrato = estrato or "3"
        motivo_viaje = motivo_viaje or "Trabajo"

        logger.info(
            f"Final params: {municipio_origen} → {municipio_destino}, "
            f"Estrato={estrato}, Motivo={motivo_viaje}"
        )

        results = model.calcular_consumo_y_costos_viaje(
            origin_lat, origin_lng,
            dest_lat, dest_lng,
            municipio_origen,
            municipio_destino,
            estrato,
            motivo_viaje,
        )

        if not results:
            return {"error": "Model returned empty results"}

        return results

    except Exception as exc:
        logger.error(f"Error executing model calculation: {exc}")
        return {"error": "Calculation execution failed", "details": str(exc)}
