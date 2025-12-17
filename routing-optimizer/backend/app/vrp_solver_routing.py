"""
VRP Solver with Smart Routing Engine Selection

Questo modulo estende VRPSolver per selezionare intelligentemente il motore
di routing basato sul tipo di veicolo:
- Car/Van: OSRM (ottimizzato per auto)
- Truck: Valhalla (supporta vincoli fisici peso/altezza/larghezza)

Autore: Senior DevOps Engineer & Python Developer
Data: 2025-12-17
"""

import os
import time
import logging
from typing import List, Tuple, Dict, Optional
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

from .models import (
    OptimizationRequest, 
    OptimizationResult, 
    VehicleRoute, 
    RouteStop,
    VehicleSpecifications
)
from .services.osrm_client import OSRMClient, OSRMClientError
from .services.valhalla_client import ValhallaClient, ValhallaClientError, TruckSpecs

logger = logging.getLogger(__name__)


class VRPSolverWithRoutingEngines:
    """
    VRP Solver con selezione intelligente del routing engine
    
    Features:
    - OSRM per car/van (veloce, ottimizzato per traffico)
    - Valhalla per truck (supporta vincoli fisici)
    - Fallback automatico a distanza Haversine se servizi non disponibili
    """
    
    # Colori per visualizzazione mappa (fino a 10 veicoli)
    VEHICLE_COLORS = [
        "#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A", "#98D8C8",
        "#F7DC6F", "#BB8FCE", "#85C1E2", "#F8B739", "#52C77C"
    ]
    
    def __init__(self, request: OptimizationRequest):
        """
        Inizializza il solver con parametri di ottimizzazione
        
        Args:
            request: OptimizationRequest contenente ordini, flotta, config OR-Tools
        """
        self.request = request
        self.orders = request.orders
        self.fleet_config = request.fleet_config
        self.ortools_config = request.ortools_config
        self.vehicle_specs = request.vehicle_specs or VehicleSpecifications()
        
        # Identifica il tipo di veicolo
        self.vehicle_type = self.vehicle_specs.vehicle_type.lower()
        
        # Prepara lista unificata di locazioni: [depot, order1, order2, ...]
        self.locations = self._prepare_locations()
        
        # Inizializza routing clients
        self.osrm_client = None
        self.valhalla_client = None
        self.use_osrm = os.getenv('USE_OSRM', 'false').lower() == 'true'
        self.use_valhalla = os.getenv('USE_VALHALLA', 'false').lower() == 'true'
        
        logger.info(f"VRP Solver initialized: {len(self.orders)} orders, {self.fleet_config.num_vehicles} vehicles")
        logger.info(f"Vehicle type: {self.vehicle_type}")
        logger.info(f"Routing engines: OSRM={self.use_osrm}, Valhalla={self.use_valhalla}")
    
    def _prepare_locations(self) -> List[Tuple[float, float, str, str]]:
        """
        Prepara lista unificata di locazioni per OR-Tools
        
        Returns:
            Lista di tuple (lat, lon, name, id)
        """
        locations = []
        
        # Depot sempre in posizione 0
        depot = self.fleet_config.depot
        locations.append((depot.latitude, depot.longitude, depot.name, "DEPOT"))
        
        # Ordini clienti
        for order in self.orders:
            locations.append((
                order.latitude, 
                order.longitude, 
                order.customer_name, 
                order.id
            ))
        
        return locations
    
    def _get_routing_engine_info(self) -> str:
        """Ottiene informazioni sul routing engine selezionato"""
        if self.vehicle_type == "truck" and self.use_valhalla:
            return "Valhalla (Truck routing with physical constraints)"
        elif self.vehicle_type in ["car", "van"] and self.use_osrm:
            return "OSRM (Car routing optimized)"
        else:
            return "Haversine (Euclidean distance fallback)"
    
    def _compute_distance_matrix_smart(self) -> Tuple[List[List[int]], Optional[List[List[int]]]]:
        """
        Calcola matrice distanze usando il routing engine appropriato
        
        Returns:
            Tuple (distance_matrix, duration_matrix)
            - distance_matrix: sempre presente (metri)
            - duration_matrix: opzionale (secondi), None se non disponibile
        """
        coordinates = [(lat, lon) for lat, lon, _, _ in self.locations]
        
        # Strategy 1: Valhalla per TRUCK
        if self.vehicle_type == "truck" and self.use_valhalla:
            logger.info("🚛 Using Valhalla for TRUCK routing (with physical constraints)")
            try:
                self.valhalla_client = ValhallaClient()
                
                if not self.valhalla_client.health_check():
                    raise ValhallaClientError("Valhalla service not available")
                
                # Converti VehicleSpecifications → TruckSpecs
                truck_specs = TruckSpecs(
                    weight=self.vehicle_specs.weight or 21.77,
                    height=self.vehicle_specs.height or 4.11,
                    width=self.vehicle_specs.width or 2.6,
                    length=self.vehicle_specs.length or 21.64,
                    axle_load=self.vehicle_specs.axle_load or 9.07,
                    axle_count=self.vehicle_specs.axle_count or 5,
                    hazmat=self.vehicle_specs.hazmat or False
                )
                
                logger.info(f"Truck specs: {truck_specs.weight}t, {truck_specs.height}m height, hazmat={truck_specs.hazmat}")
                
                distance_matrix, duration_matrix = self.valhalla_client.get_matrix(
                    coordinates, 
                    truck_specs=truck_specs
                )
                
                logger.info("✅ Valhalla matrix computed successfully")
                return distance_matrix, duration_matrix
                
            except ValhallaClientError as e:
                logger.warning(f"Valhalla failed: {e}. Falling back to Haversine.")
                return self._compute_haversine_distance_matrix(), None
        
        # Strategy 2: OSRM per CAR/VAN
        elif self.vehicle_type in ["car", "van"] and self.use_osrm:
            logger.info("🚗 Using OSRM for CAR/VAN routing")
            try:
                self.osrm_client = OSRMClient()
                
                if not self.osrm_client.health_check():
                    raise OSRMClientError("OSRM service not available")
                
                distance_matrix, duration_matrix = self.osrm_client.get_matrix(coordinates)
                
                logger.info("✅ OSRM matrix computed successfully")
                return distance_matrix, duration_matrix
                
            except OSRMClientError as e:
                logger.warning(f"OSRM failed: {e}. Falling back to Haversine.")
                return self._compute_haversine_distance_matrix(), None
        
        # Strategy 3: Fallback Haversine
        else:
            logger.info("📍 Using Haversine distance (no routing engine configured)")
            return self._compute_haversine_distance_matrix(), None
    
    def _compute_haversine_distance_matrix(self) -> List[List[int]]:
        """
        Calcola matrice distanze con formula Haversine (fallback)
        
        Returns:
            Matrice NxN di distanze in metri (arrotondate)
        """
        import math
        
        def haversine(lat1, lon1, lat2, lon2):
            """Calcola distanza in metri tra due coordinate"""
            R = 6371000  # Raggio Terra in metri
            phi1 = math.radians(lat1)
            phi2 = math.radians(lat2)
            delta_phi = math.radians(lat2 - lat1)
            delta_lambda = math.radians(lon2 - lon1)
            
            a = math.sin(delta_phi/2)**2 + \
                math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
            
            return R * c
        
        n = len(self.locations)
        distance_matrix = []
        
        for i in range(n):
            row = []
            lat1, lon1, _, _ = self.locations[i]
            for j in range(n):
                lat2, lon2, _, _ = self.locations[j]
                if i == j:
                    row.append(0)
                else:
                    distance = haversine(lat1, lon1, lat2, lon2)
                    row.append(int(math.ceil(distance)))
            distance_matrix.append(row)
        
        logger.info(f"Haversine matrix computed: {n}x{n}")
        return distance_matrix
    
    def _get_first_solution_strategy(self, strategy_name: str):
        """Mappa nome strategia a enum OR-Tools"""
        strategies = {
            "PATH_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            "GLOBAL_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
            "AUTOMATIC": routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        }
        return strategies.get(strategy_name, routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
    
    def _get_local_search_metaheuristic(self, metaheuristic_name: str):
        """Mappa nome metaheuristic a enum OR-Tools"""
        metaheuristics = {
            "GUIDED_LOCAL_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
            "TABU_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
            "SIMULATED_ANNEALING": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING
        }
        return metaheuristics.get(metaheuristic_name, routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
    
    def solve(self) -> OptimizationResult:
        """
        Risolve il CVRP usando OR-Tools con routing engine intelligente
        
        Returns:
            OptimizationResult con route ottimizzate
        """
        start_time = time.time()
        
        logger.info("=" * 60)
        logger.info("🚀 Starting VRP Optimization")
        logger.info(f"📦 Orders: {len(self.orders)}")
        logger.info(f"🚛 Vehicles: {self.fleet_config.num_vehicles} (type: {self.vehicle_type})")
        logger.info(f"⚙️  Engine: {self._get_routing_engine_info()}")
        logger.info("=" * 60)
        
        # Step 1: Calcola matrice distanze con routing engine appropriato
        distance_matrix, duration_matrix = self._compute_distance_matrix_smart()
        
        # Step 2: Crea OR-Tools Manager e Model
        manager = pywrapcp.RoutingIndexManager(
            len(self.locations),
            self.fleet_config.num_vehicles,
            0  # depot index
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # Step 3: Registra distance callback
        def distance_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return distance_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(distance_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Step 4: Registra demand callback (capacità veicoli)
        demands = [0]  # depot ha demand 0
        for order in self.orders:
            demands.append(int(order.demand * 1000))  # kg → grammi
        
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return demands[from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            [int(self.fleet_config.vehicle_capacity * 1000)] * self.fleet_config.num_vehicles,  # kg → grammi
            True,  # start cumul to zero
            'Capacity'
        )
        
        # Step 5: Configura parametri OR-Tools
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = self._get_first_solution_strategy(
            self.ortools_config.first_solution_strategy
        )
        search_parameters.local_search_metaheuristic = self._get_local_search_metaheuristic(
            self.ortools_config.local_search_metaheuristic
        )
        search_parameters.time_limit.seconds = self.ortools_config.time_limit_seconds
        
        logger.info(f"⚙️  OR-Tools config:")
        logger.info(f"   - Strategy: {self.ortools_config.first_solution_strategy}")
        logger.info(f"   - Metaheuristic: {self.ortools_config.local_search_metaheuristic}")
        logger.info(f"   - Time limit: {self.ortools_config.time_limit_seconds}s")
        
        # Step 6: Risolvi
        logger.info("🔄 Solving...")
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            logger.info("✅ Solution found!")
            result = self._extract_solution(manager, routing, solution, distance_matrix)
            computation_time = time.time() - start_time
            result.computation_time = computation_time
            
            logger.info(f"📊 Results:")
            logger.info(f"   - Total distance: {result.total_distance:.2f} km")
            logger.info(f"   - Orders served: {result.num_orders_served}/{len(self.orders)}")
            logger.info(f"   - Vehicles used: {result.num_vehicles_used}/{self.fleet_config.num_vehicles}")
            logger.info(f"   - Computation time: {computation_time:.3f}s")
            logger.info("=" * 60)
            
            return result
        else:
            logger.error("❌ No solution found!")
            return OptimizationResult(
                success=False,
                routes=[],
                total_distance=0.0,
                total_load=0.0,
                computation_time=time.time() - start_time,
                num_orders_served=0,
                num_vehicles_used=0,
                message="OR-Tools non ha trovato una soluzione valida"
            )
    
    def _extract_solution(self, manager, routing, solution, distance_matrix) -> OptimizationResult:
        """
        Estrae le route dalla soluzione OR-Tools
        
        Returns:
            OptimizationResult con tutte le route
        """
        routes = []
        total_distance = 0.0
        total_load = 0.0
        vehicles_used = 0
        orders_served = 0
        
        for vehicle_id in range(self.fleet_config.num_vehicles):
            index = routing.Start(vehicle_id)
            route_distance = 0
            route_load = 0
            stops = []
            
            # Fermata iniziale: depot
            depot = self.fleet_config.depot
            stops.append(RouteStop(
                order_id=None,
                customer_name=depot.name,
                latitude=depot.latitude,
                longitude=depot.longitude,
                demand=0.0,
                cumulative_load=0.0,
                is_depot=True
            ))
            
            # Percorri la route
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                next_index = solution.Value(routing.NextVar(index))
                next_node_index = manager.IndexToNode(next_index)
                
                # Calcola distanza arco
                route_distance += distance_matrix[node_index][next_node_index]
                
                # Se non è il depot, aggiungi la fermata
                if next_node_index > 0:  # 0 è il depot
                    order = self.orders[next_node_index - 1]
                    route_load += order.demand
                    orders_served += 1
                    
                    stops.append(RouteStop(
                        order_id=order.id,
                        customer_name=order.customer_name,
                        latitude=order.latitude,
                        longitude=order.longitude,
                        demand=order.demand,
                        cumulative_load=route_load,
                        is_depot=False
                    ))
                
                index = next_index
            
            # Fermata finale: ritorno al depot
            stops.append(RouteStop(
                order_id=None,
                customer_name=depot.name,
                latitude=depot.latitude,
                longitude=depot.longitude,
                demand=0.0,
                cumulative_load=route_load,
                is_depot=True
            ))
            
            # Se la route ha fermate (non è vuota)
            if len(stops) > 2:  # Più del depot iniziale e finale
                vehicles_used += 1
                routes.append(VehicleRoute(
                    vehicle_id=vehicle_id + 1,
                    stops=stops,
                    total_distance=round(route_distance / 1000, 2),  # metri → km
                    total_load=round(route_load, 2),
                    color=self.VEHICLE_COLORS[vehicle_id % len(self.VEHICLE_COLORS)]
                ))
                
                total_distance += route_distance
                total_load += route_load
        
        return OptimizationResult(
            success=True,
            routes=routes,
            total_distance=round(total_distance / 1000, 2),  # metri → km
            total_load=round(total_load, 2),
            computation_time=0.0,  # Verrà impostato dopo
            num_orders_served=orders_served,
            num_vehicles_used=vehicles_used,
            message=f"Ottimizzazione completata con {self._get_routing_engine_info()}"
        )
