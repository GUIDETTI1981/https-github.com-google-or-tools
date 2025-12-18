"""
Celery Tasks for VRP Optimization

Background tasks for heavy OR-Tools computations with routing engines (OSRM/Valhalla).

Task Flow:
1. FastAPI receives POST /api/optimize
2. Enqueues task: solve_vrp_task.delay(request_data)
3. Returns 202 Accepted with task_id
4. Celery worker picks up task
5. Executes OR-Tools optimization (can take minutes)
6. Stores result in Redis
7. Frontend polls GET /api/tasks/{task_id} until SUCCESS

Autore: Senior Backend Architect
Data: 2025-12-18
"""

import os
import logging
import time
from typing import Dict, Any
from celery import Task

from app.core.celery_app import celery_app
from app.models import (
    Order,
    DepotLocation,
    FleetConfiguration,
    ORToolsConfiguration,
    VehicleSpecifications,
    OptimizationRequest
)
from app.vrp_solver import VRPSolver
from app.vrp_solver_routing import VRPSolverWithRoutingEngines

logger = logging.getLogger(__name__)


class VRPTask(Task):
    """
    Custom Celery Task class with state management
    
    Tracks task progress and handles failures gracefully
    """
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails"""
        logger.error(f"❌ Task {task_id} FAILED: {exc}")
        logger.error(f"   Args: {args}")
        logger.error(f"   Exception info: {einfo}")
        
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds"""
        logger.info(f"✅ Task {task_id} SUCCESS")
        
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried"""
        logger.warning(f"🔄 Task {task_id} RETRY: {exc}")


@celery_app.task(
    name='app.tasks.vrp_tasks.solve_vrp_task',
    base=VRPTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,  # Retry after 60 seconds
    time_limit=3600,  # 1 hour max
    soft_time_limit=3300  # 55 minutes soft limit
)
def solve_vrp_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task for VRP optimization with OR-Tools
    
    This task is executed asynchronously by Celery workers, freeing up
    the FastAPI server to handle other requests while heavy computation runs.
    
    Args:
        self: Celery task instance (injected by bind=True)
        request_data: Dict containing:
            - orders: List of Order dicts
            - fleet_config: FleetConfiguration dict
            - ortools_config: ORToolsConfiguration dict
            - vehicle_specs: Optional VehicleSpecifications dict
            
    Returns:
        Dict with optimization result:
        {
            "success": bool,
            "routes": [...],
            "total_distance": float,
            "total_load": int,
            "computation_time": float,
            "num_orders_served": int,
            "num_vehicles_used": int,
            "message": str
        }
        
    Raises:
        Exception: If optimization fails (will be retried up to 3 times)
        
    Example:
        >>> task = solve_vrp_task.delay(request_dict)
        >>> task_id = task.id
        >>> # Poll for result
        >>> result = task.get(timeout=3600)
    """
    
    try:
        # Log task start
        logger.info("=" * 70)
        logger.info(f"🚀 VRP TASK STARTED: {self.request.id}")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Update task state to STARTED with metadata
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Initializing',
                'progress': 0
            }
        )
        
        # Reconstruct OptimizationRequest from dict
        logger.info("📦 Reconstructing OptimizationRequest...")
        
        orders = [Order(**o) for o in request_data['orders']]
        fleet_config = FleetConfiguration(**request_data['fleet_config'])
        ortools_config = ORToolsConfiguration(**request_data['ortools_config'])
        
        vehicle_specs = None
        if 'vehicle_specs' in request_data and request_data['vehicle_specs']:
            vehicle_specs = VehicleSpecifications(**request_data['vehicle_specs'])
        
        request = OptimizationRequest(
            orders=orders,
            fleet_config=fleet_config,
            ortools_config=ortools_config,
            vehicle_specs=vehicle_specs
        )
        
        logger.info(f"   Orders: {len(request.orders)}")
        logger.info(f"   Vehicles: {request.fleet_config.num_vehicles}")
        logger.info(f"   Vehicle Capacity: {request.fleet_config.vehicle_capacity} kg")
        logger.info(f"   Strategy: {request.ortools_config.first_solution_strategy}")
        logger.info(f"   Metaheuristic: {request.ortools_config.local_search_metaheuristic}")
        
        # Update state
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Validating input',
                'progress': 10,
                'num_orders': len(request.orders),
                'num_vehicles': request.fleet_config.num_vehicles
            }
        )
        
        # Validation
        if len(request.orders) == 0:
            raise ValueError("No orders to optimize")
        
        total_demand = sum(order.demand for order in request.orders)
        total_capacity = request.fleet_config.num_vehicles * request.fleet_config.vehicle_capacity
        
        if total_demand > total_capacity:
            logger.warning(
                f"⚠️  Total demand ({total_demand} kg) exceeds total capacity ({total_capacity} kg)"
            )
        
        # Determine vehicle type and routing engine
        vehicle_type = "car"
        if request.vehicle_specs:
            vehicle_type = request.vehicle_specs.vehicle_type.lower()
        
        use_osrm = os.getenv('USE_OSRM', 'false').lower() == 'true'
        use_valhalla = os.getenv('USE_VALHALLA', 'false').lower() == 'true'
        
        logger.info(f"🚗/🚛 Vehicle type: {vehicle_type}")
        logger.info(f"⚙️  Routing engines: OSRM={use_osrm}, Valhalla={use_valhalla}")
        
        # Update state
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Selecting routing engine',
                'progress': 20,
                'vehicle_type': vehicle_type,
                'use_osrm': use_osrm,
                'use_valhalla': use_valhalla
            }
        )
        
        # Select solver based on routing engines
        if use_osrm or use_valhalla:
            logger.info("🧠 Using Smart Routing Solver (OSRM/Valhalla)")
            solver = VRPSolverWithRoutingEngines(request)
        else:
            logger.info("📐 Using Basic Solver (Haversine distance)")
            solver = VRPSolver(request)
        
        # Update state
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Computing distance matrix',
                'progress': 30
            }
        )
        
        # Execute optimization (this is the heavy part - can take minutes)
        logger.info("⚙️  Starting OR-Tools optimization...")
        
        result = solver.solve()
        
        elapsed_time = time.time() - start_time
        
        # Log result
        if result.success:
            logger.info("=" * 70)
            logger.info("✅ VRP OPTIMIZATION COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"   Total distance: {result.total_distance} km")
            logger.info(f"   Total load: {result.total_load} kg")
            logger.info(f"   Vehicles used: {result.num_vehicles_used}/{request.fleet_config.num_vehicles}")
            logger.info(f"   Orders served: {result.num_orders_served}/{len(request.orders)}")
            logger.info(f"   Computation time: {result.computation_time}s")
            logger.info(f"   Task elapsed time: {elapsed_time:.2f}s")
            logger.info("=" * 70)
        else:
            logger.warning(f"⚠️  Optimization failed: {result.message}")
        
        # Convert result to dict for JSON serialization
        result_dict = result.model_dump()
        
        return result_dict
        
    except Exception as e:
        logger.error(f"❌ Task {self.request.id} FAILED: {str(e)}", exc_info=True)
        
        # Update state to FAILURE with error details
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        
        # Retry if possible
        if self.request.retries < self.max_retries:
            logger.info(f"🔄 Retrying task {self.request.id} (attempt {self.request.retries + 1}/{self.max_retries})")
            raise self.retry(exc=e)
        else:
            logger.error(f"❌ Task {self.request.id} FAILED after {self.max_retries} retries")
            raise


@celery_app.task(
    name='app.tasks.vrp_tasks.solve_vrp_with_geocoding_task',
    base=VRPTask,
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    time_limit=3600,
    soft_time_limit=3300
)
def solve_vrp_with_geocoding_task(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Celery task for VRP optimization with automatic geocoding
    
    This task:
    1. Geocodes addresses to coordinates using Photon (with Redis cache)
    2. Executes VRP optimization with OR-Tools
    
    Args:
        self: Celery task instance
        request_data: Dict containing:
            - orders: List of OrderWithAddress dicts (address instead of lat/lon)
            - fleet_config: FleetConfiguration dict
            - ortools_config: ORToolsConfiguration dict
            - bias_city: Optional str for geocoding bias
            
    Returns:
        Dict with optimization result + geocoding errors
        
    Example:
        >>> task = solve_vrp_with_geocoding_task.delay(request_dict)
        >>> result = task.get(timeout=3600)
    """
    
    try:
        logger.info("=" * 70)
        logger.info(f"🚀 VRP + GEOCODING TASK STARTED: {self.request.id}")
        logger.info("=" * 70)
        
        start_time = time.time()
        
        # Update state
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Geocoding addresses',
                'progress': 0
            }
        )
        
        # Import geocoding pipeline
        from app.geocoding_pipeline import get_geocoding_pipeline
        from app.models import OrderWithAddress
        
        # Reconstruct OrderWithAddress objects
        orders_with_address = [OrderWithAddress(**o) for o in request_data['orders']]
        bias_city = request_data.get('bias_city', 'roma')
        
        logger.info(f"📍 Geocoding {len(orders_with_address)} addresses...")
        logger.info(f"   Bias city: {bias_city}")
        
        # Geocode addresses
        pipeline = get_geocoding_pipeline()
        valid_orders, geocoding_errors, stats = pipeline.process_orders(
            orders_with_address,
            bias_city=bias_city
        )
        
        logger.info(f"   Geocoding success rate: {stats.success_rate:.1f}%")
        logger.info(f"   Valid orders: {len(valid_orders)}")
        logger.info(f"   Failed orders: {len(geocoding_errors)}")
        
        # Update state
        self.update_state(
            state='STARTED',
            meta={
                'status': 'Processing',
                'stage': 'Optimizing routes',
                'progress': 50,
                'geocoding_success_rate': stats.success_rate,
                'valid_orders': len(valid_orders),
                'failed_orders': len(geocoding_errors)
            }
        )
        
        # If no valid orders, return error
        if len(valid_orders) == 0:
            raise ValueError("No valid orders after geocoding")
        
        # Reconstruct OptimizationRequest with geocoded orders
        fleet_config = FleetConfiguration(**request_data['fleet_config'])
        ortools_config = ORToolsConfiguration(**request_data['ortools_config'])
        
        vehicle_specs = None
        if 'vehicle_specs' in request_data and request_data['vehicle_specs']:
            vehicle_specs = VehicleSpecifications(**request_data['vehicle_specs'])
        
        request = OptimizationRequest(
            orders=valid_orders,
            fleet_config=fleet_config,
            ortools_config=ortools_config,
            vehicle_specs=vehicle_specs
        )
        
        # Solve VRP
        logger.info("⚙️  Starting OR-Tools optimization...")
        
        use_osrm = os.getenv('USE_OSRM', 'false').lower() == 'true'
        use_valhalla = os.getenv('USE_VALHALLA', 'false').lower() == 'true'
        
        if use_osrm or use_valhalla:
            solver = VRPSolverWithRoutingEngines(request)
        else:
            solver = VRPSolver(request)
        
        result = solver.solve()
        
        elapsed_time = time.time() - start_time
        
        # Log result
        if result.success:
            logger.info("=" * 70)
            logger.info("✅ VRP + GEOCODING COMPLETED SUCCESSFULLY")
            logger.info("=" * 70)
            logger.info(f"   Geocoding success rate: {stats.success_rate:.1f}%")
            logger.info(f"   Total distance: {result.total_distance} km")
            logger.info(f"   Task elapsed time: {elapsed_time:.2f}s")
            logger.info("=" * 70)
        
        # Convert result to dict
        result_dict = result.model_dump()
        
        # Add geocoding errors
        result_dict['geocoding_errors'] = [e.model_dump() for e in geocoding_errors]
        result_dict['geocoding_stats'] = stats.to_dict()
        
        return result_dict
        
    except Exception as e:
        logger.error(f"❌ Task {self.request.id} FAILED: {str(e)}", exc_info=True)
        
        self.update_state(
            state='FAILURE',
            meta={
                'status': 'Failed',
                'error': str(e),
                'error_type': type(e).__name__
            }
        )
        
        if self.request.retries < self.max_retries:
            raise self.retry(exc=e)
        else:
            raise
