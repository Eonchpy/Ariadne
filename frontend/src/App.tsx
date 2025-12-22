import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthLayout } from './layouts/AuthLayout';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import { ConfigProvider } from 'antd';

const App: React.FC = () => {
  return (
    <ConfigProvider
      theme={{
        token: {
          colorPrimary: '#1890ff',
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route element={<AuthLayout />}>
            <Route path="/login" element={<LoginPage />} />
          </Route>

          {/* Protected Routes */}
          <Route element={<ProtectedRoute />}>
            <Route element={<MainLayout />}>
              <Route path="/" element={<div>Dashboard Placeholder</div>} />
              <Route path="/sources" element={<div>Sources Placeholder</div>} />
              <Route path="/metadata/tables" element={<div>Tables Placeholder</div>} />
              <Route path="/metadata/fields" element={<div>Fields Placeholder</div>} />
              <Route path="/lineage" element={<div>Lineage Placeholder</div>} />
              <Route path="/import" element={<div>Import Placeholder</div>} />
              <Route path="/ai" element={<div>AI Placeholder</div>} />
            </Route>
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
};

export default App;