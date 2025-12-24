import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  Position
} from 'reactflow';
import type { Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, Space, Select, Typography, Slider, Button, message, Empty, Modal } from 'antd';
import { FilterOutlined, RetweetOutlined, DownloadOutlined, PlusOutlined, SearchOutlined } from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { lineageApi } from '@/api/endpoints/lineage';
import { tablesApi } from '@/api/endpoints/tables';
import TableNode from '@/components/lineage/TableNode';
import FieldNode from '@/components/lineage/FieldNode';
import LineageErrorBoundary from '@/components/lineage/LineageErrorBoundary';
import CreateLineageModal from '@/components/lineage/CreateLineageModal';
import type { LineageGraphNode, Table as MetadataTable } from '@/types/api';
import dagre from 'dagre';

const { Text } = Typography;
const { Option } = Select;

const nodeTypes = {
  table: TableNode,
  field: FieldNode,
};

// --- DAGRE LAYOUT ENGINE ---
const dagreGraph = new dagre.graphlib.Graph();
dagreGraph.setDefaultEdgeLabel(() => ({}));

const getLayoutedElements = (nodes: any[], edges: any[], direction = 'LR') => {
  dagreGraph.setGraph({ rankdir: direction });

  nodes.forEach((node) => {
    // Approx dimensions of TableNode
    dagreGraph.setNode(node.id, { width: 260, height: 120 });
  });

  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  dagre.layout(dagreGraph);

  return nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      targetPosition: Position.Left,
      sourcePosition: Position.Right,
      position: {
        x: nodeWithPosition.x - 130,
        y: nodeWithPosition.y - 60,
      },
    };
  });
};
// ----------------------------

