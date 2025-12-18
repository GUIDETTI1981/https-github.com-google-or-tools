/**
 * Main Layout Component
 * Navigation bar con link alle 2 pagine principali
 */
import React from 'react';
import { Link, useLocation } from 'react-router-dom';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const location = useLocation();

  const isActive = (path: string) => location.pathname === path;

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      {/* Header with Navigation */}
      <header className="bg-white shadow-md sticky top-0 z-50">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            {/* Logo e Titolo */}
            <div className="flex items-center gap-3">
              <div className="text-4xl">🚚</div>
              <div>
                <h1 className="text-2xl font-bold text-gray-800">
                  VRP Optimizer Pro
                </h1>
                <p className="text-xs text-gray-600">
                  Powered by Google OR-Tools + Valhalla
                </p>
              </div>
            </div>

            {/* Navigation Tabs */}
            <nav className="flex gap-2">
              <Link
                to="/config"
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  isActive('/config')
                    ? 'bg-blue-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                ⚙️ Configurazione & Setup
              </Link>
              
              <Link
                to="/planning"
                className={`px-6 py-3 rounded-lg font-semibold transition-all ${
                  isActive('/planning')
                    ? 'bg-green-600 text-white shadow-lg'
                    : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                }`}
              >
                📋 Pianificazione Giornaliera
              </Link>
            </nav>

            {/* Status Indicator */}
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 bg-green-500 rounded-full animate-pulse" />
              <span className="text-sm text-gray-600">Sistema Operativo</span>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 mt-12">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between text-sm text-gray-600">
            <div>
              © 2024 VRP Optimizer Pro - Vehicle Routing Problem Solution
            </div>
            <div className="flex gap-4">
              <span>OR-Tools v9.8</span>
              <span>•</span>
              <span>Valhalla Routing</span>
              <span>•</span>
              <span>OSRM</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default Layout;
