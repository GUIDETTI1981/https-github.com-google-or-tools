/**
 * Daily Planning Page
 * AREA 2: Pianificazione Giornaliera - Mission Control
 * Wizard 3 Steps: Upload Ordini → Selezione Flotta → Ottimizzazione
 */
import React, { useState } from 'react';
import { useConfiguration } from '../contexts/ConfigurationContext';
import { DailyOrder, DailyFleetAvailability, OptimizationResult } from '../types/models';
import { optimizeRoutes } from '../services/api';
import ResultsMap from '../components/ResultsMap';
import ResultsPanel from '../components/ResultsPanel';

type WizardStep = 1 | 2 | 3;

const DailyPlanningPage: React.FC = () => {
  const config = useConfiguration();
  const [currentStep, setCurrentStep] = useState<WizardStep>(1);
  const [orders, setOrders] = useState<DailyOrder[]>([]);
  const [selectedFleet, setSelectedFleet] = useState<DailyFleetAvailability[]>([]);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Upload CSV Orders
  const handleCSVUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    const reader = new FileReader();
    reader.onload = (event) => {
      const csv = event.target?.result as string;
      const lines = csv.split('\n').filter(l => l.trim());
      const headers = lines[0].split(',').map(h => h.trim());
      
      const parsedOrders: DailyOrder[] = lines.slice(1).map((line, idx) => {
        const values = line.split(',').map(v => v.trim());
        return {
          id: values[headers.indexOf('order_id')] || `ORD-${idx}`,
          address: values[headers.indexOf('address')] || '',
          demand_kg: parseFloat(values[headers.indexOf('demand_kg')] || values[headers.indexOf('demand')] || '10'),
          service_duration_minutes: parseInt(values[headers.indexOf('service_duration_minutes')] || '10'),
          priority: (values[headers.indexOf('priority')] as any) || 'medium',
          customer_name: values[headers.indexOf('customer_name')],
          notes: values[headers.indexOf('notes')]
        };
      });
      
      setOrders(parsedOrders);
      setCurrentStep(2);
    };
    reader.readAsText(file);
  };

  // Step 2: Toggle Fleet Availability
  const toggleVehicle = (profileId: string) => {
    const exists = selectedFleet.find(f => f.vehicle_profile_id === profileId);
    if (exists) {
      setSelectedFleet(selectedFleet.filter(f => f.vehicle_profile_id !== profileId));
    } else {
      setSelectedFleet([...selectedFleet, {
        vehicle_profile_id: profileId,
        vehicle_instance_id: `${profileId}-${Date.now()}`,
        is_available: true
      }]);
    }
  };

  // Step 3: Optimize
  const handleOptimize = async () => {
    if (orders.length === 0 || selectedFleet.length === 0) {
      setError('Seleziona almeno un ordine e un veicolo');
      return;
    }

    setIsLoading(true);
    setError(null);

    const depot = config.getDefaultDepot();
    const ortoolsConfig = config.getDefaultORToolsConfig();

    if (!depot || !ortoolsConfig) {
      setError('Configurare almeno un deposito e una config OR-Tools');
      setIsLoading(false);
      return;
    }

    try {
      // Transform to API format (legacy)
      const apiOrders = orders.map(o => ({
        id: o.id,
        latitude: o.latitude || 0,
        longitude: o.longitude || 0,
        demand: o.demand_kg,
        priority: o.priority === 'urgent' ? 1 : o.priority === 'high' ? 2 : 3,
        service_time: o.service_duration_minutes
      }));

      const fleetConfig = {
        num_vehicles: selectedFleet.length,
        vehicle_capacity: config.vehicleProfiles.find(v => v.id === selectedFleet[0].vehicle_profile_id)?.capacity_kg || 1000,
        depot: {
          latitude: depot.latitude,
          longitude: depot.longitude,
          name: depot.name
        }
      };

      const request = {
        orders: apiOrders,
        fleet_config: fleetConfig,
        ortools_config: {
          time_limit_seconds: ortoolsConfig.time_limit_seconds,
          first_solution_strategy: ortoolsConfig.first_solution_strategy,
          local_search_metaheuristic: ortoolsConfig.local_search_metaheuristic
        }
      };

      const optimizationResult = await optimizeRoutes(request);
      setResult(optimizationResult);
      setCurrentStep(3);

      if (!optimizationResult.success) {
        setError(optimizationResult.message || 'Ottimizzazione fallita');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore durante l\'ottimizzazione');
      console.error('Errore ottimizzazione:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const depot = config.getDefaultDepot();

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          📋 Pianificazione Giornaliera
        </h1>
        <p className="text-gray-600">
          Mission Control - Ottimizza i percorsi per la giornata
        </p>
      </div>

      {/* Wizard Progress */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between">
          <div className={`flex-1 text-center ${currentStep >= 1 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center font-bold ${currentStep >= 1 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>1</div>
            <div className="text-sm font-semibold">Upload Ordini</div>
          </div>
          <div className={`flex-1 h-1 ${currentStep >= 2 ? 'bg-blue-600' : 'bg-gray-200'}`} />
          <div className={`flex-1 text-center ${currentStep >= 2 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center font-bold ${currentStep >= 2 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>2</div>
            <div className="text-sm font-semibold">Selezione Flotta</div>
          </div>
          <div className={`flex-1 h-1 ${currentStep >= 3 ? 'bg-blue-600' : 'bg-gray-200'}`} />
          <div className={`flex-1 text-center ${currentStep >= 3 ? 'text-blue-600' : 'text-gray-400'}`}>
            <div className={`w-10 h-10 rounded-full mx-auto mb-2 flex items-center justify-center font-bold ${currentStep >= 3 ? 'bg-blue-600 text-white' : 'bg-gray-200'}`}>3</div>
            <div className="text-sm font-semibold">Ottimizzazione</div>
          </div>
        </div>
      </div>

      {/* Error Banner */}
      {error && (
        <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
          <div className="flex items-center">
            <span className="text-2xl mr-3">⚠️</span>
            <div>
              <h3 className="font-semibold text-red-800">Errore</h3>
              <p className="text-sm text-red-700">{error}</p>
            </div>
          </div>
        </div>
      )}

      {/* Step 1: Upload Orders */}
      {currentStep === 1 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">📥 Step 1: Carica Ordini</h2>
          <div className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <div className="text-5xl mb-4">📂</div>
              <h3 className="text-lg font-semibold mb-2">Upload CSV File</h3>
              <p className="text-sm text-gray-600 mb-4">
                Formato richiesto: order_id, address, demand_kg, service_duration_minutes, priority
              </p>
              <label className="inline-block px-6 py-3 bg-blue-600 text-white rounded-md hover:bg-blue-700 cursor-pointer font-semibold">
                📁 Seleziona File CSV
                <input type="file" accept=".csv" onChange={handleCSVUpload} className="hidden" />
              </label>
            </div>

            <div className="bg-blue-50 p-4 rounded-md border-l-4 border-blue-500">
              <h4 className="font-semibold text-sm mb-2">💡 Esempio CSV:</h4>
              <pre className="text-xs bg-white p-2 rounded overflow-x-auto">
{`order_id,address,demand_kg,service_duration_minutes,priority
ORD001,Via Roma 10 Milano,25,10,high
ORD002,Corso Vittorio 50 Milano,30,15,medium`}
              </pre>
            </div>
          </div>
        </div>
      )}

      {/* Step 2: Select Fleet */}
      {currentStep === 2 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-bold mb-4">🚚 Step 2: Seleziona Flotta Disponibile</h2>
          
          <div className="mb-4 bg-gray-50 p-3 rounded">
            <strong>Ordini Caricati:</strong> {orders.length} | <strong>Veicoli Selezionati:</strong> {selectedFleet.length}
          </div>

          {config.vehicleProfiles.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              Nessun modello veicolo configurato. Vai in "Configurazione & Setup" → "Modelli Veicoli"
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {config.vehicleProfiles.map(profile => {
                const isSelected = selectedFleet.some(f => f.vehicle_profile_id === profile.id);
                return (
                  <div
                    key={profile.id}
                    onClick={() => toggleVehicle(profile.id)}
                    className={`border-2 rounded-lg p-4 cursor-pointer transition-all ${
                      isSelected ? 'border-green-500 bg-green-50' : 'border-gray-200 hover:border-blue-300'
                    }`}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-3xl">{profile.vehicle_type === 'truck' ? '🚚' : profile.vehicle_type === 'van' ? '🚐' : '🚗'}</span>
                      <input type="checkbox" checked={isSelected} readOnly className="w-5 h-5" />
                    </div>
                    <h3 className="font-bold text-gray-800">{profile.name}</h3>
                    <div className="text-sm text-gray-600 mt-2">
                      <div>Capacità: {profile.capacity_kg} kg</div>
                      <div>€{profile.cost_per_km}/km</div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div className="flex gap-3 mt-6 pt-4 border-t">
            <button onClick={() => setCurrentStep(1)} className="px-6 py-2 border rounded-md hover:bg-gray-50">← Indietro</button>
            <button
              onClick={handleOptimize}
              disabled={selectedFleet.length === 0 || isLoading}
              className="flex-1 px-6 py-3 bg-green-600 text-white rounded-md hover:bg-green-700 font-semibold disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? '⏳ Ottimizzazione in corso...' : '🚀 Ottimizza Percorsi'}
            </button>
          </div>
        </div>
      )}

      {/* Step 3: Results */}
      {currentStep === 3 && result && depot && (
        <div className="space-y-6">
          <ResultsPanel result={result} />
          <ResultsMap 
            routes={result.routes || []} 
            depotLat={depot.latitude} 
            depotLon={depot.longitude} 
          />
          <div className="flex gap-3">
            <button onClick={() => { setCurrentStep(1); setResult(null); setOrders([]); setSelectedFleet([]); }} className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700">🔄 Nuova Pianificazione</button>
          </div>
        </div>
      )}
    </div>
  );
};

export default DailyPlanningPage;
