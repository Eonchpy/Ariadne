import client from '../client';
import type { LoginResponse, RefreshResponse, User } from '@/types/api';

export const authApi = {
  login: (data: any) => client.post<any, LoginResponse>('/auth/login', data),
  refresh: (refresh_token: string) => client.post<any, RefreshResponse>('/auth/refresh', { refresh_token }),
  logout: (refresh_token: string) => client.post('/auth/logout', { refresh_token }),
  me: () => client.get<any, User>('/users/me'),
};
