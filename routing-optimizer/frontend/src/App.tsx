/**
 * Main Application Component
 * Routing Optimizer - CVRP with Google OR-Tools
 */
import React, { useState } from 'react';
import ConfigurationPanel from './components/ConfigurationPanel';
import OrdersTable from './components/OrdersTable';
import ResultsMap from './components/ResultsMap';
import ResultsPanel from './components/ResultsPanel';
import { fetchCRMOrders, optimizeRoutes } from './services/api';
import type { Order, FleetConfiguration, ORToolsConfiguration, OptimizationResult } from './types';

const App: React.FC = () => {
  const [orders, setOrders] = useState<Order[]>([]);
  const [result, setResult] = useState<OptimizationResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [depotLat, setDepotLat] = useState<number>(41.9028);
  const [depotLon, setDepotLon] = useState<number>(12.4964);

  const handleImportOrders = async () => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetchCRMOrders(20);
      setOrders(response.orders);
      setResult(null); // Reset risultati precedenti
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Errore durante l\'importazione degli ordini');
      console.error('Errore importazione:', err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleOptimize = async (
    fleetConfig: FleetConfiguration,
    ortoolsConfig: ORToolsConfiguration
  ) => {
    if (orders.length === 0) {
      setError('Nessun ordine da ottimizzare. Importa prima gli ordini dal CRM.');
      return;
    }

    setIsLoading(true);
    setError(null);
    
    // Salva coordinate deposito per la mappa
    setDepotLat(fleetConfig.depot.latitude);
    setDepotLon(fleetConfig.depot.longitude);

    try {
      const request = {
        orders,
        fleet_config: fleetConfig,
        ortools_config: ortoolsConfig
      };

      const optimizationResult = await optimizeRoutes(request);
      setResult(optimizationResult);

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

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header */}
      <header className="bg-white shadow-md">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-800">
                🚚 Routing Optimizer
              </h1>
              <p className="text-sm text-gray-600 mt-1">
                Capacitated Vehicle Routing Problem with Google OR-Tools
              </p>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-gray-600">Sistema Operativo</span>
            </div>
          </div>
        </div>
      </header>

      {/* Error Banner */}
      {error && (
        <div className="container mx-auto px-4 mt-4">
          <div className="bg-red-50 border-l-4 border-red-500 p-4 rounded-md">
            <div className="flex items-center">
              <span className="text-red-500 mr-3 text-xl">⚠️</span>
              <div>
                <h3 className="text-red-800 font-semibold">Errore</h3>
                <p className="text-red-700 text-sm">{error}</p>
              </div>
              <button
                onClick={() => setError(null)}
                className="ml-auto text-red-500 hover:text-red-700"
              >
                ✕
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="space-y-6">
          {/* Configurazione */}
          <ConfigurationPanel
            orders={orders}
            onImportOrders={handleImportOrders}
            onOptimize={handleOptimize}
            isLoading={isLoading}
          />

          {/* Tabella Ordini */}
          {orders.length > 0 && (
            <OrdersTable orders={orders} />
          )}

          {/* Risultati */}
          {(result || orders.length > 0) && (
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Mappa */}
              <div>
                <h3 className="text-lg font-semibold text-gray-700 mb-3">
                  🗺️ Mappa Interattiva
                </h3>
                <ResultsMap
                  result={result}
                  orders={orders}
                  depotLat={depotLat}
                  depotLon={depotLon}
                />
              </div>

              {/* Pannello Risultati */}
              <div>
                <ResultsPanel result={result} />
              </div>
            </div>
          )}

          {/* Welcome Message */}
          {orders.length === 0 && !result && (
            <div className="bg-white rounded-lg shadow-lg p-8 text-center">
              <div className="max-w-2xl mx-auto">
                <div className="text-6xl mb-4">🚚</div>
                <h2 className="text-2xl font-bold text-gray-800 mb-3">
                  Benvenuto in Routing Optimizer
                </h2>
                <p className="text-gray-600 mb-6">
                  Questa applicazione risolve il Capacitated Vehicle Routing Problem (CVRP)
                  utilizzando Google OR-Tools per ottimizzare i percorsi di consegna.
                </p>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 text-left">
                  <h3 className="font-semibold text-blue-800 mb-3">Come iniziare:</h3>
                  <ol className="space-y-2 text-sm text-blue-700">
                    <li className="flex items-start">
                      <span className="font-bold mr-2">1.</span>
                      <span>Configura la tua flotta (numero veicoli, capacità, deposito)</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-bold mr-2">2.</span>
                      <span>Imposta i parametri dell'algoritmo OR-Tools</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-bold mr-2">3.</span>
                      <span>Clicca "Importa da CRM" per caricare gli ordini simulati</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-bold mr-2">4.</span>
                      <span>Clicca "Ottimizza Percorsi" per calcolare le rotte ottimali</span>
                    </li>
                    <li className="flex items-start">
                      <span className="font-bold mr-2">5.</span>
                      <span>Visualizza i risultati sulla mappa interattiva</span>
                    </li>
                  </ol>
                </div>
              </div>
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="container mx-auto px-4 py-6">
          <div className="flex flex-col md:flex-row justify-between items-center text-sm text-gray-600">
            <p>
              © 2024 Routing Optimizer | Powered by Google OR-Tools & FastAPI
            </p>
            <div className="flex gap-4 mt-2 md:mt-0">
              <a href="#" className="hover:text-blue-600 transition-colors">Documentazione</a>
              <a href="#" className="hover:text-blue-600 transition-colors">GitHub</a>
              <a href="#" className="hover:text-blue-600 transition-colors">Supporto</a>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default App;
