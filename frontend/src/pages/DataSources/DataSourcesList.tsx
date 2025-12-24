import React, { useEffect, useState } from 'react';
import { Table, Tag, Button, Space, Card, Input, Select, Modal, message, Typography } from 'antd';
import { PlusOutlined, SearchOutlined, DeleteOutlined, EditOutlined, CheckCircleOutlined, CloseCircleOutlined, SyncOutlined } from '@ant-design/icons';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import { dataSourcesApi } from '@/api/endpoints/dataSources';
import type { DataSource, DataSourceType } from '@/types/api';
import { useNavigate } from 'react-router-dom';

const { Title } = Typography;

const DataSourcesList: React.FC = () => {
  const navigate = useNavigate();
  const { sources, loading, fetchSources, deleteSource, testConnection } = useDataSourceStore();
  const [searchText, setSearchTerm] = useState('');
  const [typeFilter, setTypeFilter] = useState<string | undefined>(undefined);
  const [testingId, setTestingId] = useState<string | null>(null);

  // Function to enrich sources with audit log data
  const loadEnrichedSources = async (page = 1, size = 20) => {
    // 1. Fetch raw sources through store
    await fetchSources({ page, size, type: typeFilter });
    
    // 2. Fetch latest audit logs to get status/latency
    try {
      const { sources: currentSources } = useDataSourceStore.getState();
      const logsResponse = await dataSourcesApi.getAuditLogs({ limit: 100 });
      const logs = Array.isArray(logsResponse) ? logsResponse : logsResponse.items || [];

      const enriched = currentSources.map(source => {
        const latestLog = logs.find((l: any) => l.source_id === source.id);
        if (latestLog) {
          const isSuccess = latestLog.result === 'success';
          return {
            ...source,
            last_test_status: isSuccess ? 'success' : 'failed',
            last_test_success: isSuccess,
            last_tested_at: latestLog.created_at || latestLog.timestamp,
            latency_ms: latestLog.latency_ms
          };
        }
        return source;
      });

      useDataSourceStore.setState({ sources: enriched as any });
    } catch (error) {
      console.error('Failed to fetch audit logs', error);
    }
  };

  useEffect(() => {
    loadEnrichedSources();
  }, [fetchSources, typeFilter]);

  const handleFetch = (page = 1, size = 20) => {
    loadEnrichedSources(page, size);
  };

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: 'Are you sure you want to delete this data source?',
      content: 'This action cannot be undone.',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await deleteSource(id);
          message.success('Data source deleted');
        } catch (err) {
          message.error('Failed to delete data source');
        }
      },
    });
  };

  const handleTest = async (id: string) => {
    setTestingId(id);
    try {
      const result = await testConnection(id);
      if (result.success) {
        const latencyText = result.latency_ms ? ` (${result.latency_ms.toFixed(2)}ms)` : '';
        message.success(`${result.message}${latencyText}`);
        
        // Optimistic local update since backend might not persist status yet
        const updatedSources = sources.map(s => 
          s.id === id ? { 
            ...s, 
            last_test_status: 'success', 
            last_test_success: true,
            last_tested_at: new Date().toISOString() 
          } : s
        );
        useDataSourceStore.setState({ sources: updatedSources as any });
      } else {
        message.error(result.message);
        
        const updatedSources = sources.map(s => 
          s.id === id ? { 
            ...s, 
            last_test_status: 'failed', 
            last_test_success: false,
            last_tested_at: new Date().toISOString() 
          } : s
        );
        useDataSourceStore.setState({ sources: updatedSources as any });
      }
    } catch (err) {
      message.error('Connection test failed');
    } finally {
      setTestingId(null);
    }
  };

  const filteredSources = sources.filter(s => 
    s.name.toLowerCase().includes(searchText.toLowerCase()) ||
    s.description?.toLowerCase().includes(searchText.toLowerCase())
  );

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: DataSource) => {
        console.debug('Data Source Record:', record);
        return (
          <Space direction="vertical" size={0}>
            <Typography.Text strong>{text}</Typography.Text>
            <Typography.Text type="secondary">{record.description}</Typography.Text>
          </Space>
        );
      },
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: DataSourceType) => (
        <Tag color="blue">{type.toUpperCase()}</Tag>
      ),
    },
    {
      title: 'Status',
      key: 'status',
      render: (_: any, record: any) => {
        // Robust check for various possible field names from backend
        const hasTested = record.last_tested_at || record.last_test_status || record.last_test_success !== undefined;
        const isSuccess = record.last_test_status === 'success' || record.last_test_success === true;

        if (!hasTested) return <Tag icon={<SyncOutlined />} color="default">NOT TESTED</Tag>;
        return isSuccess 
          ? <Tag icon={<CheckCircleOutlined />} color="success">CONNECTED</Tag>
          : <Tag icon={<CloseCircleOutlined />} color="error">FAILED</Tag>;
      },
    },
    {
      title: 'Last Tested',
      key: 'last_tested_at',
      render: (_: any, record: any) => {
        const date = record.last_tested_at || record.last_test_at;
        return date ? new Date(date).toLocaleString() : '-';
      },
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: DataSource) => (
        <Space size="middle">
          <Button 
            type="text" 
            icon={<SyncOutlined spin={testingId === record.id} />} 
            onClick={() => handleTest(record.id)}
            disabled={testingId === record.id}
          >
            Test
          </Button>
          <Button type="text" icon={<EditOutlined />} onClick={() => navigate(`/sources/${record.id}/edit`)}>Edit</Button>
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>Data Sources</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/sources/new')}>
          Add Data Source
        </Button>
      </div>

      <Card size="small">
        <Space>
          <Input 
            placeholder="Search sources..." 
            prefix={<SearchOutlined />} 
            value={searchText}
            onChange={e => setSearchTerm(e.target.value)}
            style={{ width: 250 }}
          />
          <Select 
            placeholder="Filter by type" 
            allowClear 
            style={{ width: 150 }}
            onChange={value => {
              setTypeFilter(value);
              fetchSources({ type: value });
            }}
          >
            <Select.Option value="oracle">Oracle</Select.Option>
            <Select.Option value="mongodb">MongoDB</Select.Option>
            <Select.Option value="elasticsearch">Elasticsearch</Select.Option>
          </Select>
        </Space>
      </Card>

      <Table 
        columns={columns} 
        dataSource={filteredSources} 
        rowKey="id" 
        loading={loading}
        pagination={{
          total: filteredSources.length,
          pageSize: 20,
          showSizeChanger: true,
          onChange: (page, size) => handleFetch(page, size)
        }}
      />
    </Space>
  );
};

export default DataSourcesList;
