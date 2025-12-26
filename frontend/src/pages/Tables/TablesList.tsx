import React, { useEffect, useState } from 'react';
import { Table as AntdTable, Tag, Button, Space, Card, Input, Select, Modal, message, Typography } from 'antd';
import { 
  PlusOutlined, 
  SearchOutlined, 
  DeleteOutlined, 
  EditOutlined, 
  DatabaseOutlined,
  UserOutlined,
  LinkOutlined
} from '@ant-design/icons';
import { useNavigate, Link } from 'react-router-dom';
import { tablesApi } from '@/api/endpoints/tables';
import { tagsApi } from '@/api/endpoints/tags';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import TagSelect from '@/components/TagSelect/TagSelect';
import { Tooltip } from 'antd';
import type { Table as MetadataTable } from '@/types/api';

const { Title } = Typography;
const { Option } = Select;

const TablesList: React.FC = () => {
  const navigate = useNavigate();
  const { sources, fetchSources } = useDataSourceStore();
  const [tables, setTables] = useState<MetadataTable[]>([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);
  const [searchText, setSearchText] = useState('');
  const [sourceFilter, setSourceFilter] = useState<string | null | undefined>(undefined);
  const [tagFilter, setTagFilter] = useState<string[]>([]);
  const [tagMatchMode, setTagMatchMode] = useState<'any' | 'all'>('any');

  const loadTables = async (page = 1, size = 20) => {
    setLoading(true);
    console.debug('[TablesList] Loading tables:', { page, size, sourceFilter, searchText, tagFilter, tagMatchMode });
    try {
      const response = await tablesApi.list({
        page,
        size,
        source_id: sourceFilter,
        search: searchText,
        tags: tagFilter,
        tag_match: tagMatchMode
      });
      
      setTables(response.items);
      setTotal(response.total);

      // Background Enrichment: Fetch details for each table to get accurate counts and tags
      const enrichmentPromises = response.items.map(async (table) => {
        try {
          const detail = await tablesApi.get(table.id);
          const tagsResponse = await tagsApi.getTableTags(table.id);
          
          return {
            id: table.id,
            field_count: detail.fields?.length || 0,
            fullTags: tagsResponse.items || []
          };
        } catch (e) {
          return null;
        }
      });

      Promise.all(enrichmentPromises).then((results) => {
        const enrichmentMap = results.reduce((acc: any, curr) => {
          if (curr) acc[curr.id] = curr;
          return acc;
        }, {});

        setTables(prev => prev.map(t => enrichmentMap[t.id] ? {
          ...t,
          field_count: enrichmentMap[t.id].field_count,
          tags: enrichmentMap[t.id].fullTags
        } : t));
      });

    } catch (error) {
      message.error('Failed to load tables');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSources();
  }, [fetchSources]);

  // Trigger load when filter OR search changes (Reactive mode)
  useEffect(() => {
    const timer = setTimeout(() => {
      loadTables(1);
    }, 300); // Small debounce
    return () => clearTimeout(timer);
  }, [sourceFilter, searchText, tagFilter, tagMatchMode]);

  const handleDelete = (id: string) => {
    Modal.confirm({
      title: 'Delete Table Metadata?',
      content: 'This will remove the table and its field definitions. Lineage might be affected.',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await tablesApi.delete(id);
          message.success('Table deleted');
          loadTables();
        } catch (error) {
          message.error('Failed to delete table');
        }
      },
    });
  };

  const columns = [
    {
      title: 'Name',
      dataIndex: 'name',
      key: 'name',
      render: (text: string, record: MetadataTable) => (
        <Space direction="vertical" size={0}>
          <Link to={`/metadata/tables/${record.id}`}>
            <Typography.Text strong style={{ color: '#1890ff', cursor: 'pointer' }}>{text}</Typography.Text>
          </Link>
          {record.qualified_name && (
            <Typography.Text type="secondary" style={{ fontSize: '12px' }}>
              {record.qualified_name}
            </Typography.Text>
          )}
        </Space>
      ),
    },
    {
      title: 'Source',
      dataIndex: 'source_id',
      key: 'source',
      render: (sourceId: string | null, record: MetadataTable) => {
        if (!sourceId) return <Tag icon={<UserOutlined />} color="blue">MANUAL</Tag>;
        
        // Find source name from sources store if record.source_name is missing
        const source = sources.find(s => s.id === sourceId);
        const name = record.source_name || source?.name || 'CONNECTED';
        
        return (
          <Tag icon={<DatabaseOutlined />} color="green">
            {name}
          </Tag>
        );
      },
    },
    {
      title: 'Type',
      dataIndex: 'type',
      key: 'type',
      render: (type: string) => <Tag>{type.toUpperCase()}</Tag>,
    },
    {
      title: 'Tags',
      dataIndex: 'tags',
      key: 'tags',
      render: (tags: any[]) => {
        // 1. Sort tags by path length (deepest first)
        const sortedTags = [...(tags || [])].sort((a, b) => {
          const depthA = typeof a === 'string' ? 0 : (a.path?.split('-').length || 0);
          const depthB = typeof b === 'string' ? 0 : (b.path?.split('-').length || 0);
          return depthB - depthA;
        });

        // 2. FILTER: Hide system-generated DataSource tags
        const filteredTags = sortedTags.filter(tag => {
            const path = typeof tag === 'string' ? '' : (tag.path || '');
            return !path.startsWith('DataSource');
        });

        return (
          <Space wrap size={[0, 4]}>
            {filteredTags.slice(0, 3).map((tag, idx) => (
              <Tag key={typeof tag === 'string' ? tag + idx : tag.id} color="blue" style={{ fontSize: '10px' }}>
                {typeof tag === 'string' ? tag : tag.name}
              </Tag>
            ))}
            {filteredTags.length > 3 && (
              <Tooltip title={filteredTags.slice(3).map(t => typeof t === 'string' ? t : t.name).join(', ')}>
                <Tag>+{filteredTags.length - 3}</Tag>
              </Tooltip>
            )}
          </Space>
        );
      },
    },
    {
      title: 'Fields',
      dataIndex: 'field_count',
      key: 'field_count',
      render: (count: number, record: MetadataTable) => count ?? (record as any).fields?.length ?? 0,
    },
    {
      title: 'Created At',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (date: string) => new Date(date).toLocaleDateString(),
    },
    {
      title: 'Actions',
      key: 'actions',
      render: (_: any, record: MetadataTable) => (
        <Space size="middle">
          <Button type="text" icon={<LinkOutlined />} onClick={() => navigate(`/lineage/${record.id}`)}>Lineage</Button>
          <Button type="text" icon={<EditOutlined />} onClick={() => navigate(`/metadata/tables/${record.id}/edit`)}>Edit</Button>
          <Button type="text" danger icon={<DeleteOutlined />} onClick={() => handleDelete(record.id)}>Delete</Button>
        </Space>
      ),
    },
  ];

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Title level={3}>Table Metadata</Title>
        <Button type="primary" icon={<PlusOutlined />} onClick={() => navigate('/metadata/tables/new')}>
          Add Table
        </Button>
      </div>

      <Card size="small">
        <Space wrap>
          <Input 
            placeholder="Search tables..." 
            prefix={<SearchOutlined />} 
            value={searchText}
            onChange={e => setSearchText(e.target.value)}
            onPressEnter={() => loadTables()}
            style={{ width: 250 }}
          />
          <Select 
            placeholder="Filter by Source" 
            allowClear 
            style={{ width: 200 }}
            onChange={value => setSourceFilter(value)}
          >
            <Option value={null}>Manual Only</Option>
            {sources.map(s => (
              <Option key={s.id} value={s.id}>{s.name}</Option>
            ))}
          </Select>
          <TagSelect 
            style={{ width: 250 }} 
            value={tagFilter} 
            onChange={setTagFilter} 
            placeholder="Filter by Tags" 
          />
          <Select 
            value={tagMatchMode} 
            onChange={setTagMatchMode} 
            style={{ width: 120 }}
          >
            <Option value="any">Match Any</Option>
            <Option value="all">Match All</Option>
          </Select>
          <Button type="primary" onClick={() => loadTables()}>Search</Button>
        </Space>
      </Card>

      <AntdTable 
        columns={columns} 
        dataSource={tables} 
        rowKey="id" 
        loading={loading}
        pagination={{
          total,
          pageSize: 20,
          onChange: (page, size) => loadTables(page, size)
        }}
      />
    </Space>
  );
};

export default TablesList;
