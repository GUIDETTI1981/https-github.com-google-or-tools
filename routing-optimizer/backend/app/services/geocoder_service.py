"""
Geocoder Service - Client per Photon (OSM-based geocoding)

Questo modulo fornisce un'interfaccia per convertire indirizzi testuali
in coordinate geografiche (lat/lon) usando Photon geocoder.

Update 2025-12-17: Integrazione Redis cache per performance ottimali

Autore: Senior Data Engineer & GIS Python Developer
Data: 2025-12-17
"""

import os
import math
import requests
import logging
from typing import Optional, Tuple, Dict, List
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class GeocoderType(Enum):
    """Tipo di geocoder supportato"""
    PHOTON = "photon"
    NOMINATIM = "nominatim"


@dataclass
class GeocodingResult:
    """
    Risultato di una richiesta di geocoding
    """
    latitude: float
    longitude: float
    confidence: float = 0.0  # 0.0-1.0
    address: str = ""
    city: str = ""
    country: str = ""
    osm_type: str = ""  # node, way, relation
    osm_id: int = 0
    extent: Optional[List[float]] = None  # [min_lon, min_lat, max_lon, max_lat]
    
    def to_tuple(self) -> Tuple[float, float]:
        """Ritorna coordinate come tupla (lat, lon)"""
        return (self.latitude, self.longitude)
    
    def to_dict(self) -> Dict:
        """Ritorna risultato come dizionario"""
        return {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "confidence": self.confidence,
            "address": self.address,
            "city": self.city,
            "country": self.country,
            "osm_type": self.osm_type,
            "osm_id": self.osm_id,
            "extent": self.extent
        }


class GeocoderError(Exception):
    """Eccezione custom per errori di geocoding"""
    pass


