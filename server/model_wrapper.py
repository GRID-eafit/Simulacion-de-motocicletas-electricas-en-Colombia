import os
import sys
import logging
from typing import Dict, Any, Optional

# Configure logging
logger = logging.getLogger("ModelWrapper")

# Global variable to hold the module after lazy loading
_model_module = None
_load_error = None

def _load_model():
    """
    Loads the simulation model module.
    Because the model executes code at top-level (loading shapefiles relative to CWD),
    we must temporarily switch to its directory to import it safely.
    """
    global _model_module, _load_error
    
    if _model_module:
        return _model_module
    
    if _load_error:
        raise _load_error

    # Base paths
    current_dir = os.path.dirname(os.path.abspath(__file__))
    # Assuming structure:
    #   root/
    #     server/model_wrapper.py
    #     Modelos de Simulación/calcular_costo_viaje_aleatorio.py
    
    model_dir_name = os.path.join("Modelos de Simulación", "Modelo costos")
    project_root = os.path.dirname(current_dir)
    model_path = os.path.join(project_root, model_dir_name)
    
    if not os.path.exists(model_path):
        _load_error = FileNotFoundError(f"Model directory not found at: {model_path}")
        logger.error(str(_load_error))
        raise _load_error

    # Store old CWD
    old_cwd = os.getcwd()
    
    try:
        # Switch CWD so the model can find its shapefiles/excel
        os.chdir(model_path)
        
        # Add to sys.path so we can import it
        if model_path not in sys.path:
            sys.path.insert(0, model_path)
            
        logger.info(f"Loading model from: {model_path}")
        
        # Import the module
        # The filename is 'calcular_costo_viaje_aleatorio.py'
        import calcular_costo_viaje_aleatorio as model
        _model_module = model
        
        logger.info("Model loaded successfully.")
        return model
        
    except Exception as e:
        _load_error = e
        logger.error(f"Failed to load model: {e}")
        # Only re-raise if you want to block server startup or first request
        # For now we'll allow it to fail but subsequent calls will know.
        raise e
    finally:
        # Restore CWD
        os.chdir(old_cwd)

def compute_custom_trip(
    origin_lat: float, 
    origin_lng: float, 
    dest_lat: float, 
    dest_lng: float,
    municipio_origen: str = "Medellín",
    municipio_destino: str = "Medellín",
    estrato: str = "3",
    motivo_viaje: str = "Trabajo"
) -> Dict[str, Any]:
    """
    Wrapper function to call the model's logic.
    """
    try:
        model = _load_model()
    except Exception as e:
        return {
            "error": "Model initialization failed", 
            "details": str(e),
            "fallback": True
        }

    try:
        # Capture stdout? The model prints a lot. 
        # For now, we just let it print to server logs.
        # Calling the function:
        # def calcular_consumo_y_costos_viaje(origin_lat, origin_lon, dest_lat, dest_lon, 
        #                                    municipio_origen, municipio_destino, 
        #                                    estrato, motivo_viaje):
        # Try to infer Municipality and Stratum from coordinates
        try:
            mun_o, est_o = model.inferir_info_geo(origin_lat, origin_lng)
            mun_d, est_d = model.inferir_info_geo(dest_lat, dest_lng)
            
            if mun_o: municipio_origen = mun_o
            if mun_d: municipio_destino = mun_d
            if est_o: estrato = est_o  # Use Origin stratum for household calculation
            
            logger.info(f"Inferred: {municipio_origen}->{municipio_destino} (Estrato {estrato})")
        except AttributeError:
             # In case the model function doesn't exist yet (if reload failed)
             logger.warning("inferir_info_geo function not found in model.")
        except Exception as inf_e:
             logger.warning(f"Inference failed: {inf_e}")

        results = model.calcular_consumo_y_costos_viaje(
            origin_lat, origin_lng, 
            dest_lat, dest_lng,
            municipio_origen, 
            municipio_destino, 
            estrato, 
            motivo_viaje
        )
        
        # Verify if result is valid
        if not results:
            return {"error": "Model returned empty results"}
            
        return results
        
    except Exception as e:
        logger.error(f"Error executing model calculation: {e}")
        return {
            "error": "Calculation execution failed",
            "details": str(e)
        }
