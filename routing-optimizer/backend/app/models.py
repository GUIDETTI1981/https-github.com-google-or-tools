"""
Pydantic Models for Routing Optimizer API
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class Order(BaseModel):
    """Modello per un ordine/cliente"""
    id: str
    customer_name: str
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    demand: float = Field(..., gt=0, description="Peso del pacco in kg")


class OrderWithAddress(BaseModel):
    """Modello per un ordine con indirizzo testuale (senza coordinate)"""
    id: str
    customer_name: str
    address: str = Field(..., description="Indirizzo testuale completo")
    demand: float = Field(..., gt=0, description="Peso del pacco in kg")


class GeocodingError(BaseModel):
    """Errore di geocoding per un ordine"""
    order_id: str
    customer_name: str
    address: str
    error_message: str


class OptimizationWithGeocodingResult(BaseModel):
    """Risultato dell'ottimizzazione con geocoding"""
    success: bool
    routes: List["VehicleRoute"]
    total_distance: float
    total_load: float
    computation_time: float
    num_orders_served: int
    num_vehicles_used: int
    geocoding_errors: List[GeocodingError] = Field(default_factory=list)
    message: Optional[str] = None


class DepotLocation(BaseModel):
    """Coordinate del deposito"""
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    name: str = "Deposito Centrale"


class FleetConfiguration(BaseModel):
    """Configurazione della flotta"""
    num_vehicles: int = Field(..., ge=1, le=50, description="Numero di veicoli disponibili")
    vehicle_capacity: float = Field(..., gt=0, description="Capacità massima per veicolo in kg")
    depot: DepotLocation


class ORToolsConfiguration(BaseModel):
    """Configurazione parametri OR-Tools"""
    time_limit_seconds: int = Field(default=30, ge=1, le=300)
    first_solution_strategy: Literal[
        "PATH_CHEAPEST_ARC",
        "GLOBAL_CHEAPEST_ARC", 
        "AUTOMATIC"
    ] = "PATH_CHEAPEST_ARC"
    local_search_metaheuristic: Literal[
        "GUIDED_LOCAL_SEARCH",
        "TABU_SEARCH",
        "SIMULATED_ANNEALING"
    ] = "GUIDED_LOCAL_SEARCH"


class VehicleSpecifications(BaseModel):
    """Specifiche fisiche del veicolo (per camion)"""
    vehicle_type: Literal["car", "van", "truck"] = Field(default="car", description="Tipo di veicolo")
    weight: Optional[float] = Field(default=None, ge=0, le=50, description="Peso totale in tonnellate")
    height: Optional[float] = Field(default=None, ge=0, le=5, description="Altezza in metri")
    width: Optional[float] = Field(default=None, ge=0, le=3, description="Larghezza in metri")
    length: Optional[float] = Field(default=None, ge=0, le=25, description="Lunghezza in metri")
    axle_load: Optional[float] = Field(default=None, ge=0, le=15, description="Carico per asse in tonnellate")
    axle_count: Optional[int] = Field(default=None, ge=2, le=10, description="Numero di assi")
    hazmat: bool = Field(default=False, description="Trasporta merci pericolose")


class OptimizationRequest(BaseModel):
    """Richiesta completa di ottimizzazione"""
    orders: List[Order]
    fleet_config: FleetConfiguration
    ortools_config: ORToolsConfiguration
    vehicle_specs: Optional[VehicleSpecifications] = Field(
        default=None, 
        description="Specifiche veicolo (opzionale, solo per truck)"
    )


class RouteStop(BaseModel):
    """Singola fermata in un percorso"""
    order_id: Optional[str] = None
    customer_name: str
    latitude: float
    longitude: float
    demand: float = 0.0
    cumulative_load: float = 0.0
    is_depot: bool = False


class VehicleRoute(BaseModel):
    """Percorso completo di un veicolo"""
    vehicle_id: int
    stops: List[RouteStop]
    total_distance: float
    total_load: float
    color: str  # Colore per la visualizzazione sulla mappa


class OptimizationResult(BaseModel):
    """Risultato dell'ottimizzazione"""
    success: bool
    routes: List[VehicleRoute]
    total_distance: float
    total_load: float
    computation_time: float
    num_orders_served: int
    num_vehicles_used: int
    message: Optional[str] = None


class CRMOrdersResponse(BaseModel):
    """Risposta dal simulatore CRM"""
    orders: List[Order]
    total_count: int
    timestamp: str
