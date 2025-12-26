import React, { useEffect, useState, useCallback } from 'react';
import ReactFlow, { 
  Background, 
  Controls, 
  MiniMap, 
  useNodesState, 
  useEdgesState,
  MarkerType,
  Position,
  ReactFlowProvider,
  useReactFlow
} from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, Space, Select, Slider, Button, message, Empty, Drawer, List, Modal } from 'antd';
import { 
  FilterOutlined, 
  RetweetOutlined, 
  PlusOutlined, 
  SearchOutlined
} from '@ant-design/icons';
import { useParams, useNavigate } from 'react-router-dom';
import { tablesApi } from '@/api/endpoints/tables';
import { lineageApi } from '@/api/endpoints/lineage';
import TableNode from '@/components/lineage/TableNode';
import FieldNode from '@/components/lineage/FieldNode';
import BucketNode from '@/components/lineage/BucketNode';
import LineageErrorBoundary from '@/components/lineage/LineageErrorBoundary';
import CreateLineageModal from '@/components/lineage/CreateLineageModal';
import client from '@/api/client';
import type { Table as MetadataTable } from '@/types/api';
import dagre from 'dagre';

const { Option } = Select;

const nodeTypes = {
  table: TableNode,
  field: FieldNode,
  bucket: BucketNode,
};

// --- V6.0 CONTAINERIZED PROJECTION ENGINE ---

const projectGraphV6 = (
  rawNodes: any[], 
  rawEdges: any[],
  focalTableId: string, 
  manualExpandedPaths: string[],
  involvedInTrace: string[],
  extractedTableIds: string[]
) => {
  const getPath = (t: any) => t?.primary_tag?.path || t?.primary_tag_path || null;

  // 0. Count tables for Adaptive Threshold using rawNodes
  const tablesCount = rawNodes.filter(n => n.type === 'table');
  const threshold = Number(import.meta.env.VITE_LINEAGE_AGGREGATION_THRESHOLD) || 15;
  const shouldAggregate = tablesCount.length > threshold || manualExpandedPaths.length > 0;

  if (!shouldAggregate) {
      return { visibleTables: tablesCount, buckets: [] };
  }

  // 1. Identify Active Nodes
  const activeNodeIds = new Set([focalTableId, ...involvedInTrace, ...extractedTableIds]);
  rawEdges.forEach(e => {
      activeNodeIds.add((e.from || e.source_id).split('.')[0]);
      activeNodeIds.add((e.to || e.target_id).split('.')[0]);
  });
  const activeNodes = rawNodes.filter(n => activeNodeIds.has(n.id));
  const tables = activeNodes.filter(n => n.type === 'table');
  const visibleTables: any[] = [];
  const buckets: any[] = [];
  
  const hasUp = new Set();
  const hasDown = new Set();
  rawEdges.forEach(e => {
      hasUp.add((e.to || e.target_id).split('.')[0]);
      hasDown.add((e.from || e.source_id).split('.')[0]);
  });

  const focalNode = rawNodes.find(n => n.id === focalTableId);
  const focalPath = getPath(focalNode);

  const bridgeIds = tables.filter(t => {
      const isTechnicalBridge = hasUp.has(t.id) && hasDown.has(t.id);
      if (!isTechnicalBridge) return false;
      const myPath = getPath(t);
      if (myPath === focalPath) return false;
      const myUpstreamEdges = rawEdges.filter(e => (e.to || e.target_id).split('.')[0] === t.id);
      const sharesDomainWithParent = myUpstreamEdges.some(e => {
          const parentId = (e.from || e.source_id).split('.')[0];
          const parentNode = rawNodes.find(n => n.id === parentId);
          return getPath(parentNode) === myPath;
      });
      if (sharesDomainWithParent) return false;
      return true;
  }).map(t => t.id);

  const domainStats = new Map<string, { total: number, visible: number }>();
  tables.forEach(t => {
      const path = getPath(t);
      if (!path) return;
      const parts = path.split('-');
      const cumulativePaths = parts.map((_: string, i: number) => parts.slice(0, i + 1).join('-'));
      const isVisible = t.id === focalTableId || involvedInTrace.includes(t.id) || extractedTableIds.includes(t.id) || bridgeIds.includes(t.id);
      cumulativePaths.forEach((p: string) => {
          if (!domainStats.has(p)) domainStats.set(p, { total: 0, visible: 0 });
          const s = domainStats.get(p)!;
          s.total++;
          if (isVisible) s.visible++;
      });
  });

  const autoExpanded = Array.from(domainStats.entries())
    .filter(([_, s]) => s.total > 0 && s.total === s.visible)
    .map(([p]) => p);

  const expanded = Array.from(new Set([...manualExpandedPaths, ...autoExpanded]));

  const domainGroups = new Map<string, any[]>();
  const independentIds = new Set([focalTableId, ...involvedInTrace, ...extractedTableIds, ...bridgeIds]);

  tables.forEach(node => {
    const path = getPath(node);
    if (independentIds.has(node.id) || !path) {
      visibleTables.push(node);
      return;
    }
    const parts = path!.split('-');
    let targetBucketKey: string | null = null;
    let currentPath = "";
    for (let i = 0; i < parts.length; i++) {
        const segment = parts[i];
        currentPath = i === 0 ? segment : `${currentPath}-${segment}`;
        if (!expanded.includes(currentPath)) {
            targetBucketKey = currentPath;
            break;
        }
    }
    if (targetBucketKey) {
        if (!domainGroups.has(targetBucketKey)) domainGroups.set(targetBucketKey, []);
        domainGroups.get(targetBucketKey)!.push(node);
    } else {
        visibleTables.push(node);
    }
  });

  domainGroups.forEach((items, key) => {
      buckets.push({ 
          id: `bucket_${key}`, 
          type: 'bucket', 
          label: key.split('-').pop(), 
          tag_path: key, 
          isExpanded: false, 
          level: key.split('-').length,
          table_count: items.length, 
          tables: items 
      });
  });

  expanded.forEach(p => {
      const hasUnextractedActiveMember = activeNodes.some(n => {
          const nPath = getPath(n);
          const isIndependent = n.id === focalTableId || extractedTableIds.includes(n.id) || bridgeIds.includes(n.id);
          return !isIndependent && nPath && nPath.startsWith(p);
      });
      if (hasUnextractedActiveMember && domainStats.has(p)) {
          buckets.push({ 
              id: `bucket_${p}`, 
              type: 'bucket', 
              label: p.split('-').pop(), 
              tag_path: p, 
              isExpanded: true, 
              level: p.split('-').length,
              table_count: domainStats.get(p)?.total || 0, 
              tables: [] 
          });
      }
  });

  return { visibleTables, buckets };
};

