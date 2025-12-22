import React from 'react';
import { Layout, Typography } from 'antd';
import { Outlet } from 'react-router-dom';

const { Content, Footer } = Layout;
const { Title } = Typography;

export const AuthLayout: React.FC = () => {
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Content style={{ 
        display: 'flex', 
        justifyContent: 'center', 
        alignItems: 'center',
        background: '#f0f2f5' 
      }}>
        <div style={{ width: '100%', maxWidth: 400, padding: 24, background: '#fff', borderRadius: 8, boxShadow: '0 2px 8px rgba(0,0,0,0.1)' }}>
          <div style={{ textAlign: 'center', marginBottom: 24 }}>
            <Title level={2}>Ariadne</Title>
            <Typography.Text type="secondary">Enterprise Metadata Management</Typography.Text>
          </div>
          <Outlet />
        </div>
      </Content>
      <Footer style={{ textAlign: 'center' }}>Ariadne ©2025</Footer>
    </Layout>
  );
};
