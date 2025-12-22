import { describe, it, expect, beforeEach, vi } from 'vitest';
import { useAuthStore } from '@/stores/authStore';
import { authApi } from '@/api/endpoints/auth';

// Mock authApi
vi.mock('@/api/endpoints/auth', () => ({
  authApi: {
    login: vi.fn(),
    logout: vi.fn(),
    refresh: vi.fn(),
    me: vi.fn(),
  },
}));



// Mock zustand persist middleware to prevent actual localStorage interaction during tests
vi.mock('zustand/middleware', () => ({
  persist: (config: any) => config,
}));

// Mock localStorage for zustand persist middleware
const localStorageMock = (function () {
  let store: Record<string, string> = {};
  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      store = {};
    }),
  };
})();

Object.defineProperty(window, 'localStorage', { value: localStorageMock });

describe('useAuthStore', () => {
  beforeEach(() => {
    // Reset Zustand store and mocks before each test
    useAuthStore.setState({
      token: null,
      refreshToken: null,
      user: null,
    });
    localStorageMock.clear();
    vi.clearAllMocks();
  });
  it('should initialize with null token, refreshToken, and user', () => {
    const store = useAuthStore.getState();
    expect(store.token).toBeNull();
    expect(store.refreshToken).toBeNull();
    expect(store.user).toBeNull();
    expect(store.isAuthenticated()).toBeFalsy();
  });

  it('should handle successful login', async () => {
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['user'],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };
    const mockLoginResponse = {
      access_token: 'new-access-token',
      refresh_token: 'new-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser,
    };

    (authApi.login as vi.Mock).mockResolvedValue(mockLoginResponse);

    await useAuthStore.getState().login({ email: 'test@example.com', password: 'password' });

    const store = useAuthStore.getState();
    const { token, refreshToken, user } = store;
    const isAuthenticated = store.isAuthenticated;

    expect(authApi.login).toHaveBeenCalledWith({ email: 'test@example.com', password: 'password' });
    expect(token).toBe('new-access-token');
    expect(refreshToken).toBe('new-refresh-token');
    expect(user).toEqual(mockUser);
    expect(isAuthenticated()).toBeTruthy();
  });

  it('should handle login failure', async () => {
    (authApi.login as vi.Mock).mockRejectedValue(new Error('Login failed'));

    const store = useAuthStore.getState();
    const { token, refreshToken, user } = store;
    const isAuthenticated = store.isAuthenticated;
    expect(token).toBeNull();
    expect(refreshToken).toBeNull();
    expect(user).toBeNull();
    expect(isAuthenticated()).toBeFalsy();
    expect(localStorageMock.setItem).not.toHaveBeenCalled();
  });

  it('should handle successful logout', async () => {
    // First, log in a user to set the state
    const mockUser = {
      id: '123',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['user'],
      created_at: '2025-01-01T00:00:00Z',
      updated_at: '2025-01-01T00:00:00Z',
    };
    const mockLoginResponse = {
      access_token: 'existing-access-token',
      refresh_token: 'existing-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: mockUser,
    };
    (authApi.login as vi.Mock).mockResolvedValue(mockLoginResponse);
    await useAuthStore.getState().login({ email: 'test@example.com', password: 'password' });

    await useAuthStore.getState().logout();

    const store = useAuthStore.getState();
    const { token, refreshToken, user } = store;
    const isAuthenticated = store.isAuthenticated;
    expect(authApi.logout).toHaveBeenCalledWith('existing-refresh-token');
    expect(token).toBeNull();
    expect(refreshToken).toBeNull();
    expect(user).toBeNull();
    expect(isAuthenticated()).toBeFalsy();
  });

  it('should handle logout when no refresh token is present', async () => {
    // Ensure initial state has no refreshToken
    useAuthStore.setState({ token: 'some-token', refreshToken: null, user: { id: '1', email: 'a@b.com', name: 'A B', roles: [], created_at: '', updated_at: '' } });

    await useAuthStore.getState().logout(); // Should not throw, but clear state

    const store = useAuthStore.getState();
    const { token, refreshToken, user } = store;
    const isAuthenticated = store.isAuthenticated;
    expect(token).toBeNull();
    expect(refreshToken).toBeNull();
    expect(user).toBeNull();
    expect(isAuthenticated()).toBeFalsy();
  });

  it('should handle logout failure gracefully', async () => {
    const mockLoginResponse = {
      access_token: 'existing-access-token',
      refresh_token: 'existing-refresh-token',
      token_type: 'Bearer',
      expires_in: 3600,
      user: {
        id: '123',
        email: 'test@example.com',
        name: 'Test User',
        roles: ['user'],
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    };
    (authApi.login as vi.Mock).mockResolvedValue(mockLoginResponse);
    await useAuthStore.getState().login({ email: 'test@example.com', password: 'password' });

    (authApi.logout as vi.Mock).mockRejectedValue(new Error('Logout API failed'));

    await useAuthStore.getState().logout();

    const store = useAuthStore.getState();
    const { token, refreshToken, user } = store;
    const isAuthenticated = store.isAuthenticated;
    expect(authApi.logout).toHaveBeenCalledWith('existing-refresh-token');
    expect(token).toBeNull();
    expect(refreshToken).toBeNull();
    expect(user).toBeNull();
    expect(isAuthenticated()).toBeFalsy();
  });
});
