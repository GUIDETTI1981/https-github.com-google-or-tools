"""
Ottimizzatore per pianificazione ritiri usando OR-Tools
Vehicle Routing Problem con Time Windows, Capacità e Vincoli di Zona
"""

from ortools.constraint_solver import routing_enums_pb2
from ortools.constraint_solver import pywrapcp
import numpy as np
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class Stop:
    """Rappresenta una fermata di ritiro"""
    key: str
    name: str
    coords: Optional[Tuple[float, float]]
    total_weight: int
    orders: List[Dict]
    loading_time: int  # minuti
    zone: str
    priority_score: int
    ready_time: str  # 'mattino' o 'pomeriggio'
    appointment: Optional[str]
    appointment_time: Optional[str]
    opening_windows: List[Dict]  # [{'start': minutes, 'end': minutes}]


@dataclass
class Vehicle:
    """Rappresenta un mezzo"""
    id: str
    targa: str
    autista: str
    payload: int  # kg
    rules: Optional[Dict]


class ZoneManager:
    """Gestisce le regole di compatibilità tra zone"""
    
    ZONE_GROUPS = {
        'GROUP_A': [
            'SOLIGNANO-CAST.RANGONE', 'UBERSETTO-MARANELLO-FORMIGINE',
            'FIORANO 2', 'FIORANO 1', 'SASSUOLO 2', 'SASSUOLO 1',
            'ROTEGLIA-CASTELLARANO'
        ],
        'GROUP_B': ['SCANDIANO-CASALGRANDE-S.ANTONINO', 'ROTEGLIA-CASTELLARANO'],
        'GROUP_C': ['RUBIERA-VILLALUNGA', 'ROTEGLIA-CASTELLARANO']
    }
    
    EXCLUSIONS = {
        'ROTEGLIA-CASTELLARANO': [
            'novabell', 'century', 'coem', 'lea fora di cavola', 'panaria cavola',
            'pollini/i pietrini', 'saime roteglia', 'smalticeram', 'tempra/gambini volta',
            'petrus (roteglia)', 'durocem'
        ]
    }
    
    @classmethod
    def are_zones_compatible(cls, zones: List[str], stop_names: List[str]) -> bool:
        """Verifica se le zone sono compatibili secondo le regole"""
        if len(zones) <= 1:
            return True
        
        zones_upper = [z.upper() for z in zones]
        
        # Controllo esclusioni per ROTEGLIA-CASTELLARANO
        has_roteglia = 'ROTEGLIA-CASTELLARANO' in zones_upper
        if has_roteglia:
            excluded_stops = [
                name.lower() for name in stop_names 
                if any(excl in name.lower() for excl in cls.EXCLUSIONS['ROTEGLIA-CASTELLARANO'])
            ]
            if excluded_stops:
                # Se ci sono stop esclusi, solo ROTEGLIA è permessa
                return all(z == 'ROTEGLIA-CASTELLARANO' for z in zones_upper)
        
        # Trova gruppi comuni
        def find_groups_for_zone(zone: str) -> List[str]:
            return [group for group, zones_list in cls.ZONE_GROUPS.items() 
                    if zone.upper() in zones_list]
        
        common_groups = find_groups_for_zone(zones[0])
        if not common_groups:
            return False
        
        for zone in zones[1:]:
            zone_groups = find_groups_for_zone(zone)
            common_groups = [g for g in common_groups if g in zone_groups]
            if not common_groups:
                return False
        
        return True


