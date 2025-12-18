/**
 * Advanced Data Models for VRP Application
 * Separazione macro-aree: Configurazione & Setup + Pianificazione Giornaliera
 */

// ============================================
// AREA 1: CONFIGURAZIONE & SETUP (Set & Forget)
// ============================================

/**
 * Profilo Veicolo - Template riutilizzabile
 * Definisce le caratteristiche strutturali di un tipo di veicolo
 */
export interface VehicleProfile {
  id: string;
  name: string; // es. "Furgone Grande", "Camion 7.5t", "Auto Compatta"
  
  // Tipo per routing engine selection
  vehicle_type: 'car' | 'van' | 'truck';
  
  // Capacità
  capacity_kg: number;
  capacity_volume_m3?: number;
  
  // Costi Operativi
  cost_per_km: number; // €/km
  cost_per_hour: number; // €/ora
  fixed_cost: number; // € costo fisso per utilizzo
  
  // Vincoli Fisici (per Valhalla Truck Routing)
  physical_constraints?: {
    height_meters?: number; // Altezza max (ponti, sottopassaggi)
    width_meters?: number; // Larghezza (strade strette)
    length_meters?: number; // Lunghezza
    weight_kg?: number; // Peso totale max
    axle_load_kg?: number; // Carico per asse
    hazmat?: boolean; // Materiali pericolosi (restrizioni tunnel)
  };
  
  // Time Windows Default
  default_start_time?: string; // "08:00"
  default_end_time?: string; // "18:00"
  max_working_hours?: number; // Ore massime lavoro
  
  // Skills del veicolo (es. "frigo", "sponda", "adr")
  skills?: string[];
  
  // Metadati
  created_at: string;
  updated_at: string;
}

/**
 * Profilo Deposito
 */
export interface DepotProfile {
  id: string;
  name: string; // es. "Deposito Milano Nord"
  
  // Coordinate
  latitude: number;
  longitude: number;
  address?: string; // Indirizzo testuale
  
  // Orari Operativi
  opening_time: string; // "07:00"
  closing_time: string; // "20:00"
  
  // Metadati
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Configurazione OR-Tools
 */
export interface ORToolsConfiguration {
  id: string;
  name: string; // es. "Config Veloce", "Config Ottimale"
  
  // Parametri Algoritmo
  time_limit_seconds: number;
  first_solution_strategy: FirstSolutionStrategy;
  local_search_metaheuristic: LocalSearchMetaheuristic;
  
  // Penalità
  penalty_dropped_order?: number; // Penalità ordine non servito
  penalty_late_delivery?: number; // Penalità consegna in ritardo
  
  // Opzioni Avanzate
  use_depth_first_search?: boolean;
  optimization_step?: number;
  
  // Metadati
  is_default: boolean;
  created_at: string;
  updated_at: string;
}

/**
 * Routing Engine Configuration
 */
export interface RoutingEngineConfig {
  use_osrm: boolean; // Auto/Van routing
  use_valhalla: boolean; // Truck routing con vincoli fisici
  osrm_host: string;
  valhalla_host: string;
}

/**
 * Skill Definition (es. "Frigo", "Sponda Idraulica", "ADR")
 */
export interface SkillDefinition {
  id: string;
  name: string;
  description: string;
  icon?: string; // Emoji o classe CSS
}

/**
 * Zone Definition (es. "Centro Storico", "ZTL", "Area Portuale")
 */
export interface ZoneDefinition {
  id: string;
  name: string;
  description: string;
  restrictions?: string[]; // es. ["no_diesel", "height_limit_3m"]
}

// ============================================
// AREA 2: PIANIFICAZIONE GIORNALIERA
// ============================================

/**
 * Ordine Giornaliero (Dati Variabili)
 */
export interface DailyOrder {
  id: string;
  
  // Indirizzo
  address: string;
  latitude?: number; // Popolato dopo geocoding
  longitude?: number;
  
