import os
import sys
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger("ModelWrapper")

_model_module = None
_load_error = None

def _load_model():
    global _model_module, _load_error
    
    if _model_module:
        return _model_module

    current_dir = os.path.dirname(os.path.abspath(__file__))
    model_path = os.path.join(current_dir, "Modelos de Simulación", "Modelo costos")
    
    if not os.path.exists(model_path):
        _load_error = FileNotFoundError(f"Model directory not found at: {model_path}")
        logger.error(str(_load_error))
        raise _load_error

    old_cwd = os.getcwd()
    
    try:
        os.chdir(model_path)
        
        if model_path not in sys.path:
            sys.path.insert(0, model_path)
            
        logger.info(f"Loading model from: {model_path}")
        
        import calcular_costo_viaje_aleatorio as model
        _model_module = model
        
        logger.info("Model loaded successfully.")
        return model
        
    except Exception as e:
        _load_error = e
        logger.error(f"Failed to load model: {e}")
        raise e
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
    motivo_viaje: Optional[str] = None
) -> Dict[str, Any]:
    try:
        model = _load_model()
    except Exception as e:
        return {
            "error": "Model initialization failed", 
            "details": str(e),
            "fallback": True
        }

    try:
        if not municipio_origen or not municipio_destino:
            try:
                mun_o, _ = model.inferir_info_geo(origin_lat, origin_lng)
                mun_d, _ = model.inferir_info_geo(dest_lat, dest_lng)
                
                if not municipio_origen and mun_o:
                    municipio_origen = mun_o
                if not municipio_destino and mun_d:
                    municipio_destino = mun_d
                
                logger.info(f"Inferred municipalities: {municipio_origen}->{municipio_destino}")
            except AttributeError:
                logger.warning("inferir_info_geo function not found in model.")
            except Exception as inf_e:
                logger.warning(f"Municipality inference failed: {inf_e}")

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
                logger.warning("seleccionar_datos_viaje_desde_coordenadas function not found in model.")
            except Exception as sel_e:
                logger.warning(f"CSV data selection failed: {sel_e}")

        if not municipio_origen:
            municipio_origen = "Medellín"
        if not municipio_destino:
            municipio_destino = "Medellín"
        if not estrato:
            estrato = "3"
        if not motivo_viaje:
            motivo_viaje = "Trabajo"
        
        logger.info(f"Final parameters: {municipio_origen}->{municipio_destino}, Estrato={estrato}, Motivo={motivo_viaje}")

        results = model.calcular_consumo_y_costos_viaje(
            origin_lat, origin_lng, 
            dest_lat, dest_lng,
            municipio_origen, 
            municipio_destino, 
            estrato, 
            motivo_viaje
        )
        
        if not results:
            return {"error": "Model returned empty results"}
            
        return results
        
    except Exception as e:
        logger.error(f"Error executing model calculation: {e}")
        return {
            "error": "Calculation execution failed",
            "details": str(e)
        }