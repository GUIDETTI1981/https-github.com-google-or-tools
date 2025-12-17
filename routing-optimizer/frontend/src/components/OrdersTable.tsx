/**
 * Orders Table Component
 * Tabella per visualizzare gli ordini importati dal CRM
 */
import React from 'react';
import type { Order } from '../types';

interface OrdersTableProps {
  orders: Order[];
}

const OrdersTable: React.FC<OrdersTableProps> = ({ orders }) => {
  if (orders.length === 0) {
    return (
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h3 className="text-lg font-semibold text-gray-700 mb-4">
          📦 Ordini Importati
        </h3>
        <div className="text-center py-8 text-gray-500">
          <p className="text-lg">Nessun ordine importato</p>
          <p className="text-sm mt-2">Clicca su "Importa da CRM" per caricare gli ordini</p>
        </div>
      </div>
    );
  }

  const totalDemand = orders.reduce((sum, order) => sum + order.demand, 0);

  return (
    <div className="bg-white rounded-lg shadow-lg p-6">
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold text-gray-700">
          📦 Ordini Importati ({orders.length})
        </h3>
        <div className="text-sm text-gray-600">
          <span className="font-semibold">Peso Totale:</span> {totalDemand.toFixed(2)} kg
        </div>
      </div>

      <div className="overflow-x-auto max-h-96 overflow-y-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0">
            <tr>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ID Ordine
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Cliente
              </th>
              <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Coordinate
              </th>
              <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Peso (kg)
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {orders.map((order) => (
              <tr key={order.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-4 py-3 whitespace-nowrap text-sm font-medium text-gray-900">
                  {order.id}
                </td>
                <td className="px-4 py-3 text-sm text-gray-700">
                  {order.customer_name}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-gray-500 font-mono">
                  {order.latitude.toFixed(4)}, {order.longitude.toFixed(4)}
                </td>
                <td className="px-4 py-3 whitespace-nowrap text-sm text-right font-semibold text-gray-900">
                  {order.demand.toFixed(2)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default OrdersTable;
