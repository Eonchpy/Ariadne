import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  test: {
    globals: true, // Use global APIs like `describe`, `it`, `expect`
    environment: 'jsdom', // Simulate browser environment
    setupFiles: './src/setupTests.ts', // Path to setup file
    css: false, // Disable CSS processing for tests
    coverage: {
      provider: 'v8', // Use v8 for faster coverage
      reporter: ['text', 'json', 'html'], // Output formats for coverage report
      exclude: ['node_modules/', 'src/main.tsx', 'src/App.tsx', 'src/types/', 'src/api/client.ts'], // Exclude non-testable files
      lines: 70, // Target 70% line coverage
      functions: 70, // Target 70% function coverage
      branches: 70, // Target 70% branch coverage
      statements: 70, // Target 70% statement coverage
    },
  },
});
