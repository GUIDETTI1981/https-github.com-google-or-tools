/**
 * Results Map Component
 * Mappa interattiva con Leaflet per visualizzare i percorsi ottimizzati
 */
import React from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, Circle } from 'react-leaflet';
import L from 'leaflet';
import type { OptimizationResult, Order } from '../types';
import { stopToLatLng, formatDistance, formatWeight } from '../utils/mapUtils';

// Fix per le icone di Leaflet
import 'leaflet/dist/leaflet.css';
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
  iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
});

interface ResultsMapProps {
  result: OptimizationResult | null;
  orders: Order[];
  depotLat: number;
  depotLon: number;
}

const ResultsMap: React.FC<ResultsMapProps> = ({ result, orders, depotLat, depotLon }) => {
  // Calcola il centro della mappa
  const mapCenter: [number, number] = orders.length > 0
    ? [
        orders.reduce((sum, o) => sum + o.latitude, 0) / orders.length,
        orders.reduce((sum, o) => sum + o.longitude, 0) / orders.length
      ]
    : [depotLat, depotLon];

  // Icona personalizzata per il deposito
  const depotIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-red.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  // Icone personalizzate per i clienti
  const customerIcon = new L.Icon({
    iconUrl: 'https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-blue.png',
    shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    iconSize: [25, 41],
    iconAnchor: [12, 41],
    popupAnchor: [1, -34],
    shadowSize: [41, 41]
  });

  return (
    <div className="bg-white rounded-lg shadow-lg overflow-hidden" style={{ height: '600px' }}>
      <MapContainer
        center={mapCenter}
        zoom={12}
        style={{ height: '100%', width: '100%' }}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />

        {/* Marker del Deposito */}
        <Marker position={[depotLat, depotLon]} icon={depotIcon}>
          <Popup>
            <div className="p-2">
              <h4 className="font-bold text-red-600">🏢 Deposito Centrale</h4>
              <p className="text-xs text-gray-600">
                {depotLat.toFixed(4)}, {depotLon.toFixed(4)}
              </p>
            </div>
          </Popup>
        </Marker>

        {/* Cerchio intorno al deposito */}
        <Circle
          center={[depotLat, depotLon]}
          radius={500}
          pathOptions={{ color: 'red', fillColor: 'red', fillOpacity: 0.1 }}
        />

        {/* Se non ci sono risultati, mostra solo i marker dei clienti */}
        {!result && orders.map((order) => (
          <Marker
            key={order.id}
            position={[order.latitude, order.longitude]}
            icon={customerIcon}
          >
            <Popup>
              <div className="p-2">
                <h4 className="font-bold text-blue-600">{order.customer_name}</h4>
                <p className="text-xs text-gray-600">ID: {order.id}</p>
                <p className="text-xs text-gray-600">Peso: {order.demand.toFixed(2)} kg</p>
                <p className="text-xs text-gray-600 font-mono">
                  {order.latitude.toFixed(4)}, {order.longitude.toFixed(4)}
                </p>
              </div>
            </Popup>
          </Marker>
        ))}

        {/* Visualizza i percorsi ottimizzati */}
        {result && result.routes.map((route) => {
          const positions = route.stops.map(stopToLatLng);
          
          return (
            <React.Fragment key={route.vehicle_id}>
              {/* Polilinea del percorso */}
              <Polyline
                positions={positions}
                pathOptions={{
                  color: route.color,
                  weight: 4,
                  opacity: 0.7
                }}
              />

              {/* Marker per ogni fermata */}
              {route.stops.map((stop, idx) => {
                if (stop.is_depot) {
                  return null; // Il deposito è già visualizzato
                }

                // Crea icona colorata per il veicolo
                const vehicleIcon = new L.Icon({
                  iconUrl: `https://raw.githubusercontent.com/pointhi/leaflet-color-markers/master/img/marker-icon-2x-green.png`,
                  shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                  iconSize: [25, 41],
                  iconAnchor: [12, 41],
                  popupAnchor: [1, -34],
                  shadowSize: [41, 41]
                });

                return (
                  <Marker
                    key={`${route.vehicle_id}-${idx}`}
                    position={stopToLatLng(stop)}
                    icon={vehicleIcon}
                  >
                    <Popup>
                      <div className="p-2">
                        <h4 className="font-bold" style={{ color: route.color }}>
                          🚚 Veicolo {route.vehicle_id}
                        </h4>
                        <p className="font-semibold text-gray-800">{stop.customer_name}</p>
                        <p className="text-xs text-gray-600">Stop #{idx}</p>
                        {stop.order_id && (
                          <p className="text-xs text-gray-600">ID: {stop.order_id}</p>
                        )}
                        <p className="text-xs text-gray-600">
                          Peso consegna: {formatWeight(stop.demand)}
                        </p>
                        <p className="text-xs text-gray-600">
                          Carico cumulativo: {formatWeight(stop.cumulative_load)}
                        </p>
                      </div>
                    </Popup>
                  </Marker>
                );
              })}
            </React.Fragment>
          );
        })}
      </MapContainer>
    </div>
  );
};

export default ResultsMap;
