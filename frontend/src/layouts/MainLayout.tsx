import React, { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Space, Typography } from 'antd';
import { 
  MenuFoldOutlined, 
  MenuUnfoldOutlined, 
  UserOutlined, 
  LogoutOutlined,
  DatabaseOutlined,
  DashboardOutlined,
  TableOutlined,
  ApartmentOutlined,
  CloudUploadOutlined,
  RobotOutlined,
  SettingOutlined,
  TagsOutlined
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';

const { Header, Sider, Content, Footer } = Layout;

export const MainLayout: React.FC = () => {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const isAdmin = user?.roles?.includes('admin');

  // Helper to determine active menu key based on path
  const getSelectedKeys = () => {
    const { pathname } = location;
    if (pathname.startsWith('/metadata/tables')) return ['/metadata/tables'];
    if (pathname.startsWith('/sources')) return ['/sources'];
    if (pathname.startsWith('/lineage')) return ['/lineage'];
    if (pathname.startsWith('/import')) return ['/import'];
    if (pathname.startsWith('/settings/tags')) return ['/settings/tags'];
    return [pathname];
  };

  const menuItems: any[] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: <Link to="/">Dashboard</Link>,
    },
    {
      key: '/sources',
      icon: <DatabaseOutlined />,
      label: <Link to="/sources">Data Sources</Link>,
    },
    {
      key: '/metadata',
      icon: <TableOutlined />,
      label: 'Metadata',
      children: [
        { key: '/metadata/tables', label: <Link to="/metadata/tables">Tables</Link> },
      ]
    },
    {
      key: '/lineage',
      icon: <ApartmentOutlined />,
      label: <Link to="/lineage">Lineage</Link>,
    },
    {
      key: '/import',
      icon: <CloudUploadOutlined />,
      label: <Link to="/import">Bulk Import</Link>,
    },
    {
      key: '/ai',
      icon: <RobotOutlined />,
      label: <Link to="/ai">AI Assistant</Link>,
    },
  ];

  if (isAdmin) {
    menuItems.push({
      key: '/settings',
      icon: <SettingOutlined />,
      label: 'Settings',
      children: [
        { 
          key: '/settings/tags', 
          icon: <TagsOutlined />,
          label: <Link to="/settings/tags">Tag Management</Link> 
        },
      ]
    });
  }

  const userMenu = {
    items: [
      {
        key: 'profile',
        label: 'Profile',
        icon: <UserOutlined />,
      },
      {
        type: 'divider',
      },
      {
        key: 'logout',
        label: 'Logout',
        icon: <LogoutOutlined />,
        onClick: handleLogout,
      },
    ]
  };

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider trigger={null} collapsible collapsed={collapsed}>
                <div style={{ 
                  height: 100, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center',
                  padding: '16px 0',
                  transition: 'all 0.2s'
                }}>
                  <div style={{
                    width: collapsed ? '60px' : '90%', 
                    height: '60px', 
                    backgroundImage: 'url(/Ariadne_Logo.png)',
                    backgroundSize: 'contain',
                    backgroundRepeat: 'no-repeat',
                    backgroundPosition: 'center',
                    transition: 'all 0.2s',
                  }} />
                </div>        <Menu
          theme="dark"
          mode="inline"
          selectedKeys={getSelectedKeys()}
          items={menuItems}
        />
      </Sider>
      <Layout>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />
          <Space>
            <Typography.Text>{user?.name}</Typography.Text>
            <Dropdown menu={userMenu as any} placement="bottomRight">
              <Avatar icon={<UserOutlined />} style={{ cursor: 'pointer' }} />
            </Dropdown>
          </Space>
        </Header>
        <Content
          style={{
            margin: '24px 16px',
            padding: 24,
            minHeight: 280,
            background: '#fff',
            borderRadius: 8,
          }}
        >
          <Outlet />
        </Content>
        <Footer style={{ textAlign: 'center' }}>Ariadne ©2025</Footer>
      </Layout>
    </Layout>
  );
};
