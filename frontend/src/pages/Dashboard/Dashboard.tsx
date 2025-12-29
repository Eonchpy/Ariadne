import React, { useState, useEffect } from 'react';
import { Card, Typography, Space, Select, Button, Tag } from 'antd';
import { 
  SearchOutlined, 
  PlusOutlined, 
  RobotOutlined, 
  DatabaseOutlined, 
  ApartmentOutlined,
  ThunderboltOutlined 
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import { tablesApi } from '@/api/endpoints/tables';
import { useAuthStore } from '@/stores/authStore';

const { Title, Text } = Typography;
const { Option } = Select;

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [tables, setTables] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [stats, setStats] = useState({ totalTables: 0, totalSources: 0 });
  const { user } = useAuthStore();

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await tablesApi.list({ size: 100 });
      setTables(res.items);
      setStats({
        totalTables: res.total,
        totalSources: new Set(res.items.map((t: any) => t.source_id)).size
      });
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (value: string) => {
    navigate(`/lineage/${value}`);
  };

  const openAI = () => {
    // This is a bit of a hack to trigger the global AI drawer
    // In a real app, we might use a global event bus or context
    const btn = document.querySelector('header .ant-btn .anticon-robot')?.parentElement;
    if (btn) (btn as HTMLElement).click();
  };

  return (
    <div style={{ 
      height: '100%', 
      display: 'flex', 
      flexDirection: 'column', 
      alignItems: 'center',
      padding: '10vh 24px 48px', // Added horizontal padding constraints
      background: '#ffffff',
      overflow: 'hidden', // Prevent horizontal scroll
      position: 'relative'
    }}>
      
      {/* 1. HERO SECTION */}
      <div style={{ textAlign: 'center', marginBottom: 48, marginTop: 'auto' }}>
        <img 
          src="/logo_v2.png" 
          alt="Ariadne Logo" 
          style={{ 
            width: 200, 
            height: 'auto', 
            marginBottom: 16
          }} 
        />
        <Title level={2} style={{ marginBottom: 8 }}>
          Welcome back, {user?.name || 'Traveler'}
        </Title>
        <Text type="secondary" style={{ fontSize: 16 }}>
          Explore your data universe or extend its boundaries.
        </Text>
      </div>

      {/* 2. MEGA SEARCH */}
      <Card 
        bordered={false} 
        style={{ 
          width: '100%', 
          maxWidth: 600, 
          boxShadow: '0 4px 20px rgba(0,0,0,0.08)',
          borderRadius: 16
        }}
        styles={{ body: { padding: 8 } }}
      >
        <Select
          showSearch
          size="large"
          placeholder="Search any table to explore lineage..."
          optionFilterProp="label"
          onChange={handleSearch}
          loading={loading}
          style={{ width: '100%' }}
          suffixIcon={<SearchOutlined style={{ fontSize: 18, color: '#1890ff' }} />}
          variant="borderless"
          dropdownStyle={{ borderRadius: 12, padding: 8 }}
        >
          {tables.map(t => (
            <Option key={t.id} value={t.id} label={t.name}>
              <Space>
                <DatabaseOutlined style={{ color: '#8c8c8c' }} />
                <span>{t.name}</span>
                <Text type="secondary" style={{ fontSize: 12 }}>{t.schema_name}</Text>
              </Space>
            </Option>
          ))}
        </Select>
      </Card>

      {/* 3. QUICK ACTIONS & AI HINTS */}
      <Space size="large" style={{ marginTop: 32 }}>
        <Button 
          size="large" 
          icon={<PlusOutlined />} 
          onClick={() => navigate('/metadata/tables/new')}
        >
          Create New Table
        </Button>
        <Button 
          size="large" 
          icon={<RobotOutlined />} 
          onClick={openAI}
        >
          Ask Assistant
        </Button>
      </Space>

      <Space style={{ marginTop: 24 }}>
        <Tag icon={<ThunderboltOutlined />} color="blue" style={{ cursor: 'pointer' }} onClick={openAI}>
          Check Impact
        </Tag>
        <Tag icon={<SearchOutlined />} color="cyan" style={{ cursor: 'pointer' }} onClick={openAI}>
          Audit Quality
        </Tag>
      </Space>

      {/* 4. MINIMAL STATS FOOTER */}
      <div style={{ marginTop: 'auto', textAlign: 'center', opacity: 0.6 }}>
        <Space size={48} split={<span style={{ color: '#d9d9d9' }}>|</span>}>
          <Space>
            <DatabaseOutlined /> {stats.totalTables} Assets
          </Space>
          <Space>
            <ApartmentOutlined /> {stats.totalSources} Sources
          </Space>
        </Space>
      </div>
    </div>
  );
};

export default Dashboard;
