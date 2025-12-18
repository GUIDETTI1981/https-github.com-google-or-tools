"""
Geocode Cache Manager - Redis-based persistent caching for geocoding results

Questo modulo fornisce un layer di caching persistente per ridurre drasticamente
le chiamate a Photon, usando Redis come storage backend.

Pattern: Cache-Aside (Lazy Loading)
TTL: 30 giorni (le coordinate di indirizzi fisici raramente cambiano)

Autore: Senior Backend Engineer
Data: 2025-12-17
"""

import os
import hashlib
import json
import logging
from typing import Optional, Tuple, Dict
from dataclasses import asdict

try:
    import redis
    from redis.exceptions import ConnectionError, TimeoutError, RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("redis-py not installed. Cache will be disabled.")

from .geocoder_service import GeocodingResult

logger = logging.getLogger(__name__)


class GeocodeCache:
    """
    Cache manager per risultati di geocoding usando Redis
    
    Features:
    - Pattern Cache-Aside (check cache → miss → fetch → set cache)
    - Key hashing (MD5) per evitare problemi con caratteri speciali
    - Serializzazione JSON per storage
    - TTL configurabile (default: 30 giorni)
    - Fail-open: se Redis è giù, passa attraverso senza crashare
    - Statistics tracking (hits, misses, errors)
    
    Architecture:
    ┌─────────────────────────────────────────────────────────┐
    │  1. Input: cleaned_address = "Via Roma 1, Milano"      │
    └────────────────────┬────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  2. Generate key: md5("via roma 1, milano")            │
    │     → "a3f5e8d2c1b4..."                                │
    └────────────────────┬────────────────────────────────────┘
                         │
                         ▼
    ┌─────────────────────────────────────────────────────────┐
    │  3. Check Redis: GET "geocode:a3f5e8d2c1b4..."         │
    └────────────────────┬────────────────────────────────────┘
                         │
          ┌──────────────┴──────────────┐
          │                             │
          ▼ CACHE HIT                   ▼ CACHE MISS
    ┌─────────────┐            ┌────────────────────┐
    │  Deserialize│            │  4. Call Photon    │
    │  JSON       │            │     Geocoder       │
    │  → Return   │            └────────┬───────────┘
    └─────────────┘                     │
                                        ▼
                              ┌────────────────────┐
                              │  5. Set Redis:     │
                              │  SET key value     │
                              │  EXPIRE key TTL    │
                              └────────┬───────────┘
                                       │
                                       ▼
                              ┌────────────────────┐
                              │  Return result     │
                              └────────────────────┘
    """
    
    # Prefisso per chiavi Redis
    KEY_PREFIX = "geocode:"
    
    # TTL default: 30 giorni (in secondi)
    DEFAULT_TTL = 30 * 24 * 60 * 60  # 2,592,000 secondi
    
    def __init__(
        self,
        host: str = None,
        port: int = None,
        ttl: int = None,
        enabled: bool = True
    ):
        """
        Inizializza il cache manager
        
        Args:
            host: Redis host (default da env REDIS_HOST o 'localhost')
            port: Redis port (default da env REDIS_PORT o 6379)
            ttl: Time-to-live in secondi (default: 30 giorni)
            enabled: Abilita/disabilita cache (default: True)
        """
        self.enabled = enabled and REDIS_AVAILABLE
        self.host = host or os.getenv('REDIS_HOST', 'localhost')
        self.port = port or int(os.getenv('REDIS_PORT', 6379))
        self.ttl = ttl or int(os.getenv('REDIS_CACHE_TTL', self.DEFAULT_TTL))
        
        # Statistics
        self.stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'errors': 0
        }
        
        # Redis client
        self.redis_client = None
        
        if self.enabled:
            try:
                self.redis_client = redis.Redis(
                    host=self.host,
                    port=self.port,
                    db=0,
                    decode_responses=True,  # Auto-decode bytes to strings
                    socket_connect_timeout=2,
                    socket_timeout=2
                )
                
                # Test connection
                self.redis_client.ping()
                
                logger.info(f"GeocodeCache initialized: {self.host}:{self.port} (TTL: {self.ttl}s)")
                logger.info(f"  Cache enabled: {self.enabled}")
                
            except (ConnectionError, TimeoutError) as e:
                logger.warning(f"Redis connection failed: {e}. Cache will be disabled (fail-open mode).")
                self.enabled = False
                self.redis_client = None
            except Exception as e:
                logger.error(f"Redis initialization error: {e}. Cache disabled.")
                self.enabled = False
                self.redis_client = None
        else:
            logger.info("GeocodeCache disabled (redis-py not available or enabled=False)")
    
    def _generate_cache_key(self, address: str) -> str:
        """
        Genera chiave univoca per Redis usando MD5 hash
        
        Motivi per usare hash:
        - Evita problemi con caratteri speciali nelle chiavi Redis
        - Lunghezza fissa (32 caratteri)
        - Distribuzione uniforme
        
        Args:
            address: Indirizzo pulito (lowercase normalizzato)
            
        Returns:
            Chiave Redis: "geocode:a3f5e8d2c1b4..."
        """
        # Normalizza: lowercase + strip
        normalized = address.lower().strip()
        
        # MD5 hash
        hash_obj = hashlib.md5(normalized.encode('utf-8'))
        hash_hex = hash_obj.hexdigest()
        
        # Aggiungi prefisso
        key = f"{self.KEY_PREFIX}{hash_hex}"
        
        logger.debug(f"Cache key generated: '{address}' → '{key}'")
        
        return key
    
    def get(self, address: str) -> Optional[GeocodingResult]:
        """
        Recupera risultato di geocoding dalla cache
        
        Args:
            address: Indirizzo pulito da cercare
            
        Returns:
            GeocodingResult se trovato in cache, None altrimenti
        """
        if not self.enabled or not self.redis_client:
            return None
        
        try:
            # Genera chiave
            key = self._generate_cache_key(address)
            
            # GET da Redis
            cached_value = self.redis_client.get(key)
            
            if cached_value:
                # CACHE HIT
                self.stats['hits'] += 1
                
                # Deserializza JSON
                data = json.loads(cached_value)
                
                # Ricostruisci GeocodingResult
                result = GeocodingResult(
                    latitude=data['latitude'],
                    longitude=data['longitude'],
                    confidence=data.get('confidence', 0.0),
                    address=data.get('address', ''),
                    city=data.get('city', ''),
                    country=data.get('country', ''),
                    osm_type=data.get('osm_type', ''),
                    osm_id=data.get('osm_id', 0),
                    extent=data.get('extent')
                )
                
                logger.info(f"🎯 CACHE HIT: '{address}' → ({result.latitude:.6f}, {result.longitude:.6f})")
                
                return result
            else:
                # CACHE MISS
                self.stats['misses'] += 1
                logger.debug(f"❌ CACHE MISS: '{address}'")
                return None
                
        except (ConnectionError, TimeoutError) as e:
            # Redis connection error → fail-open
            logger.warning(f"Redis GET error: {e}. Bypassing cache (fail-open).")
            self.stats['errors'] += 1
            return None
        except json.JSONDecodeError as e:
            # JSON parsing error
            logger.error(f"Cache JSON decode error for '{address}': {e}")
            self.stats['errors'] += 1
            return None
        except Exception as e:
            # Generic error → fail-open
            logger.error(f"Cache GET error for '{address}': {e}")
            self.stats['errors'] += 1
            return None
    
    def set(self, address: str, result: GeocodingResult) -> bool:
        """
        Salva risultato di geocoding in cache
        
        Args:
            address: Indirizzo pulito
            result: GeocodingResult da cachare
            
        Returns:
            True se salvato con successo, False altrimenti
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            # Genera chiave
            key = self._generate_cache_key(address)
            
            # Serializza a JSON
            data = {
                'latitude': result.latitude,
                'longitude': result.longitude,
                'confidence': result.confidence,
                'address': result.address,
                'city': result.city,
                'country': result.country,
                'osm_type': result.osm_type,
                'osm_id': result.osm_id,
                'extent': result.extent
            }
            
            json_value = json.dumps(data)
            
            # SET in Redis con TTL
            self.redis_client.setex(
                key,
                self.ttl,
                json_value
            )
            
            self.stats['sets'] += 1
            
            logger.info(f"💾 CACHE SET: '{address}' → stored with TTL {self.ttl}s")
            
            return True
            
        except (ConnectionError, TimeoutError) as e:
            # Redis connection error → fail-open (don't crash)
            logger.warning(f"Redis SET error: {e}. Cache write skipped (fail-open).")
            self.stats['errors'] += 1
            return False
        except Exception as e:
            # Generic error → fail-open
            logger.error(f"Cache SET error for '{address}': {e}")
            self.stats['errors'] += 1
            return False
    
    def get_or_fetch(
        self,
        address: str,
        fetch_func: callable
    ) -> Optional[GeocodingResult]:
        """
        Pattern Cache-Aside completo
        
        1. Controlla cache
        2. Se HIT → ritorna cached
        3. Se MISS → chiama fetch_func(), salva in cache, ritorna
        
        Args:
            address: Indirizzo pulito
            fetch_func: Funzione per fetchare da Photon (es. geocoder.geocode)
            
        Returns:
            GeocodingResult o None
            
        Example:
            >>> cache = GeocodeCache()
            >>> geocoder = GeocoderService()
            >>> 
            >>> # Cache-aside pattern
            >>> result = cache.get_or_fetch(
            ...     "Via Roma 1, Milano",
            ...     lambda: geocoder.geocode("Via Roma 1, Milano")
            ... )
        """
        # Step 1: Check cache
        cached_result = self.get(address)
        
        if cached_result:
            # CACHE HIT → return immediately
            return cached_result
        
        # Step 2: CACHE MISS → fetch from source
        logger.debug(f"Fetching from source (Photon) for: '{address}'")
        
        try:
            result = fetch_func()
            
            if result:
                # Step 3: Set cache for future requests
                self.set(address, result)
            
            return result
            
        except Exception as e:
            logger.error(f"Fetch function error for '{address}': {e}")
            return None
    
    def delete(self, address: str) -> bool:
        """
        Elimina un indirizzo dalla cache
        
        Args:
            address: Indirizzo da rimuovere
            
        Returns:
            True se eliminato, False altrimenti
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            key = self._generate_cache_key(address)
            deleted = self.redis_client.delete(key)
            
            if deleted:
                logger.info(f"🗑️  CACHE DELETE: '{address}'")
                return True
            else:
                logger.debug(f"CACHE DELETE: '{address}' not found")
                return False
                
        except Exception as e:
            logger.error(f"Cache DELETE error for '{address}': {e}")
            self.stats['errors'] += 1
            return False
    
    def clear_all(self) -> int:
        """
        Elimina tutte le chiavi geocode dalla cache
        
        ⚠️  ATTENZIONE: Operazione distruttiva!
        
        Returns:
            Numero di chiavi eliminate
        """
        if not self.enabled or not self.redis_client:
            return 0
        
        try:
            # Trova tutte le chiavi con pattern "geocode:*"
            pattern = f"{self.KEY_PREFIX}*"
            keys = list(self.redis_client.scan_iter(match=pattern, count=100))
            
            if keys:
                deleted = self.redis_client.delete(*keys)
                logger.warning(f"🗑️  CACHE CLEAR ALL: {deleted} keys deleted")
                return deleted
            else:
                logger.info("CACHE CLEAR ALL: No keys found")
                return 0
                
        except Exception as e:
            logger.error(f"Cache CLEAR ALL error: {e}")
            self.stats['errors'] += 1
            return 0
    
    def get_stats(self) -> Dict:
        """
        Ottiene statistiche della cache
        
        Returns:
            Dict con hits, misses, hit_rate, errors
        """
        total_requests = self.stats['hits'] + self.stats['misses']
        hit_rate = (self.stats['hits'] / total_requests * 100) if total_requests > 0 else 0.0
        
        return {
            'enabled': self.enabled,
            'host': self.host,
            'port': self.port,
            'ttl_seconds': self.ttl,
            'ttl_days': self.ttl / (24 * 60 * 60),
            'hits': self.stats['hits'],
            'misses': self.stats['misses'],
            'sets': self.stats['sets'],
            'errors': self.stats['errors'],
            'total_requests': total_requests,
            'hit_rate': round(hit_rate, 2)
        }
    
    def health_check(self) -> bool:
        """
        Verifica che Redis sia raggiungibile
        
        Returns:
            True se connesso, False altrimenti
        """
        if not self.enabled or not self.redis_client:
            return False
        
        try:
            self.redis_client.ping()
            return True
        except Exception as e:
            logger.warning(f"Redis health check failed: {e}")
            return False
    
    def get_info(self) -> Dict:
        """
        Ottiene informazioni dettagliate sulla cache
        
        Returns:
            Dict con configurazione e stato
        """
        info = {
            'enabled': self.enabled,
            'available': self.redis_client is not None,
            'host': self.host,
            'port': self.port,
            'ttl': self.ttl,
            'ttl_human': f"{self.ttl // (24*60*60)} giorni",
            'key_prefix': self.KEY_PREFIX,
            'is_connected': self.health_check(),
            'statistics': self.get_stats(),
            'features': [
                'Pattern Cache-Aside',
                'MD5 key hashing',
                'JSON serialization',
                'Fail-open on Redis errors',
                'Statistics tracking',
                'Persistent storage'
            ]
        }
        
        return info


# Singleton instance (opzionale)
_geocode_cache_instance: Optional[GeocodeCache] = None


def get_geocode_cache() -> GeocodeCache:
    """
    Factory function per ottenere un'istanza singleton della cache
    
    Returns:
        GeocodeCache instance
    """
    global _geocode_cache_instance
    
    if _geocode_cache_instance is None:
        # Leggi configurazione da environment
        enabled = os.getenv('USE_REDIS_CACHE', 'true').lower() == 'true'
        _geocode_cache_instance = GeocodeCache(enabled=enabled)
    
    return _geocode_cache_instance