// --- DAGRE LAYOUT ENGINE ---
const getLayoutedElements = (nodes: any[], edges: any[], direction = 'LR') => {
  const dagreGraph = new dagre.graphlib.Graph({ compound: true });
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ rankdir: direction, nodesep: 120, ranksep: 240, ranker: 'longest-path' });

  const getPath = (n: any) => n.data?.tag_path || n.data?.primary_tag?.path || n.data?.primary_tag_path || null;
  const expandedBuckets = nodes.filter(n => n.data?.isExpanded).sort((a, b) => b.data.tag_path.split('-').length - a.data.tag_path.length);

  const nodeParentMap = new Map<string, string>();
  nodes.forEach(n => {
      const path = getPath(n);
      if (!path) return;
      const parts = path.split('-');
      const startDepth = n.type === 'bucket' ? parts.length - 1 : parts.length;
      for (let i = startDepth; i >= 1; i--) {
          const pPath = parts.slice(0, i).join('-');
          const parent = expandedBuckets.find(eb => eb.data.tag_path === pPath && eb.id !== n.id);
          if (parent) { nodeParentMap.set(n.id, parent.id); break; }
      }
  });

  nodes.forEach((node) => {
    if (!node.data?.isExpanded) {
        dagreGraph.setNode(node.id, { width: node.type === 'bucket' ? 240 : 300, height: node.type === 'bucket' ? 80 : 200 });
    } else { dagreGraph.setNode(node.id, {}); }
    const parentId = nodeParentMap.get(node.id);
    if (parentId) { dagreGraph.setParent(node.id, parentId); }
  });

  edges.forEach((edge) => { dagreGraph.setEdge(edge.source, edge.target); });
  dagre.layout(dagreGraph);

  const absoluteNodes = nodes.map((node) => {
    const pos = dagreGraph.node(node.id);
    if (!node.data?.isExpanded) {
        return { ...node, targetPosition: Position.Left, sourcePosition: Position.Right, position: { x: pos.x - (pos.width / 2), y: pos.y - (pos.height / 2) } };
    }
    return { ...node, position: { x: pos.x - (pos.width / 2), y: pos.y - (pos.height / 2) }, style: { width: pos.width + 40, height: pos.height + 40, zIndex: -1 }, data: { ...node.data, width: pos.width + 40, height: pos.height + 40 } };
  });

  return absoluteNodes.map(node => {
      const parentId = nodeParentMap.get(node.id);
      if (parentId) {
          const parent = absoluteNodes.find(n => n.id === parentId)!;
          return { ...node, parentNode: parentId, extent: 'parent' as const, position: { x: node.position.x - parent.position.x, y: node.position.y - parent.position.y } };
      }
      return node;
  });
};