class RouteOptimizer:
    """Ottimizzatore principale usando OR-Tools"""
    
    DEPOT_COORDS = (44.5225, 10.7480)  # Via Raffaello 3, Castellarano
    TRAVEL_BUFFER = 40  # 20 min andata + 20 min ritorno
    
    def __init__(self):
        self.stops: List[Stop] = []
        self.vehicles: List[Vehicle] = []
        self.distance_matrix = []
        self.time_matrix = []
        
    def calculate_distance(self, coord1: Tuple[float, float], 
                          coord2: Tuple[float, float]) -> float:
        """Calcola distanza euclidea approssimativa in km"""
        if not coord1 or not coord2:
            return 999  # Penalità alta per coordinate mancanti
        
        lat1, lon1 = coord1
        lat2, lon2 = coord2
        
        # Approssimazione: 1 grado lat ≈ 111 km, 1 grado lon ≈ 85 km (a questa latitudine)
        dx = (lon2 - lon1) * 85
        dy = (lat2 - lat1) * 111
        return np.sqrt(dx**2 + dy**2)
    
    def build_distance_matrix(self):
        """Costruisce matrice delle distanze (depot + stops)"""
        n = len(self.stops) + 1  # +1 per depot
        self.distance_matrix = np.zeros((n, n))
        
        coords = [self.DEPOT_COORDS] + [s.coords for s in self.stops]
        
        for i in range(n):
            for j in range(n):
                if i != j:
                    self.distance_matrix[i][j] = self.calculate_distance(
                        coords[i], coords[j]
                    )
        
        # Converte in tempo di viaggio (assumendo 40 km/h media)
        self.time_matrix = (self.distance_matrix / 40 * 60).astype(int)  # minuti
        
    def create_data_model(self, time_window: Dict) -> Dict:
        """Crea il modello dati per OR-Tools"""
        data = {}
        data['distance_matrix'] = self.distance_matrix.tolist()
        data['time_matrix'] = self.time_matrix.tolist()
        data['num_vehicles'] = len(self.vehicles)
        data['depot'] = 0
        
        # Capacità mezzi
        data['vehicle_capacities'] = [v.payload for v in self.vehicles]
        
        # Pesi delle fermate
        data['demands'] = [0] + [s.total_weight for s in self.stops]  # depot ha demand 0
        
        # Time windows (in minuti dalla mezzanotte)
        # Format: [(earliest, latest)]
        tw_start = time_window['start']
        tw_end = time_window['end']
        
        time_windows = [(tw_start, tw_end)]  # depot
        
        for stop in self.stops:
            if stop.opening_windows:
                # Usa le finestre di carico della ceramica
                earliest = min(w['start'] for w in stop.opening_windows)
                latest = max(w['end'] for w in stop.opening_windows)
            else:
                # Usa la finestra generale
                earliest = tw_start
                latest = tw_end
            
            # Aggiusta per appuntamenti
            if stop.appointment_time:
                try:
                    h, m = map(int, stop.appointment_time.split(':'))
                    appt_time = h * 60 + m
                    # Finestra stretta intorno all'appuntamento (±30 min)
                    earliest = max(earliest, appt_time - 30)
                    latest = min(latest, appt_time + 30)
                except:
                    pass
            
            time_windows.append((earliest, latest))
        
        data['time_windows'] = time_windows
        
        # Service times (tempo di carico)
        data['service_times'] = [0] + [s.loading_time for s in self.stops]
        
        # Priorità
        data['priorities'] = [0] + [s.priority_score for s in self.stops]
        
        return data
    
    def solve(self, stops: List[Dict], vehicles: List[Dict], 
              time_window_name: str) -> Dict:
        """
        Risolve il VRP
        
        Args:
            stops: Lista di fermate
            vehicles: Lista di mezzi disponibili
            time_window_name: 'mattino' o 'pomeriggio'
        
        Returns:
            Dict con routes e unassigned
        """
        logger.info(f"Ottimizzazione per {time_window_name} con {len(stops)} fermate "
                   f"e {len(vehicles)} mezzi")
        
        # Converti dati in oggetti
        self.stops = [self._dict_to_stop(s) for s in stops]
        self.vehicles = [self._dict_to_vehicle(v) for v in vehicles]
        
        if not self.stops or not self.vehicles:
            return {'routes': [], 'unassigned': stops}
        
        # Filtra stops per ready_time
        if time_window_name == 'mattino':
            self.stops = [s for s in self.stops if s.ready_time != 'pomeriggio']
        
        if not self.stops:
            return {'routes': [], 'unassigned': []}
        
        # Time window
        time_windows = {
            'mattino': {'start': 6*60, 'end': 12*60},
            'pomeriggio': {'start': 14*60, 'end': 18*60}
        }
        tw = time_windows.get(time_window_name, time_windows['mattino'])
        
        # Costruisci matrici
        self.build_distance_matrix()
        
        # Crea modello dati
        data = self.create_data_model(tw)
        
        # Crea routing manager e model
        manager = pywrapcp.RoutingIndexManager(
            len(data['time_matrix']),
            data['num_vehicles'],
            data['depot']
        )
        routing = pywrapcp.RoutingModel(manager)
        
        # === DIMENSIONE PESO (Capacity) ===
        def demand_callback(from_index):
            from_node = manager.IndexToNode(from_index)
            return data['demands'][from_node]
        
        demand_callback_index = routing.RegisterUnaryTransitCallback(demand_callback)
        
        routing.AddDimensionWithVehicleCapacity(
            demand_callback_index,
            0,  # null capacity slack
            data['vehicle_capacities'],
            True,  # start cumul to zero
            'Capacity'
        )
        
        # === DIMENSIONE TEMPO (Semplificata) ===
        def time_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            travel_time = data['time_matrix'][from_node][to_node]
            service_time = data['service_times'][from_node]
            return travel_time + service_time
        
        time_callback_index = routing.RegisterTransitCallback(time_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(time_callback_index)
        
        # Aggiungi dimensione tempo senza vincoli rigidi
        time = 'Time'
        routing.AddDimension(
            time_callback_index,
            300,  # allow waiting time (5 hours - molto permissivo)
            tw['end'] - tw['start'] + 300,  # maximum time per vehicle
            False,  # Don't force start cumul to zero
            time
        )
        
        # === PENALITÀ PER NODI NON VISITATI ===
        penalty = 100000
        for node in range(1, len(data['time_matrix'])):
            routing.AddDisjunction([manager.NodeToIndex(node)], penalty)
        
        # === PARAMETRI DI RICERCA ===
        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
        )
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
        )
        search_parameters.time_limit.seconds = 30
        search_parameters.log_search = False
        
        # === RISOLVI ===
        solution = routing.SolveWithParameters(search_parameters)
        
        if not solution:
            logger.warning("Nessuna soluzione trovata")
            return {'routes': [], 'unassigned': stops}
        
        # === ESTRAI SOLUZIONE ===
        return self._extract_solution(data, manager, routing, solution)
    
    def _extract_solution(self, data, manager, routing, solution) -> Dict:
        """Estrae le routes dalla soluzione OR-Tools"""
        routes = []
        unassigned_indices = set()
        
        # Identifica nodi non assegnati
        for node in range(1, len(data['time_matrix'])):
            if solution.Value(routing.NextVar(manager.NodeToIndex(node))) == node:
                unassigned_indices.add(node - 1)  # -1 perché depot è 0
        
        # Estrai routes per ogni veicolo
        for vehicle_id in range(data['num_vehicles']):
            index = routing.Start(vehicle_id)
            route_stops = []
            route_weight = 0
            route_zones = set()
            
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                
                if node_index != 0:  # Non il depot
                    stop = self.stops[node_index - 1]
                    route_stops.append(stop)
                    route_weight += stop.total_weight
                    route_zones.add(stop.zone)
                
                index = solution.Value(routing.NextVar(index))
            
            if route_stops:
                # Verifica compatibilità zone
                stop_names = [s.name for s in route_stops]
                if not ZoneManager.are_zones_compatible(list(route_zones), stop_names):
                    logger.warning(f"Route del veicolo {vehicle_id} viola regole di zona")
                
                routes.append({
                    'vehicle': self._vehicle_to_dict(self.vehicles[vehicle_id]),
                    'stops': [self._stop_to_dict(s) for s in route_stops],
                    'totalWeight': route_weight,
                    'zones': list(route_zones)
                })
        
        # Stops non assegnati
        unassigned = [
            self._stop_to_dict(self.stops[i]) 
            for i in unassigned_indices
        ]
        
        logger.info(f"Soluzione: {len(routes)} routes, {len(unassigned)} non assegnati")
        
        return {
            'routes': routes,
            'unassigned': unassigned
        }
    
    def _dict_to_stop(self, d: Dict) -> Stop:
        """Converte dict in Stop object"""
        return Stop(
            key=d.get('key', ''),
            name=d.get('name', ''),
            coords=tuple(d['coords']) if d.get('coords') else None,
            total_weight=d.get('totalWeight', 0),
            orders=d.get('orders', []),
            loading_time=d.get('loadingTime', 15),
            zone=d.get('zone', ''),
            priority_score=d.get('priorityScore', 0),
            ready_time=d.get('readyTime', 'mattino'),
            appointment=d.get('appointment'),
            appointment_time=d.get('appointmentTime'),
            opening_windows=d.get('openingWindows', [])
        )
    
    def _dict_to_vehicle(self, d: Dict) -> Vehicle:
        """Converte dict in Vehicle object"""
        return Vehicle(
            id=str(d.get('id', '')),
            targa=d.get('targa', ''),
            autista=d.get('autista', ''),
            payload=d.get('payload', 0),
            rules=d.get('rules')
        )
    
    def _stop_to_dict(self, stop: Stop) -> Dict:
        """Converte Stop object in dict"""
        return {
            'key': stop.key,
            'name': stop.name,
            'coords': list(stop.coords) if stop.coords else None,
            'totalWeight': stop.total_weight,
            'orders': stop.orders,
            'loadingTime': stop.loading_time,
            'zone': stop.zone,
            'priorityScore': stop.priority_score,
            'readyTime': stop.ready_time,
            'appointment': stop.appointment,
            'appointmentTime': stop.appointment_time,
            'openingWindows': stop.opening_windows,
            'ceramicsDetail': {}  # Verrà popolato dal frontend
        }
    
    def _vehicle_to_dict(self, vehicle: Vehicle) -> Dict:
        """Converte Vehicle object in dict"""
        return {
            'id': vehicle.id,
            'targa': vehicle.targa,
            'autista': vehicle.autista,
            'payload': vehicle.payload,
            'rules': vehicle.rules
        }


