/**
 * Main Application Component with React Router
 * 2-Page Architecture: Configuration & Setup + Daily Planning
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ConfigurationProvider } from './contexts/ConfigurationContext';
import Layout from './components/Layout';
import ConfigurationPage from './pages/ConfigurationPage';
import DailyPlanningPage from './pages/DailyPlanningPage';

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <ConfigurationProvider>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/planning" replace />} />
            <Route path="/config" element={<ConfigurationPage />} />
            <Route path="/planning" element={<DailyPlanningPage />} />
          </Routes>
        </Layout>
      </ConfigurationProvider>
    </BrowserRouter>
  );
};

export default App;
