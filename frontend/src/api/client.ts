import axios from 'axios';
import { message } from 'antd';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

client.interceptors.request.use(
  (config) => {
    // DEBUG LOGGING
    console.log(`[API Request] ${config.method?.toUpperCase()} ${config.url}`, {
      headers: config.headers,
      data: config.data,
      params: config.params
    });

    try {
      const storageItem = localStorage.getItem('auth-storage');
      if (storageItem) {
        const parsed = JSON.parse(storageItem);
        const token = parsed?.state?.token;
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      }
    } catch (e) {
      console.error('Error parsing auth token from storage', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => {
    // DEBUG LOGGING FOR SUCCESSFUL RESPONSES
    console.log('[API Response Success]', {
      url: response.config.url,
      status: response.status,
      data: response.data
    });
    return response.data;
  },
  async (error) => {
    const { response } = error;
    if (response) {
      // DEBUG LOGGING FOR ERRORS
      console.error('[API Error Response]', {
        status: response.status,
        data: response.data,
        headers: response.headers
      });

      if (response.status === 401) {
        // Only show message if it's not a login attempt
        if (!response.config.url?.includes('/auth/login')) {
            message.error('Session expired. Please log in again.');
            
            // IMPORT: Access the store from outside React components to reset state
            const { useAuthStore } = await import('@/stores/authStore');
            useAuthStore.getState().logout();
            
            // Force a redirect if the store update doesn't trigger fast enough
            if (window.location.pathname !== '/login') {
                window.location.href = '/login';
            }
        }
      } else {
        const errorMsg = response.data?.error?.message || 'An error occurred';
        message.error(errorMsg);
      }
    } else {
      message.error('Network error. Please check your connection.');
    }
    return Promise.reject(error);
  }
);

export default client;