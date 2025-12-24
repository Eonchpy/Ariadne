import client from '../client';
import type { Tag, TagCreateRequest, TagUpdateRequest, TagUsage, TagListResponse } from '@/types/tag';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

// Mock Data
const mockTags: Tag[] = [
  {
    id: 'tag-1',
    name: 'F10-Company Overview',
    parent_id: null,
    level: 1,
    path: 'F10-Company Overview',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
    children: [
      {
        id: 'tag-1-1',
        name: 'Company Info',
        parent_id: 'tag-1',
        level: 2,
        path: 'F10-Company Overview-Company Info',
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        children: []
      }
    ]
  }
];

export const tagsApi = {
  list: async (params?: { level?: number; parent_id?: string }) => {
    if (USE_MOCKS) {
      await sleep(300);
      return { items: mockTags } as TagListResponse;
    }
    return client.get<any, TagListResponse>('/tags', { params });
  },
  
  create: async (data: TagCreateRequest) => {
    if (USE_MOCKS) {
      await sleep(500);
      const newTag: Tag = {
        ...data,
        id: crypto.randomUUID(),
        path: data.name,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
        children: []
      };
      return newTag;
    }
    return client.post<any, Tag>('/tags', data);
  },
  
  update: async (id: string, data: TagUpdateRequest) => {
    if (USE_MOCKS) {
      await sleep(300);
      return { id, name: data.name } as any;
    }
    return client.put<any, Tag>(`/tags/${id}`, data);
  },
  
  delete: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      return;
    }
    return client.delete(`/tags/${id}`);
  },
  
  usage: async (id: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      return {
        tag_id: id,
        tag_name: 'Mock Tag',
        table_count: 2,
        tables: [
          { id: 't1', name: 'table_1', source_id: 's1' },
          { id: 't2', name: 'table_2', source_id: 's1' }
        ]
      } as TagUsage;
    }
    return client.get<any, TagUsage>(`/tags/${id}/usage`);
  },
  
  getTableTags: async (tableId: string) => {
    if (USE_MOCKS) {
      await sleep(200);
      return { items: [] } as TagListResponse;
    }
    return client.get<any, TagListResponse>(`/tables/${tableId}/tags`);
  },
  
  addTableTags: async (tableId: string, tagIds: string[]) => {
    if (USE_MOCKS) {
      await sleep(300);
      return;
    }
    return client.post(`/tables/${tableId}/tags`, { tag_ids: tagIds });
  },
  
  removeTableTag: async (tableId: string, tagId: string) => {
    if (USE_MOCKS) {
      await sleep(200);
      return;
    }
    return client.delete(`/tables/${tableId}/tags/${tagId}`);
  },
};