class GeocoderService:
    """
    Client per Photon Geocoder (OpenStreetMap-based)
    
    Features:
    - Conversione indirizzo → coordinate (geocoding)
    - Bias geografico per priorità regionale
    - Gestione errori e timeout
    - Supporto lingua italiana
    - Caching opzionale (TODO)
    """
    
    # Coordinate di bias per città italiane principali
    CITY_BIASES = {
        "roma": (41.9028, 12.4964),
        "milano": (45.4642, 9.1900),
        "napoli": (40.8518, 14.2681),
        "torino": (45.0703, 7.6869),
        "firenze": (43.7696, 11.2558),
        "bologna": (44.4949, 11.3426),
        "venezia": (45.4408, 12.3155),
        "genova": (44.4056, 8.9463),
        "palermo": (38.1157, 13.3615),
        "bari": (41.1171, 16.8719)
    }
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        timeout: int = 10,
        default_bias: Tuple[float, float] = None,
        language: str = "it"
    ):
        """
        Inizializza il Geocoder Service
        
        Args:
            host: Hostname Photon server (default da env PHOTON_HOST o 'localhost')
            port: Porta Photon server (default da env PHOTON_PORT o 2322)
            timeout: Timeout richieste HTTP in secondi (default: 10s)
            default_bias: Coordinate di bias default (lat, lon) per priorità geografica
            language: Lingua preferita per i risultati (default: 'it')
        """
        self.host = host or os.getenv('PHOTON_HOST', 'localhost')
        self.port = port or int(os.getenv('PHOTON_PORT', 2322))
        self.timeout = timeout
        self.language = language
        self.base_url = f"http://{self.host}:{self.port}"
        
        # Bias geografico default (centro Italia)
        self.default_bias = default_bias or self.CITY_BIASES.get("roma")
        
        logger.info(f"GeocoderService initialized: {self.base_url} (lang: {language})")
        if self.default_bias:
            logger.info(f"  Default bias: {self.default_bias}")
    
    def health_check(self) -> bool:
        """
        Verifica che Photon server sia raggiungibile
        
        Returns:
            True se Photon risponde, False altrimenti
        """
        try:
            # Test query semplice
            response = requests.get(
                f"{self.base_url}/api",
                params={"q": "Roma"},
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Photon health check failed: {e}")
            return False
    
    def geocode(
        self,
        address: str,
        limit: int = 1,
        bias: Optional[Tuple[float, float]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None,
        use_cache: bool = True
    ) -> Optional[GeocodingResult]:
        """
        Converte un indirizzo in coordinate geografiche
        
        Con cache Redis integrata:
        1. Check cache (se abilitata)
        2. Se CACHE HIT → return cached result
        3. Se CACHE MISS → query Photon → cache result → return
        
        Args:
            address: Indirizzo da geocodificare
            limit: Numero massimo di risultati (default: 1, prende il migliore)
            bias: Coordinate di bias (lat, lon) per priorità geografica
            bbox: Bounding box (min_lon, min_lat, max_lon, max_lat) per limitare l'area
            use_cache: Usa cache per questa richiesta (default: True)
            
        Returns:
            GeocodingResult con coordinate e metadata, None se non trovato
            
        Raises:
            GeocoderError: Se Photon non risponde o ritorna errore
            
        Example:
            >>> geocoder = GeocoderService()
            >>> result = geocoder.geocode("Via Roma 1, Milano")
            >>> result.to_tuple()
            (45.4642, 9.1900)
        """
        if not address or not isinstance(address, str) or len(address.strip()) < 3:
            logger.warning(f"Invalid address for geocoding: '{address}'")
            return None
        
        # Cache-aside pattern (se abilitata)
        if use_cache and self.cache and self.cache.enabled:
            return self.cache.get_or_fetch(
                address,
                lambda: self._geocode_from_photon(address, limit, bias, bbox)
            )
        else:
            # No cache, direct Photon query
            return self._geocode_from_photon(address, limit, bias, bbox)
    
    def _geocode_from_photon(
        self,
        address: str,
        limit: int = 1,
        bias: Optional[Tuple[float, float]] = None,
        bbox: Optional[Tuple[float, float, float, float]] = None
    ) -> Optional[GeocodingResult]:
        """
        Geocoding diretto da Photon (senza cache)
        
        Metodo interno chiamato dal cache manager o direttamente
        se cache disabilitata.
        """
        
        # Usa bias default se non specificato
        if bias is None and self.default_bias:
            bias = self.default_bias
        
        # Costruisci parametri query
        params = {
            "q": address.strip(),
            "limit": limit,
            "lang": self.language
        }
        
        # Aggiungi bias geografico
        if bias:
            params["lat"] = bias[0]
            params["lon"] = bias[1]
        
        # Aggiungi bounding box
        if bbox:
            params["bbox"] = f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}"
        
        logger.info(f"🔍 Geocoding (Photon): '{address}' (limit={limit}, bias={bias})")
        
        try:
            response = requests.get(
                f"{self.base_url}/api",
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            
            # Verifica presenza risultati
            if "features" not in data or len(data["features"]) == 0:
                logger.warning(f"No geocoding results for: '{address}'")
                return None
            
            # Prendi il primo risultato (il migliore)
            feature = data["features"][0]
            result = self._parse_photon_feature(feature)
            
            logger.info(f"✅ Geocoded: '{address}' → ({result.latitude:.6f}, {result.longitude:.6f})")
            
            return result
            
        except requests.exceptions.Timeout:
            raise GeocoderError(
                f"Photon timeout dopo {self.timeout} secondi per indirizzo: '{address}'"
            )
        except requests.exceptions.ConnectionError:
            raise GeocoderError(
                f"Impossibile connettersi a Photon su {self.base_url}. "
                "Verifica che il container Photon sia in esecuzione."
            )
        except requests.exceptions.HTTPError as e:
            raise GeocoderError(f"Photon HTTP error: {e}")
        except Exception as e:
            raise GeocoderError(f"Errore generico Photon per '{address}': {e}")
    
    def geocode_batch(
        self,
        addresses: List[str],
        bias: Optional[Tuple[float, float]] = None
    ) -> List[Optional[GeocodingResult]]:
        """
        Geocodifica un batch di indirizzi
        
        Args:
            addresses: Lista di indirizzi da geocodificare
            bias: Coordinate di bias per tutti gli indirizzi
            
        Returns:
            Lista di GeocodingResult (None per indirizzi non trovati)
        """
        results = []
        
        for i, address in enumerate(addresses):
            try:
                result = self.geocode(address, bias=bias)
                results.append(result)
                
                # Log progresso ogni 10 indirizzi
                if (i + 1) % 10 == 0:
                    logger.info(f"Geocoding progress: {i+1}/{len(addresses)}")
                
            except GeocoderError as e:
                logger.error(f"Geocoding failed for '{address}': {e}")
                results.append(None)
        
        # Statistiche
        success_count = sum(1 for r in results if r is not None)
        logger.info(f"Batch geocoding complete: {success_count}/{len(addresses)} successful")
        
        return results
    
    def _parse_photon_feature(self, feature: Dict) -> GeocodingResult:
        """
        Parse un feature GeoJSON da Photon in GeocodingResult
        
        Args:
            feature: Feature GeoJSON da Photon
            
        Returns:
            GeocodingResult parsed
        """
        # Estrai coordinate (Photon usa [lon, lat])
        coords = feature["geometry"]["coordinates"]
        lon, lat = coords[0], coords[1]
        
        # Estrai properties
        props = feature.get("properties", {})
        
        # Calcola confidence basata su osm_type
        # way e relation sono più affidabili di node
        osm_type = props.get("osm_type", "")
        confidence = 0.9 if osm_type in ["way", "relation"] else 0.7
        
        # Estrai extent (bounding box)
        extent = props.get("extent", None)
        
        # Costruisci address display
        address_parts = []
        if props.get("name"):
            address_parts.append(props["name"])
        if props.get("street"):
            address_parts.append(props["street"])
        if props.get("housenumber"):
            address_parts.append(props["housenumber"])
        
        address_display = ", ".join(filter(None, address_parts))
        
        return GeocodingResult(
            latitude=lat,
            longitude=lon,
            confidence=confidence,
            address=address_display or props.get("name", ""),
            city=props.get("city", ""),
            country=props.get("country", ""),
            osm_type=osm_type,
            osm_id=props.get("osm_id", 0),
            extent=extent
        )
    
    def reverse_geocode(
        self,
        latitude: float,
        longitude: float,
        limit: int = 1
    ) -> Optional[GeocodingResult]:
        """
        Reverse geocoding: coordinate → indirizzo
        
        Args:
            latitude: Latitudine
            longitude: Longitudine
            limit: Numero massimo di risultati
            
        Returns:
            GeocodingResult con indirizzo, None se non trovato
        """
        params = {
            "lat": latitude,
            "lon": longitude,
            "limit": limit,
            "lang": self.language
        }
        
        logger.info(f"Reverse geocoding: ({latitude:.6f}, {longitude:.6f})")
        
        try:
            response = requests.get(
                f"{self.base_url}/reverse",
                params=params,
                timeout=self.timeout,
                headers={'Accept': 'application/json'}
            )
            response.raise_for_status()
            
            data = response.json()
            
            if "features" not in data or len(data["features"]) == 0:
                logger.warning(f"No reverse geocoding results for: ({latitude}, {longitude})")
                return None
            
            feature = data["features"][0]
            result = self._parse_photon_feature(feature)
            
            logger.info(f"Reverse geocoded: ({latitude:.6f}, {longitude:.6f}) → '{result.address}'")
            
            return result
            
        except Exception as e:
            logger.error(f"Reverse geocoding failed: {e}")
            return None
    
    def set_bias_by_city(self, city: str) -> bool:
        """
        Imposta bias geografico basato su nome città
        
        Args:
            city: Nome città (es. "roma", "milano")
            
        Returns:
            True se città trovata, False altrimenti
        """
        city_lower = city.lower()
        
        if city_lower in self.CITY_BIASES:
            self.default_bias = self.CITY_BIASES[city_lower]
            logger.info(f"Bias set to {city}: {self.default_bias}")
            return True
        else:
            logger.warning(f"City '{city}' not found in bias database")
            return False
    
    def calculate_distance(
        self,
        coord1: Tuple[float, float],
        coord2: Tuple[float, float]
    ) -> float:
        """
        Calcola distanza Haversine tra due coordinate
        
        Args:
            coord1: Prima coordinata (lat, lon)
            coord2: Seconda coordinata (lat, lon)
            
        Returns:
            Distanza in metri
        """
        R = 6371000  # Raggio Terra in metri
        
        lat1, lon1 = math.radians(coord1[0]), math.radians(coord1[1])
        lat2, lon2 = math.radians(coord2[0]), math.radians(coord2[1])
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        
        a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance = R * c
        
        return distance
    
    def get_info(self) -> Dict:
        """
        Ottiene informazioni sul geocoder
        
        Returns:
            Dict con configurazione e statistiche
        """
        return {
            "host": self.host,
            "port": self.port,
            "base_url": self.base_url,
            "timeout": self.timeout,
            "language": self.language,
            "default_bias": self.default_bias,
            "is_available": self.health_check(),
            "supported_cities": list(self.CITY_BIASES.keys()),
            "features": [
                "Address to coordinates (geocoding)",
                "Coordinates to address (reverse geocoding)",
                "Geographic bias for regional priority",
                "Batch geocoding",
                "Italian language support",
                "OSM-based data"
            ]
        }


# Singleton instance (opzionale)
_geocoder_service_instance: Optional[GeocoderService] = None


def get_geocoder_service() -> GeocoderService:
    """
    Factory function per ottenere un'istanza singleton del geocoder
    
    Returns:
        GeocoderService instance
    """
    global _geocoder_service_instance
    
    if _geocoder_service_instance is None:
        _geocoder_service_instance = GeocoderService()
    
    return _geocoder_service_instance
