import client from '../client';
import type { LineageGraphResponse, TableLineageCreateRequest, FieldLineageCreateRequest, LineageRelationship } from '@/types/api';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const lineageApi = {
  getUpstream: async (tableId: string, depth: number = 3, granularity: string = 'table') => {
    if (USE_MOCKS) {
      await sleep(600);
      return {
        root_id: tableId,
        nodes: [
          { id: tableId, label: 'Target Table', type: 'table' },
          { id: 'source-1', label: 'Upstream Oracle DB', type: 'table' }
        ],
        edges: [
          { id: 'e1', from: 'source-1', to: tableId, lineage_source: 'manual' }
        ]
      } as LineageGraphResponse;
    }
    return client.get<any, LineageGraphResponse>(`/lineage/table/${tableId}/upstream`, {
      params: { depth, granularity },
    });
  },

  getDownstream: async (tableId: string, depth: number = 3, granularity: string = 'table') => {
    if (USE_MOCKS) {
      await sleep(600);
      return {
        root_id: tableId,
        nodes: [
          { id: tableId, label: 'Source Table', type: 'table' },
          { id: 'target-1', label: 'Downstream Analytics', type: 'table' }
        ],
        edges: [
          { id: 'e2', from: tableId, to: 'target-1', lineage_source: 'approved' }
        ]
      } as LineageGraphResponse;
    }
    return client.get<any, LineageGraphResponse>(`/lineage/table/${tableId}/downstream`, {
      params: { depth, granularity },
    });
  },

  createTableLineage: async (data: TableLineageCreateRequest) => {
    if (USE_MOCKS) {
      await sleep(500);
      return { id: 'new-id', ...data, status: 'pending' } as any;
    }
    return client.post<any, LineageRelationship>('/lineage/table', data);
  },

  createFieldLineage: async (data: FieldLineageCreateRequest) => {
    if (USE_MOCKS) {
      await sleep(500);
      return { id: 'new-id', ...data, status: 'pending' } as any;
    }
    return client.post<any, LineageRelationship>('/lineage/field', data);
  },

  delete: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      return;
    }
    return client.delete(`/lineage/${id}`);
  },
};
