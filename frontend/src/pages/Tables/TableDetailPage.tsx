import React, { useEffect, useState } from 'react';
import { Card, Tabs, Descriptions, Table, Tag, Button, Space, Typography, message, Breadcrumb, Divider } from 'antd';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { EditOutlined, NodeIndexOutlined, DatabaseOutlined } from '@ant-design/icons';
import { tablesApi } from '@/api/endpoints/tables';
import { lineageApi } from '@/api/endpoints/lineage';
import { tagsApi } from '@/api/endpoints/tags';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import client from '@/api/client';
import type { TableDetail } from '@/types/api';
import BlastRadius from '@/components/analysis/BlastRadius';
import QualityCheck from '@/components/analysis/QualityCheck';
import { Badge } from 'antd';
import { useTranslation } from 'react-i18next';

const { Title, Text } = Typography;

const TableDetailPage: React.FC = () => {
  const { t } = useTranslation();
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const { sources, fetchSources } = useDataSourceStore();
  const [table, setTable] = useState<TableDetail | null>(null);
  const [tableTags, setTableTags] = useState<any[]>([]);
  const [lineage, setLineage] = useState<{ upstream: any[], downstream: any[] }>({ upstream: [], downstream: [] });
  const [loading, setLoading] = useState(false);
  const [hasQualityIssues, setHasQualityIssues] = useState(false);

  useEffect(() => {
    fetchSources();
    if (id) {
      loadTable(id);
      loadLineage(id);
      checkQuality(id);
    }
  }, [id, fetchSources]);

  const checkQuality = async (tableId: string) => {
    try {
      const response = await client.get<any, any>(`/lineage/analysis/quality-check/${tableId}`);
      setHasQualityIssues(response.has_cycles);
    } catch (e) { /* ignore quality badge errors */ }
  };

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
    { title: t('table_detail.field_name'), dataIndex: 'name', key: 'name', render: (text: string) => <Text strong>{text}</Text> },
    { title: t('table_detail.data_type'), dataIndex: 'data_type', key: 'data_type', render: (text: string) => <Tag color="orange">{text}</Tag> },
    { title: t('table_detail.nullable'), dataIndex: 'is_nullable', key: 'is_nullable', render: (val: boolean) => val ? t('table_detail.yes') : t('table_detail.no') },
    { title: t('table_detail.primary_key'), dataIndex: 'is_primary_key', key: 'pk', render: (val: boolean) => val ? <Tag color="gold">PK</Tag> : null },
    { title: t('table_detail.description'), dataIndex: 'description', key: 'description' },
  ];

  const lineageColumns = (type: 'Source' | 'Target') => [
    { 
      title: type === 'Source' ? 'Source Table' : 'Target Table', 
      key: 'name', 
      render: (_: any, record: any) => (
        <Link to={`/metadata/tables/${record.node?.id}`}>
          <Text strong style={{ color: '#1890ff' }}>{record.node?.label}</Text>
        </Link>
      ) 
    },
    { 
      title: t('table_detail.source_system'), 
      key: 'source', 
      render: (_: any, record: any) => <Tag color="blue">{record.node?.source_name || 'Manual'}</Tag> 
    },
    { 
      title: t('table_detail.transformation'), 
      dataIndex: 'label', 
      key: 'type',
      render: (text: string) => <Tag color="green">{text}</Tag>
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <Breadcrumb items={[
        { title: <Link to="/">{t('common.dashboard')}</Link> },
        { title: <Link to="/metadata/tables">{t('common.tables')}</Link> },
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
          <Button icon={<NodeIndexOutlined />} onClick={() => navigate(`/lineage/${table.id}`)}>{t('table_detail.view_graph')}</Button>
          <Button type="primary" icon={<EditOutlined />} onClick={() => navigate(`/metadata/tables/${table.id}/edit`)}>{t('table_detail.edit')}</Button>
        </Space>
      </div>

      <Card>
        <Tabs
          defaultActiveKey="schema"
          items={[
            {
              key: 'schema',
              label: t('table_detail.overview'),
              children: (
                <Space direction="vertical" size="large" style={{ width: '100%' }}>
                  <Descriptions bordered column={2} size="small">
                    <Descriptions.Item label={t('table_detail.type')}>{table.type.toUpperCase()}</Descriptions.Item>
                    <Descriptions.Item label={t('table_detail.schema')}>{table.schema_name || '-'}</Descriptions.Item>
                    <Descriptions.Item label={t('table_detail.created_at')}>{new Date(table.created_at).toLocaleString()}</Descriptions.Item>
                    <Descriptions.Item label={t('table_detail.tags')}>
                      <Space wrap>
                        {tableTags.length > 0 ? (
                          tableTags.map(t => <Tag key={t.id} color="blue">{t.name}</Tag>)
                        ) : (
                          <Text type="secondary">No tags</Text>
                        )}
                      </Space>
                    </Descriptions.Item>
                    <Descriptions.Item label={t('table_detail.description')} span={2}>
                      {table.description || <Text type="secondary">{t('table_detail.no_description')}</Text>}
                    </Descriptions.Item>
                  </Descriptions>
                  
                  <div>
                    <Title level={5}>{t('table_detail.fields')} ({table.fields?.length || 0})</Title>
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
              label: t('table_detail.lineage_direct'),
              children: (
                <Space direction="vertical" size="middle" style={{ width: '100%' }}>
                  <Title level={5}>{t('table_detail.upstream')}</Title>
                  <Table 
                    dataSource={lineage.upstream} 
                    columns={lineageColumns('Source')} 
                    rowKey="id" 
                    pagination={false} 
                    size="small" 
                    locale={{ emptyText: t('table_detail.no_upstream') }}
                  />
                  <Divider style={{ margin: '16px 0' }} />
                  <Title level={5}>{t('table_detail.downstream')}</Title>
                  <Table 
                    dataSource={lineage.downstream} 
                    columns={lineageColumns('Target')} 
                    rowKey="id" 
                    pagination={false} 
                    size="small"
                    locale={{ emptyText: t('table_detail.no_downstream') }}
                  />
                </Space>
              )
            },
            {
              key: 'analysis',
              label: t('table_detail.blast_radius'),
              children: (
                <div style={{ padding: '8px 0' }}>
                  <BlastRadius tableId={table.id} />
                </div>
              )
            },
            {
              key: 'quality',
              label: (
                <Space>
                  {t('table_detail.quality_check')}
                  {hasQualityIssues && <Badge dot status="error" />}
                </Space>
              ),
              children: (
                <div style={{ padding: '8px 0' }}>
                  <QualityCheck tableId={table.id} />
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
