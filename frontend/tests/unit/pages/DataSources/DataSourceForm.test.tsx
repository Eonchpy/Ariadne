import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import DataSourceForm from '@/pages/DataSources/DataSourceForm';
import { BrowserRouter } from 'react-router-dom';

// Mock matchMedia for Antd components
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
});

vi.mock('@/api/endpoints/dataSources', () => ({
  dataSourcesApi: {
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    testConnectionConfig: vi.fn(),
  },
}));

vi.mock('@/stores/dataSourceStore', () => ({
  useDataSourceStore: () => ({
    fetchSources: vi.fn(),
  }),
}));

const renderForm = () => {
  return render(
    <BrowserRouter>
      <DataSourceForm />
    </BrowserRouter>
  );
};

describe('DataSourceForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render basic fields and Oracle as default', () => {
    renderForm();
    expect(screen.getByText('New Data Source')).toBeInTheDocument();
    expect(screen.getByText('Name')).toBeInTheDocument();
    expect(screen.getByText('Type')).toBeInTheDocument();
    
    // Check for Oracle specific fields
    expect(screen.getByText('Service Name')).toBeInTheDocument();
  });

  it('should show MongoDB specific fields when MongoDB is selected', async () => {
    renderForm();
    
    // Select MongoDB - Antd Select implementation
    // We search for the select by its role or label text container
    const typeSelect = screen.getByRole('combobox');
    fireEvent.mouseDown(typeSelect);
    const mongoOption = await screen.findByText('MongoDB');
    fireEvent.click(mongoOption);

    // Check for MongoDB specific fields
    expect(screen.getByText(/Connection String/i)).toBeInTheDocument();
    expect(screen.getByText('Database Name')).toBeInTheDocument();
    
    // Oracle fields should be gone
    expect(screen.queryByText('Service Name')).not.toBeInTheDocument();
  });

  it('should validate required fields on submit', async () => {
    renderForm();
    
    const submitBtn = screen.getByText('Create');
    fireEvent.click(submitBtn);

    expect(await screen.findByText('Name must be at least 3 characters')).toBeInTheDocument();
    expect(await screen.findByText('Host is required')).toBeInTheDocument();
  });
});
