/**
 * OR-Tools Configuration Tab
 */
import React, { useState, useEffect } from 'react';
import { useConfiguration } from '../../contexts/ConfigurationContext';
import { ORToolsConfiguration, FirstSolutionStrategy, LocalSearchMetaheuristic } from '../../types/models';
import { fetchAvailableStrategies } from '../../services/api';

const ORToolsConfigTab: React.FC = () => {
  const { ortoolsConfigs, addORToolsConfig, updateORToolsConfig, deleteORToolsConfig } = useConfiguration();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [strategies, setStrategies] = useState<any>(null);
  
  const [formData, setFormData] = useState<Partial<ORToolsConfiguration>>({
    name: '',
    time_limit_seconds: 30,
    first_solution_strategy: 'PATH_CHEAPEST_ARC',
    local_search_metaheuristic: 'GUIDED_LOCAL_SEARCH',
    penalty_dropped_order: 10000,
    penalty_late_delivery: 100,
    is_default: false
  });

  useEffect(() => {
    fetchAvailableStrategies().then(setStrategies).catch(console.error);
  }, []);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const config: ORToolsConfiguration = {
      id: editingId || `ortools-${Date.now()}`,
      name: formData.name || 'Config',
      time_limit_seconds: formData.time_limit_seconds || 30,
      first_solution_strategy: formData.first_solution_strategy as FirstSolutionStrategy,
      local_search_metaheuristic: formData.local_search_metaheuristic as LocalSearchMetaheuristic,
      penalty_dropped_order: formData.penalty_dropped_order,
      penalty_late_delivery: formData.penalty_late_delivery,
      use_depth_first_search: formData.use_depth_first_search,
      optimization_step: formData.optimization_step,
      is_default: formData.is_default || false,
      created_at: editingId ? ortoolsConfigs.find(c => c.id === editingId)?.created_at || new Date().toISOString() : new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    if (editingId) {
      updateORToolsConfig(editingId, config);
    } else {
      addORToolsConfig(config);
    }
    resetForm();
  };

  const resetForm = () => {
    setFormData({ name: '', time_limit_seconds: 30, first_solution_strategy: 'PATH_CHEAPEST_ARC', local_search_metaheuristic: 'GUIDED_LOCAL_SEARCH', penalty_dropped_order: 10000, penalty_late_delivery: 100, is_default: false });
    setShowForm(false);
    setEditingId(null);
  };

  const handleEdit = (config: ORToolsConfiguration) => {
    setFormData(config);
    setEditingId(config.id);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">⚙️ Configurazioni OR-Tools</h2>
          <p className="text-sm text-gray-600 mt-1">Parametri algoritmo di ottimizzazione</p>
        </div>
        <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold">➕ Nuova Config</button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-xl font-bold">{editingId ? '✏️ Modifica Config' : '➕ Nuova Configurazione'}</h3>
              <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 text-2xl">✕</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Nome Configurazione *</label>
                <input type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="es. Configurazione Veloce, Ottimale" className="w-full px-3 py-2 border rounded-md" />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Time Limit (secondi) *</label>
                  <input type="number" required min="1" max="600" value={formData.time_limit_seconds} onChange={e => setFormData({...formData, time_limit_seconds: parseInt(e.target.value)})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Optimization Step</label>
                  <input type="number" min="1" value={formData.optimization_step || ''} onChange={e => setFormData({...formData, optimization_step: parseInt(e.target.value) || undefined})} className="w-full px-3 py-2 border rounded-md" />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">First Solution Strategy *</label>
                <select value={formData.first_solution_strategy} onChange={e => setFormData({...formData, first_solution_strategy: e.target.value as any})} className="w-full px-3 py-2 border rounded-md">
                  {strategies?.first_solution_strategies.map((s: any) => (
                    <option key={s.value} value={s.value}>{s.label}</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Local Search Metaheuristic *</label>
                <select value={formData.local_search_metaheuristic} onChange={e => setFormData({...formData, local_search_metaheuristic: e.target.value as any})} className="w-full px-3 py-2 border rounded-md">
                  {strategies?.local_search_metaheuristics.map((m: any) => (
                    <option key={m.value} value={m.value}>{m.label}</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Penalità Ordine Non Servito</label>
                  <input type="number" min="0" value={formData.penalty_dropped_order || ''} onChange={e => setFormData({...formData, penalty_dropped_order: parseFloat(e.target.value) || undefined})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Penalità Ritardo</label>
                  <input type="number" min="0" value={formData.penalty_late_delivery || ''} onChange={e => setFormData({...formData, penalty_late_delivery: parseFloat(e.target.value) || undefined})} className="w-full px-3 py-2 border rounded-md" />
                </div>
              </div>

              <div>
                <label className="flex items-center cursor-pointer">
                  <input type="checkbox" checked={formData.use_depth_first_search || false} onChange={e => setFormData({...formData, use_depth_first_search: e.target.checked})} className="mr-2" />
                  <span className="text-sm font-medium">Usa Depth-First Search</span>
                </label>
              </div>

              <div>
                <label className="flex items-center cursor-pointer">
                  <input type="checkbox" checked={formData.is_default || false} onChange={e => setFormData({...formData, is_default: e.target.checked})} className="mr-2" />
                  <span className="text-sm font-medium">Imposta come configurazione predefinita</span>
                </label>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t">
                <button type="button" onClick={resetForm} className="px-6 py-2 border rounded-md hover:bg-gray-50">Annulla</button>
                <button type="submit" className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold">{editingId ? '💾 Salva' : '➕ Crea'}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {ortoolsConfigs.map(config => (
          <div key={config.id} className={`border rounded-lg p-4 ${config.is_default ? 'border-green-500 bg-green-50' : 'border-gray-200 bg-white'}`}>
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-bold text-gray-800 flex items-center gap-2">
                {config.name}
                {config.is_default && <span className="text-xs bg-green-600 text-white px-2 py-0.5 rounded">DEFAULT</span>}
              </h3>
              <div className="flex gap-1">
                <button onClick={() => handleEdit(config)} className="text-blue-600 hover:bg-blue-100 p-1 rounded">✏️</button>
                <button onClick={() => confirm(`Eliminare "${config.name}"?`) && deleteORToolsConfig(config.id)} className="text-red-600 hover:bg-red-100 p-1 rounded">🗑️</button>
              </div>
            </div>
            <div className="text-sm space-y-1">
              <div><span className="text-gray-600">⏱️ Time Limit:</span> <span className="font-semibold">{config.time_limit_seconds}s</span></div>
              <div><span className="text-gray-600">🎯 Strategy:</span> <span className="text-xs font-mono">{config.first_solution_strategy}</span></div>
              <div><span className="text-gray-600">🔍 Metaheuristic:</span> <span className="text-xs font-mono">{config.local_search_metaheuristic}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default ORToolsConfigTab;
