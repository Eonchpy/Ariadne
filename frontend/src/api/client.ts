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
    try {
      const storageItem = localStorage.getItem('auth-storage');
      if (storageItem) {
        const { state } = JSON.parse(storageItem);
        if (state?.token) {
          config.headers.Authorization = `Bearer ${state.token}`;
        }
      }
    } catch (e) {
      console.error('Error parsing auth token', e);
    }
    return config;
  },
  (error) => Promise.reject(error)
);

client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error;
    if (response) {
      const errorMsg = response.data?.error?.message || 'An error occurred';
      // We don't automatically redirect on 401 here to avoid circular dependencies.
      // The calling code or a global event listener should handle it.
      // But we will show the error message for non-401s, or even 401s if we want.
      if (response.status === 401) {
         message.error('Session expired or invalid credentials');
      } else if (response.status === 403) {
         message.error('You do not have permission to perform this action');
      } else if (response.status >= 500) {
         message.error('Server error, please try again later');
      } else {
         message.error(errorMsg);
      }
    } else {
      message.error('Network error. Please check your connection.');
    }
    return Promise.reject(error);
  }
);

export default client;
