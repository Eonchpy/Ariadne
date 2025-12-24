import type { DataSource, DataSourceListResponse } from '@/types/api';

export const mockDataSources: DataSource[] = [
  {
    id: '550e8400-e29b-41d4-a716-446655440000',
    name: 'Oracle Production',
    type: 'oracle',
    description: 'Main production database for customer records',
    is_active: true,
    last_tested_at: '2025-12-23T09:30:00Z',
    last_test_status: 'success',
    created_at: '2025-12-20T10:00:00Z',
    updated_at: '2025-12-23T09:30:00Z',
  },
  {
    id: 'a1b2c3d4-e5f6-4g7h-8i9j-k0l1m2n3o4p5',
    name: 'MongoDB Analytics',
    type: 'mongodb',
    description: 'Staging environment for web analytics',
    is_active: true,
    last_tested_at: '2025-12-22T15:45:00Z',
    last_test_status: 'failed',
    created_at: '2025-12-21T11:30:00Z',
    updated_at: '2025-12-22T15:45:00Z',
  },
  {
    id: 'f1e2d3c4-b5a6-9z8y-7x6w-5v4u3t2s1r0q',
    name: 'ES Logs Cluster',
    type: 'elasticsearch',
    description: 'Centralized logging cluster',
    is_active: false,
    created_at: '2025-12-22T08:00:00Z',
    updated_at: '2025-12-22T08:00:00Z',
  }
];

export const mockDataSourceList: DataSourceListResponse = {
  total: mockDataSources.length,
  page: 1,
  size: 20,
  items: mockDataSources,
};
