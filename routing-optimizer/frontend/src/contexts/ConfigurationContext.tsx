/**
 * Configuration Context
 * Gestione stato globale per AREA 1: Configurazione & Setup
 * Persistenza su LocalStorage
 */
import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';
import {
  VehicleProfile,
  DepotProfile,
  ORToolsConfiguration,
  SkillDefinition,
  ZoneDefinition,
  RoutingEngineConfig
} from '../types/models';

interface ConfigurationContextType {
  // Vehicle Profiles
  vehicleProfiles: VehicleProfile[];
  addVehicleProfile: (profile: VehicleProfile) => void;
  updateVehicleProfile: (id: string, profile: Partial<VehicleProfile>) => void;
  deleteVehicleProfile: (id: string) => void;
  
  // Depots
  depots: DepotProfile[];
  addDepot: (depot: DepotProfile) => void;
  updateDepot: (id: string, depot: Partial<DepotProfile>) => void;
  deleteDepot: (id: string) => void;
  getDefaultDepot: () => DepotProfile | undefined;
  
  // OR-Tools Configurations
  ortoolsConfigs: ORToolsConfiguration[];
  addORToolsConfig: (config: ORToolsConfiguration) => void;
  updateORToolsConfig: (id: string, config: Partial<ORToolsConfiguration>) => void;
  deleteORToolsConfig: (id: string) => void;
  getDefaultORToolsConfig: () => ORToolsConfiguration | undefined;
  
  // Skills
  skills: SkillDefinition[];
  addSkill: (skill: SkillDefinition) => void;
  deleteSkill: (id: string) => void;
  
  // Zones
  zones: ZoneDefinition[];
  addZone: (zone: ZoneDefinition) => void;
  deleteZone: (id: string) => void;
  
  // Routing Engine Config
  routingEngineConfig: RoutingEngineConfig;
  updateRoutingEngineConfig: (config: Partial<RoutingEngineConfig>) => void;
  
  // Utility
  clearAllConfigurations: () => void;
  exportConfigurations: () => string;
  importConfigurations: (json: string) => void;
}

const ConfigurationContext = createContext<ConfigurationContextType | undefined>(undefined);

// LocalStorage Keys
const STORAGE_KEYS = {
  VEHICLE_PROFILES: 'vrp_vehicle_profiles',
  DEPOTS: 'vrp_depots',
  ORTOOLS_CONFIGS: 'vrp_ortools_configs',
  SKILLS: 'vrp_skills',
  ZONES: 'vrp_zones',
  ROUTING_ENGINE: 'vrp_routing_engine'
};

// Default Configurations
const DEFAULT_ROUTING_ENGINE: RoutingEngineConfig = {
  use_osrm: true,
  use_valhalla: true,
  osrm_host: 'http://localhost:5000',
  valhalla_host: 'http://localhost:8002'
};

