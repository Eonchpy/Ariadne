import React, { useState } from 'react';
import { Layout, Menu, Button, Dropdown, Avatar, Space, Typography, Tooltip } from 'antd';
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
  TagsOutlined,
  GlobalOutlined
} from '@ant-design/icons';
import { Outlet, useNavigate, useLocation, Link } from 'react-router-dom';
import { useAuthStore } from '@/stores/authStore';
import ChatSidebar from '@/components/ai/ChatSidebar';
import { useTranslation } from 'react-i18next';

const { Header, Sider, Content, Footer } = Layout;
export const MainLayout: React.FC = () => {
  const { t, i18n } = useTranslation();
  const [collapsed, setCollapsed] = useState(false);
  const [chatVisible, setChatVisible] = useState(false);
  const { user, logout } = useAuthStore();
  const navigate = useNavigate();
  const location = useLocation();

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
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
      label: <Link to="/">{t('common.dashboard')}</Link>,
    },
    {
      key: '/sources',
      icon: <DatabaseOutlined />,
      label: <Link to="/sources">{t('common.data_sources')}</Link>,
    },
    {
      key: '/metadata',
      icon: <TableOutlined />,
      label: t('common.metadata'),
      children: [
        { key: '/metadata/tables', label: <Link to="/metadata/tables">{t('common.tables')}</Link> },
      ]
    },
    {
      key: '/lineage',
      icon: <ApartmentOutlined />,
      label: <Link to="/lineage">{t('common.lineage')}</Link>,
    },
    {
      key: '/import',
      icon: <CloudUploadOutlined />,
      label: <Link to="/import">{t('common.bulk_import')}</Link>,
    },
  ];

  if (isAdmin) {
    menuItems.push({
      key: '/settings',
      icon: <SettingOutlined />,
      label: t('common.settings'),
      children: [
        { 
          key: '/settings/tags', 
          icon: <TagsOutlined />,
          label: <Link to="/settings/tags">{t('common.tag_management')}</Link> 
        },
      ]
    });
  }

  const userMenu = {
    items: [
      {
        key: 'profile',
        label: t('common.profile'),
        icon: <UserOutlined />,
      },
      {
        type: 'divider' as const,
      },
      {
        key: 'logout',
        label: t('common.logout'),
        icon: <LogoutOutlined />,
        onClick: handleLogout,
      },
    ]
  };

  const langMenu = {
    items: [
      { key: 'en', label: 'English', onClick: () => changeLanguage('en') },
      { key: 'zh', label: '中文', onClick: () => changeLanguage('zh') },
    ]
  };

  const isDashboard = location.pathname === '/';

  return (
    <Layout style={{ height: '100vh', overflow: 'hidden' }}>
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
      <Layout style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
        <Header style={{ padding: '0 16px', background: '#fff', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexShrink: 0 }}>
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            style={{ fontSize: '16px', width: 64, height: 64 }}
          />
          <Space size="middle">
            <Dropdown menu={langMenu} placement="bottomRight" arrow>
              <Button type="text" icon={<GlobalOutlined style={{ fontSize: '18px' }} />} />
            </Dropdown>
            <Tooltip title={t('common.ai_assistant')}>
              <Button 
                type="text" 
                icon={<RobotOutlined style={{ fontSize: '20px', color: chatVisible ? '#1890ff' : 'inherit' }} />} 
                onClick={() => setChatVisible(true)}
                style={{ width: 44, height: 44, display: 'flex', alignItems: 'center', justifyContent: 'center' }}
              />
            </Tooltip>
            <Dropdown menu={userMenu} placement="bottomRight" arrow>
              <Space style={{ cursor: 'pointer' }}>
                <Avatar icon={<UserOutlined />} />
                <Typography.Text strong>{user?.name}</Typography.Text>
              </Space>
            </Dropdown>
          </Space>
        </Header>
                <Content
                  style={{
                    margin: '24px 16px',
                    padding: isDashboard ? 0 : 24,
                    minHeight: 'calc(100vh - 112px)',
                    background: '#fff', // Always white, ensuring Footer is 'inside'
                    borderRadius: 8,
                    overflowX: 'hidden',
                    overflowY: 'auto',
                    position: 'relative',
                    paddingBottom: 60
                  }}
                >
                  <Outlet />
                  <Footer style={{
                    textAlign: 'center',
                    background: 'transparent',
                    position: isDashboard ? 'absolute' : 'relative',
                    bottom: isDashboard ? 20 : 0,
                    width: '100%',
                    opacity: 0.5
                  }}>            Ariadne ©2025
          </Footer>
        </Content>
      </Layout>
      <ChatSidebar open={chatVisible} onClose={() => setChatVisible(false)} />
    </Layout>
  );
};
