import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthLayout } from './layouts/AuthLayout';
import { MainLayout } from './layouts/MainLayout';
import { LoginPage } from './pages/auth/LoginPage';
import { ProtectedRoute } from './components/common/ProtectedRoute';
import DataSourceForm from './pages/DataSources/DataSourceForm';
import DataSourcesList from './pages/DataSources/DataSourcesList';
import TableForm from './pages/Tables/TableForm';
import TablesList from './pages/Tables/TablesList';
import TableDetailPage from './pages/Tables/TableDetailPage';
import LineageGraph from './pages/Lineage/LineageGraph';
import BulkOperations from './pages/Bulk/BulkOperations';
import TagManagement from './pages/Settings/TagManagement';
import Dashboard from './pages/Dashboard/Dashboard';
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
              <Route path="/" element={<Dashboard />} />
              <Route path="/sources" element={<DataSourcesList />} />
              <Route path="/sources/new" element={<DataSourceForm />} />
              <Route path="/sources/:id/edit" element={<DataSourceForm />} />
              <Route path="/metadata/tables" element={<TablesList />} />
              <Route path="/metadata/tables/:id" element={<TableDetailPage />} />
              <Route path="/metadata/tables/new" element={<TableForm />} />
              <Route path="/metadata/tables/:id/edit" element={<TableForm />} />
              <Route path="/lineage" element={<LineageGraph />} />
              <Route path="/lineage/:tableId" element={<LineageGraph />} />
              <Route path="/import" element={<BulkOperations />} />
              <Route path="/settings/tags" element={<TagManagement />} />
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