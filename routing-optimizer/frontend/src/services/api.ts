/**
 * API Service - Communication with FastAPI Backend
 */
import axios from 'axios';
import type {
  CRMOrdersResponse,
  OptimizationRequest,
  OptimizationResult,
  ConfigStrategies
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 120000, // 2 minuti per ottimizzazioni complesse
});

/**
 * Recupera gli ordini dal CRM simulato
 */
export const fetchCRMOrders = async (numOrders: number = 20): Promise<CRMOrdersResponse> => {
  const response = await api.get<CRMOrdersResponse>(`/api/crm/orders?num_orders=${numOrders}`);
  return response.data;
};

/**
 * Esegue l'ottimizzazione dei percorsi
 */
export const optimizeRoutes = async (request: OptimizationRequest): Promise<OptimizationResult> => {
  const response = await api.post<OptimizationResult>('/api/optimize', request);
  return response.data;
};

/**
 * Recupera le strategie disponibili
 */
export const fetchAvailableStrategies = async (): Promise<ConfigStrategies> => {
  const response = await api.get<ConfigStrategies>('/api/config/strategies');
  return response.data;
};

/**
 * Health check
 */
export const healthCheck = async (): Promise<{ status: string }> => {
  const response = await api.get('/health');
  return response.data;
};

export default api;
