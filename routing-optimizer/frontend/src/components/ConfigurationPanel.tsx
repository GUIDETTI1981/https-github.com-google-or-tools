/**
 * Configuration Panel Component
 * Pannello per configurare flotta e parametri OR-Tools
 */
import React, { useState, useEffect } from 'react';
import type { FleetConfiguration, ORToolsConfiguration, Order, ConfigStrategies } from '../types';
import { fetchAvailableStrategies } from '../services/api';

interface ConfigurationPanelProps {
  orders: Order[];
  onImportOrders: () => void;
  onOptimize: (fleet: FleetConfiguration, ortools: ORToolsConfiguration) => void;
  isLoading: boolean;
}

const ConfigurationPanel: React.FC<ConfigurationPanelProps> = ({
  orders,
  onImportOrders,
  onOptimize,
  isLoading
}) => {
  // Fleet Configuration State
  const [numVehicles, setNumVehicles] = useState<number>(3);
  const [vehicleCapacity, setVehicleCapacity] = useState<number>(100);
  const [depotLat, setDepotLat] = useState<number>(41.9028);
  const [depotLon, setDepotLon] = useState<number>(12.4964);

  // OR-Tools Configuration State
  const [timeLimit, setTimeLimit] = useState<number>(30);
  const [firstSolutionStrategy, setFirstSolutionStrategy] = useState<string>('PATH_CHEAPEST_ARC');
  const [localSearchMetaheuristic, setLocalSearchMetaheuristic] = useState<string>('GUIDED_LOCAL_SEARCH');

  // Available Strategies
  const [strategies, setStrategies] = useState<ConfigStrategies | null>(null);

  useEffect(() => {
    // Carica le strategie disponibili
    fetchAvailableStrategies()
      .then(data => setStrategies(data))
      .catch(err => console.error('Errore caricamento strategie:', err));
  }, []);

  const handleOptimize = () => {
    const fleetConfig: FleetConfiguration = {
      num_vehicles: numVehicles,
      vehicle_capacity: vehicleCapacity,
      depot: {
        latitude: depotLat,
        longitude: depotLon,
        name: 'Deposito Centrale'
      }
    };

    const ortoolsConfig: ORToolsConfiguration = {
      time_limit_seconds: timeLimit,
      first_solution_strategy: firstSolutionStrategy as any,
      local_search_metaheuristic: localSearchMetaheuristic as any
    };

    onOptimize(fleetConfig, ortoolsConfig);
  };

  const totalDemand = orders.reduce((sum, order) => sum + order.demand, 0);
  const totalCapacity = numVehicles * vehicleCapacity;
  const isCapacitySufficient = totalDemand <= totalCapacity;

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b pb-3">
        ⚙️ Configurazione
      </h2>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Colonna Sinistra - Impostazioni Flotta */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            🚚 Impostazioni Flotta
          </h3>

          {/* Numero Veicoli */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Numero di Veicoli
            </label>
            <input
              type="number"
              min="1"
              max="50"
              value={numVehicles}
              onChange={(e) => setNumVehicles(parseInt(e.target.value) || 1)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Capacità Veicolo */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Capacità Veicolo (kg)
            </label>
            <input
              type="number"
              min="1"
              value={vehicleCapacity}
              onChange={(e) => setVehicleCapacity(parseInt(e.target.value) || 1)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
          </div>

          {/* Coordinate Deposito */}
          <div className="border-t pt-4">
            <h4 className="text-sm font-semibold text-gray-700 mb-2">📍 Coordinate Deposito</h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Latitudine
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={depotLat}
                  onChange={(e) => setDepotLat(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>

              <div>
                <label className="block text-xs font-medium text-gray-600 mb-1">
                  Longitudine
                </label>
                <input
                  type="number"
                  step="0.000001"
                  value={depotLon}
                  onChange={(e) => setDepotLon(parseFloat(e.target.value) || 0)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md text-sm focus:ring-2 focus:ring-primary-500"
                />
              </div>
            </div>
          </div>

          {/* Info Capacità */}
          <div className={`p-3 rounded-md ${isCapacitySufficient ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
            <p className="text-sm">
              <span className="font-semibold">Domanda totale:</span> {totalDemand.toFixed(2)} kg
            </p>
            <p className="text-sm">
              <span className="font-semibold">Capacità totale:</span> {totalCapacity.toFixed(2)} kg
            </p>
            {!isCapacitySufficient && (
              <p className="text-xs text-red-600 mt-1">
                ⚠️ Capacità insufficiente! Aumenta i veicoli o la capacità.
              </p>
            )}
          </div>
        </div>

        {/* Colonna Destra - Impostazioni OR-Tools */}
        <div className="space-y-4">
          <h3 className="text-lg font-semibold text-gray-700 mb-3">
            🔧 Impostazioni Algoritmo OR-Tools
          </h3>

          {/* Time Limit */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Time Limit (secondi)
            </label>
            <input
              type="number"
              min="1"
              max="300"
              value={timeLimit}
              onChange={(e) => setTimeLimit(parseInt(e.target.value) || 1)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            />
            <p className="text-xs text-gray-500 mt-1">
              Tempo massimo per l'ottimizzazione
            </p>
          </div>

          {/* First Solution Strategy */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              First Solution Strategy
            </label>
            <select
              value={firstSolutionStrategy}
              onChange={(e) => setFirstSolutionStrategy(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {strategies?.first_solution_strategies.map((strategy) => (
                <option key={strategy.value} value={strategy.value}>
                  {strategy.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {strategies?.first_solution_strategies.find(s => s.value === firstSolutionStrategy)?.description}
            </p>
          </div>

          {/* Local Search Metaheuristic */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Local Search Metaheuristic
            </label>
            <select
              value={localSearchMetaheuristic}
              onChange={(e) => setLocalSearchMetaheuristic(e.target.value)}
              className="w-full px-4 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              {strategies?.local_search_metaheuristics.map((meta) => (
                <option key={meta.value} value={meta.value}>
                  {meta.label}
                </option>
              ))}
            </select>
            <p className="text-xs text-gray-500 mt-1">
              {strategies?.local_search_metaheuristics.find(m => m.value === localSearchMetaheuristic)?.description}
            </p>
          </div>
        </div>
      </div>

      {/* Action Buttons */}
      <div className="mt-6 flex gap-3 border-t pt-4">
        <button
          onClick={onImportOrders}
          disabled={isLoading}
          className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-3 px-6 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳ Caricamento...' : '📥 Importa da CRM'}
        </button>

        <button
          onClick={handleOptimize}
          disabled={isLoading || orders.length === 0}
          className="flex-1 bg-green-600 hover:bg-green-700 text-white font-semibold py-3 px-6 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isLoading ? '⏳ Ottimizzazione...' : '🚀 Ottimizza Percorsi'}
        </button>
      </div>
    </div>
  );
};

export default ConfigurationPanel;
