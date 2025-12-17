/**
 * TypeScript Type Definitions
 */

export interface Order {
  id: string;
  customer_name: string;
  latitude: number;
  longitude: number;
  demand: number;
}

export interface DepotLocation {
  latitude: number;
  longitude: number;
  name: string;
}

export interface FleetConfiguration {
  num_vehicles: number;
  vehicle_capacity: number;
  depot: DepotLocation;
}

export interface ORToolsConfiguration {
  time_limit_seconds: number;
  first_solution_strategy: 'PATH_CHEAPEST_ARC' | 'GLOBAL_CHEAPEST_ARC' | 'AUTOMATIC';
  local_search_metaheuristic: 'GUIDED_LOCAL_SEARCH' | 'TABU_SEARCH' | 'SIMULATED_ANNEALING';
}

export interface OptimizationRequest {
  orders: Order[];
  fleet_config: FleetConfiguration;
  ortools_config: ORToolsConfiguration;
}

export interface RouteStop {
  order_id?: string | null;
  customer_name: string;
  latitude: number;
  longitude: number;
  demand: number;
  cumulative_load: number;
  is_depot: boolean;
}

export interface VehicleRoute {
  vehicle_id: number;
  stops: RouteStop[];
  total_distance: number;
  total_load: number;
  color: string;
}

export interface OptimizationResult {
  success: boolean;
  routes: VehicleRoute[];
  total_distance: number;
  total_load: number;
  computation_time: number;
  num_orders_served: number;
  num_vehicles_used: number;
  message?: string;
}

export interface CRMOrdersResponse {
  orders: Order[];
  total_count: number;
  timestamp: string;
}

export interface Strategy {
  value: string;
  label: string;
  description: string;
}

export interface ConfigStrategies {
  first_solution_strategies: Strategy[];
  local_search_metaheuristics: Strategy[];
}
