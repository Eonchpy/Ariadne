import { memo } from 'react';
import { Handle, Position } from 'reactflow';
import { Typography, Tag } from 'antd';

const { Text } = Typography;

const FieldNode = ({ data }: any) => {
  return (
    <div style={{ 
      padding: '4px 10px', 
      borderRadius: '4px', 
      background: '#fff', 
      border: '1px solid #d9d9d9',
      minWidth: '120px',
      fontSize: '12px',
      boxShadow: '0 1px 2px rgba(0,0,0,0.05)'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#1890ff' }} />
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8 }}>
        <Text strong style={{ fontSize: '11px' }}>{data.label}</Text>
        <Tag color="cyan" style={{ fontSize: '9px', margin: 0, padding: '0 2px' }}>FIELD</Tag>
      </div>
      <Handle type="source" position={Position.Right} style={{ background: '#1890ff' }} />
    </div>
  );
};

export default memo(FieldNode);
