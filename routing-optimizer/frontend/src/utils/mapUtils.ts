/**
 * Map Utilities
 */
import type { LatLngExpression } from 'leaflet';
import type { Order, RouteStop } from '../types';

/**
 * Converte un ordine in coordinate Leaflet
 */
export const orderToLatLng = (order: Order): LatLngExpression => {
  return [order.latitude, order.longitude];
};

/**
 * Converte una fermata in coordinate Leaflet
 */
export const stopToLatLng = (stop: RouteStop): LatLngExpression => {
  return [stop.latitude, stop.longitude];
};

/**
 * Calcola il centro della mappa basato sugli ordini
 */
export const calculateMapCenter = (orders: Order[]): LatLngExpression => {
  if (orders.length === 0) {
    return [41.9028, 12.4964]; // Roma default
  }

  const avgLat = orders.reduce((sum, order) => sum + order.latitude, 0) / orders.length;
  const avgLng = orders.reduce((sum, order) => sum + order.longitude, 0) / orders.length;

  return [avgLat, avgLng];
};

/**
 * Formatta la distanza in modo leggibile
 */
export const formatDistance = (km: number): string => {
  if (km < 1) {
    return `${Math.round(km * 1000)} m`;
  }
  return `${km.toFixed(2)} km`;
};

/**
 * Formatta il peso in modo leggibile
 */
export const formatWeight = (kg: number): string => {
  return `${kg.toFixed(2)} kg`;
};
