import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useDataSourceStore } from '@/stores/dataSourceStore';
import { dataSourcesApi } from '@/api/endpoints/dataSources';

// Mock dataSourcesApi
vi.mock('@/api/endpoints/dataSources', () => ({
  dataSourcesApi: {
    list: vi.fn(),
    delete: vi.fn(),
    testConnection: vi.fn(),
  },
}));

describe('useDataSourceStore', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    useDataSourceStore.setState({
      sources: [],
      total: 0,
      loading: false,
      error: null,
    });
  });

  it('should initialize with default values', () => {
    const state = useDataSourceStore.getState();
    expect(state.sources).toEqual([]);
    expect(state.total).toBe(0);
    expect(state.loading).toBeFalsy();
    expect(state.error).toBeNull();
  });

  it('should fetch sources successfully', async () => {
    const mockSources = [
      { id: '1', name: 'Source 1', type: 'oracle' },
      { id: '2', name: 'Source 2', type: 'mongodb' },
    ];
    (dataSourcesApi.list as any).mockResolvedValue({
      items: mockSources,
      total: 2,
    });

    await useDataSourceStore.getState().fetchSources();

    const state = useDataSourceStore.getState();
    expect(state.sources).toEqual(mockSources);
    expect(state.total).toBe(2);
    expect(state.loading).toBeFalsy();
    expect(state.error).toBeNull();
  });

  it('should handle fetch sources failure', async () => {
    (dataSourcesApi.list as any).mockRejectedValue(new Error('Fetch failed'));

    await useDataSourceStore.getState().fetchSources();

    const state = useDataSourceStore.getState();
    expect(state.loading).toBeFalsy();
    expect(state.error).toBe('Fetch failed');
  });

  it('should delete a source successfully', async () => {
    const mockSources = [{ id: '1', name: 'Source 1' }];
    useDataSourceStore.setState({ sources: mockSources as any, total: 1 });
    (dataSourcesApi.delete as any).mockResolvedValue(undefined);

    await useDataSourceStore.getState().deleteSource('1');

    const state = useDataSourceStore.getState();
    expect(state.sources).toEqual([]);
    expect(state.total).toBe(0);
    expect(state.loading).toBeFalsy();
  });

  it('should test connection', async () => {
    const mockResult = { status: 'success', message: 'OK' };
    (dataSourcesApi.testConnection as any).mockResolvedValue(mockResult);

    const result = await useDataSourceStore.getState().testConnection('1');

    expect(dataSourcesApi.testConnection).toHaveBeenCalledWith('1');
    expect(result).toEqual(mockResult);
  });
});