const DEFAULT_DEPOT: DepotProfile = {
  id: 'depot-default',
  name: 'Deposito Centrale',
  latitude: 41.9028,
  longitude: 12.4964,
  address: 'Roma, Italia',
  opening_time: '07:00',
  closing_time: '20:00',
  is_default: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

const DEFAULT_ORTOOLS_CONFIG: ORToolsConfiguration = {
  id: 'ortools-default',
  name: 'Configurazione Standard',
  time_limit_seconds: 30,
  first_solution_strategy: 'PATH_CHEAPEST_ARC',
  local_search_metaheuristic: 'GUIDED_LOCAL_SEARCH',
  penalty_dropped_order: 10000,
  penalty_late_delivery: 100,
  is_default: true,
  created_at: new Date().toISOString(),
  updated_at: new Date().toISOString()
};

export const ConfigurationProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  // State
  const [vehicleProfiles, setVehicleProfiles] = useState<VehicleProfile[]>([]);
  const [depots, setDepots] = useState<DepotProfile[]>([DEFAULT_DEPOT]);
  const [ortoolsConfigs, setORToolsConfigs] = useState<ORToolsConfiguration[]>([DEFAULT_ORTOOLS_CONFIG]);
  const [skills, setSkills] = useState<SkillDefinition[]>([]);
  const [zones, setZones] = useState<ZoneDefinition[]>([]);
  const [routingEngineConfig, setRoutingEngineConfig] = useState<RoutingEngineConfig>(DEFAULT_ROUTING_ENGINE);

  // Load from LocalStorage on mount
  useEffect(() => {
    loadFromLocalStorage();
  }, []);

  // Save to LocalStorage on state changes
  useEffect(() => {
    saveToLocalStorage();
  }, [vehicleProfiles, depots, ortoolsConfigs, skills, zones, routingEngineConfig]);

  const loadFromLocalStorage = () => {
    try {
      const storedProfiles = localStorage.getItem(STORAGE_KEYS.VEHICLE_PROFILES);
      if (storedProfiles) setVehicleProfiles(JSON.parse(storedProfiles));

      const storedDepots = localStorage.getItem(STORAGE_KEYS.DEPOTS);
      if (storedDepots) setDepots(JSON.parse(storedDepots));

      const storedConfigs = localStorage.getItem(STORAGE_KEYS.ORTOOLS_CONFIGS);
      if (storedConfigs) setORToolsConfigs(JSON.parse(storedConfigs));

      const storedSkills = localStorage.getItem(STORAGE_KEYS.SKILLS);
      if (storedSkills) setSkills(JSON.parse(storedSkills));

      const storedZones = localStorage.getItem(STORAGE_KEYS.ZONES);
      if (storedZones) setZones(JSON.parse(storedZones));

      const storedRoutingEngine = localStorage.getItem(STORAGE_KEYS.ROUTING_ENGINE);
      if (storedRoutingEngine) setRoutingEngineConfig(JSON.parse(storedRoutingEngine));
    } catch (error) {
      console.error('Error loading from LocalStorage:', error);
    }
  };

  const saveToLocalStorage = () => {
    try {
      localStorage.setItem(STORAGE_KEYS.VEHICLE_PROFILES, JSON.stringify(vehicleProfiles));
      localStorage.setItem(STORAGE_KEYS.DEPOTS, JSON.stringify(depots));
      localStorage.setItem(STORAGE_KEYS.ORTOOLS_CONFIGS, JSON.stringify(ortoolsConfigs));
      localStorage.setItem(STORAGE_KEYS.SKILLS, JSON.stringify(skills));
      localStorage.setItem(STORAGE_KEYS.ZONES, JSON.stringify(zones));
      localStorage.setItem(STORAGE_KEYS.ROUTING_ENGINE, JSON.stringify(routingEngineConfig));
    } catch (error) {
      console.error('Error saving to LocalStorage:', error);
    }
  };

  // Vehicle Profiles
  const addVehicleProfile = (profile: VehicleProfile) => {
    setVehicleProfiles(prev => [...prev, profile]);
  };

  const updateVehicleProfile = (id: string, updates: Partial<VehicleProfile>) => {
    setVehicleProfiles(prev =>
      prev.map(p => p.id === id ? { ...p, ...updates, updated_at: new Date().toISOString() } : p)
    );
  };

  const deleteVehicleProfile = (id: string) => {
    setVehicleProfiles(prev => prev.filter(p => p.id !== id));
  };

  // Depots
  const addDepot = (depot: DepotProfile) => {
    setDepots(prev => [...prev, depot]);
  };

  const updateDepot = (id: string, updates: Partial<DepotProfile>) => {
    setDepots(prev =>
      prev.map(d => d.id === id ? { ...d, ...updates, updated_at: new Date().toISOString() } : d)
    );
  };

  const deleteDepot = (id: string) => {
    setDepots(prev => prev.filter(d => d.id !== id));
  };

  const getDefaultDepot = () => depots.find(d => d.is_default) || depots[0];

  // OR-Tools Configs
  const addORToolsConfig = (config: ORToolsConfiguration) => {
    setORToolsConfigs(prev => [...prev, config]);
  };

  const updateORToolsConfig = (id: string, updates: Partial<ORToolsConfiguration>) => {
    setORToolsConfigs(prev =>
      prev.map(c => c.id === id ? { ...c, ...updates, updated_at: new Date().toISOString() } : c)
    );
  };

  const deleteORToolsConfig = (id: string) => {
    setORToolsConfigs(prev => prev.filter(c => c.id !== id));
  };

  const getDefaultORToolsConfig = () => ortoolsConfigs.find(c => c.is_default) || ortoolsConfigs[0];

  // Skills
  const addSkill = (skill: SkillDefinition) => {
    setSkills(prev => [...prev, skill]);
  };

  const deleteSkill = (id: string) => {
    setSkills(prev => prev.filter(s => s.id !== id));
  };

  // Zones
  const addZone = (zone: ZoneDefinition) => {
    setZones(prev => [...prev, zone]);
  };

  const deleteZone = (id: string) => {
    setZones(prev => prev.filter(z => z.id !== id));
  };

  // Routing Engine
  const updateRoutingEngineConfig = (updates: Partial<RoutingEngineConfig>) => {
    setRoutingEngineConfig(prev => ({ ...prev, ...updates }));
  };

  // Utility
  const clearAllConfigurations = () => {
    setVehicleProfiles([]);
    setDepots([DEFAULT_DEPOT]);
    setORToolsConfigs([DEFAULT_ORTOOLS_CONFIG]);
    setSkills([]);
    setZones([]);
    setRoutingEngineConfig(DEFAULT_ROUTING_ENGINE);
    localStorage.clear();
  };

  const exportConfigurations = () => {
    return JSON.stringify({
      vehicleProfiles,
      depots,
      ortoolsConfigs,
      skills,
      zones,
      routingEngineConfig
    }, null, 2);
  };

  const importConfigurations = (json: string) => {
    try {
      const data = JSON.parse(json);
      if (data.vehicleProfiles) setVehicleProfiles(data.vehicleProfiles);
      if (data.depots) setDepots(data.depots);
      if (data.ortoolsConfigs) setORToolsConfigs(data.ortoolsConfigs);
      if (data.skills) setSkills(data.skills);
      if (data.zones) setZones(data.zones);
      if (data.routingEngineConfig) setRoutingEngineConfig(data.routingEngineConfig);
    } catch (error) {
      console.error('Error importing configurations:', error);
      throw new Error('Invalid JSON format');
    }
  };

  const value: ConfigurationContextType = {
    vehicleProfiles,
    addVehicleProfile,
    updateVehicleProfile,
    deleteVehicleProfile,
    depots,
    addDepot,
    updateDepot,
    deleteDepot,
    getDefaultDepot,
    ortoolsConfigs,
    addORToolsConfig,
    updateORToolsConfig,
    deleteORToolsConfig,
    getDefaultORToolsConfig,
    skills,
    addSkill,
    deleteSkill,
    zones,
    addZone,
    deleteZone,
    routingEngineConfig,
    updateRoutingEngineConfig,
    clearAllConfigurations,
    exportConfigurations,
    importConfigurations
  };

  return (
    <ConfigurationContext.Provider value={value}>
      {children}
    </ConfigurationContext.Provider>
  );
};

export const useConfiguration = () => {
  const context = useContext(ConfigurationContext);
  if (!context) {
    throw new Error('useConfiguration must be used within ConfigurationProvider');
  }
  return context;
};
