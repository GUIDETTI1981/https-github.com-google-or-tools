"""
Main FastAPI Application - Routing Optimizer

ASYNC ARCHITECTURE WITH CELERY:
- Heavy OR-Tools computations are offloaded to Celery workers
- API returns 202 Accepted with task_id immediately
- Frontend polls GET /tasks/{task_id} for results
- Redis serves as message broker and result backend
"""
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from typing import Dict, Optional
import logging

from .models import (
    OptimizationRequest,
    OptimizationResult,
    CRMOrdersResponse
)
from .crm_client import CRMClient
from .vrp_solver import VRPSolver
from .vrp_solver_osrm import VRPSolverOSRM
from .vrp_solver_routing import VRPSolverWithRoutingEngines
from .services.osrm_client import OSRMClient, OSRMClientError
from .services.valhalla_client import ValhallaClient, ValhallaClientError, TruckSpecs
from .services.address_sanitizer import AddressSanitizer, get_address_sanitizer
from .services.geocoder_service import GeocoderService, GeocoderError, get_geocoder_service
from .geocoding_pipeline import GeocodingPipeline, get_geocoding_pipeline
from .models import OrderWithAddress, OptimizationWithGeocodingResult
import os
import time

# Celery imports
from .core.celery_app import celery_app, get_celery_info
from .tasks.vrp_tasks import solve_vrp_task, solve_vrp_with_geocoding_task
from celery.result import AsyncResult

# Configurazione logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inizializza FastAPI
app = FastAPI(
    title="Routing Optimizer API",
    description="API per l'ottimizzazione dei percorsi di consegna usando Google OR-Tools (CVRP)",
    version="1.0.0"
)

# Configurazione CORS per permettere richieste dal frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In produzione, specificare domini esatti
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Istanza del CRM Client
crm_client = CRMClient(seed=42)


@app.get("/", tags=["Root"])
async def root() -> Dict[str, str]:
    """
    Endpoint radice - informazioni sull'API
    """
    return {
        "message": "Routing Optimizer API",
        "version": "1.0.0",
        "docs": "/docs",
        "status": "operational"
    }