  // Domanda
  demand_kg: number;
  demand_volume_m3?: number;
  
  // Time Windows
  time_window_start?: string; // "09:00"
  time_window_end?: string; // "12:00"
  
  // Service Time
  service_duration_minutes: number; // Tempo scarico
  
  // Priorità
  priority: 'low' | 'medium' | 'high' | 'urgent';
  
  // Skills Richieste
  required_skills?: string[];
  
  // Note
  notes?: string;
  customer_name?: string;
}

/**
 * Disponibilità Flotta Giornaliera
 * Collega i VehicleProfile salvati alla pianificazione di oggi
 */
export interface DailyFleetAvailability {
  vehicle_profile_id: string; // Riferimento a VehicleProfile
  vehicle_instance_id: string; // ID univoco per oggi (es. "VAN-001-20241218")
  
  // Overrides per oggi (opzionali)
  driver_name?: string;
  start_time?: string; // Override orario partenza
  end_time?: string; // Override orario ritorno
  
  // Stato
  is_available: boolean;
}

/**
 * Parametri Ottimizzazione Giornaliera
 */
export interface DailyOptimizationParams {
  depot_id: string; // Riferimento a DepotProfile
  ortools_config_id: string; // Riferimento a ORToolsConfiguration
  fleet_availability: DailyFleetAvailability[];
  orders: DailyOrder[];
  
  // Routing Engine Selection (override da config)
  force_routing_engine?: 'osrm' | 'valhalla' | 'haversine';
}

// ============================================
// OR-TOOLS ENUMS
// ============================================

export type FirstSolutionStrategy = 
  | 'AUTOMATIC'
  | 'PATH_CHEAPEST_ARC'
  | 'PATH_MOST_CONSTRAINED_ARC'
  | 'EVALUATOR_STRATEGY'
  | 'SAVINGS'
  | 'SWEEP'
  | 'CHRISTOFIDES'
  | 'ALL_UNPERFORMED'
  | 'BEST_INSERTION'
  | 'PARALLEL_CHEAPEST_INSERTION'
  | 'SEQUENTIAL_CHEAPEST_INSERTION'
  | 'LOCAL_CHEAPEST_INSERTION'
  | 'GLOBAL_CHEAPEST_ARC'
  | 'LOCAL_CHEAPEST_ARC'
  | 'FIRST_UNBOUND_MIN_VALUE';

export type LocalSearchMetaheuristic =
  | 'AUTOMATIC'
  | 'GREEDY_DESCENT'
  | 'GUIDED_LOCAL_SEARCH'
  | 'SIMULATED_ANNEALING'
  | 'TABU_SEARCH'
  | 'GENERIC_TABU_SEARCH';

// ============================================
// LEGACY TYPES (per compatibilità con API esistente)
// ============================================

export interface Order {
  id: string;
  latitude: number;
  longitude: number;
  demand: number;
  priority?: number;
  time_window_start?: number;
  time_window_end?: number;
  service_time?: number;
}

export interface FleetConfiguration {
  num_vehicles: number;
  vehicle_capacity: number;
  depot: {
    latitude: number;
    longitude: number;
    name: string;
  };
}

export interface OptimizationResult {
  success: boolean;
  message?: string;
  routes?: Route[];
  total_distance?: number;
  total_duration?: number;
  unassigned_orders?: string[];
}

export interface Route {
  vehicle_id: string;
  stops: Stop[];
  total_distance: number;
  total_duration: number;
  total_load: number;
}

export interface Stop {
  order_id?: string;
  latitude: number;
  longitude: number;
  arrival_time?: number;
  departure_time?: number;
  cumulative_load?: number;
  type: 'depot' | 'delivery';
}

export interface ConfigStrategies {
  first_solution_strategies: {
    value: string;
    label: string;
    description: string;
  }[];
  local_search_metaheuristics: {
    value: string;
    label: string;
    description: string;
  }[];
}
