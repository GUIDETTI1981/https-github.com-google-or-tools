"""
Valhalla Client - Interface con Valhalla Routing Engine per camion

Questo modulo gestisce la comunicazione con il server Valhalla per ottenere
matrici di distanze e tempi di percorrenza per veicoli pesanti (truck)
con vincoli fisici: peso, altezza, larghezza, merci pericolose.
"""
import os
import math
import requests
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class TruckSpecs:
    """
    Specifiche fisiche del camion per routing Valhalla
    
    Attributes:
        weight: Peso totale in tonnellate (default: 21.77t = 48k lbs)
        height: Altezza in metri (default: 4.11m = 13.5 ft)
        width: Larghezza in metri (default: 2.6m = 8.5 ft)
        length: Lunghezza in metri (default: 21.64m = 71 ft)
        axle_load: Carico per asse in tonnellate (default: 9.07t = 20k lbs)
        axle_count: Numero di assi (default: 5)
        hazmat: Trasporta merci pericolose (default: False)
    """
    weight: float = 21.77  # tonnellate (max legal weight)
    height: float = 4.11   # metri (max height for bridges)
    width: float = 2.6     # metri (max width for roads)
    length: float = 21.64  # metri (max truck length)
    axle_load: float = 9.07  # tonnellate per asse
    axle_count: int = 5
    hazmat: bool = False


class ValhallaClientError(Exception):
    """Eccezione custom per errori Valhalla"""
    pass


