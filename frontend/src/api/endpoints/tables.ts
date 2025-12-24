import client from '../client';
import type { 
  Table, 
  TableListResponse, 
  TableDetail, 
  CreateTableRequest, 
  UpdateTableRequest,
  IntrospectTableRequest,
  IntrospectTableResponse,
  BatchCreateFieldsRequest
} from '@/types/api';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock Data for Tables
const mockTables: Table[] = [
  {
    id: 't1',
    name: 'CUSTOMERS',
    source_id: '550e8400-e29b-41d4-a716-446655440000',
    source_name: 'Oracle Production',
    schema_name: 'HR',
    type: 'table',
    field_count: 15,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  },
  {
    id: 't2',
    name: 'users_manual',
    source_id: null,
    type: 'table',
    field_count: 8,
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  }
];

export const tablesApi = {
  list: async (params: { 
    page?: number; 
    size?: number; 
    source_id?: string | null; 
    search?: string;
    tags?: string[];
    tag_match?: 'any' | 'all';
    include_subtags?: boolean;
  }) => {
    if (USE_MOCKS) {
      await sleep(400);
      let items = [...mockTables];
      if (params.source_id !== undefined) items = items.filter(t => t.source_id === params.source_id);
      if (params.search) items = items.filter(t => t.name.toLowerCase().includes(params.search!.toLowerCase()));
      // Mock tag filtering is simplified
      return {
        total: items.length,
        page: params.page || 1,
        size: params.size || 20,
        items
      } as TableListResponse;
    }
    
    // Format tags as comma-separated string for API if array provided
    const apiParams = {
      ...params,
      tags: params.tags?.join(',')
    };
    
    return client.get<any, TableListResponse>('/tables', { params: apiParams });
  },

  get: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      const table = mockTables.find(t => t.id === id);
      if (!table) throw new Error('Not found');
      return { ...table, fields: [] } as TableDetail;
    }
    return client.get<any, TableDetail>(`/tables/${id}`);
  },

  create: async (data: CreateTableRequest) => {
    if (USE_MOCKS) {
      await sleep(600);
      const newTable: Table = {
        ...data,
        id: crypto.randomUUID(),
        field_count: 0,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockTables.push(newTable);
      return newTable;
    }
    return client.post<any, Table>('/tables', data);
  },

  update: async (id: string, data: UpdateTableRequest) => {
    if (USE_MOCKS) {
      await sleep(500);
      const index = mockTables.findIndex(t => t.id === id);
      if (index === -1) throw new Error('Not found');
      mockTables[index] = { ...mockTables[index], ...data, updated_at: new Date().toISOString() };
      return mockTables[index];
    }
    return client.put<any, Table>(`/tables/${id}`, data);
  },

  delete: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      const index = mockTables.findIndex(t => t.id === id);
      if (index !== -1) mockTables.splice(index, 1);
      return;
    }
    return client.delete(`/tables/${id}`);
  },

  introspect: async (sourceId: string, data: IntrospectTableRequest) => {
    if (USE_MOCKS) {
      await sleep(1200);
      return {
        table: { name: data.table_name, schema_name: data.schema_name, type: 'TABLE' },
        fields: [
          { name: 'ID', data_type: 'NUMBER', is_nullable: false, is_primary_key: true },
          { name: 'NAME', data_type: 'VARCHAR2(100)', is_nullable: true, is_primary_key: false },
          { name: 'CREATED_AT', data_type: 'TIMESTAMP', is_nullable: false, is_primary_key: false },
        ]
      } as IntrospectTableResponse;
    }
    return client.post<any, IntrospectTableResponse>(`/sources/${sourceId}/introspect/table`, data);
  },

  batchCreateFields: async (tableId: string, data: BatchCreateFieldsRequest) => {
    if (USE_MOCKS) {
      await sleep(800);
      return { created_count: data.length };
    }
    return client.post(`/tables/${tableId}/fields/batch`, data);
  }
};
