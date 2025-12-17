"""
CRM Client Simulator - Simula l'integrazione con un CRM esterno
"""
import random
from datetime import datetime
from typing import List
from .models import Order, CRMOrdersResponse


class CRMClient:
    """
    Simulatore di un client CRM esterno.
    In produzione, questo sarebbe sostituito con chiamate API reali.
    """
    
    # Coordinate reali di Roma centro
    ROME_CENTER = {"lat": 41.9028, "lon": 12.4964}
    
    # Nomi clienti italiani realistici
    CUSTOMER_NAMES = [
        "Trattoria da Giovanni", "Farmacia Centrale", "Bar Caffè Italiano",
        "Supermercato Conad", "Pizzeria Napoli", "Ristorante La Pergola",
        "Gelateria Giolitti", "Panificio Bonci", "Macelleria Feroci",
        "Libreria Mondadori", "Tabacchi & Edicola", "Ottica Vision Center",
        "Parrucchiere Elegante", "Ferramenta Rossi", "Pasticceria Boccione",
        "Enoteche Bulzoni", "Salumeria Roscioli", "Mercato Testaccio",
        "Negozio Bio Natura", "Fioraio Margherita", "Centro Estetico Venere",
        "Palestra Fitness Plus", "Studio Medico Dr. Bianchi", "Officina Auto Speedy"
    ]
    
    def __init__(self, seed: int = 42):
        """
        Inizializza il client CRM con un seed per la riproducibilità
        
        Args:
            seed: Seed per la generazione casuale
        """
        random.seed(seed)
    
    def _generate_realistic_coordinates(self, num_points: int = 20) -> List[tuple]:
        """
        Genera coordinate realistiche in un raggio di circa 5-10 km dal centro di Roma
        
        Args:
            num_points: Numero di coordinate da generare
            
        Returns:
            Lista di tuple (latitudine, longitudine)
        """
        coordinates = []
        
        # Genera punti in un raggio di circa 0.05-0.10 gradi (circa 5-10 km)
        for _ in range(num_points):
            # Aggiungi variazione casuale
            radius = random.uniform(0.02, 0.08)
            angle = random.uniform(0, 360)
            
            # Converti in coordinate cartesiane
            import math
            lat_offset = radius * math.cos(math.radians(angle))
            lon_offset = radius * math.sin(math.radians(angle))
            
            lat = self.ROME_CENTER["lat"] + lat_offset
            lon = self.ROME_CENTER["lon"] + lon_offset
            
            coordinates.append((lat, lon))
        
        return coordinates
    
    def get_orders(self, num_orders: int = 20) -> CRMOrdersResponse:
        """
        Simula il recupero degli ordini dal CRM
        
        Args:
            num_orders: Numero di ordini da generare (default: 20)
            
        Returns:
            CRMOrdersResponse contenente la lista degli ordini
        """
        # Genera coordinate realistiche
        coordinates = self._generate_realistic_coordinates(num_orders)
        
        # Seleziona nomi clienti casuali
        selected_customers = random.sample(
            self.CUSTOMER_NAMES, 
            min(num_orders, len(self.CUSTOMER_NAMES))
        )
        
        # Se servono più ordini dei nomi disponibili, riutilizza con suffissi
        if num_orders > len(self.CUSTOMER_NAMES):
            additional_names = [
                f"{name} - Filiale {i}" 
                for i, name in enumerate(
                    self.CUSTOMER_NAMES * ((num_orders // len(self.CUSTOMER_NAMES)) + 1),
                    start=1
                )
            ]
            selected_customers = additional_names[:num_orders]
        
        # Genera ordini
        orders = []
        for i, (customer_name, (lat, lon)) in enumerate(zip(selected_customers, coordinates), start=1):
            # Genera domanda (peso) realistica tra 5 e 50 kg
            demand = round(random.uniform(5.0, 50.0), 2)
            
            order = Order(
                id=f"ORD{i:04d}",
                customer_name=customer_name,
                latitude=round(lat, 6),
                longitude=round(lon, 6),
                demand=demand
            )
            orders.append(order)
        
        return CRMOrdersResponse(
            orders=orders,
            total_count=len(orders),
            timestamp=datetime.now().isoformat()
        )
    
    def get_order_by_id(self, order_id: str) -> Order:
        """
        Simula il recupero di un singolo ordine per ID
        
        Args:
            order_id: ID dell'ordine da recuperare
            
        Returns:
            Order object
        """
        # Per semplicità, genera un ordine casuale
        coords = self._generate_realistic_coordinates(1)[0]
        customer_name = random.choice(self.CUSTOMER_NAMES)
        
        return Order(
            id=order_id,
            customer_name=customer_name,
            latitude=round(coords[0], 6),
            longitude=round(coords[1], 6),
            demand=round(random.uniform(5.0, 50.0), 2)
        )
    
    def validate_orders(self, orders: List[Order]) -> dict:
        """
        Valida una lista di ordini
        
        Args:
            orders: Lista di ordini da validare
            
        Returns:
            Dizionario con risultati della validazione
        """
        validation_results = {
            "valid": True,
            "total_orders": len(orders),
            "total_demand": sum(order.demand for order in orders),
            "errors": []
        }
        
        # Verifica coordinate valide
        for order in orders:
            if not (-90 <= order.latitude <= 90):
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Ordine {order.id}: latitudine non valida"
                )
            
            if not (-180 <= order.longitude <= 180):
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Ordine {order.id}: longitudine non valida"
                )
            
            if order.demand <= 0:
                validation_results["valid"] = False
                validation_results["errors"].append(
                    f"Ordine {order.id}: domanda deve essere positiva"
                )
        
        return validation_results