class ValhallaClient:
    """
    Client per interfacciarsi con Valhalla Routing Engine
    
    Supporta routing per camion con vincoli fisici e restrizioni stradali.
    Utilizza l'API Matrix (sources_to_targets) di Valhalla.
    """
    
    def __init__(
        self, 
        host: str = None, 
        port: int = None,
        timeout: int = 60,
        costing: str = "truck"
    ):
        """
        Inizializza il client Valhalla
        
        Args:
            host: Hostname Valhalla server (default da env VALHALLA_HOST o 'localhost')
            port: Porta Valhalla server (default da env VALHALLA_PORT o 8002)
            timeout: Timeout richieste HTTP in secondi (default: 60s per camion)
            costing: Metodo di costing (truck, auto, pedestrian, bicycle)
        """
        self.host = host or os.getenv('VALHALLA_HOST', 'localhost')
        self.port = port or int(os.getenv('VALHALLA_PORT', 8002))
        self.timeout = timeout
        self.costing = costing
        self.base_url = f"http://{self.host}:{self.port}"
        
        logger.info(f"Valhalla Client initialized: {self.base_url} (costing: {costing})")
    
    def health_check(self) -> bool:
        """
        Verifica che Valhalla server sia raggiungibile
        
        Returns:
            True se Valhalla risponde, False altrimenti
        """
        try:
            response = requests.get(f"{self.base_url}/status", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Valhalla health check failed: {e}")
            return False
    
    def get_matrix(
        self, 
        coordinates: List[Tuple[float, float]],
        truck_specs: Optional[TruckSpecs] = None,
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Tuple[List[List[int]], List[List[int]]]:
        """
        Ottiene matrici di distanze e tempi da Valhalla Matrix API
        
        Args:
            coordinates: Lista di tuple (latitude, longitude)
            truck_specs: Specifiche del camion (peso, altezza, larghezza, hazmat)
            sources: Indici dei punti sorgente (None = tutti)
            destinations: Indici dei punti destinazione (None = tutti)
            
        Returns:
            Tuple di due matrici:
            - distance_matrix: Distanze in metri (int)
            - duration_matrix: Tempi in secondi (int)
            
        Raises:
            ValhallaClientError: Se Valhalla non risponde o ritorna errore
        """
        if not coordinates or len(coordinates) < 2:
            raise ValhallaClientError("Servono almeno 2 coordinate per calcolare una matrice")
        
        # Costruisci payload JSON per Valhalla
        payload = self._build_matrix_payload(coordinates, truck_specs, sources, destinations)
        
        logger.info(f"Valhalla Matrix request: {len(coordinates)} locations (truck routing)")
        if truck_specs:
            logger.info(f"  Truck specs: {truck_specs.weight}t, {truck_specs.height}m height, hazmat={truck_specs.hazmat}")
        
        # Endpoint: /sources_to_targets
        url = f"{self.base_url}/sources_to_targets"
        
        try:
            response = requests.post(
                url, 
                json=payload, 
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica presenza matrici
            if "sources_to_targets" not in data:
                raise ValhallaClientError("Valhalla response missing sources_to_targets data")
            
            # Estrai matrici
            matrices = data["sources_to_targets"]
            distance_matrix = self._extract_matrix(matrices, "distance")
            duration_matrix = self._extract_matrix(matrices, "time")
            
            logger.info(f"Valhalla matrix computed: {len(distance_matrix)}x{len(distance_matrix[0])}")
            
            return distance_matrix, duration_matrix
            
        except requests.exceptions.Timeout:
            raise ValhallaClientError(
                f"Valhalla timeout dopo {self.timeout} secondi. "
                "Il calcolo per camion può richiedere più tempo."
            )
        except requests.exceptions.ConnectionError:
            raise ValhallaClientError(
                f"Impossibile connettersi a Valhalla su {self.base_url}. "
                "Verifica che il container Valhalla sia in esecuzione."
            )
        except requests.exceptions.HTTPError as e:
            raise ValhallaClientError(f"Valhalla HTTP error: {e}")
        except Exception as e:
            raise ValhallaClientError(f"Errore generico Valhalla: {e}")
    
    def _build_matrix_payload(
        self,
        coordinates: List[Tuple[float, float]],
        truck_specs: Optional[TruckSpecs],
        sources: Optional[List[int]],
        destinations: Optional[List[int]]
    ) -> Dict:
        """
        Costruisce il payload JSON per la richiesta Valhalla Matrix
        
        Args:
            coordinates: Lista coordinate (lat, lon)
            truck_specs: Specifiche camion
            sources: Indici sorgenti
            destinations: Indici destinazioni
            
        Returns:
            Dizionario payload per Valhalla API
        """
        # Converti coordinate in formato Valhalla: [{"lat": x, "lon": y}]
        locations = [{"lat": lat, "lon": lon} for lat, lon in coordinates]
        
        # Costruisci costing_options per truck
        costing_options = {}
        
        if self.costing == "truck" and truck_specs:
            costing_options["truck"] = {
                # Peso e dimensioni
                "weight": truck_specs.weight,        # tonnellate
                "height": truck_specs.height,        # metri
                "width": truck_specs.width,          # metri
                "length": truck_specs.length,        # metri
                "axle_load": truck_specs.axle_load,  # tonnellate per asse
                "axle_count": truck_specs.axle_count,
                
                # Merci pericolose
                "hazmat": truck_specs.hazmat,
                
                # Altri parametri utili
                "use_highways": 1.0,      # Preferenza autostrade (0.0-1.0)
                "use_tolls": 1.0,         # Accetta pedaggi (0.0-1.0)
                "use_tracks": 0.0,        # Evita strade non asfaltate
                
                # Velocità e costi
                "top_speed": 90.0,        # km/h max (tipico per camion)
                "fixed_speed": 0.0,       # 0 = usa velocità strada
            }
        elif self.costing == "auto":
            costing_options["auto"] = {
                "use_highways": 1.0,
                "use_tolls": 1.0,
            }
        
        # Costruisci payload completo
        payload = {
            "sources": locations if sources is None else [locations[i] for i in sources],
            "targets": locations if destinations is None else [locations[i] for i in destinations],
            "costing": self.costing,
            "costing_options": costing_options,
            # Unità metriche
            "units": "kilometers",
            # Matrici richieste
            "verbose": False,
        }
        
        # Se non specificato, sources/targets sono tutti i punti
        if sources is None and destinations is None:
            payload = {
                "sources": locations,
                "targets": locations,
                "costing": self.costing,
                "costing_options": costing_options,
                "units": "kilometers",
            }
        
        return payload
    
    def _extract_matrix(self, matrices: List[List[Dict]], metric: str) -> List[List[int]]:
        """
        Estrae matrice di distanze o tempi dalla risposta Valhalla
        
        Args:
            matrices: Array 2D dalla risposta Valhalla
            metric: "distance" (km) o "time" (secondi)
            
        Returns:
            Matrice di interi (metri o secondi)
        """
        result = []
        
        for row in matrices:
            result_row = []
            for cell in row:
                if metric == "distance":
                    # Valhalla ritorna km, converti in metri
                    value_km = cell.get("distance", None)
                    if value_km is None:
                        # Percorso impossibile
                        result_row.append(999999999)
                    else:
                        # Converti km → metri e arrotonda per eccesso
                        result_row.append(math.ceil(value_km * 1000))
                elif metric == "time":
                    # Valhalla ritorna secondi
                    value_sec = cell.get("time", None)
                    if value_sec is None:
                        result_row.append(999999999)
                    else:
                        result_row.append(math.ceil(value_sec))
            result.append(result_row)
        
        return result
    
    def get_route(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float],
        truck_specs: Optional[TruckSpecs] = None
    ) -> Dict:
        """
        Ottiene un singolo percorso tra due punti per camion
        
        Args:
            start: Coordinate partenza (lat, lon)
            end: Coordinate arrivo (lat, lon)
            truck_specs: Specifiche del camion
            
        Returns:
            Dizionario con distance (metri), duration (secondi), geometry
            
        Raises:
            ValhallaClientError: Se Valhalla non risponde o ritorna errore
        """
        payload = {
            "locations": [
                {"lat": start[0], "lon": start[1]},
                {"lat": end[0], "lon": end[1]}
            ],
            "costing": self.costing,
            "units": "kilometers"
        }
        
        # Aggiungi truck specs se presenti
        if truck_specs and self.costing == "truck":
            payload["costing_options"] = {
                "truck": {
                    "weight": truck_specs.weight,
                    "height": truck_specs.height,
                    "width": truck_specs.width,
                    "hazmat": truck_specs.hazmat
                }
            }
        
        url = f"{self.base_url}/route"
        
        try:
            response = requests.post(url, json=payload, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if "trip" not in data or "legs" not in data["trip"]:
                raise ValhallaClientError("Valhalla route response invalid")
            
            leg = data["trip"]["legs"][0]
            summary = leg["summary"]
            
            return {
                "distance": int(summary["length"] * 1000),  # km → metri
                "duration": int(summary["time"]),  # secondi
                "geometry": leg.get("shape", "")  # Encoded polyline
            }
            
        except Exception as e:
            raise ValhallaClientError(f"Error getting route: {e}")
    
    def get_info(self) -> Dict:
        """
        Ottiene informazioni sul server Valhalla
        
        Returns:
            Dizionario con info sul server
        """
        return {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "costing": self.costing,
            "timeout": self.timeout,
            "is_available": self.health_check(),
            "supports_truck": True,
            "supports_hazmat": True
        }


# Singleton instance (opzionale)
_valhalla_client_instance: Optional[ValhallaClient] = None


def get_valhalla_client(truck_specs: Optional[TruckSpecs] = None) -> ValhallaClient:
    """
    Factory function per ottenere un'istanza singleton del client Valhalla
    
    Args:
        truck_specs: Specifiche camion (per logging)
        
    Returns:
        ValhallaClient instance
    """
    global _valhalla_client_instance
    
    if _valhalla_client_instance is None:
        _valhalla_client_instance = ValhallaClient(costing="truck")
    
    return _valhalla_client_instance