const LineageGraphContent: React.FC = () => {
  const { tableId } = useParams<{ tableId: string }>();
  const navigate = useNavigate();
  const { setCenter } = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [depth, setDepth] = useState(3);
  const [direction, setDirection] = useState<'upstream' | 'downstream'>('upstream');
  const [loading, setLoading] = useState(false);
  const [isCreateModalVisible, setCreateModalVisible] = useState(false);
  const [rawLineageData, setRawLineageData] = useState<any>(null);
  const [allTables, setAllTables] = useState<MetadataTable[]>([]);
  const [highlightedFieldIds, setHighlightedFieldIds] = useState<string[]>([]);
  const [isFirstLoad, setIsFirstLoad] = useState(true);
  
  const [manualExpandedPaths, setManualExpandedPaths] = useState<string[]>([]);
  const [involvedTables, setInvolvedTables] = useState<string[]>([]);
  const [bucketDrawerVisible, setBucketDrawerVisible] = useState(false);
  const [activeBucket, setActiveBucket] = useState<any>(null);
  const [bucketTables, setBucketTables] = useState<any[]>([]);
  const [extractedTableIds, setExtractedTableIds] = useState<string[]>([]);
  const [lastExtractedId, setLastExtractedId] = useState<string | null>(null);

  const fetchTables = async () => {
    try { const response = await tablesApi.list({ size: 500 }); setAllTables(response.items); } catch (error) { console.error(error); }
  };

  const performLocalTrace = (fieldId: string) => {
    if (!rawLineageData) return;
    const { nodes: rNodes, edges: rEdges } = rawLineageData;
    const related = new Set<string>([fieldId]);
    const tables = new Set<string>();
    let size;
    do {
      size = related.size;
      rEdges.forEach((edge: any) => {
        const src = edge.from || edge.source_id;
        const tgt = edge.to || edge.target_id;
        if (related.has(src)) related.add(tgt);
        if (related.has(tgt)) related.add(src);
      });
    } while (related.size > size);
    related.forEach(fid => {
      const n = rNodes.find((node:any) => node.id === fid);
      if (n?.parent_id) tables.add(n.parent_id);
      else if (n?.type === 'table') tables.add(n.id);
    });
    setInvolvedTables(Array.from(tables));
    setHighlightedFieldIds(Array.from(related));
  };

  const onFieldClick = async (fieldId: string) => {
    try {
      const result = await client.get<any, any>(`/lineage/trace/field/${fieldId}`);
      setInvolvedTables(result.involved_tables || []);
      setHighlightedFieldIds(result.involved_fields || []);
    } catch (error) { performLocalTrace(fieldId); }
  };

  const fetchLineage = useCallback(async () => {
    if (!tableId) return;
    setLoading(true);
    try {
      setIsFirstLoad(true);
      const params = { table_id: tableId, direction, depth };
      const data = await client.get<any, any>(`/lineage/graph`, { params });
      setRawLineageData(data);
    } catch (error) { message.error('Failed to load'); }
    finally { setLoading(false); }
  }, [tableId, direction, depth]);

  const resetHighlight = () => {
    setHighlightedFieldIds([]);
    setInvolvedTables([]);
    setIsFirstLoad(false); 
  };

  useEffect(() => { fetchTables(); fetchLineage(); }, [fetchLineage]);
  useEffect(() => {
    setHighlightedFieldIds([]); setInvolvedTables([]); setManualExpandedPaths([]); setExtractedTableIds([]); setIsFirstLoad(true);
  }, [tableId, direction]);

  const onNodeClick = (_: any, node: any) => {
    if (node.type === 'bucket' && !node.data?.isExpanded) {
      setActiveBucket(node.data);
      setBucketTables(node.data.tables || []);
      setBucketDrawerVisible(true);
    }
  };


  const onEdgeClick = (_: any, edge: any) => {
    if (edge.id.startsWith('path-') || edge.id.startsWith('e-')) {
        Modal.confirm({
            title: 'Delete Lineage Relationship?',
            content: 'This will permanently remove the relationship.',
            onOk: async () => {
                try {
                    const originalId = edge.id.replace('e-', '').replace('path-', '').split('-')[0];
                    await lineageApi.delete(originalId);
                    message.success('Deleted');
                    fetchLineage();
                } catch (error) { message.error('Failed'); }
            }
        });
    }
  };

  const handleBucketExpand = (p: string) => { setManualExpandedPaths(prev => [...prev, p]); setIsFirstLoad(false); };
  const handleBucketCollapse = (p: string) => { setManualExpandedPaths(prev => prev.filter(x => !x.startsWith(p))); setIsFirstLoad(false); };
  const extractTable = (t: any) => { setExtractedTableIds(prev => [...prev, t.id]); setLastExtractedId(t.id); setBucketDrawerVisible(false); setIsFirstLoad(false); };

  useEffect(() => {
    if (lastExtractedId && nodes.length > 0) {
      const timeout = setTimeout(() => {
        const node = nodes.find(n => n.id === lastExtractedId);
        if (node) {
          let absX = node.position.x, absY = node.position.y, curr = node;
          while (curr.parentNode) {
              const parent = nodes.find(n => n.id === curr.parentNode);
              if (parent) { absX += parent.position.x; absY += parent.position.y; curr = parent; } else break;
          }
          setCenter(absX + 150, absY + 80, { zoom: 1.2, duration: 800 });
        }
        setTimeout(() => setLastExtractedId(null), 6000);
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [lastExtractedId, nodes, setCenter]);

  useEffect(() => {
    if (!rawLineageData || !tableId) return;
    const { nodes: rNodes, edges: rEdges } = rawLineageData;
    const isTracing = highlightedFieldIds.length > 0;
    const getPath = (n: any) => n?.tag_path || n?.primary_tag?.path || n?.primary_tag_path || null;

    const { visibleTables, buckets } = projectGraphV6(rNodes, rEdges, tableId, manualExpandedPaths, involvedTables, extractedTableIds);

    const flowNodes = [...visibleTables, ...buckets].map(n => {
        const isBucket = n.type === 'bucket';
        const fields = isBucket ? [] : rNodes.filter((f: any) => f.type === 'field' && f.parent_id === n.id);
        const isTracedTable = involvedTables.includes(n.id) || n.id === tableId;
        
        return {
            id: n.id, type: isBucket ? 'bucket' : 'table', position: { x: 0, y: 0 },
            data: { 
                ...n, 
                label: n.label || n.name, 
                fields, 
                highlightedFields: highlightedFieldIds, 
                isNew: n.id === lastExtractedId, 
                isTraced: isTracedTable, 
                onFieldClick, onExpand: handleBucketExpand, onCollapse: handleBucketCollapse, 
                isDimmed: isTracing && !isTracedTable, 
                side: direction === 'upstream' ? 'left' : 'right' 
            }
        };
    });

    const finalEdges: any[] = [];
    const edgeSet = new Set<string>();

    rEdges.forEach((e: any) => {
        const rawSrcId = e.from || e.source_id, rawTgtId = e.to || e.target_id;
        const getVisibleProxyId = (nodeId: string) => {
            const node = rNodes.find((n: any) => n.id === nodeId);
            if (!node) return nodeId;
            const ownerId = node.type === 'field' ? node.parent_id : node.id;
            if (ownerId === tableId || visibleTables.some((vn:any) => vn.id === ownerId)) return ownerId;
            const ownerNode = rNodes.find((n:any) => n.id === ownerId);
            const path = getPath(ownerNode);
            if (path) {
                const parts = path.split('-');
                for (let i = parts.length; i >= 1; i--) {
                    const sub = parts.slice(0, i).join('-');
                    const b = buckets.find(vb => vb.tag_path === sub && !vb.isExpanded);
                    if (b) return b.id;
                }
            }
            return ownerId;
        };

        const sProxyId = getVisibleProxyId(rawSrcId), tProxyId = getVisibleProxyId(rawTgtId);
        if (sProxyId === tProxyId) return;

        let sH: string | undefined = undefined, tH: string | undefined = undefined;
        const srcN = rNodes.find((n: any) => n.id === rawSrcId), tgtN = rNodes.find((n: any) => n.id === rawTgtId);
        if (srcN?.type === 'field' && sProxyId === srcN.parent_id) sH = rawSrcId;
        if (tgtN?.type === 'field' && tProxyId === tgtN.parent_id) tH = rawTgtId;

        const edgeKey = `${sProxyId}-${tProxyId}-${sH || ''}-${tH || ''}`;
        if (!edgeSet.has(edgeKey)) {
            edgeSet.add(edgeKey);
            const isRel = isTracing && (highlightedFieldIds.includes(rawSrcId) || highlightedFieldIds.includes(rawTgtId));
            
            finalEdges.push({ 
                id: `e-${edgeKey}`, 
                source: sProxyId, 
                target: tProxyId, 
                sourceHandle: sH, 
                targetHandle: tH, 
                label: isRel || !isTracing ? (e.lineage_source?.toUpperCase() || "") : "", 
                animated: isRel || e.lineage_source === 'inferred', 
                style: { 
                    stroke: isRel ? '#1890ff' : '#d9d9d9', 
                    strokeWidth: isRel ? 3 : (sH || tH ? 1 : 2), 
                    opacity: isTracing && !isRel ? 0.2 : 1 
                }, 
                markerEnd: { type: MarkerType.ArrowClosed, color: isRel ? '#1890ff' : '#d9d9d9' } 
            });
        }
    });

    const layouted = getLayoutedElements(flowNodes, finalEdges, 'LR');
    setNodes(layouted as any);
    setEdges(finalEdges as any);
  }, [rawLineageData, highlightedFieldIds, tableId, manualExpandedPaths, extractedTableIds, involvedTables, direction, setNodes, setEdges]);

  return (
    <LineageErrorBoundary>
      <div style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
        <Card size="small" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Space size="large" wrap>
              <Space><SearchOutlined /><Select showSearch placeholder="Select a table" style={{ width: 250 }} optionFilterProp="children" onChange={(id) => navigate(`/lineage/${id}`)} value={tableId}>
                {allTables.map(t => (<Option key={t.id} value={t.id}>{t.name}</Option>))}
              </Select></Space>
              <Space><FilterOutlined /><Select value={direction} onChange={(val) => setDirection(val as any)} style={{ width: 120 }}>
                <Option value="upstream">Upstream</Option><Option value="downstream">Downstream</Option>
              </Select></Space>
              <div style={{ width: 150, marginLeft: 8 }}><Slider min={1} max={5} value={depth} onChange={setDepth} marks={{ 1: '1', 5: '5' }} /></div>
            </Space>
            <Space>
              {highlightedFieldIds.length > 0 && <Button danger onClick={resetHighlight}>Clear Trace</Button>}
              <Button icon={<RetweetOutlined />} onClick={fetchLineage} loading={loading} disabled={!tableId}>Refresh</Button>
              <Button icon={<PlusOutlined />} onClick={() => setCreateModalVisible(true)}>Create Lineage</Button>
            </Space>
          </div>
        </Card>
        <div style={{ flex: 1, border: '1px solid #f0f0f0', borderRadius: 8, background: '#fafafa', position: 'relative' }}>
          {tableId ? (
            <ReactFlow 
              nodes={nodes} 
              edges={edges} 
              onNodesChange={onNodesChange} 
              onEdgesChange={onEdgesChange} 
              onNodeClick={onNodeClick} 
              onEdgeClick={onEdgeClick}
              nodeTypes={nodeTypes} 
              fitView={isFirstLoad}
            >
              <Background /><Controls /><MiniMap />
            </ReactFlow>
          ) : <Empty style={{ marginTop: 100 }} />}
        </div>
      </div>
      <Drawer title={activeBucket ? `Bucket: ${activeBucket.label}` : 'Bucket Contents'} placement="right" onClose={() => setBucketDrawerVisible(false)} open={bucketDrawerVisible} width={400}>
        <List itemLayout="horizontal" dataSource={bucketTables} renderItem={(item: any) => (<List.Item actions={[<Button type="link" onClick={() => extractTable(item)}>Extract</Button>]}>
          <List.Item.Meta title={item.label || item.name} description={item.description || 'No description'} /></List.Item>)} />
      </Drawer>
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

const LineageGraph: React.FC = () => (
  <ReactFlowProvider>
    <LineageGraphContent />
  </ReactFlowProvider>
);

export default LineageGraph;