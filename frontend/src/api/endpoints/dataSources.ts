import client from '../client';
import type { DataSource, DataSourceListResponse, CreateDataSourceRequest, UpdateDataSourceRequest, TestConnectionResponse } from '@/types/api';
import { mockDataSources } from '../mocks/data';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';

const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const dataSourcesApi = {
  list: async (params: { page?: number; size?: number; type?: string; is_active?: boolean }) => {
    if (USE_MOCKS) {
      await sleep(500);
      let items = [...mockDataSources];
      if (params.type) items = items.filter(s => s.type === params.type);
      if (params.is_active !== undefined) items = items.filter(s => s.is_active === params.is_active);
      return {
        total: items.length,
        page: params.page || 1,
        size: params.size || 20,
        items: items
      } as DataSourceListResponse;
    }
    return client.get<any, DataSourceListResponse>('/sources', { params });
  },

  get: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      const source = mockDataSources.find(s => s.id === id);
      if (!source) throw new Error('Not found');
      return source;
    }
    return client.get<any, DataSource>(`/sources/${id}`);
  },

  create: async (data: CreateDataSourceRequest) => {
    if (USE_MOCKS) {
      await sleep(800);
      const newSource: DataSource = {
        ...data,
        id: crypto.randomUUID(),
        is_active: data.is_active ?? true,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      mockDataSources.push(newSource);
      return newSource;
    }
    return client.post<any, DataSource>('/sources', data);
  },

  update: async (id: string, data: UpdateDataSourceRequest) => {
    if (USE_MOCKS) {
      await sleep(600);
      const index = mockDataSources.findIndex(s => s.id === id);
      if (index === -1) throw new Error('Not found');
      mockDataSources[index] = { ...mockDataSources[index], ...data, updated_at: new Date().toISOString() };
      return mockDataSources[index];
    }
    return client.put<any, DataSource>(`/sources/${id}`, data);
  },

  delete: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(400);
      const index = mockDataSources.findIndex(s => s.id === id);
      if (index !== -1) mockDataSources.splice(index, 1);
      return;
    }
    return client.delete(`/sources/${id}`);
  },

  testConnection: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(1500);
      const isSuccess = Math.random() > 0.2;
      return {
        success: isSuccess,
        message: isSuccess ? 'Connection successful' : 'Connection timeout',
        tested_at: new Date().toISOString(),
        latency_ms: isSuccess ? Math.floor(Math.random() * 200) : undefined
      } as TestConnectionResponse;
    }
    return client.post<any, TestConnectionResponse>(`/sources/${id}/test`);
  },

  testConnectionConfig: async (data: any) => {
    if (USE_MOCKS) {
      await sleep(1500);
      const isSuccess = Math.random() > 0.2;
      return {
        success: isSuccess,
        message: isSuccess ? 'Connection successful' : 'Connection timeout',
        tested_at: new Date().toISOString(),
        latency_ms: isSuccess ? Math.floor(Math.random() * 200) : undefined
      } as TestConnectionResponse;
    }
    return client.post<any, TestConnectionResponse>('/sources/test-connection', data);
  },

  getAuditLogs: async (params: { source_id?: string; limit?: number }) => {
    if (USE_MOCKS) {
      await sleep(300);
      return { items: [] };
    }
    return client.get<any, any>('/audit/connection-tests', { params });
  }
};
