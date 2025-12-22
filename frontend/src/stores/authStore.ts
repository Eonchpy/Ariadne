import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { authApi } from '@/api/endpoints/auth';
import type { User } from '@/types/api';

interface AuthState {
  token: string | null;
  refreshToken: string | null;
  user: User | null;
  login: (data: any) => Promise<void>;
  logout: () => Promise<void>;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      refreshToken: null,
      user: null,

      login: async (data) => {
        const response = await authApi.login(data);
        set({ 
          token: response.access_token, 
          refreshToken: response.refresh_token,
          user: response.user 
        });
      },

      logout: async () => {
        const { refreshToken } = get();
        if (refreshToken) {
          try {
            await authApi.logout(refreshToken);
          } catch (e) {
            console.error('Logout failed', e);
          }
        }
        set({ token: null, refreshToken: null, user: null });
      },

      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'auth-storage',
    }
  )
);
