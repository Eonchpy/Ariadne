import React, { useEffect, useState } from 'react';
import { Card, Tabs, Descriptions, Table, Tag, Button, Space, Typography, message, Breadcrumb, Divider } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { EditOutlined, NodeIndexOutlined, DatabaseOutlined } from '@ant-design/icons';
import { tablesApi } from '@/api/endpoints/tables';
import { lineageApi } from '@/api/endpoints/lineage';
import { tagsApi } from '@/api/endpoints/tags';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import type { TableDetail } from '@/types/api';
import BlastRadius from '@/components/analysis/BlastRadius';

const { Title, Text } = Typography;

const TableDetailPage: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { sources, fetchSources } = useDataSourceStore();
  const [table, setTable] = useState<TableDetail | null>(null);
  const [tableTags, setTableTags] = useState<any[]>([]);
  const [lineage, setLineage] = useState<{ upstream: any[], downstream: any[] }>({ upstream: [], downstream: [] });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchSources();
    if (id) {
      loadTable(id);
      loadLineage(id);
    }
  }, [id, fetchSources]);

  const loadTable = async (tableId: string) => {
    setLoading(true);
    try {
      const [data, tagsData] = await Promise.all([
        tablesApi.get(tableId),
        tagsApi.getTableTags(tableId)
      ]);
      setTable(data);
      
      // Reconstruct hierarchy from path for system tags, keep others
      const uniqueTags = new Map<string, any>();
      (tagsData.items || []).forEach((t: any) => {
        if (t.path?.startsWith('DataSource')) {
          const parts = t.path.split('-');
          if (parts[0]) uniqueTags.set('ds-root', { id: 'ds-root', name: parts[0], level: 1, path: parts[0] });
          if (parts[1]) uniqueTags.set('ds-type', { id: 'ds-type', name: parts[1], level: 2, path: `${parts[0]}-${parts[1]}` });
        } else {
          uniqueTags.set(t.id, t);
        }
      });
      
      setTableTags(Array.from(uniqueTags.values()).sort((a, b) => b.level - a.level));
    } catch (error) {
      message.error('Failed to load table details');
      navigate('/metadata/tables');
    } finally {
      setLoading(false);
    }
  };

  const loadLineage = async (tableId: string) => {
    try {
      // Call unified API for depth 1 to get immediate neighbors
      const data = await lineageApi.getGraph({ table_id: tableId, direction: 'both', depth: 1 });
      
      const upstreamEdges = (data.edges || []).filter(e => (e.to || e.target_id) === tableId);
      const downstreamEdges = (data.edges || []).filter(e => (e.from || e.source_id) === tableId);

      setLineage({ 
        upstream: upstreamEdges.map(e => ({ ...e, node: data.nodes.find(n => n.id === (e.from || e.source_id)) })),
        downstream: downstreamEdges.map(e => ({ ...e, node: data.nodes.find(n => n.id === (e.to || e.target_id)) }))
      });
    } catch (e) {
      console.error('Failed to load direct lineage', e);
    }
  };

  if (!table && loading) return <Card loading />;
  if (!table) return null;

  const source = sources.find(s => s.id === table.source_id);
  const sourceName = table.source_name || source?.name || 'Connected';

  const fieldColumns = [
    { title: 'Name', dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
    { title: 'Data Type', dataIndex: 'data_type', key: 'data_type', render: (text: string) => <Tag color="orange">{text}</Tag> },
    { title: 'Nullable', dataIndex: 'is_nullable', key: 'is_nullable', render: (val: boolean) => val ? 'Yes' : 'No' },
    { title: 'Primary Key', dataIndex: 'is_primary_key', key: 'pk', render: (val: boolean) => val ? <Tag color="gold">PK</Tag> : null },
    { title: 'Description', dataIndex: 'description', key: 'description' },
  ];

  const lineageColumns = (type: 'Source' | 'Target') => [
    { 
      title: type, 
      key: 'name', 
      render: (_: any, record: any) => (
        <Link to={`/metadata/tables/${record.node?.id}`}>
          <Text strong style={{ color: '#1890ff' }}>{record.node?.label}</Text>
        </Link>
      ) 
    },
    { 
      title: 'Source System', 
      key: 'source', 
      render: (_: any, record: any) => <Tag color="blue">{record.node?.source_name || 'Manual'}</Tag> 
    },
    { 
      title: 'Transformation', 
      dataIndex: 'label', 
      key: 'type',
      render: (text: string) => <Tag color="green">{text}</Tag>
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Breadcrumb items={[
        { title: <Link to="/">Home</Link> },
        { title: <Link to="/metadata/tables">Tables</Link> },
        { title: table.name },
      ]} />

      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
        <Space direction="vertical" size={0}>
          <Title level={2} style={{ margin: 0 }}>
            {table.name}
          </Title>
          <Space>
            {table.source_id && <Tag icon={<DatabaseOutlined />} color="green">{sourceName}</Tag>}
            <Text type="secondary">{table.qualified_name}</Text>
          </Space>
        </Space>
        <Space>
          <Button icon={<NodeIndexOutlined />} onClick={() => navigate(`/lineage/${table.id}`)}>View Graph</Button>
          <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/metadata/tables/${table.id}/edit`)}>Edit</Button>
        </Space>
      </div>

      <Card>
        <Tabs
          defaultActiveKey="schema"
          items={[
            {
              key: 'schema',
              label: 'Overview & Fields',
              children: (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Descriptions bordered column={2} size="small">
                    <Descriptions.Item label="Type">{table.type.toUpperCase()}</Descriptions.Item>
                    <Descriptions.Item label="Schema">{table.schema_name || '-'}</Descriptions.Item>
                    <Descriptions.Item label="Created At">{new Date(table.created_at).toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label="Tags">
                      <Space wrap>
                        {tableTags.length > 0 ? (
                          tableTags.map(t => <Tag key={t.id} color="blue">{t.name}</Tag>)
                        ) : (
                          <Text type="secondary">No tags</Text>
                        )}
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label="Description" span={2}>
                      {table.description || <Text type="secondary">No description provided.</Text>}
                    </Descriptions.Item>
                  </Descriptions>
                  
                  <div>
                    <Title level={5}>Fields ({table.fields?.length || 0})</Title>
                    <Table 
                      dataSource={table.fields} 
                      columns={fieldColumns} 
                      rowKey="id" 
                      pagination={false} 
                      size="small"
                    />
                  </div>
                </Space>
              )
            },
            {
              key: 'lineage',
              label: 'Lineage (Direct)',
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Title level={5}>Upstream (Data Sources)</Title>
                  <Table 
                    dataSource={lineage.upstream} 
                    columns={lineageColumns('Source')} 
                    rowKey="id" 
                    pagination={false} 
                    size="small" 
                    locale={{ emptyText: 'No upstream dependencies found.' }}
                  />
                  <Divider style={{ margin: '16px 0' }} />
                  <Title level={5}>Downstream (Impacted Tables)</Title>
                  <Table 
                    dataSource={lineage.downstream} 
                    columns={lineageColumns('Target')} 
                    rowKey="id" 
                    pagination={false} 
                    size="small"
                    locale={{ emptyText: 'No downstream tables dependent on this table.' }}
                  />
                </Space>
              )
            },
            {
              key: 'analysis',
              label: 'Blast Radius (Business Impact)',
              children: (
                <div style={{ padding: '8px 0' }}>
                  <BlastRadius tableId={table.id} />
                </div>
              )
            }
          ]}
        />
      </Card>
    </Space>
  );
};

export default TableDetailPage;
