import { create } from 'zustand';
import type { DataSource } from '@/types/api';
import { dataSourcesApi } from '@/api/endpoints/dataSources';

interface DataSourceState {
  sources: DataSource[];
  total: number;
  loading: boolean;
  error: string | null;
  
  fetchSources: (params?: { page?: number; size?: number; type?: string; is_active?: boolean }) => Promise<void>;
  deleteSource: (id: string) => Promise<void>;
  testConnection: (id: string) => Promise<any>;
}

export const useDataSourceStore = create<DataSourceState>((set, get) => ({
  sources: [],
  total: 0,
  loading: false,
  error: null,

  fetchSources: async (params) => {
    set({ loading: true, error: null });
    try {
      const response = await dataSourcesApi.list(params || {});
      set({ sources: response.items, total: response.total, loading: false });
    } catch (err: any) {
      set({ error: err.message || 'Failed to fetch data sources', loading: false });
    }
  },

  deleteSource: async (id) => {
    set({ loading: true });
    try {
      await dataSourcesApi.delete(id);
      const { sources, total } = get();
      set({ 
        sources: sources.filter(s => s.id !== id),
        total: total - 1,
        loading: false 
      });
    } catch (err: any) {
      set({ error: err.message || 'Failed to delete data source', loading: false });
      throw err;
    }
  },

  testConnection: async (id) => {
    return dataSourcesApi.testConnection(id);
  }
}));
