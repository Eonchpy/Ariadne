import { memo, useState } from 'react';
import { Handle, Position } from 'reactflow';
import { Card, Typography, Space, List, Divider, Button, Modal, Input } from 'antd';
import { TableOutlined, DownOutlined, UpOutlined, SearchOutlined } from '@ant-design/icons';

const { Text } = Typography;

const TableNode = ({ data }: any) => {
  const [isExpanded, setIsExpanded] = useState(data.forceExpand || false);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [fieldSearch, setFieldSearch] = useState('');

  const allFields = data.fields || [];
  const highlightedFieldIds = data.highlightedFields || [];
  
  // Specific check: Is this table or its fields part of the trace?
  // isNew should NOT trigger a permanent blue border
  const isTraced = data.isTraced; 
  const hasInternalHighlights = allFields.some((f: any) => highlightedFieldIds.includes(f.id));
  const isHighPriority = isTraced || hasInternalHighlights;

  // A field should be visible if it's in the top 10 OR if it's highlighted
  const displayFields = allFields.filter((f: any, idx: number) => 
    idx < 10 || highlightedFieldIds.includes(f.id)
  );
  
  const hasMoreFields = allFields.length > 10;

  const filteredFields = allFields.filter((f: any) => 
    f.label.toLowerCase().includes(fieldSearch.toLowerCase())
  );

  const isDimmed = data.isDimmed;

  return (
    <Card 
      size="small" 
      className={data.isNew ? 'highlight-new-node' : ''}
      style={{ 
        width: 240, 
        borderRadius: 8, 
        border: isHighPriority ? '2px solid #1890ff' : '1px solid #d9d9d9', 
        boxShadow: isHighPriority ? '0 0 10px rgba(24, 144, 255, 0.3)' : '0 2px 4px rgba(0,0,0,0.1)',
        opacity: isDimmed ? 0.4 : 1,
        transition: 'all 0.3s'
      }}
      styles={{ body: { padding: '8px 12px' } }}
      title={
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            <TableOutlined style={{ color: isHighPriority ? '#1890ff' : 'inherit' }} />
            <Text strong style={{ fontSize: '12px' }}>{data.label}</Text>
          </Space>
          <Button 
            type="text" 
            size="small" 
            icon={(isExpanded || data.forceExpand) ? <UpOutlined /> : <DownOutlined />} 
            onClick={(e) => {
                e.stopPropagation();
                setIsExpanded(!isExpanded);
            }}
          />
        </div>
      }
    >
      <Handle type="target" position={Position.Left} style={{ background: '#555', top: '20px' }} />
      <Handle type="source" position={Position.Right} style={{ background: '#555', top: '20px' }} />
      
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4 }}>
        <Text type="secondary" style={{ fontSize: '10px' }}>{data.source_name || 'Manual'}</Text>
        <Text type="secondary" style={{ fontSize: '10px' }}>{allFields.length} Fields</Text>
      </div>

      {(isExpanded || data.forceExpand) && allFields.length > 0 && (
        <>
          <Divider style={{ margin: '8px 0' }} />
          <List
            size="small"
            dataSource={displayFields}
            renderItem={(item: any) => {
              const isHighlighted = highlightedFieldIds.includes(item.id);
              return (
                <List.Item style={{ 
                  padding: '2px 0', 
                  border: 'none', 
                  position: 'relative',
                  background: isHighlighted ? '#e6f7ff' : 'transparent',
                  borderRadius: '2px'
                }}>
                  <Handle 
                    type="target" 
                    position={Position.Left} 
                    id={item.id} 
                    style={{ left: -12, background: isHighlighted ? '#1890ff' : '#d9d9d9', width: 6, height: 6 }} 
                  />
                  <Text style={{ 
                    fontSize: '11px', 
                    color: isHighlighted ? '#1890ff' : 'inherit',
                    fontWeight: isHighlighted ? 'bold' : 'normal'
                  }}>
                    {item.label}
                  </Text>
                  <Handle 
                    type="source" 
                    position={Position.Right} 
                    id={item.id} 
                    style={{ right: -12, background: isHighlighted ? '#1890ff' : '#d9d9d9', width: 6, height: 6 }} 
                  />
                </List.Item>
              );
            }}
          />
          {hasMoreFields && (
            <Button 
                type="link" 
                size="small" 
                onClick={(e) => {
                    e.stopPropagation();
                    setIsModalOpen(true);
                }} 
                style={{ padding: 0, fontSize: '11px' }}
            >
              + {allFields.length - 10} more fields
            </Button>
          )}
        </>
      )}

      <Modal
        title={`Fields for ${data.label}`}
        open={isModalOpen}
        onCancel={() => setIsModalOpen(false)}
        footer={null}
        width={400}
      >
        <Input 
          placeholder="Search fields..." 
          prefix={<SearchOutlined />} 
          style={{ marginBottom: 16 }} 
          value={fieldSearch}
          onChange={e => setFieldSearch(e.target.value)}
        />
        <List
          size="small"
          bordered
          dataSource={filteredFields}
          style={{ maxHeight: 400, overflow: 'auto' }}
          renderItem={(item: any) => (
            <List.Item 
              style={{ cursor: 'pointer' }}
              onClick={() => {
                console.log(`Trace requested for field: ${item.id}`, item);
                if (data.onFieldClick) data.onFieldClick(item.id);
                setIsModalOpen(false);
              }}
            >
              <Text>{item.label}</Text>
              <Button type="link" size="small" icon={<SearchOutlined />}>Trace</Button>
            </List.Item>
          )}
        />
      </Modal>
    </Card>
  );
};

export default memo(TableNode);
