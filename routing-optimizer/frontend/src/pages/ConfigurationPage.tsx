/**
 * Configuration & Setup Page
 * AREA 1: Admin / Set & Forget
 * Tabs: Veicoli | Depositi | OR-Tools | Skills & Zone
 */
import React, { useState } from 'react';
import { useConfiguration } from '../contexts/ConfigurationContext';
import VehicleProfilesTab from '../components/config/VehicleProfilesTab';
import DepotsTab from '../components/config/DepotsTab';
import ORToolsConfigTab from '../components/config/ORToolsConfigTab';
import SkillsZonesTab from '../components/config/SkillsZonesTab';

type TabType = 'vehicles' | 'depots' | 'ortools' | 'skills';

const ConfigurationPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<TabType>('vehicles');
  const config = useConfiguration();

  const tabs = [
    { id: 'vehicles' as TabType, icon: '🚚', label: 'Modelli Veicoli', count: config.vehicleProfiles.length },
    { id: 'depots' as TabType, icon: '📍', label: 'Depositi', count: config.depots.length },
    { id: 'ortools' as TabType, icon: '⚙️', label: 'OR-Tools', count: config.ortoolsConfigs.length },
    { id: 'skills' as TabType, icon: '🏷️', label: 'Skills & Zone', count: config.skills.length + config.zones.length }
  ];

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h1 className="text-3xl font-bold text-gray-800 mb-2">
          ⚙️ Configurazione & Setup
        </h1>
        <p className="text-gray-600">
          Area amministrativa - Definisci modelli e parametri tecnici (Set & Forget)
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="bg-white rounded-lg shadow-md p-2 flex gap-2">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`flex-1 px-4 py-3 rounded-md font-semibold transition-all ${
              activeTab === tab.id
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-gray-50 text-gray-700 hover:bg-gray-100'
            }`}
          >
            <span className="text-xl mr-2">{tab.icon}</span>
            {tab.label}
            <span className={`ml-2 px-2 py-0.5 rounded-full text-xs ${
              activeTab === tab.id ? 'bg-blue-500' : 'bg-gray-200'
            }`}>
              {tab.count}
            </span>
          </button>
        ))}
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow-md p-6">
        {activeTab === 'vehicles' && <VehicleProfilesTab />}
        {activeTab === 'depots' && <DepotsTab />}
        {activeTab === 'ortools' && <ORToolsConfigTab />}
        {activeTab === 'skills' && <SkillsZonesTab />}
      </div>

      {/* Quick Actions */}
      <div className="bg-blue-50 border-l-4 border-blue-500 p-4 rounded-md">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-semibold text-gray-800">💡 Suggerimento</h3>
            <p className="text-sm text-gray-600 mt-1">
              Configura questi parametri UNA VOLTA. Nella "Pianificazione Giornaliera" 
              dovrai solo caricare gli ordini e selezionare i veicoli disponibili.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              onClick={() => {
                const json = config.exportConfigurations();
                const blob = new Blob([json], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `vrp-config-${new Date().toISOString().split('T')[0]}.json`;
                a.click();
              }}
              className="px-4 py-2 bg-white border border-gray-300 rounded-md hover:bg-gray-50 text-sm font-medium"
            >
              📥 Esporta Config
            </button>
            <button
              onClick={() => {
                const input = document.createElement('input');
                input.type = 'file';
                input.accept = 'application/json';
                input.onchange = (e: any) => {
                  const file = e.target.files[0];
                  const reader = new FileReader();
                  reader.onload = (e: any) => {
                    try {
                      config.importConfigurations(e.target.result);
                      alert('✅ Configurazione importata con successo!');
                    } catch (error) {
                      alert('❌ Errore nell\'importazione: ' + error);
                    }
                  };
                  reader.readAsText(file);
                };
                input.click();
              }}
              className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 text-sm font-medium"
            >
              📤 Importa Config
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigurationPage;
