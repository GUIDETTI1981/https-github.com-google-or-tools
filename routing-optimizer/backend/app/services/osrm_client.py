"""
OSRM Client - Interface con OSRM Backend per distanze e tempi reali

Questo modulo gestisce la comunicazione con il server OSRM per ottenere
matrici di distanze e tempi di percorrenza stradali reali.
"""
import os
import math
import requests
from typing import List, Tuple, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OSRMClientError(Exception):
    """Eccezione custom per errori OSRM"""
    pass


class OSRMClient:
    """
    Client per interfacciarsi con OSRM (Open Source Routing Machine)
    
    Utilizza l'API Table di OSRM per calcolare matrici di distanze e tempi
    tra multipli punti geografici.
    """
    
    def __init__(
        self, 
        host: str = None, 
        port: int = None,
        timeout: int = 30,
        profile: str = "driving"
    ):
        """
        Inizializza il client OSRM
        
        Args:
            host: Hostname OSRM server (default da env OSRM_HOST o 'localhost')
            port: Porta OSRM server (default da env OSRM_PORT o 5000)
            timeout: Timeout richieste HTTP in secondi
            profile: Profilo routing (driving, walking, cycling)
        """
        self.host = host or os.getenv('OSRM_HOST', 'localhost')
        self.port = port or int(os.getenv('OSRM_PORT', 5000))
        self.timeout = timeout
        self.profile = profile
        self.base_url = f"http://{self.host}:{self.port}"
        
        logger.info(f"OSRM Client initialized: {self.base_url}")
    
    def health_check(self) -> bool:
        """
        Verifica che OSRM server sia raggiungibile
        
        Returns:
            True se OSRM risponde, False altrimenti
        """
        try:
            # OSRM non ha un endpoint /health standard, 
            # ma possiamo testare con una query minima
            test_url = f"{self.base_url}/route/v1/{self.profile}/13.388860,52.517037;13.397634,52.529407"
            response = requests.get(test_url, timeout=5, params={"overview": "false"})
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OSRM health check failed: {e}")
            return False
    
    def get_matrix(
        self, 
        coordinates: List[Tuple[float, float]],
        sources: Optional[List[int]] = None,
        destinations: Optional[List[int]] = None
    ) -> Tuple[List[List[int]], List[List[int]]]:
        """
        Ottiene matrici di distanze e tempi da OSRM Table API
        
        Args:
            coordinates: Lista di tuple (latitude, longitude)
            sources: Indici dei punti sorgente (None = tutti)
            destinations: Indici dei punti destinazione (None = tutti)
            
        Returns:
            Tuple di due matrici:
            - distance_matrix: Distanze in metri (int)
            - duration_matrix: Tempi in secondi (int)
            
        Raises:
            OSRMClientError: Se OSRM non risponde o ritorna errore
        """
        if not coordinates or len(coordinates) < 2:
            raise OSRMClientError("Servono almeno 2 coordinate per calcolare una matrice")
        
        # Converti coordinate in formato OSRM: "lon,lat;lon,lat;..."
        # ATTENZIONE: OSRM usa (longitude, latitude) non (lat, lon)!
        coords_str = ";".join([f"{lon},{lat}" for lat, lon in coordinates])
        
        # Costruisci URL
        url = f"{self.base_url}/table/v1/{self.profile}/{coords_str}"
        
        # Parametri query
        params = {
            "annotations": "distance,duration",  # Richiedi entrambe le metriche
            "generate_hints": "false"  # Non generare hints per performance
        }
        
        # Aggiungi sources/destinations se specificati
        if sources is not None:
            params["sources"] = ";".join(map(str, sources))
        if destinations is not None:
            params["destinations"] = ";".join(map(str, destinations))
        
        logger.info(f"OSRM Table request: {len(coordinates)} locations")
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica codice risposta OSRM
            if data.get("code") != "Ok":
                error_msg = data.get("message", "Unknown OSRM error")
                raise OSRMClientError(f"OSRM returned error: {error_msg}")
            
            # Estrai matrici
            distances_raw = data.get("distances", [])
            durations_raw = data.get("durations", [])
            
            if not distances_raw or not durations_raw:
                raise OSRMClientError("OSRM response missing distance or duration data")
            
            # Converti in int e gestisci valori null (percorsi impossibili)
            distance_matrix = self._convert_matrix_to_int(distances_raw)
            duration_matrix = self._convert_matrix_to_int(durations_raw)
            
            logger.info(f"OSRM matrix computed: {len(distance_matrix)}x{len(distance_matrix[0])}")
            
            return distance_matrix, duration_matrix
            
        except requests.exceptions.Timeout:
            raise OSRMClientError(
                f"OSRM timeout dopo {self.timeout} secondi. "
                "Il server potrebbe essere sovraccarico o non raggiungibile."
            )
        except requests.exceptions.ConnectionError:
            raise OSRMClientError(
                f"Impossibile connettersi a OSRM su {self.base_url}. "
                "Verifica che il container OSRM sia in esecuzione."
            )
        except requests.exceptions.HTTPError as e:
            raise OSRMClientError(f"OSRM HTTP error: {e}")
        except Exception as e:
            raise OSRMClientError(f"Errore generico OSRM: {e}")
    
    def _convert_matrix_to_int(self, matrix: List[List[float]]) -> List[List[int]]:
        """
        Converte matrice di float in int, arrotondando per eccesso
        
        OR-Tools richiede valori interi. Arrotondiamo per eccesso per evitare
        sottostime nelle distanze/tempi.
        
        Args:
            matrix: Matrice di float (può contenere None per percorsi impossibili)
            
        Returns:
            Matrice di int
        """
        int_matrix = []
        for row in matrix:
            int_row = []
            for value in row:
                if value is None:
                    # Percorso impossibile: usa un valore molto alto
                    # ma non infinito (OR-Tools potrebbe avere problemi)
                    int_row.append(999999999)
                else:
                    # Arrotonda per eccesso
                    int_row.append(math.ceil(value))
            int_matrix.append(int_row)
        return int_matrix
    
    def get_route(
        self, 
        start: Tuple[float, float], 
        end: Tuple[float, float]
    ) -> Dict:
        """
        Ottiene un singolo percorso tra due punti
        
        Args:
            start: Coordinate partenza (lat, lon)
            end: Coordinate arrivo (lat, lon)
            
        Returns:
            Dizionario con distance (metri), duration (secondi), geometry
            
        Raises:
            OSRMClientError: Se OSRM non risponde o ritorna errore
        """
        # Converti in formato OSRM (lon, lat)
        start_lon, start_lat = start[1], start[0]
        end_lon, end_lat = end[1], end[0]
        
        url = f"{self.base_url}/route/v1/{self.profile}/{start_lon},{start_lat};{end_lon},{end_lat}"
        
        params = {
            "overview": "full",
            "geometries": "geojson"
        }
        
        try:
            response = requests.get(url, params=params, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            
            if data.get("code") != "Ok":
                error_msg = data.get("message", "Unknown OSRM error")
                raise OSRMClientError(f"OSRM route error: {error_msg}")
            
            route = data["routes"][0]
            
            return {
                "distance": int(route["distance"]),  # metri
                "duration": int(route["duration"]),  # secondi
                "geometry": route["geometry"]  # GeoJSON LineString
            }
            
        except Exception as e:
            raise OSRMClientError(f"Error getting route: {e}")
    
    def get_info(self) -> Dict:
        """
        Ottiene informazioni sul server OSRM
        
        Returns:
            Dizionario con info sul server
        """
        return {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "profile": self.profile,
            "timeout": self.timeout,
            "is_available": self.health_check()
        }


# Singleton instance (opzionale, per riutilizzo)
_osrm_client_instance: Optional[OSRMClient] = None


def get_osrm_client() -> OSRMClient:
    """
    Factory function per ottenere un'istanza singleton del client OSRM
    
    Returns:
        OSRMClient instance
    """
    global _osrm_client_instance
    
    if _osrm_client_instance is None:
        _osrm_client_instance = OSRMClient()
    
    return _osrm_client_instance
