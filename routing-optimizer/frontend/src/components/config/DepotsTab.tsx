/**
 * Depots Tab - Gestione Depositi
 */
import React, { useState } from 'react';
import { useConfiguration } from '../../contexts/ConfigurationContext';
import { DepotProfile } from '../../types/models';

const DepotsTab: React.FC = () => {
  const { depots, addDepot, updateDepot, deleteDepot } = useConfiguration();
  const [showForm, setShowForm] = useState(false);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [formData, setFormData] = useState<Partial<DepotProfile>>({
    name: '',
    latitude: 41.9028,
    longitude: 12.4964,
    address: '',
    opening_time: '07:00',
    closing_time: '20:00',
    is_default: false
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const depot: DepotProfile = {
      id: editingId || `depot-${Date.now()}`,
      name: formData.name || 'Deposito',
      latitude: formData.latitude || 0,
      longitude: formData.longitude || 0,
      address: formData.address,
      opening_time: formData.opening_time || '07:00',
      closing_time: formData.closing_time || '20:00',
      is_default: formData.is_default || false,
      created_at: editingId ? depots.find(d => d.id === editingId)?.created_at || new Date().toISOString() : new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    if (editingId) {
      updateDepot(editingId, depot);
    } else {
      addDepot(depot);
    }
    resetForm();
  };

  const resetForm = () => {
    setFormData({ name: '', latitude: 41.9028, longitude: 12.4964, address: '', opening_time: '07:00', closing_time: '20:00', is_default: false });
    setShowForm(false);
    setEditingId(null);
  };

  const handleEdit = (depot: DepotProfile) => {
    setFormData(depot);
    setEditingId(depot.id);
    setShowForm(true);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-gray-800">📍 Depositi</h2>
          <p className="text-sm text-gray-600 mt-1">Configura i depositi con coordinate e orari operativi</p>
        </div>
        <button onClick={() => setShowForm(true)} className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 font-semibold">➕ Nuovo Deposito</button>
      </div>

      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full">
            <div className="px-6 py-4 border-b flex items-center justify-between">
              <h3 className="text-xl font-bold">{editingId ? '✏️ Modifica Deposito' : '➕ Nuovo Deposito'}</h3>
              <button onClick={resetForm} className="text-gray-500 hover:text-gray-700 text-2xl">✕</button>
            </div>
            <form onSubmit={handleSubmit} className="p-6 space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Nome Deposito *</label>
                  <input type="text" required value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Latitudine *</label>
                  <input type="number" required step="0.000001" value={formData.latitude} onChange={e => setFormData({...formData, latitude: parseFloat(e.target.value)})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Longitudine *</label>
                  <input type="number" required step="0.000001" value={formData.longitude} onChange={e => setFormData({...formData, longitude: parseFloat(e.target.value)})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div className="col-span-2">
                  <label className="block text-sm font-medium text-gray-700 mb-1">Indirizzo</label>
                  <input type="text" value={formData.address} onChange={e => setFormData({...formData, address: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Apertura</label>
                  <input type="time" value={formData.opening_time} onChange={e => setFormData({...formData, opening_time: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Chiusura</label>
                  <input type="time" value={formData.closing_time} onChange={e => setFormData({...formData, closing_time: e.target.value})} className="w-full px-3 py-2 border rounded-md" />
                </div>
                <div className="col-span-2">
                  <label className="flex items-center cursor-pointer">
                    <input type="checkbox" checked={formData.is_default || false} onChange={e => setFormData({...formData, is_default: e.target.checked})} className="mr-2" />
                    <span className="text-sm font-medium">Imposta come deposito predefinito</span>
                  </label>
                </div>
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
        {depots.map(depot => (
          <div key={depot.id} className={`border rounded-lg p-4 ${depot.is_default ? 'border-blue-500 bg-blue-50' : 'border-gray-200 bg-white'}`}>
            <div className="flex justify-between items-start mb-2">
              <div>
                <h3 className="font-bold text-gray-800 flex items-center gap-2">
                  {depot.name}
                  {depot.is_default && <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded">DEFAULT</span>}
                </h3>
                {depot.address && <p className="text-sm text-gray-600">{depot.address}</p>}
              </div>
              <div className="flex gap-1">
                <button onClick={() => handleEdit(depot)} className="text-blue-600 hover:bg-blue-100 p-1 rounded">✏️</button>
                <button onClick={() => confirm(`Eliminare "${depot.name}"?`) && deleteDepot(depot.id)} className="text-red-600 hover:bg-red-100 p-1 rounded">🗑️</button>
              </div>
            </div>
            <div className="text-sm space-y-1">
              <div><span className="text-gray-600">📍 Coordinate:</span> <span className="font-mono text-xs">{depot.latitude.toFixed(6)}, {depot.longitude.toFixed(6)}</span></div>
              <div><span className="text-gray-600">🕒 Orari:</span> <span className="font-semibold">{depot.opening_time} - {depot.closing_time}</span></div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default DepotsTab;
