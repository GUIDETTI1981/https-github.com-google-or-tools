/**
 * Vehicle Profiles Tab
 * Gestione template veicoli con tutti i parametri (costi, capacità, vincoli fisici)
 */
import React, { useState } from 'react';
import { useConfiguration } from '../../contexts/ConfigurationContext';
import { VehicleProfile } from '../../types/models';

const VehicleProfilesTab: React.FC = () => {
  const { vehicleProfiles, addVehicleProfile, updateVehicleProfile, deleteVehicleProfile } = useConfiguration();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  
  // Form State
  const [formData, setFormData] = useState<Partial<VehicleProfile>>({
    name: '',
    vehicle_type: 'van',
    capacity_kg: 1000,
    capacity_volume_m3: 10,
    cost_per_km: 0.5,
    cost_per_hour: 25,
    fixed_cost: 50,
    default_start_time: '08:00',
    default_end_time: '18:00',
    max_working_hours: 9,
    skills: [],
    physical_constraints: {
      height_meters: undefined,
      width_meters: undefined,
      length_meters: undefined,
      weight_kg: undefined,
      axle_load_kg: undefined,
      hazmat: false
    }
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    const profile: VehicleProfile = {
      id: editingId || `vehicle-${Date.now()}`,
      name: formData.name || 'Veicolo Senza Nome',
      vehicle_type: formData.vehicle_type || 'van',
      capacity_kg: formData.capacity_kg || 1000,
      capacity_volume_m3: formData.capacity_volume_m3,
      cost_per_km: formData.cost_per_km || 0.5,
      cost_per_hour: formData.cost_per_hour || 25,
      fixed_cost: formData.fixed_cost || 50,
      physical_constraints: formData.physical_constraints,
      default_start_time: formData.default_start_time,
      default_end_time: formData.default_end_time,
      max_working_hours: formData.max_working_hours,
      skills: formData.skills || [],
      created_at: editingId 
        ? vehicleProfiles.find(v => v.id === editingId)?.created_at || new Date().toISOString()
        : new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    if (editingId) {
      updateVehicleProfile(editingId, profile);
    } else {
      addVehicleProfile(profile);
    }

    resetForm();
  };

  const resetForm = () => {
    setFormData({
      name: '',
      vehicle_type: 'van',
      capacity_kg: 1000,
      capacity_volume_m3: 10,
      cost_per_km: 0.5,
      cost_per_hour: 25,
      fixed_cost: 50,
      default_start_time: '08:00',
      default_end_time: '18:00',
      max_working_hours: 9,
      skills: [],
      physical_constraints: {}
    });
    setShowForm(false);
    setEditingId(null);
  };

  const handleEdit = (profile: VehicleProfile) => {
    setFormData(profile);
    setEditingId(profile.id);
    setShowForm(true);
  };

  const getVehicleIcon = (type: string) => {
    switch (type) {
      case 'car': return '🚗';
      case 'van': return '🚐';
      case 'truck': return '🚚';
      default: return '🚛';
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">🚚 Modelli Veicoli</h2>
          <p className="text-sm text-gray-600 mt-1">
            Definisci i profili veicolo con capacità, costi e vincoli fisici (per Valhalla)
          </p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold"
        >
          ➕ Nuovo Modello
        </button>
      </div>

      {/* Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="sticky top-0 bg-white border-b px-6 py-4 flex items-center justify-between">
              <h3 className="text-xl font-bold">
                {editingId ? '✏️ Modifica Modello' : '➕ Nuovo Modello Veicolo'}
              </h3>
              <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 text-2xl">
                ✕
              </button>
            </div>

            <form onSubmit={handleSubmit} className="p-6 space-y-6">
              {/* Sezione 1: Informazioni Base */}
              <div className="bg-gray-50 p-4 rounded-md space-y-4">
                <h4 className="font-semibold text-gray-700 border-b pb-2">📋 Informazioni Base</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Nome Modello *
                    </label>
                    <input
                      type="text"
                      required
                      value={formData.name}
                      onChange={e => setFormData({...formData, name: e.target.value})}
                      placeholder="es. Furgone Grande, Camion 7.5t"
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Tipo Veicolo *
                    </label>
                    <select
                      value={formData.vehicle_type}
                      onChange={e => setFormData({...formData, vehicle_type: e.target.value as any})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="car">🚗 Auto (OSRM)</option>
                      <option value="van">🚐 Van (OSRM)</option>
                      <option value="truck">🚚 Camion (Valhalla + vincoli fisici)</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Sezione 2: Capacità */}
              <div className="bg-gray-50 p-4 rounded-md space-y-4">
                <h4 className="font-semibold text-gray-700 border-b pb-2">📦 Capacità</h4>
                
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Capacità Peso (kg) *
                    </label>
                    <input
                      type="number"
                      required
                      min="1"
                      value={formData.capacity_kg}
                      onChange={e => setFormData({...formData, capacity_kg: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Capacità Volume (m³)
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.1"
                      value={formData.capacity_volume_m3 || ''}
                      onChange={e => setFormData({...formData, capacity_volume_m3: parseFloat(e.target.value) || undefined})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Sezione 3: Costi Operativi */}
              <div className="bg-gray-50 p-4 rounded-md space-y-4">
                <h4 className="font-semibold text-gray-700 border-b pb-2">💰 Costi Operativi</h4>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      € per km *
                    </label>
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={formData.cost_per_km}
                      onChange={e => setFormData({...formData, cost_per_km: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      € per ora *
                    </label>
                    <input
                      type="number"
                      required
                      min="0"
                      step="0.01"
                      value={formData.cost_per_hour}
                      onChange={e => setFormData({...formData, cost_per_hour: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Costo Fisso €
                    </label>
                    <input
                      type="number"
                      min="0"
                      step="0.01"
                      value={formData.fixed_cost}
                      onChange={e => setFormData({...formData, fixed_cost: parseFloat(e.target.value)})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Sezione 4: Vincoli Fisici (Valhalla) */}
              {formData.vehicle_type === 'truck' && (
                <div className="bg-yellow-50 p-4 rounded-md space-y-4 border-l-4 border-yellow-500">
                  <h4 className="font-semibold text-gray-700 border-b pb-2">
                    🚧 Vincoli Fisici (Valhalla Truck Routing)
                  </h4>
                  
                  <div className="grid grid-cols-3 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Altezza (m)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        value={formData.physical_constraints?.height_meters || ''}
                        onChange={e => setFormData({
                          ...formData,
                          physical_constraints: {
                            ...formData.physical_constraints,
                            height_meters: parseFloat(e.target.value) || undefined
                          }
                        })}
                        placeholder="es. 3.5"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-yellow-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Larghezza (m)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        value={formData.physical_constraints?.width_meters || ''}
                        onChange={e => setFormData({
                          ...formData,
                          physical_constraints: {
                            ...formData.physical_constraints,
                            width_meters: parseFloat(e.target.value) || undefined
                          }
                        })}
                        placeholder="es. 2.5"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-yellow-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Lunghezza (m)
                      </label>
                      <input
                        type="number"
                        min="0"
                        step="0.1"
                        value={formData.physical_constraints?.length_meters || ''}
                        onChange={e => setFormData({
                          ...formData,
                          physical_constraints: {
                            ...formData.physical_constraints,
                            length_meters: parseFloat(e.target.value) || undefined
                          }
                        })}
                        placeholder="es. 7.5"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-yellow-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Peso Totale (kg)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={formData.physical_constraints?.weight_kg || ''}
                        onChange={e => setFormData({
                          ...formData,
                          physical_constraints: {
                            ...formData.physical_constraints,
                            weight_kg: parseFloat(e.target.value) || undefined
                          }
                        })}
                        placeholder="es. 7500"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-yellow-500"
                      />
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-1">
                        Carico Asse (kg)
                      </label>
                      <input
                        type="number"
                        min="0"
                        value={formData.physical_constraints?.axle_load_kg || ''}
                        onChange={e => setFormData({
                          ...formData,
                          physical_constraints: {
                            ...formData.physical_constraints,
                            axle_load_kg: parseFloat(e.target.value) || undefined
                          }
                        })}
                        placeholder="es. 3500"
                        className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-yellow-500"
                      />
                    </div>

                    <div className="flex items-center">
                      <label className="flex items-center cursor-pointer">
                        <input
                          type="checkbox"
                          checked={formData.physical_constraints?.hazmat || false}
                          onChange={e => setFormData({
                            ...formData,
                            physical_constraints: {
                              ...formData.physical_constraints,
                              hazmat: e.target.checked
                            }
                          })}
                          className="mr-2"
                        />
                        <span className="text-sm font-medium text-gray-700">
                          ☢️ Materiali Pericolosi (Hazmat)
                        </span>
                      </label>
                    </div>
                  </div>

                  <div className="text-xs text-gray-600 bg-white p-2 rounded">
                    💡 <strong>Valhalla</strong> userà questi vincoli per evitare ponti bassi, 
                    tunnel con restrizioni, strade strette incompatibili, ecc.
                  </div>
                </div>
              )}

              {/* Sezione 5: Orari Default */}
              <div className="bg-gray-50 p-4 rounded-md space-y-4">
                <h4 className="font-semibold text-gray-700 border-b pb-2">🕒 Orari Default</h4>
                
                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ora Partenza
                    </label>
                    <input
                      type="time"
                      value={formData.default_start_time || ''}
                      onChange={e => setFormData({...formData, default_start_time: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Ora Rientro
                    </label>
                    <input
                      type="time"
                      value={formData.default_end_time || ''}
                      onChange={e => setFormData({...formData, default_end_time: e.target.value})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">
                      Max Ore Lavoro
                    </label>
                    <input
                      type="number"
                      min="1"
                      max="24"
                      value={formData.max_working_hours || ''}
                      onChange={e => setFormData({...formData, max_working_hours: parseInt(e.target.value) || undefined})}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
              </div>

              {/* Actions */}
              <div className="flex justify-end gap-3 pt-4 border-t">
                <button
                  type="button"
                  onClick={resetForm}
                  className="px-6 py-2 border border-gray-300 rounded-md hover:bg-gray-50 font-medium"
                >
                  Annulla
                </button>
                <button
                  type="submit"
                  className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold"
                >
                  {editingId ? '💾 Salva Modifiche' : '➕ Crea Modello'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Lista Veicoli */}
      {vehicleProfiles.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-300">
          <div className="text-6xl mb-4">🚚</div>
          <h3 className="text-xl font-semibold text-gray-700 mb-2">
            Nessun Modello Veicolo
          </h3>
          <p className="text-gray-600 mb-4">
            Crea il primo profilo veicolo per iniziare
          </p>
          <button
            onClick={() => setShowForm(true)}
            className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold"
          >
            ➕ Crea Primo Modello
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {vehicleProfiles.map(profile => (
            <div key={profile.id} className="bg-white border border-gray-200 rounded-lg p-4 hover:shadow-lg transition-shadow">
              <div className="flex items-start justify-between mb-3">
                <div className="flex items-center gap-2">
                  <span className="text-3xl">{getVehicleIcon(profile.vehicle_type)}</span>
                  <div>
                    <h3 className="font-bold text-gray-800">{profile.name}</h3>
                    <span className="text-xs text-gray-500 uppercase">{profile.vehicle_type}</span>
                  </div>
                </div>
                <div className="flex gap-1">
                  <button
                    onClick={() => handleEdit(profile)}
                    className="text-blue-600 hover:bg-blue-50 p-1 rounded"
                    title="Modifica"
                  >
                    ✏️
                  </button>
                  <button
                    onClick={() => {
                      if (confirm(`Eliminare "${profile.name}"?`)) {
                        deleteVehicleProfile(profile.id);
                      }
                    }}
                    className="text-red-600 hover:bg-red-50 p-1 rounded"
                    title="Elimina"
                  >
                    🗑️
                  </button>
                </div>
              </div>

              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span className="text-gray-600">Capacità:</span>
                  <span className="font-semibold">{profile.capacity_kg} kg</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Costo/km:</span>
                  <span className="font-semibold">€{profile.cost_per_km.toFixed(2)}</span>
                </div>
                <div className="flex justify-between">
                  <span className="text-gray-600">Costo/ora:</span>
                  <span className="font-semibold">€{profile.cost_per_hour.toFixed(2)}</span>
                </div>
                
                {profile.vehicle_type === 'truck' && profile.physical_constraints && (
                  <div className="mt-3 pt-3 border-t border-gray-200">
                    <div className="text-xs text-gray-600 font-semibold mb-1">Vincoli Fisici:</div>
                    {profile.physical_constraints.height_meters && (
                      <div className="text-xs">📏 H: {profile.physical_constraints.height_meters}m</div>
                    )}
                    {profile.physical_constraints.weight_kg && (
                      <div className="text-xs">⚖️ {profile.physical_constraints.weight_kg}kg</div>
                    )}
                    {profile.physical_constraints.hazmat && (
                      <div className="text-xs text-orange-600 font-semibold">☢️ Hazmat</div>
                    )}
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default VehicleProfilesTab;
