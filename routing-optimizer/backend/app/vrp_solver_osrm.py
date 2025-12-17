"""
VRP Solver con OSRM - Risolve il CVRP usando distanze stradali reali

Versione aggiornata che integra OSRM per calcoli di distanza e tempo reali,
sostituendo il calcolo euclideo con dati stradali accurati.
"""
import math
import time
import logging
from typing import List, Dict, Tuple, Optional
from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp

from .models import (
    Order, 
    OptimizationRequest, 
    OptimizationResult,
    VehicleRoute,
    RouteStop,
    DepotLocation
)
from .services.osrm_client import OSRMClient, OSRMClientError

logger = logging.getLogger(__name__)


class VRPSolverOSRM:
    """
    Solver per il Capacitated Vehicle Routing Problem (CVRP)
    utilizzando Google OR-Tools con distanze OSRM reali
    """
    
    # Colori per visualizzazione veicoli sulla mappa
    VEHICLE_COLORS = [
        "#FF5733", "#33FF57", "#3357FF", "#FF33F5", "#F5FF33",
        "#33FFF5", "#FF8C33", "#8C33FF", "#33FF8C", "#FF3333",
        "#33FF33", "#3333FF", "#FFFF33", "#FF33FF", "#33FFFF"
    ]
    
    def __init__(
        self, 
        request: OptimizationRequest,
        use_osrm: bool = True,
        osrm_client: Optional[OSRMClient] = None
    ):
        """
        Inizializza il solver con la richiesta di ottimizzazione
        
        Args:
            request: Richiesta contenente ordini, configurazione flotta e OR-Tools
            use_osrm: Se True, usa OSRM per distanze reali, altrimenti Haversine
            osrm_client: Client OSRM (se None, ne crea uno nuovo)
        """
        self.request = request
        self.orders = request.orders
        self.depot = request.fleet_config.depot
        self.num_vehicles = request.fleet_config.num_vehicles
        self.vehicle_capacity = request.fleet_config.vehicle_capacity
        
        # OSRM configuration
        self.use_osrm = use_osrm
        self.osrm_client = osrm_client or OSRMClient()
        
        # Crea lista completa di locazioni (deposito + ordini)
        self.locations = self._create_locations_list()
        
        # Matrici delle distanze e tempi
        self.distance_matrix = None
        self.duration_matrix = None
        
        # Demands (il deposito ha demand 0)
        self.demands = [0] + [order.demand for order in self.orders]
    
    def _create_locations_list(self) -> List[Dict]:
        """
        Crea lista unificata di tutte le locazioni (deposito + clienti)
        
        Returns:
            Lista di dizionari con coordinate e informazioni
        """
        locations = [{
            "id": "DEPOT",
            "name": self.depot.name,
            "lat": self.depot.latitude,
            "lon": self.depot.longitude,
            "demand": 0.0,
            "is_depot": True
        }]
        
        for order in self.orders:
            locations.append({
                "id": order.id,
                "name": order.customer_name,
                "lat": order.latitude,
                "lon": order.longitude,
                "demand": order.demand,
                "is_depot": False
            })
        
        return locations
    
    def compute_distance_matrix(self) -> Tuple[List[List[int]], Optional[List[List[int]]]]:
        """
        Calcola matrice delle distanze usando OSRM o fallback a Haversine
        
        Returns:
            Tuple (distance_matrix, duration_matrix)
            - distance_matrix: sempre presente
            - duration_matrix: None se usa Haversine, popolata se usa OSRM
        """
        if self.use_osrm:
            try:
                logger.info("Tentativo calcolo distanze con OSRM...")
                
                # Verifica connessione OSRM
                if not self.osrm_client.health_check():
                    logger.warning("OSRM health check fallito, fallback a Haversine")
                    return self._compute_haversine_matrix(), None
                
                # Prepara coordinate per OSRM (lat, lon)
                coordinates = [(loc["lat"], loc["lon"]) for loc in self.locations]
                
                # Chiama OSRM
                distance_matrix, duration_matrix = self.osrm_client.get_matrix(coordinates)
                
                logger.info(f"✅ Matrici OSRM calcolate: {len(distance_matrix)}x{len(distance_matrix[0])}")
                logger.info(f"   Distanza max: {max(max(row) for row in distance_matrix)} m")
                logger.info(f"   Tempo max: {max(max(row) for row in duration_matrix)} s")
                
                return distance_matrix, duration_matrix
                
            except OSRMClientError as e:
                logger.error(f"❌ Errore OSRM: {e}")
                logger.warning("Fallback a calcolo Haversine")
                return self._compute_haversine_matrix(), None
            except Exception as e:
                logger.error(f"❌ Errore imprevisto OSRM: {e}", exc_info=True)
                logger.warning("Fallback a calcolo Haversine")
                return self._compute_haversine_matrix(), None
        else:
            logger.info("OSRM disabilitato, uso Haversine")
            return self._compute_haversine_matrix(), None
    
    def _compute_haversine_matrix(self) -> List[List[int]]:
        """
        Calcola matrice distanze con formula Haversine (fallback)
        
        Returns:
            Matrice delle distanze in metri (int)
        """
        def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
            """
            Calcola la distanza tra due punti geografici usando la formula di Haversine
            
            Returns:
                Distanza in metri
            """
            # Raggio della Terra in metri
            R = 6371000
            
            # Converti gradi in radianti
            lat1_rad = math.radians(lat1)
            lat2_rad = math.radians(lat2)
            delta_lat = math.radians(lat2 - lat1)
            delta_lon = math.radians(lon2 - lon1)
            
            # Formula di Haversine
            a = (math.sin(delta_lat / 2) ** 2 + 
                 math.cos(lat1_rad) * math.cos(lat2_rad) * 
                 math.sin(delta_lon / 2) ** 2)
            c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
            
            return R * c
        
        num_locations = len(self.locations)
        distance_matrix = []
        
        for i in range(num_locations):
            row = []
            for j in range(num_locations):
                if i == j:
                    row.append(0)
                else:
                    dist = haversine_distance(
                        self.locations[i]["lat"],
                        self.locations[i]["lon"],
                        self.locations[j]["lat"],
                        self.locations[j]["lon"]
                    )
                    row.append(int(dist))  # OR-Tools lavora con interi
            distance_matrix.append(row)
        
        logger.info(f"Matrice Haversine calcolata: {len(distance_matrix)}x{len(distance_matrix[0])}")
        return distance_matrix
    
    def _get_first_solution_strategy(self) -> int:
        """Mappa la strategia configurata al valore enum di OR-Tools"""
        strategies = {
            "PATH_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC,
            "GLOBAL_CHEAPEST_ARC": routing_enums_pb2.FirstSolutionStrategy.GLOBAL_CHEAPEST_ARC,
            "AUTOMATIC": routing_enums_pb2.FirstSolutionStrategy.AUTOMATIC
        }
        return strategies.get(
            self.request.ortools_config.first_solution_strategy,
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
    
    def _get_local_search_metaheuristic(self) -> int:
        """Mappa la metaheuristic configurata al valore enum di OR-Tools"""
        metaheuristics = {
            "GUIDED_LOCAL_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH,
            "TABU_SEARCH": routing_enums_pb2.LocalSearchMetaheuristic.TABU_SEARCH,
            "SIMULATED_ANNEALING": routing_enums_pb2.LocalSearchMetaheuristic.SIMULATED_ANNEALING
        }
        return metaheuristics.get(
            self.request.ortools_config.local_search_metaheuristic,
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
    
    def solve(self) -> OptimizationResult:
        """
        Risolve il CVRP e restituisce il risultato ottimizzato
        
        Returns:
            OptimizationResult con i percorsi ottimizzati
        """
        start_time = time.time()
        
        # Calcola matrici delle distanze (e tempi se OSRM)
        logger.info("=== Calcolo matrice distanze ===")
        self.distance_matrix, self.duration_matrix = self.compute_distance_matrix()
        
        # Determina quale matrice usare per OR-Tools
        # Di default usiamo distanza, ma potremmo ottimizzare per tempo
        cost_matrix = self.distance_matrix
        
        # Crea il Routing Index Manager
        manager = pywrapcp.RoutingIndexManager(
            len(cost_matrix),
            self.num_vehicles,
            0  # Indice del deposito
        )
        
        # Crea il Routing Model
        routing = pywrapcp.RoutingModel(manager)
        
        # Callback per il costo (distanza o tempo)
        def cost_callback(from_index: int, to_index: int) -> int:
            """Ritorna il costo tra due nodi"""
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return cost_matrix[from_node][to_node]
        
        transit_callback_index = routing.RegisterTransitCallback(cost_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)
        
        # Callback per la capacità (demand)
        def demand_callback(from_index: int) -> int:
            """Ritorna la domanda del nodo"""
            from_node = manager.IndexToNode(from_index)
            return int(self.demands[from_node])
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        # Aggiungi dimensione capacità
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # Slack (buffer) nullo
            [int(self.vehicle_capacity)] * self.num_vehicles,  # Capacità per veicolo
            True,  # Start cumul to zero
            'Capacity'
        )
        
        # Configura i parametri di ricerca
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = self._get_first_solution_strategy()
        search_parameters.local_search_metaheuristic = self._get_local_search_metaheuristic()
        search_parameters.time_limit.seconds = self.request.ortools_config.time_limit_seconds
        
        # Risolvi il problema
        logger.info("=== Inizio ottimizzazione OR-Tools ===")
        solution = routing.SolveWithParameters(search_parameters)
        
        computation_time = time.time() - start_time
        
        # Verifica se è stata trovata una soluzione
        if not solution:
            return OptimizationResult(
                success=False,
                routes=[],
                total_distance=0.0,
                total_load=0.0,
                computation_time=computation_time,
                num_orders_served=0,
                num_vehicles_used=0,
                message="Nessuna soluzione trovata. Prova ad aumentare il numero di veicoli o la capacità."
            )
        
        # Estrai le rotte dalla soluzione
        routes = self._extract_routes(manager, routing, solution)
        
        # Calcola statistiche
        total_distance = sum(route.total_distance for route in routes)
        total_load = sum(route.total_load for route in routes)
        num_orders_served = sum(len(route.stops) - 2 for route in routes)  # -2 per escludere depositi iniziale e finale
        num_vehicles_used = len([r for r in routes if len(r.stops) > 2])
        
        return OptimizationResult(
            success=True,
            routes=routes,
            total_distance=round(total_distance / 1000, 2),  # Converti in km
            total_load=round(total_load, 2),
            computation_time=round(computation_time, 3),
            num_orders_served=num_orders_served,
            num_vehicles_used=num_vehicles_used,
            message=f"Ottimizzazione completata con successo {'(OSRM)' if self.use_osrm and self.duration_matrix else '(Haversine)'}"
        )
    
    def _extract_routes(
        self, 
        manager: pywrapcp.RoutingIndexManager,
        routing: pywrapcp.RoutingModel,
        solution
    ) -> List[VehicleRoute]:
        """
        Estrae le rotte dalla soluzione OR-Tools
        
        Returns:
            Lista di VehicleRoute
        """
        routes = []
        capacity_dimension = routing.GetDimensionOrDie('Capacity')
        
        for vehicle_id in range(self.num_vehicles):
            index = routing.Start(vehicle_id)
            stops = []
            route_distance = 0
            route_load = 0
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                location = self.locations[node_index]
                
                # Ottieni carico cumulativo
                load_var = capacity_dimension.CumulVar(index)
                cumulative_load = solution.Value(load_var)
                
                stop = RouteStop(
                    order_id=location["id"] if not location["is_depot"] else None,
                    customer_name=location["name"],
                    latitude=location["lat"],
                    longitude=location["lon"],
                    demand=location["demand"],
                    cumulative_load=round(cumulative_load, 2),
                    is_depot=location["is_depot"]
                )
                stops.append(stop)
                
                # Calcola distanza al prossimo nodo
                previous_index = index
                index = solution.Value(routing.NextVar(index))
                route_distance += routing.GetArcCostForVehicle(previous_index, index, vehicle_id)
                route_load = cumulative_load
            
            # Aggiungi l'ultima fermata (ritorno al deposito)
            node_index = manager.IndexToNode(index)
            location = self.locations[node_index]
            stops.append(RouteStop(
                order_id=None,
                customer_name=location["name"],
                latitude=location["lat"],
                longitude=location["lon"],
                demand=0.0,
                cumulative_load=0.0,
                is_depot=True
            ))
            
            # Crea rotta solo se ci sono fermate oltre al deposito
            if len(stops) > 2:
                route = VehicleRoute(
                    vehicle_id=vehicle_id + 1,
                    stops=stops,
                    total_distance=round(route_distance / 1000, 2),  # Converti in km
                    total_load=round(route_load, 2),
                    color=self.VEHICLE_COLORS[vehicle_id % len(self.VEHICLE_COLORS)]
                )
                routes.append(route)
        
        return routes
