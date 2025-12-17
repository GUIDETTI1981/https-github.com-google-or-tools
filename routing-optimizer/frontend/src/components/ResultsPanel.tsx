/**
 * Results Panel Component
 * Pannello per visualizzare statistiche e dettagli dei percorsi ottimizzati
 */
import React, { useState } from 'react';
import type { OptimizationResult } from '../types';
import { formatDistance, formatWeight } from '../utils/mapUtils';

interface ResultsPanelProps {
  result: OptimizationResult | null;
}

const ResultsPanel: React.FC<ResultsPanelProps> = ({ result }) => {
  const [expandedVehicles, setExpandedVehicles] = useState<Set<number>>(new Set());

  if (!result) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">
          📊 Risultati Ottimizzazione
        </h3>
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">Nessun risultato disponibile</p>
          <p className="text-sm mt-2">Esegui l'ottimizzazione per visualizzare i percorsi</p>
        </div>
      </div>
    );
  }

  if (!result.success) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">
          ❌ Ottimizzazione Fallita
        </h3>
        <div className="bg-red-50 border border-red-200 rounded-md p-4">
          <p className="text-red-800">{result.message}</p>
        </div>
      </div>
    );
  }

  const toggleVehicle = (vehicleId: number) => {
    setExpandedVehicles(prev => {
      const newSet = new Set(prev);
      if (newSet.has(vehicleId)) {
        newSet.delete(vehicleId);
      } else {
        newSet.add(vehicleId);
      }
      return newSet;
    });
  };

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <h3 className="text-lg font-semibold text-gray-700 mb-4">
        ✅ Risultati Ottimizzazione
      </h3>

      {/* Statistiche Generali */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
          <p className="text-xs text-blue-600 font-medium mb-1">Distanza Totale</p>
          <p className="text-2xl font-bold text-blue-700">
            {formatDistance(result.total_distance)}
          </p>
        </div>

        <div className="bg-green-50 rounded-lg p-4 border border-green-200">
          <p className="text-xs text-green-600 font-medium mb-1">Carico Totale</p>
          <p className="text-2xl font-bold text-green-700">
            {formatWeight(result.total_load)}
          </p>
        </div>

        <div className="bg-purple-50 rounded-lg p-4 border border-purple-200">
          <p className="text-xs text-purple-600 font-medium mb-1">Veicoli Usati</p>
          <p className="text-2xl font-bold text-purple-700">
            {result.num_vehicles_used}
          </p>
        </div>

        <div className="bg-orange-50 rounded-lg p-4 border border-orange-200">
          <p className="text-xs text-orange-600 font-medium mb-1">Ordini Serviti</p>
          <p className="text-2xl font-bold text-orange-700">
            {result.num_orders_served}
          </p>
        </div>
      </div>

      {/* Info Computazione */}
      <div className="bg-gray-50 rounded-md p-3 mb-6 border border-gray-200">
        <p className="text-sm text-gray-700">
          <span className="font-semibold">Tempo di computazione:</span> {result.computation_time.toFixed(3)}s
        </p>
        {result.message && (
          <p className="text-sm text-gray-600 mt-1">{result.message}</p>
        )}
      </div>

      {/* Dettagli Percorsi per Veicolo */}
      <div className="space-y-3">
        <h4 className="font-semibold text-gray-700 mb-3">🚚 Dettaglio Percorsi per Veicolo</h4>
        
        {result.routes.map((route) => (
          <div
            key={route.vehicle_id}
            className="border border-gray-200 rounded-lg overflow-hidden"
          >
            {/* Header del veicolo */}
            <button
              onClick={() => toggleVehicle(route.vehicle_id)}
              className="w-full px-4 py-3 bg-gray-50 hover:bg-gray-100 transition-colors flex justify-between items-center"
            >
              <div className="flex items-center gap-3">
                <div
                  className="w-4 h-4 rounded-full"
                  style={{ backgroundColor: route.color }}
                />
                <span className="font-semibold text-gray-800">
                  Veicolo {route.vehicle_id}
                </span>
              </div>
              
              <div className="flex items-center gap-4">
                <span className="text-sm text-gray-600">
                  {formatDistance(route.total_distance)} · {formatWeight(route.total_load)}
                </span>
                <span className="text-gray-400">
                  {expandedVehicles.has(route.vehicle_id) ? '▼' : '▶'}
                </span>
              </div>
            </button>

            {/* Dettaglio fermate (espandibile) */}
            {expandedVehicles.has(route.vehicle_id) && (
              <div className="p-4 bg-white">
                <ol className="relative border-l-2 border-gray-200 ml-3">
                  {route.stops.map((stop, idx) => (
                    <li key={idx} className="mb-4 ml-6">
                      <div
                        className="absolute w-4 h-4 rounded-full -left-2 border-2 border-white"
                        style={{
                          backgroundColor: stop.is_depot ? '#EF4444' : route.color
                        }}
                      />
                      
                      <div className="bg-gray-50 rounded-md p-3 border border-gray-200">
                        <div className="flex justify-between items-start mb-1">
                          <h5 className="font-semibold text-gray-800 text-sm">
                            {stop.is_depot ? '🏢' : '📦'} {stop.customer_name}
                          </h5>
                          <span className="text-xs text-gray-500">
                            Stop #{idx + 1}
                          </span>
                        </div>
                        
                        {stop.order_id && (
                          <p className="text-xs text-gray-600">ID: {stop.order_id}</p>
                        )}
                        
                        <div className="flex gap-4 mt-2 text-xs text-gray-600">
                          {!stop.is_depot && (
                            <>
                              <span>Consegna: {formatWeight(stop.demand)}</span>
                              <span>Carico: {formatWeight(stop.cumulative_load)}</span>
                            </>
                          )}
                        </div>
                        
                        <p className="text-xs text-gray-500 mt-1 font-mono">
                          {stop.latitude.toFixed(4)}, {stop.longitude.toFixed(4)}
                        </p>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Suggerimenti */}
      <div className="mt-6 bg-blue-50 border border-blue-200 rounded-md p-4">
        <h5 className="font-semibold text-blue-800 mb-2">💡 Suggerimenti</h5>
        <ul className="text-sm text-blue-700 space-y-1">
          <li>• Clicca su un veicolo per espandere il dettaglio delle fermate</li>
          <li>• I colori sulla mappa corrispondono ai veicoli</li>
          <li>• Puoi esportare questi dati per ulteriori analisi</li>
        </ul>
      </div>
    </div>
  );
};

export default ResultsPanel;
