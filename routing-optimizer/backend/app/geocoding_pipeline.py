"""
Geocoding Pipeline - Pipeline per geocoding automatico di ordini CRM

Questo modulo fornisce una pipeline completa per:
1. Pulizia indirizzi sporchi
2. Geocoding (indirizzo → coordinate)
3. Gestione errori
4. Integrazione con VRP solver

Autore: Senior Data Engineer & GIS Python Developer
Data: 2025-12-17
"""

import logging
from typing import List, Tuple
from dataclasses import dataclass

from .models import Order, OrderWithAddress, GeocodingError
from .services.address_sanitizer import AddressSanitizer, get_address_sanitizer
from .services.geocoder_service import GeocoderService, get_geocoder_service, GeocoderError as ServiceGeocoderError

logger = logging.getLogger(__name__)


@dataclass
class GeocodingStats:
    """Statistiche di geocoding"""
    total_orders: int = 0
    successful: int = 0
    failed: int = 0
    success_rate: float = 0.0
    
    def to_dict(self) -> dict:
        return {
            "total_orders": self.total_orders,
            "successful": self.successful,
            "failed": self.failed,
            "success_rate": self.success_rate
        }


class GeocodingPipeline:
    """
    Pipeline completa per geocoding di ordini CRM
    
    Features:
    - Pulizia automatica indirizzi
    - Geocoding con bias geografico
    - Gestione errori senza crash
    - Statistiche dettagliate
    - Logging completo
    """
    
    def __init__(
        self,
        sanitizer: AddressSanitizer = None,
        geocoder: GeocoderService = None
    ):
        """
        Inizializza la pipeline di geocoding
        
        Args:
            sanitizer: AddressSanitizer instance (default: singleton)
            geocoder: GeocoderService instance (default: singleton)
        """
        self.sanitizer = sanitizer or get_address_sanitizer()
        self.geocoder = geocoder or get_geocoder_service()
        
        logger.info("GeocodingPipeline initialized")
    
    def process_orders(
        self,
        orders: List[OrderWithAddress],
        bias_city: str = "roma"
    ) -> Tuple[List[Order], List[GeocodingError], GeocodingStats]:
        """
        Processa un batch di ordini con indirizzi testuali
        
        Pipeline:
        1. Valida indirizzo
        2. Pulisce indirizzo (AddressSanitizer)
        3. Geocodifica (GeocoderService)
        4. Se successo → Order con coordinate
        5. Se fallito → GeocodingError
        
        Args:
            orders: Lista di OrderWithAddress (con indirizzi testuali)
            bias_city: Città per bias geografico (default: "roma")
            
        Returns:
            Tuple:
            - Lista di Order (con coordinate)
            - Lista di GeocodingError (ordini falliti)
            - GeocodingStats (statistiche)
        """
        logger.info("=" * 60)
        logger.info("🗺️  GEOCODING PIPELINE START")
        logger.info(f"📦 Total orders: {len(orders)}")
        logger.info(f"📍 Bias city: {bias_city}")
        logger.info("=" * 60)
        
        # Imposta bias geografico
        if bias_city:
            self.geocoder.set_bias_by_city(bias_city)
        
        # Liste di output
        valid_orders = []
        geocoding_errors = []
        
        # Statistiche
        stats = GeocodingStats(total_orders=len(orders))
        
        # Processa ogni ordine
        for i, order in enumerate(orders):
            try:
                # Log progresso
                if (i + 1) % 10 == 0:
                    logger.info(f"Progress: {i+1}/{len(orders)} orders processed")
                
                # Step 1: Valida indirizzo
                if not self.sanitizer.validate_address(order.address):
                    logger.warning(f"❌ Invalid address for order {order.id}: '{order.address}'")
                    geocoding_errors.append(GeocodingError(
                        order_id=order.id,
                        customer_name=order.customer_name,
                        address=order.address,
                        error_message="Indirizzo non valido o troppo corto"
                    ))
                    stats.failed += 1
                    continue
                
                # Step 2: Pulisci indirizzo
                cleaned_address = self.sanitizer.clean(order.address)
                logger.debug(f"Order {order.id}: '{order.address}' → '{cleaned_address}'")
                
                # Step 3: Geocodifica
                result = self.geocoder.geocode(cleaned_address)
                
                if result is None:
                    # Geocoding fallito
                    logger.warning(f"❌ Geocoding failed for order {order.id}: '{cleaned_address}'")
                    geocoding_errors.append(GeocodingError(
                        order_id=order.id,
                        customer_name=order.customer_name,
                        address=order.address,
                        error_message="Indirizzo non trovato nel database OSM"
                    ))
                    stats.failed += 1
                    continue
                
                # Step 4: Crea Order con coordinate
                valid_order = Order(
                    id=order.id,
                    customer_name=order.customer_name,
                    latitude=result.latitude,
                    longitude=result.longitude,
                    demand=order.demand
                )
                
                valid_orders.append(valid_order)
                stats.successful += 1
                
                logger.info(f"✅ Order {order.id}: ({result.latitude:.6f}, {result.longitude:.6f})")
                
            except ServiceGeocoderError as e:
                # Errore del servizio di geocoding
                logger.error(f"❌ Geocoding service error for order {order.id}: {e}")
                geocoding_errors.append(GeocodingError(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    address=order.address,
                    error_message=f"Errore servizio geocoding: {str(e)}"
                ))
                stats.failed += 1
            
            except Exception as e:
                # Errore generico
                logger.error(f"❌ Unexpected error for order {order.id}: {e}", exc_info=True)
                geocoding_errors.append(GeocodingError(
                    order_id=order.id,
                    customer_name=order.customer_name,
                    address=order.address,
                    error_message=f"Errore imprevisto: {str(e)}"
                ))
                stats.failed += 1
        
        # Calcola success rate
        if stats.total_orders > 0:
            stats.success_rate = (stats.successful / stats.total_orders) * 100
        
        # Log finale
        logger.info("=" * 60)
        logger.info("🗺️  GEOCODING PIPELINE COMPLETE")
        logger.info(f"✅ Successful: {stats.successful}/{stats.total_orders} ({stats.success_rate:.1f}%)")
        logger.info(f"❌ Failed: {stats.failed}/{stats.total_orders}")
        logger.info("=" * 60)
        
        return valid_orders, geocoding_errors, stats
    
    def get_info(self) -> dict:
        """
        Ottiene informazioni sulla pipeline
        
        Returns:
            Dict con configurazione
        """
        return {
            "sanitizer_info": self.sanitizer.get_info(),
            "geocoder_info": self.geocoder.get_info(),
            "features": [
                "Pulizia automatica indirizzi",
                "Geocoding OSM-based",
                "Gestione errori resiliente",
                "Bias geografico",
                "Statistiche dettagliate"
            ]
        }


# Singleton instance (opzionale)
_geocoding_pipeline_instance = None


def get_geocoding_pipeline() -> GeocodingPipeline:
    """
    Factory function per ottenere un'istanza singleton della pipeline
    
    Returns:
        GeocodingPipeline instance
    """
    global _geocoding_pipeline_instance
    
    if _geocoding_pipeline_instance is None:
        _geocoding_pipeline_instance = GeocodingPipeline()
    
    return _geocoding_pipeline_instance
