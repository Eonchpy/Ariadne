import client from '../client';
import type { LoginResponse, RefreshResponse, User } from '@/types/api';

const USE_MOCKS = import.meta.env.VITE_USE_MOCKS === 'true';
const sleep = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const authApi = {
  login: async (data: any): Promise<LoginResponse> => {
    if (USE_MOCKS) {
      await sleep(1000);
      // Accept any password for mock mode, but usually use admin/admin
      return {
        access_token: 'mock-access-token',
        refresh_token: 'mock-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600,
        user: {
          id: 'mock-user-id',
          email: data.email || 'admin@ariadne.com',
          name: 'Admin User',
          roles: ['admin'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
      };
    }
    return client.post<any, LoginResponse>('/auth/login', data);
  },

  refresh: async (refresh_token: string): Promise<RefreshResponse> => {
    if (USE_MOCKS) {
      await sleep(500);
      return {
        access_token: 'new-mock-access-token',
        refresh_token: 'new-mock-refresh-token',
        token_type: 'Bearer',
        expires_in: 3600,
      };
    }
    return client.post<any, RefreshResponse>('/auth/refresh', { refresh_token });
  },

  logout: async (refresh_token: string) => {
    if (USE_MOCKS) {
      await sleep(300);
      return;
    }
    return client.post('/auth/logout', { refresh_token });
  },

  me: async (): Promise<User> => {
    if (USE_MOCKS) {
      await sleep(300);
      return {
        id: 'mock-user-id',
        email: 'admin@ariadne.com',
        name: 'Admin User',
        roles: ['admin'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
    }
    return client.get<any, User>('/users/me');
  },
};