const LineageGraph: React.FC = () => {
  const { tableId } = useParams<{ tableId: string }>();
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [depth, setDepth] = useState(3);
  const [direction, setDirection] = useState<'upstream' | 'downstream'>('upstream');
  const [loading, setLoading] = useState(false);
  const [isCreateModalVisible, setCreateModalVisible] = useState(false);
  const [allTables, setAllTables] = useState<MetadataTable[]>([]);
  const [highlightedFieldIds, setHighlightedFieldIds] = useState<string[]>([]);
  const [rawLineageData, setRawLineageData] = useState<any>(null);

  const fetchTables = async () => {
    try {
      const response = await tablesApi.list({ size: 100 });
      setAllTables(response.items);
    } catch (error) {
      console.error('Failed to fetch tables for search');
    }
  };

  const onFieldClick = (fieldId: string) => {
    console.log(`Starting trace from field: ${fieldId}`);
    if (!rawLineageData) return;

    const related = new Set<string>([fieldId]);
    let size;
    
    // Use raw backend edges for tracing to ensure we catch all connections
    do {
      size = related.size;
      rawLineageData.edges.forEach((edge: any) => {
        const src = edge.from || edge.source_id;
        const tgt = edge.to || edge.target_id;
        
        if (related.has(src)) related.add(tgt);
        if (related.has(tgt)) related.add(src);
      });
    } while (related.size > size);

    setHighlightedFieldIds(Array.from(related));
    message.info(`Tracing field lineage: ${related.size} nodes found`);
  };

  const resetHighlight = () => {
    setHighlightedFieldIds([]);
  };

  const handleDeleteEdge = (edgeId: string) => {
    Modal.confirm({
      title: 'Delete Lineage Relationship?',
      content: 'Are you sure you want to remove this connection? This will delete the relationship from the graph database.',
      okText: 'Delete',
      okType: 'danger',
      onOk: async () => {
        try {
          await lineageApi.delete(edgeId);
          message.success('Lineage relationship deleted');
          fetchLineage();
        } catch (error) {
          message.error('Failed to delete lineage');
        }
      },
    });
  };

  const onEdgeClick = (_: React.MouseEvent, edge: Edge) => {
    handleDeleteEdge(edge.id);
  };

  const fetchLineage = useCallback(async () => {
    if (!tableId) {
      setNodes([]);
      setEdges([]);
      setRawLineageData(null);
      return;
    }
    setLoading(true);
    try {
      const data = direction === 'upstream' 
        ? await lineageApi.getUpstream(tableId, depth)
        : await lineageApi.getDownstream(tableId, depth);

      setRawLineageData(data);
    } catch (error) {
      message.error('Failed to load lineage graph');
    } finally {
      setLoading(false);
    }
  }, [tableId, depth, direction]);

  // Transform raw data into ReactFlow nodes/edges whenever data or highlighting changes
  useEffect(() => {
    if (!rawLineageData) return;

    const data = rawLineageData;
    const isTracing = highlightedFieldIds.length > 0;

    const tableNodesData = data.nodes.filter((n: LineageGraphNode) => n.type === 'table');
    const fieldNodesData = data.nodes.filter((n: LineageGraphNode) => n.type === 'field');

        const initialNodes = tableNodesData.map((n: LineageGraphNode) => {

          const tableFields = fieldNodesData.filter((f: LineageGraphNode) => f.parent_id === n.id);

          const hasHighlightedField = tableFields.some((f: LineageGraphNode) => highlightedFieldIds.includes(f.id));

          

          return {

            id: n.id,

            type: 'table',

            position: { x: 0, y: 0 },

            data: { 

              label: n.label, 

              source_name: n.source_name,

              fields: tableFields,

              highlightedFields: highlightedFieldIds,

              forceExpand: hasHighlightedField,

              onFieldClick: onFieldClick,

              isDimmed: isTracing && !hasHighlightedField && n.id !== tableId

            },

          };

        });

    

        const flowEdges = data.edges.map((e: any) => {

          const rawSrc = e.from || e.source_id;

          const rawTgt = e.to || e.target_id;

          

          let sourceId = rawSrc;

          let targetId = rawTgt;

          let sourceHandle: string | undefined = undefined;

          let targetHandle: string | undefined = undefined;

    

          const sourceNode = data.nodes.find((n: any) => n.id === sourceId);

          const targetNode = data.nodes.find((n: any) => n.id === targetId);

    

          if (sourceNode?.type === 'field' && sourceNode.parent_id) {

            sourceHandle = sourceId;

            sourceId = sourceNode.parent_id;

          }

    

          if (targetNode?.type === 'field' && targetNode.parent_id) {

            targetHandle = targetId;

            targetId = targetNode.parent_id;

          }

    

          const type = e.lineage_source?.toLowerCase() || 'manual';

          const isRelatedToTrace = isTracing && (

            highlightedFieldIds.includes(rawSrc) || 

            highlightedFieldIds.includes(rawTgt)

          );

          

          return {

            id: e.id || `e-${sourceId}-${targetId}-${sourceHandle || ''}-${targetHandle || ''}`,

            source: sourceId as string,

            target: targetId as string,

            sourceHandle,

            targetHandle,

            label: isTracing && !isRelatedToTrace ? "" : type.toUpperCase(),

            animated: !!(type === 'inferred' || isRelatedToTrace),

            style: { 

              stroke: isTracing ? (isRelatedToTrace ? '#1890ff' : '#f0f0f0') : (type === 'manual' ? '#1890ff' : type === 'approved' ? '#52c41a' : '#d9d9d9'),

              strokeWidth: isRelatedToTrace ? 3 : (sourceHandle || targetHandle ? 1 : 2),

              opacity: isTracing && !isRelatedToTrace ? 0.2 : 1,

              cursor: 'pointer',

              zIndex: isRelatedToTrace ? 1000 : 1

            },

            markerEnd: {

              type: MarkerType.ArrowClosed,

              color: isTracing ? (isRelatedToTrace ? '#1890ff' : '#f0f0f0') : (type === 'manual' ? '#1890ff' : type === 'approved' ? '#52c41a' : '#d9d9d9'),

            },

          };

        });

    

        const layoutedNodes = getLayoutedElements(initialNodes, flowEdges, 'LR');

    

        setNodes(layoutedNodes as any);

        setEdges(flowEdges as any);
  }, [rawLineageData, highlightedFieldIds, tableId, setNodes, setEdges]);

  useEffect(() => {
    fetchTables();
  }, []);

  useEffect(() => {
    fetchLineage();
  }, [fetchLineage]);

  const handleTableSelect = (id: string) => {
    setHighlightedFieldIds([]);
    navigate(`/lineage/${id}`);
  };

  return (
    <LineageErrorBoundary>
      <div style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size="large" wrap>
              <Space>
                <SearchOutlined />
                <Select
                  showSearch
                  placeholder="Select a table"
                  style={{ width: 250 }}
                  optionFilterProp="children"
                  onChange={handleTableSelect}
                  value={tableId}
                >
                  {allTables.map(t => (
                    <Option key={t.id} value={t.id}>{t.name}</Option>
                  ))}
                </Select>
              </Space>
              
              <Space>
                <FilterOutlined />
                <Select value={direction} onChange={(val) => setDirection(val as any)} style={{ width: 120 }}>
                  <Option value="upstream">Upstream</Option>
                  <Option value="downstream">Downstream</Option>
                </Select>
              </Space>
              
              <div style={{ width: 150, marginLeft: 8 }}>
                <Text type="secondary" style={{ fontSize: '11px' }}>Depth: {depth}</Text>
                <Slider 
                  min={1} 
                  max={5} 
                  value={depth} 
                  onChange={setDepth} 
                  marks={{ 1: '1', 5: '5' }}
                />
              </div>
            </Space>
            <Space>
              {highlightedFieldIds.length > 0 && (
                <Button danger onClick={resetHighlight}>Clear Trace</Button>
              )}
              <Button icon={<RetweetOutlined />} onClick={fetchLineage} loading={loading} disabled={!tableId}>Refresh</Button>
              <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>Create Lineage</Button>
              <Button icon={<DownloadOutlined />} disabled={!tableId}>Export</Button>
            </Space>
          </div>
        </Card>

        <div style={{ flex: 1, border: '1px solid #f0f0f0', borderRadius: 8, background: '#fafafa', position: 'relative' }}>
          {!tableId ? (
            <div style={{ position: 'absolute', top: '50%', left: '50%', transform: 'translate(-50%, -50%)', zIndex: 10 }}>
              <Empty description="Select a table from the search bar above to visualize its lineage relationships." />
            </div>
          ) : (
            <ReactFlow
              nodes={nodes}
              edges={edges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onEdgeClick={onEdgeClick}
              nodeTypes={nodeTypes}
              fitView
            >
              <Background />
              <Controls />
              <MiniMap />
            </ReactFlow>
          )}
        </div>
      </div>
      <CreateLineageModal 
        visible={isCreateModalVisible} 
        onClose={() => setCreateModalVisible(false)}
        onSuccess={fetchLineage}
        initialSourceTableId={direction === 'downstream' ? tableId : undefined}
        initialTargetTableId={direction === 'upstream' ? tableId : undefined}
      />
    </LineageErrorBoundary>
  );
};

export default LineageGraph;
