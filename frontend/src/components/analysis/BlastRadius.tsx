import React, { useState, useEffect, useCallback } from 'react';
import { Card, Space, Typography, Tag, Slider, Radio, Statistic, Row, Col, List, message, Skeleton, Empty, Collapse } from 'antd';
import { FireOutlined, BranchesOutlined, ApartmentOutlined, AlertOutlined, InfoCircleOutlined } from '@ant-design/icons';
import { Link } from 'react-router-dom';
import client from '@/api/client';

const { Title, Text } = Typography;
const { Panel } = Collapse;

interface BlastRadiusProps {
  tableId: string;
}

const BlastRadius: React.FC<BlastRadiusProps> = ({ tableId }) => {
  const [direction, setDirection] = useState<'upstream' | 'downstream'>('downstream');
  const [depth, setDepth] = useState(5);
  const [loading, setLoading] = useState(false);
  const [data, setData] = useState<any>(null);

  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const response = await client.get<any, any>(`/lineage/analysis/blast-radius/${tableId}`, {
        params: { direction, depth, granularity: 'table' }
      });
      setData(response);
    } catch (error) {
      console.error('Failed to fetch blast radius data', error);
      message.error('Failed to load impact analysis');
    } finally {
      setLoading(false);
    }
  }, [tableId, direction, depth]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading && !data) {
    return <Skeleton active paragraph={{ rows: 10 }} />;
  }

  if (!data) return <Empty description="No analysis data available" />;

  const severityColor = {
    high: '#ff4d4f',
    medium: '#faad14',
    low: '#52c41a'
  }[data.severity_level as 'high' | 'medium' | 'low'] || '#d9d9d9';

  return (
    <Space direction="vertical" size="large" style={{ width: '100%' }}>
      {/* Controls */}
      <Card size="small">
        <Row align="middle" gutter={24}>
          <Col>
            <Text strong>Direction: </Text>
            <Radio.Group value={direction} onChange={e => setDirection(e.target.value)} size="small">
              <Radio.Button value="downstream">Impact (Downstream)</Radio.Button>
              <Radio.Button value="upstream">Vulnerability (Upstream)</Radio.Button>
            </Radio.Group>
          </Col>
          <Col flex="auto">
            <Space style={{ width: '100%' }}>
              <Text strong>Depth: </Text>
              <Slider 
                min={1} 
                max={20} 
                value={depth} 
                onChange={setDepth} 
                style={{ width: 200 }} 
                marks={{ 1: '1', 5: '5', 10: '10', 20: '20' }}
              />
            </Space>
          </Col>
        </Row>
      </Card>

      {/* Summary Metrics */}
      <Row gutter={16}>
        <Col span={6}>
          <Card bordered={false} style={{ borderTop: `4px solid ${severityColor}` }}>
            <Statistic 
              title="Severity Level" 
              value={data.severity_level?.toUpperCase()} 
              valueStyle={{ color: severityColor }}
              prefix={<AlertOutlined />}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderTop: '4px solid #1890ff' }}>
            <Statistic 
              title="Impacted Tables" 
              value={data.total_impacted_tables} 
              prefix={<ApartmentOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderTop: '4px solid #722ed1' }}>
            <Statistic 
              title="Affected Domains" 
              value={data.total_impacted_domains} 
              prefix={<BranchesOutlined />} 
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card bordered={false} style={{ borderTop: '4px solid #fa8c16' }}>
            <Statistic 
              title="Max Depth" 
              value={data.max_depth_reached} 
              suffix={`/ ${depth}`}
              prefix={<FireOutlined />} 
            />
          </Card>
        </Col>
      </Row>

      {/* Domain Distribution */}
      <div>
        <Title level={5}><BranchesOutlined /> Impact by Business Domain</Title>
        <Collapse ghost expandIconPosition="end">
          {(data.domain_groups || []).map((group: any) => (
            <Panel 
              header={
                <Space size="large" style={{ width: '100%', justifyContent: 'space-between' }}>
                  <Space>
                    <Tag color={group.severity === 'high' ? 'red' : group.severity === 'medium' ? 'orange' : 'green'}>
                      {group.severity?.toUpperCase()}
                    </Tag>
                    <Text strong>{group.tag_name}</Text>
                    <Text type="secondary" style={{ fontSize: '12px' }}>{group.tag_path}</Text>
                  </Space>
                  <Text type="secondary">{group.table_count} Tables Affected</Text>
                </Space>
              } 
              key={group.tag_id}
            >
              <List
                size="small"
                dataSource={group.sample_tables || []}
                renderItem={(table: any) => (
                  <List.Item>
                    <Space>
                      <Link to={`/metadata/tables/${table.id}`}>{table.name}</Link>
                      <Tag color="default">{table.distance} hops</Tag>
                    </Space>
                  </List.Item>
                )}
              />
            </Panel>
          ))}
        </Collapse>
      </div>

      {/* Depth Map (Optional Visual) */}
      {data.depth_map && Object.keys(data.depth_map).length > 0 && (
        <Card size="small" title={<Space><InfoCircleOutlined /> Impact Distribution by Depth</Space>}>
          <Row gutter={[16, 16]}>
            {Object.entries(data.depth_map).sort(([a], [b]) => Number(a) - Number(b)).map(([hop, count]) => (
              <Col key={hop}>
                <div style={{ textAlign: 'center', padding: '8px', background: '#f5f5f5', borderRadius: 4, minWidth: 80 }}>
                  <div style={{ fontSize: '12px', color: '#8c8c8c' }}>Hop {hop}</div>
                  <div style={{ fontSize: '18px', fontWeight: 'bold' }}>{count as number}</div>
                </div>
              </Col>
            ))}
          </Row>
        </Card>
      )}
    </Space>
  );
};

export default BlastRadius;
