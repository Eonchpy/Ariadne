import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Typography, Space, Button } from 'antd';
import { ClusterOutlined, PlusOutlined, MinusOutlined } from '@ant-design/icons';

const { Text } = Typography;

const BucketNode = ({ data }: any) => {
  const isLeft = data.side === 'left';
  const isExpanded = data.isExpanded;

  // Visual Container Style (for expanded state)
  if (isExpanded) {
    return (
      <div style={{ 
        width: data.width || 240, 
        height: data.height || 100, 
        background: 'rgba(24, 144, 255, 0.02)', 
        border: '1px dashed #1890ff', 
        borderRadius: 12,
        padding: '8px',
        position: 'relative'
      }}>
        <div style={{ position: 'absolute', top: -22, left: 0, display: 'flex', alignItems: 'center', gap: 8 }}>
          <Text strong style={{ fontSize: '12px', color: '#1890ff' }}>
            <ClusterOutlined /> {data.label}
          </Text>
          <Button 
            type="text" 
            size="small" 
            icon={<MinusOutlined style={{ fontSize: '10px' }} />} 
            onClick={() => data.onCollapse(data.tag_path)}
            style={{ color: '#ff4d4f', padding: 0, height: 'auto' }}
          />
        </div>
        {/* NO HANDLES IN EXPANDED STATE - Lines pierce through to children */}
      </div>
    );
  }

  // Regular Proxy Style (for collapsed state)
  return (
    <div style={{ position: 'relative', width: 220, height: 80, cursor: 'pointer' }}>
      <div style={{ position: 'absolute', top: 4, left: 4, width: '100%', height: '100%', background: '#f6ffed', border: '1px solid #b7eb8f', borderRadius: 8, zIndex: 1 }} />
      <div style={{ 
        position: 'absolute', 
        top: 0, 
        left: 0, 
        width: '100%', 
        height: '100%', 
        background: '#f6ffed', 
        border: '2px solid #52c41a', 
        borderRadius: 8, 
        zIndex: 2, 
        padding: '12px', 
        display: 'flex', 
        flexDirection: 'column', 
        justifyContent: 'center',
        boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
      }}>
        <Space>
          <ClusterOutlined style={{ color: '#52c41a' }} />
          <Text strong style={{ fontSize: '13px' }}>{data.label}</Text>
        </Space>
        <Text type="secondary" style={{ fontSize: '11px', marginTop: 4 }}>
          {data.table_count || 0} Tables
        </Text>
        
        {/* Expansion Trigger */}
        <div style={{ 
          position: 'absolute', 
          zIndex: 10,
          top: '50%',
          transform: 'translateY(-50%)',
          [isLeft ? 'left' : 'right']: -12
        }}>
            <Button 
                type="primary" 
                shape="circle" 
                size="small" 
                icon={<PlusOutlined />} 
                style={{ border: '2px solid #fff', boxShadow: '0 2px 4px rgba(0,0,0,0.2)' }}
                onClick={(e) => {
                  e.stopPropagation();
                  data.onExpand(data.tag_path);
                }}
            />
        </div>

        <Handle type="target" position={Position.Left} style={{ background: '#52c41a' }} />
        <Handle type="source" position={Position.Right} style={{ background: '#52c41a' }} />
      </div>
    </div>
  );
};

export default memo(BucketNode);
