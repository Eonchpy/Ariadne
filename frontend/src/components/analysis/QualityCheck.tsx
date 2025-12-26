import React, { useState, useEffect, useCallback } from 'react';
import { Card, Space, Typography, Tag, List, message, Skeleton, Empty, Result, Alert, Button, Divider } from 'antd';
import { CheckCircleOutlined, WarningOutlined, RetweetOutlined, NodeIndexOutlined, ArrowRightOutlined } from '@ant-design/icons';
import { Link, useNavigate } from 'react-router-dom';
import client from '@/api/client';

const { Title, Text } = Typography;

interface QualityCheckProps {
  tableId: string;
}

const QualityCheck: React.FC<QualityCheckProps> = ({ tableId }) => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.get<any, any>(`/lineage/analysis/quality-check/${tableId}`);
      setData(response);
    } catch (error) {
      console.error('Failed to fetch quality check data', error);
      message.error('Failed to load quality audit');
    } finally {
      setLoading(false);
    }
  }, [tableId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading && !data) {
    return <Skeleton active paragraph={{ rows: 8 }} />;
  }

  if (!data) return <Empty description="No quality data available" />;

  const hasCycles = data.has_cycles;

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* 1. OVERALL STATUS */}
      <Card size="small">
        {hasCycles ? (
          <Result
            status="warning"
            icon={<WarningOutlined style={{ color: '#ff4d4f' }} />}
            title="Logic Conflict Detected"
            subTitle="This table is part of one or more circular dependency loops."
            extra={[
              <Button type="primary" danger key="graph" icon={<NodeIndexOutlined />} onClick={() => navigate(`/lineage/${tableId}`)}>
                Investigate in Graph
              </Button>,
              <Button key="retry" icon={<RetweetOutlined />} onClick={fetchData}>
                Re-scan
              </Button>,
            ]}
          />
        ) : (
          <Result
            status="success"
            title="Logic Audit Passed"
            subTitle="No circular dependencies or immediate logic conflicts found for this table."
            extra={[
              <Button key="retry" icon={<RetweetOutlined />} onClick={fetchData}>
                Scan Again
              </Button>
            ]}
          />
        )}
      </Card>

      {/* 2. CIRCULAR DEPENDENCIES LIST */}
      {hasCycles && (
        <div>
          <Title level={5}><WarningOutlined style={{ color: '#ff4d4f' }} /> Circular Dependency Paths</Title>
          <Alert 
            message="Circular dependencies violate the technical Directed Acyclic Graph (DAG) principle and may cause ETL execution failures or data inflation."
            type="error"
            showIcon
            style={{ marginBottom: 16 }}
          />
          
          <List
            dataSource={data.cycles || []}
            renderItem={(path: any[], index: number) => (
              <Card size="small" style={{ marginBottom: 12, borderLeft: '4px solid #ff4d4f' }} key={index}>
                <Space wrap size={[8, 16]} align="center">
                  {path.map((node: any, nIdx: number) => (
                    <React.Fragment key={node.id + nIdx}>
                      <div style={{ display: 'inline-block', textAlign: 'center' }}>
                        <Tag color={node.id === tableId ? 'red' : 'default'} style={{ margin: 0 }}>
                          <Link to={`/metadata/tables/${node.id}`}>{node.name}</Link>
                        </Tag>
                        {node.primary_tag_path && (
                          <div style={{ fontSize: '10px', color: '#8c8c8c', marginTop: 2 }}>{node.primary_tag_path}</div>
                        )}
                      </div>
                      {nIdx < path.length - 1 && <ArrowRightOutlined style={{ color: '#d9d9d9' }} />}
                    </React.Fragment>
                  ))}
                </Space>
              </Card>
            )}
          />
        </div>
      )}

      {/* 3. FUTURE CHECKS PLACEHOLDER */}
      <Divider>
        <Text type="secondary" style={{ fontSize: '12px' }}>Future Quality Metrics</Text>
      </Divider>
      <div style={{ opacity: 0.5 }}>
        <Space size="large">
          <Text disabled><CheckCircleOutlined /> Orphan Table Check (Pass)</Text>
          <Text disabled><CheckCircleOutlined /> Stale Metadata Check (Pass)</Text>
          <Text disabled><CheckCircleOutlined /> Schema Drift Monitor (N/A)</Text>
        </Space>
      </div>
    </Space>
  );
};

export default QualityCheck;