def optimize_routes(data: Dict) -> Dict:
    """
    Funzione principale di ottimizzazione
    
    Args:
        data: {
            'stops': List[Dict],
            'morningVehicles': List[Dict],
            'afternoonVehicles': List[Dict],
            'timeWindows': List[str]  # ['mattino', 'pomeriggio']
        }
    
    Returns:
        {
            'morningRoutes': List[Dict],
            'afternoonRoutes': List[Dict],
            'unassigned': List[Dict]
        }
    """
    optimizer = RouteOptimizer()
    result = {
        'morningRoutes': [],
        'afternoonRoutes': [],
        'unassigned': []
    }
    
    stops = data.get('stops', [])
    time_windows = data.get('timeWindows', [])
    
    unassigned_stops = stops.copy()
    
    # Ottimizza mattino
    if 'mattino' in time_windows:
        morning_vehicles = data.get('morningVehicles', [])
        if morning_vehicles:
            morning_result = optimizer.solve(
                unassigned_stops, 
                morning_vehicles, 
                'mattino'
            )
            result['morningRoutes'] = morning_result['routes']
            
            # Rimuovi stops assegnati
            assigned_keys = {
                stop['key'] 
                for route in morning_result['routes'] 
                for stop in route['stops']
            }
            unassigned_stops = [
                s for s in unassigned_stops 
                if s['key'] not in assigned_keys
            ]
    
    # Ottimizza pomeriggio
    if 'pomeriggio' in time_windows:
        afternoon_vehicles = data.get('afternoonVehicles', [])
        if afternoon_vehicles:
            afternoon_result = optimizer.solve(
                unassigned_stops,
                afternoon_vehicles,
                'pomeriggio'
            )
            result['afternoonRoutes'] = afternoon_result['routes']
            
            # Rimuovi stops assegnati
            assigned_keys = {
                stop['key']
                for route in afternoon_result['routes']
                for stop in route['stops']
            }
            unassigned_stops = [
                s for s in unassigned_stops
                if s['key'] not in assigned_keys
            ]
    
    # Aggiungi motivo per non assegnati
    for stop in unassigned_stops:
        stop['reason'] = "Capacità insufficiente o vincoli non rispettabili"
    
    result['unassigned'] = unassigned_stops
    
    return result


if __name__ == '__main__':
    # Test di base
    print("Optimizer caricato correttamente")
    print("Usa l'API Flask per l'ottimizzazione")