@app.get("/health", tags=["Health"])
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint
    """
    return {"status": "healthy", "service": "routing-optimizer"}


@app.get("/api/crm/orders", response_model=CRMOrdersResponse, tags=["CRM"])
async def get_crm_orders(num_orders: int = 20) -> CRMOrdersResponse:
    """
    Recupera gli ordini dal CRM simulato
    
    Args:
        num_orders: Numero di ordini da recuperare (default: 20, max: 100)
        
    Returns:
        CRMOrdersResponse con la lista degli ordini
    """
    try:
        if num_orders < 1 or num_orders > 100:
            raise HTTPException(
                status_code=400,
                detail="Il numero di ordini deve essere tra 1 e 100"
            )
        
        logger.info(f"Recupero {num_orders} ordini dal CRM simulato")
        response = crm_client.get_orders(num_orders)
        
        logger.info(f"Recuperati {response.total_count} ordini con successo")
        return response
        
    except Exception as e:
        logger.error(f"Errore nel recupero ordini CRM: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Errore CRM: {str(e)}")


@app.post("/api/optimize", tags=["Optimization"], status_code=status.HTTP_202_ACCEPTED)
async def optimize_routes_async(request: OptimizationRequest) -> Dict:
    """
    🚀 ASYNC ENDPOINT: Enqueues VRP optimization task to Celery
    
    Returns 202 Accepted immediately with task_id.
    Frontend should poll GET /api/tasks/{task_id} for results.
    
    Args:
        request: Configurazione completa (ordini, flotta, parametri OR-Tools)
        
    Returns:
        202 Accepted with:
        {
            "task_id": "abc-123-def-456",
            "status": "PENDING",
            "message": "Optimization task enqueued successfully",
            "poll_url": "/api/tasks/abc-123-def-456"
        }
        
    Example:
        >>> POST /api/optimize
        >>> {"orders": [...], "fleet_config": {...}}
        >>> 
        >>> Response (202 Accepted):
        >>> {
        >>>   "task_id": "abc-123",
        >>>   "status": "PENDING",
        >>>   "poll_url": "/api/tasks/abc-123"
        >>> }
        >>>
        >>> # Frontend polls for result
        >>> GET /api/tasks/abc-123  (status: "PENDING" or "STARTED")
        >>> GET /api/tasks/abc-123  (status: "SUCCESS" → result ready!)
    """
    try:
        logger.info("=" * 70)
        logger.info("🚀 ASYNC OPTIMIZATION REQUEST RECEIVED")
        logger.info("=" * 70)
        logger.info(f"   Orders: {len(request.orders)}")
        logger.info(f"   Vehicles: {request.fleet_config.num_vehicles}")
        logger.info(f"   Vehicle Capacity: {request.fleet_config.vehicle_capacity} kg")
        logger.info(f"   Strategy: {request.ortools_config.first_solution_strategy}")
        logger.info(f"   Metaheuristic: {request.ortools_config.local_search_metaheuristic}")
        
        # Validazione base
        if len(request.orders) == 0:
            raise HTTPException(
                status_code=400,
                detail="Nessun ordine da ottimizzare"
            )
        
        # Converti request a dict per serializzazione JSON
        request_data = request.model_dump()
        
        # Enqueue task to Celery
        logger.info("📤 Enqueuing task to Celery worker...")
        
        task = solve_vrp_task.delay(request_data)
        
        logger.info(f"✅ Task enqueued successfully: {task.id}")
        logger.info("=" * 70)
        
        return {
            "task_id": task.id,
            "status": "PENDING",
            "message": "Optimization task enqueued successfully. Poll /api/tasks/{task_id} for results.",
            "poll_url": f"/api/tasks/{task.id}",
            "num_orders": len(request.orders),
            "num_vehicles": request.fleet_config.num_vehicles
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Failed to enqueue task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to enqueue optimization task: {str(e)}"
        )


@app.get("/api/tasks/{task_id}", tags=["Optimization"])
async def get_task_status(task_id: str) -> Dict:
    """
    🔍 POLLING ENDPOINT: Get status and result of async optimization task
    
    Frontend should call this endpoint every 2-5 seconds until status is SUCCESS or FAILURE.
    
    Args:
        task_id: Celery task ID (received from POST /api/optimize)
        
    Returns:
        Task status with one of:
        - PENDING: Task is waiting in queue
        - STARTED: Task is being processed
        - SUCCESS: Task completed successfully (result included)
        - FAILURE: Task failed (error included)
        
    Example:
        >>> GET /api/tasks/abc-123-def-456
        >>>
        >>> # While processing:
        >>> {
        >>>   "task_id": "abc-123",
        >>>   "status": "STARTED",
        >>>   "progress": 30,
        >>>   "stage": "Computing distance matrix",
        >>>   "result": null
        >>> }
        >>>
        >>> # When complete:
        >>> {
        >>>   "task_id": "abc-123",
        >>>   "status": "SUCCESS",
        >>>   "result": {
        >>>     "success": true,
        >>>     "routes": [...],
        >>>     "total_distance": 123.45,
        >>>     ...
        >>>   }
        >>> }
    """
    try:
        # Get task result from Celery
        task_result = AsyncResult(task_id, app=celery_app)
        
        logger.debug(f"📊 Task {task_id} status: {task_result.state}")
        
        # Build response based on task state
        response = {
            "task_id": task_id,
            "status": task_result.state
        }
        
        if task_result.state == 'PENDING':
            # Task is waiting in queue
            response.update({
                "message": "Task is waiting in queue",
                "progress": 0
            })
            
        elif task_result.state == 'STARTED':
            # Task is being processed
            info = task_result.info or {}
            response.update({
                "message": "Task is being processed",
                "progress": info.get('progress', 0),
                "stage": info.get('stage', 'Processing'),
                "meta": info
            })
            
        elif task_result.state == 'SUCCESS':
            # Task completed successfully
            result = task_result.result
            response.update({
                "message": "Optimization completed successfully",
                "result": result,
                "progress": 100
            })
            
        elif task_result.state == 'FAILURE':
            # Task failed
            error_info = task_result.info or {}
            response.update({
                "message": "Task failed",
                "error": str(error_info.get('error', 'Unknown error')),
                "error_type": error_info.get('error_type', 'Exception'),
                "progress": 0
            })
            
        elif task_result.state == 'RETRY':
            # Task is being retried
            response.update({
                "message": "Task is being retried",
                "progress": 0
            })
            
        else:
            # Unknown state
            response.update({
                "message": f"Task state: {task_result.state}",
                "progress": 0
            })
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Error retrieving task status: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve task status: {str(e)}"
        )


@app.delete("/api/tasks/{task_id}", tags=["Optimization"])
async def cancel_task(task_id: str) -> Dict:
    """
    ❌ CANCEL TASK: Revoke/cancel a running task
    
    Args:
        task_id: Celery task ID
        
    Returns:
        Cancellation confirmation
        
    Example:
        >>> DELETE /api/tasks/abc-123
        >>> {
        >>>   "task_id": "abc-123",
        >>>   "status": "revoked",
        >>>   "message": "Task cancelled successfully"
        >>> }
    """
    try:
        # Revoke task (terminate=True to kill worker process)
        celery_app.control.revoke(task_id, terminate=True, signal='SIGKILL')
        
        logger.info(f"❌ Task {task_id} revoked")
        
        return {
            "task_id": task_id,
            "status": "revoked",
            "message": "Task cancelled successfully"
        }
        
    except Exception as e:
        logger.error(f"❌ Error cancelling task: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to cancel task: {str(e)}"
        )


@app.get("/api/celery/status", tags=["System"])
async def get_celery_status() -> Dict:
    """
    📊 CELERY STATUS: Get Celery configuration and worker status
    
    Returns:
        Celery system status and configuration
    """
    try:
        # Get Celery info
        info = get_celery_info()
        
        # Check active workers
        inspector = celery_app.control.inspect()
        
        active_workers = inspector.active()
        registered_tasks = inspector.registered()
        stats = inspector.stats()
        
        return {
            "celery_config": info,
            "workers": {
                "active": list(active_workers.keys()) if active_workers else [],
                "count": len(active_workers) if active_workers else 0,
                "stats": stats
            },
            "tasks": {
                "registered": list(registered_tasks.values())[0] if registered_tasks else []
            },
            "broker_url": info['broker_url'],
            "result_backend": info['result_backend'],
            "status": "operational" if active_workers else "no_workers"
        }
        
    except Exception as e:
        logger.error(f"❌ Error retrieving Celery status: {str(e)}", exc_info=True)
        return {
            "status": "error",
            "message": str(e),
            "celery_config": get_celery_info()
        }


@app.get("/api/config/strategies", tags=["Configuration"])
async def get_available_strategies() -> Dict:
    """
    Restituisce le strategie e metaheuristiche disponibili
    """
    return {
        "first_solution_strategies": [
            {
                "value": "PATH_CHEAPEST_ARC",
                "label": "Path Cheapest Arc",
                "description": "Inizia con il percorso più economico disponibile"
            },
            {
                "value": "GLOBAL_CHEAPEST_ARC",
                "label": "Global Cheapest Arc",
                "description": "Seleziona globalmente l'arco più economico"
            },
            {
                "value": "AUTOMATIC",
                "label": "Automatico",
                "description": "Lascia che OR-Tools scelga la strategia migliore"
            }
        ],
        "local_search_metaheuristics": [
            {
                "value": "GUIDED_LOCAL_SEARCH",
                "label": "Guided Local Search",
                "description": "Ricerca locale guidata (consigliato)"
            },
            {
                "value": "TABU_SEARCH",
                "label": "Tabu Search",
                "description": "Tabu search per evitare cicli"
            },
            {
                "value": "SIMULATED_ANNEALING",
                "label": "Simulated Annealing",
                "description": "Simulated annealing per esplorazione globale"
            }
        ]
    }


@app.get("/api/stats", tags=["Statistics"])
async def get_system_stats() -> Dict:
    """
    Restituisce statistiche di sistema
    """
    # Verifica stato OSRM
    osrm_available = False
    osrm_info = {}
    
    try:
        osrm_client = OSRMClient()
        osrm_available = osrm_client.health_check()
        osrm_info = osrm_client.get_info()
    except Exception as e:
        logger.warning(f"Impossibile verificare OSRM: {e}")
    
    # Verifica stato Valhalla
    valhalla_available = False
    valhalla_info = {}
    
    try:
        valhalla_client = ValhallaClient()
        valhalla_available = valhalla_client.health_check()
        valhalla_info = valhalla_client.get_info()
    except Exception as e:
        logger.warning(f"Impossibile verificare Valhalla: {e}")
    
    return {
        "crm_available": True,
        "ortools_version": "9.8.3296",
        "max_vehicles": 50,
        "max_orders": 100,
        "default_time_limit": 30,
        "osrm_enabled": os.getenv('USE_OSRM', 'false').lower() == 'true',
        "osrm_available": osrm_available,
        "osrm_info": osrm_info if osrm_available else None,
        "valhalla_enabled": os.getenv('USE_VALHALLA', 'false').lower() == 'true',
        "valhalla_available": valhalla_available,
        "valhalla_info": valhalla_info if valhalla_available else None,
        "routing_engines": {
            "car_van": "OSRM" if osrm_available else "Haversine",
            "truck": "Valhalla" if valhalla_available else "Haversine"
        }
    }


@app.get("/api/osrm/status", tags=["OSRM"])
async def get_osrm_status() -> Dict:
    """
    Verifica stato dettagliato del servizio OSRM
    """
    try:
        osrm_client = OSRMClient()
        
        # Health check
        is_available = osrm_client.health_check()
        
        # Info dettagliate
        info = osrm_client.get_info()
        
        return {
            "status": "available" if is_available else "unavailable",
            "enabled": os.getenv('USE_OSRM', 'false').lower() == 'true',
            "host": info["host"],
            "port": info["port"],
            "base_url": info["base_url"],
            "profile": info["profile"],
            "is_available": is_available,
            "message": "OSRM is operational" if is_available else "OSRM is not responding"
        }
    except OSRMClientError as e:
        return {
            "status": "error",
            "enabled": os.getenv('USE_OSRM', 'false').lower() == 'true',
            "is_available": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Errore verifica OSRM: {e}", exc_info=True)
        return {
            "status": "error",
            "enabled": False,
            "is_available": False,
            "message": f"Errore: {str(e)}"
        }


@app.get("/api/valhalla/status", tags=["Valhalla"])
async def get_valhalla_status() -> Dict:
    """
    Verifica stato dettagliato del servizio Valhalla
    """
    try:
        valhalla_client = ValhallaClient()
        
        # Health check
        is_available = valhalla_client.health_check()
        
        # Info dettagliate
        info = valhalla_client.get_info()
        
        return {
            "status": "available" if is_available else "unavailable",
            "enabled": os.getenv('USE_VALHALLA', 'false').lower() == 'true',
            "host": info["host"],
            "port": info["port"],
            "base_url": info["base_url"],
            "costing": info["costing"],
            "supports_truck": info["supports_truck"],
            "supports_hazmat": info["supports_hazmat"],
            "is_available": is_available,
            "message": "Valhalla is operational" if is_available else "Valhalla is not responding"
        }
    except ValhallaClientError as e:
        return {
            "status": "error",
            "enabled": os.getenv('USE_VALHALLA', 'false').lower() == 'true',
            "is_available": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Errore verifica Valhalla: {e}", exc_info=True)
        return {
            "status": "error",
            "enabled": False,
            "is_available": False,
            "message": f"Errore: {str(e)}"
        }


@app.get("/api/photon/status", tags=["Photon"])
async def get_photon_status() -> Dict:
    """
    Verifica stato dettagliato del servizio Photon (Geocoder)
    """
    try:
        geocoder = GeocoderService()
        
        # Health check
        is_available = geocoder.health_check()
        
        # Info dettagliate
        info = geocoder.get_info()
        
        return {
            "status": "available" if is_available else "unavailable",
            "enabled": os.getenv('USE_PHOTON', 'false').lower() == 'true',
            "host": info["host"],
            "port": info["port"],
            "base_url": info["base_url"],
            "language": info["language"],
            "default_bias": info["default_bias"],
            "supported_cities": info["supported_cities"],
            "is_available": is_available,
            "message": "Photon geocoder is operational" if is_available else "Photon is not responding"
        }
    except GeocoderError as e:
        return {
            "status": "error",
            "enabled": os.getenv('USE_PHOTON', 'false').lower() == 'true',
            "is_available": False,
            "message": str(e)
        }
    except Exception as e:
        logger.error(f"Errore verifica Photon: {e}", exc_info=True)
        return {
            "status": "error",
            "enabled": False,
            "is_available": False,
            "message": f"Errore: {str(e)}"
        }


@app.get("/api/redis/status", tags=["Redis"])
async def get_redis_status() -> Dict:
    """
    Verifica stato dettagliato del servizio Redis (Geocode Cache)
    """
    try:
        from .services.geocode_cache import get_geocode_cache
        
        cache = get_geocode_cache()
        
        # Health check
        is_available = cache.health_check()
        
        # Info dettagliate
        info = cache.get_info()
        
        # Statistiche cache
        stats = cache.get_stats()
        
        return {
            "status": "available" if is_available else "unavailable",
            "enabled": info["enabled"],
            "host": info["host"],
            "port": info["port"],
            "ttl_seconds": info["ttl"],
            "ttl_days": info["ttl_human"],
            "is_connected": info["is_connected"],
            "statistics": stats,
            "features": info["features"],
            "message": "Redis cache is operational" if is_available else "Redis is not responding"
        }
    except Exception as e:
        logger.error(f"Errore verifica Redis: {e}", exc_info=True)
        return {
            "status": "error",
            "enabled": False,
            "is_available": False,
            "message": f"Errore: {str(e)}"
        }


@app.post("/api/geocode", tags=["Geocoding"])
async def geocode_address(request: Dict) -> Dict:
    """
    Converte un indirizzo in coordinate geografiche (geocoding)
    
    Body:
        {
            "address": "Via Roma 1, Milano",
            "clean": true  (opzionale, default: true)
        }
    
    Returns:
        {
            "success": true,
            "original_address": "v. roma  1 - milano",
            "cleaned_address": "Via Roma 1, Milano",
            "latitude": 45.4642,
            "longitude": 9.1900,
            "confidence": 0.9,
            "city": "Milano",
            "country": "Italia"
        }
    """
    try:
        address = request.get("address", "").strip()
        should_clean = request.get("clean", True)
        
        if not address:
            raise HTTPException(status_code=400, detail="Address is required")
        
        logger.info(f"📍 Geocoding request: '{address}'")
        
        # Step 1: Pulizia indirizzo (opzionale)
        cleaned_address = address
        if should_clean:
            sanitizer = get_address_sanitizer()
            cleaned_address = sanitizer.clean(address)
            logger.info(f"  Cleaned: '{address}' → '{cleaned_address}'")
        
        # Step 2: Geocoding
        geocoder = get_geocoder_service()
        result = geocoder.geocode(cleaned_address)
        
        if result is None:
            return {
                "success": False,
                "original_address": address,
                "cleaned_address": cleaned_address,
                "message": "Address not found"
            }
        
        logger.info(f"  ✅ Geocoded: ({result.latitude:.6f}, {result.longitude:.6f})")
        
        return {
            "success": True,
            "original_address": address,
            "cleaned_address": cleaned_address,
            "latitude": result.latitude,
            "longitude": result.longitude,
            "confidence": result.confidence,
            "city": result.city,
            "country": result.country,
            "osm_type": result.osm_type
        }
        
    except GeocoderError as e:
        logger.error(f"Geocoding failed: {e}")
        raise HTTPException(status_code=503, detail=f"Geocoding service error: {str(e)}")
    except Exception as e:
        logger.error(f"Geocoding error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/api/optimize-with-geocoding", response_model=OptimizationWithGeocodingResult, tags=["Optimization"])
async def optimize_routes_with_geocoding(request: Dict) -> OptimizationWithGeocodingResult:
    """
    Ottimizza percorsi con geocoding automatico degli indirizzi
    
    Pipeline:
    1. Ricezione ordini con indirizzi testuali (non coordinate)
    2. Pulizia automatica indirizzi (AddressSanitizer)
    3. Geocoding (indirizzo → coordinate) via Photon
    4. Solo ordini con coordinate valide passano al VRP solver
    5. Ordini falliti vengono ritornati in "geocoding_errors"
    
    Body:
        {
            "orders_with_addresses": [
                {
                    "id": "ORD001",
                    "customer_name": "Cliente A",
                    "address": "Via Roma 1, Milano",
                    "demand": 15.5
                },
                ...
            ],
            "fleet_config": {...},
            "ortools_config": {...},
            "vehicle_specs": {...},  (opzionale)
            "bias_city": "milano"  (opzionale, default: "roma")
        }
    
    Returns:
        OptimizationWithGeocodingResult con:
        - routes: Route ottimizzate
        - geocoding_errors: Ordini non geocodificati
        - statistiche complete
    """
    start_time = time.time()
    
    try:
        logger.info("=" * 80)
        logger.info("🚀 OPTIMIZATION WITH GEOCODING START")
        logger.info("=" * 80)
        
        # Estrai parametri
        orders_with_addresses_data = request.get("orders_with_addresses", [])
        fleet_config_data = request.get("fleet_config")
        ortools_config_data = request.get("ortools_config")
        vehicle_specs_data = request.get("vehicle_specs")
        bias_city = request.get("bias_city", "roma")
        
        # Validazione
        if not orders_with_addresses_data:
            raise HTTPException(status_code=400, detail="orders_with_addresses is required")
        if not fleet_config_data:
            raise HTTPException(status_code=400, detail="fleet_config is required")
        if not ortools_config_data:
            raise HTTPException(status_code=400, detail="ortools_config is required")
        
        # Parse orders
        from .models import FleetConfiguration, ORToolsConfiguration, VehicleSpecifications
        
        orders_with_addresses = [OrderWithAddress(**order) for order in orders_with_addresses_data]
        fleet_config = FleetConfiguration(**fleet_config_data)
        ortools_config = ORToolsConfiguration(**ortools_config_data)
        vehicle_specs = VehicleSpecifications(**vehicle_specs_data) if vehicle_specs_data else None
        
        logger.info(f"📦 Orders received: {len(orders_with_addresses)}")
        logger.info(f"📍 Bias city: {bias_city}")
        
        # Step 1: Geocoding Pipeline
        logger.info("🗺️  Step 1: Geocoding Pipeline")
        pipeline = get_geocoding_pipeline()
        
        valid_orders, geocoding_errors, geocoding_stats = pipeline.process_orders(
            orders_with_addresses,
            bias_city=bias_city
        )
        
        logger.info(f"✅ Valid orders: {len(valid_orders)}")
        logger.info(f"❌ Failed orders: {len(geocoding_errors)}")
        
        # Se nessun ordine valido, ritorna errore
        if len(valid_orders) == 0:
            return OptimizationWithGeocodingResult(
                success=False,
                routes=[],
                total_distance=0.0,
                total_load=0.0,
                computation_time=time.time() - start_time,
                num_orders_served=0,
                num_vehicles_used=0,
                geocoding_errors=geocoding_errors,
                message=f"Geocoding fallito per tutti i {len(orders_with_addresses)} ordini"
            )
        
        # Step 2: VRP Optimization
        logger.info("🚗 Step 2: VRP Optimization")
        
        # Crea OptimizationRequest
        from .models import OptimizationRequest
        
        opt_request = OptimizationRequest(
            orders=valid_orders,
            fleet_config=fleet_config,
            ortools_config=ortools_config,
            vehicle_specs=vehicle_specs
        )
        
        # Validazione capacità
        total_demand = sum(order.demand for order in valid_orders)
        total_capacity = fleet_config.num_vehicles * fleet_config.vehicle_capacity
        
        if total_demand > total_capacity:
            logger.warning(
                f"⚠️  Domanda totale ({total_demand} kg) supera capacità totale ({total_capacity} kg)"
            )
        
        # Determina solver
        use_osrm = os.getenv('USE_OSRM', 'false').lower() == 'true'
        use_valhalla = os.getenv('USE_VALHALLA', 'false').lower() == 'true'
        
        vehicle_type = "car"
        if vehicle_specs:
            vehicle_type = vehicle_specs.vehicle_type.lower()
        
        logger.info(f"🚗/🚛 Vehicle type: {vehicle_type}")
        
        # Usa smart solver se routing engines attivi
        if use_osrm or use_valhalla:
            logger.info("🧠 Using Smart Routing Solver")
            solver = VRPSolverWithRoutingEngines(opt_request)
        else:
            logger.info("📐 Using Basic Solver (Haversine)")
            solver = VRPSolver(opt_request)
        
        # Risolvi VRP
        result = solver.solve()
        
        # Aggiungi geocoding errors al risultato
        computation_time = time.time() - start_time
        
        logger.info("=" * 80)
        logger.info("🎉 OPTIMIZATION WITH GEOCODING COMPLETE")
        logger.info(f"⏱️  Total time: {computation_time:.2f}s")
        logger.info(f"📊 Geocoding: {len(valid_orders)}/{len(orders_with_addresses)} success ({geocoding_stats.success_rate:.1f}%)")
        logger.info(f"📊 VRP: {result.num_orders_served}/{len(valid_orders)} served")
        logger.info("=" * 80)
        
        return OptimizationWithGeocodingResult(
            success=result.success,
            routes=result.routes,
            total_distance=result.total_distance,
            total_load=result.total_load,
            computation_time=computation_time,
            num_orders_served=result.num_orders_served,
            num_vehicles_used=result.num_vehicles_used,
            geocoding_errors=geocoding_errors,
            message=f"Ottimizzazione completata. Geocoding: {geocoding_stats.success_rate:.1f}% success. VRP: {result.num_orders_served} ordini serviti."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Optimization with geocoding failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Errore durante l'ottimizzazione con geocoding: {str(e)}"
        )


# Entry point per uvicorn
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
