import React, { useState, useEffect } from 'react';
import { Drawer, Descriptions, Typography, Tag, Button, Empty, Skeleton, Space, Divider, message } from 'antd';
import { CodeOutlined, DeleteOutlined, ArrowRightOutlined, InfoCircleOutlined } from '@ant-design/icons';
import client from '@/api/client';
import { lineageApi } from '@/api/endpoints/lineage';

const { Title, Text, Paragraph } = Typography;

interface EdgeDetailDrawerProps {
  id: string | null;
  open: boolean;
  onClose: () => void;
  onDeleteSuccess: () => void;
}

const EdgeDetailDrawer: React.FC<EdgeDetailDrawerProps> = ({ id, open, onClose, onDeleteSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  useEffect(() => {
    if (open && id) {
      fetchDetail();
    } else {
      setData(null);
    }
  }, [open, id]);

  const fetchDetail = async () => {
    setLoading(true);
    try {
      const res = await client.get<any, any>(`/lineage/relationship/${id}`);
      setData(res);
    } catch (error) {
      console.error('Failed to fetch edge detail', error);
      message.error('Failed to load relationship details');
    } finally {
      setLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!id) return;
    try {
      await lineageApi.delete(id);
      message.success('Lineage relationship deleted');
      onDeleteSuccess();
      onClose();
    } catch (error) {
      message.error('Failed to delete relationship');
    }
  };

  return (
    <Drawer
      title="Relationship Details"
      placement="right"
      width={500}
      onClose={onClose}
      open={open}
      extra={
        <Button danger type="text" icon={<DeleteOutlined />} onClick={handleDelete}>
          Delete
        </Button>
      }
    >
      {loading ? (
        <Skeleton active paragraph={{ rows: 10 }} />
      ) : data ? (
        <Space direction="vertical" size="large" style={{ width: '100%' }}>
          
          {/* Header: Flow Summary */}
          <Card size="small" style={{ background: '#f0f5ff', border: '1px solid #adc6ff' }}>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ textAlign: 'center', flex: 1 }}>
                <Text strong>{data.source?.name}</Text>
                <div style={{ fontSize: '10px', color: '#8c8c8c' }}>{data.source?.type?.toUpperCase()}</div>
              </div>
              <ArrowRightOutlined style={{ color: '#1890ff', fontSize: '20px', margin: '0 16px' }} />
              <div style={{ textAlign: 'center', flex: 1 }}>
                <Text strong>{data.target?.name}</Text>
                <div style={{ fontSize: '10px', color: '#8c8c8c' }}>{data.target?.type?.toUpperCase()}</div>
              </div>
            </div>
          </Card>

          {/* Transformation Logic */}
          <div>
            <Title level={5}><CodeOutlined /> Transformation Logic</Title>
            {data.transformation?.logic ? (
              <div style={{ 
                background: '#001529', 
                color: '#fff', 
                padding: '16px', 
                borderRadius: 8, 
                fontFamily: 'monospace',
                fontSize: '13px',
                overflowX: 'auto',
                whiteSpace: 'pre-wrap',
                marginTop: 8
              }}>
                {data.transformation.logic}
              </div>
            ) : (
              <Empty description="No transformation logic provided" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            )}
            {data.transformation?.description && (
              <Paragraph style={{ marginTop: 12, color: '#595959', fontStyle: 'italic' }}>
                <InfoCircleOutlined /> {data.transformation.description}
              </Paragraph>
            )}
          </div>

          <div style={{ marginTop: 'auto', paddingTop: 24 }}>
            <Divider style={{ margin: '12px 0' }} />

            {/* Metadata */}
            <Descriptions title="Audit Metadata" column={1} size="small" bordered>
              <Descriptions.Item label="Source Type">
                <Tag color={data.metadata?.source === 'manual' ? 'blue' : 'green'}>
                  {data.metadata?.source?.toUpperCase()}
                </Tag>
              </Descriptions.Item>
              {data.metadata?.confidence !== undefined && (
                <Descriptions.Item label="AI Confidence">
                  {(data.metadata.confidence * 100).toFixed(1)}%
                </Descriptions.Item>
              )}
              <Descriptions.Item label="Created By">{data.metadata?.created_by || 'Unknown'}</Descriptions.Item>
            </Descriptions>
          </div>

        </Space>
      ) : (
        <Empty description="No data found" />
      )}
    </Drawer>
  );
};

// Internal Card helper to avoid extra imports
const Card = ({ children, style, size }: any) => (
  <div style={{ padding: size === 'small' ? '12px' : '24px', borderRadius: 8, border: '1px solid #f0f0f0', ...style }}>
    {children}
  </div>
);

export default EdgeDetailDrawer;
