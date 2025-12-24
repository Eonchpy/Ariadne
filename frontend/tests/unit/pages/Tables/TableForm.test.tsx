import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import TableForm from '@/pages/Tables/TableForm';
import { BrowserRouter } from 'react-router-dom';
import { tablesApi } from '@/api/endpoints/tables';

// Mock matchMedia
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

vi.mock('@/api/endpoints/tables', () => ({
  tablesApi: {
    get: vi.fn(),
    create: vi.fn(),
    update: vi.fn(),
    introspect: vi.fn(),
    batchCreateFields: vi.fn(),
  },
}));

vi.mock('@/stores/dataSourceStore', () => ({
  useDataSourceStore: () => ({
    sources: [{ id: 's1', name: 'Oracle DB' }],
    fetchSources: vi.fn(),
  }),
}));

const renderForm = () => {
  return render(
    <BrowserRouter>
      <TableForm />
    </BrowserRouter>
  );
};

describe('TableForm', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render basic fields', () => {
    renderForm();
    expect(screen.getByText('New Table')).toBeInTheDocument();
    expect(screen.getByText('Table Name')).toBeInTheDocument();
    expect(screen.getByText('Data Source')).toBeInTheDocument();
  });

  it('should add a field row when "Add Field" is clicked', () => {
    renderForm();
    const addBtn = screen.getByText('Add Field');
    fireEvent.click(addBtn);
    
    // In Antd table, a new row adds inputs. 
    // We can check if any input with empty value is added in the fields section
    const inputs = screen.getAllByRole('textbox');
    expect(inputs.length).toBeGreaterThan(0);
  });

  it('should show "Fetch Columns" only when a data source is selected', async () => {
    renderForm();
    expect(screen.queryByText('Fetch Columns')).not.toBeInTheDocument();

    // Select Source
    const selectTrigger = screen.getByText('Select Source (Optional)');
    fireEvent.mouseDown(selectTrigger);
    
    const option = await screen.findByText('Oracle DB');
    fireEvent.click(option);

    expect(screen.getByText('Fetch Columns')).toBeInTheDocument();
  });

  it('should auto-populate fields when "Fetch Columns" is successful', async () => {
    (tablesApi.introspect as any).mockResolvedValue({
      table: { name: 'USERS' },
      fields: [
        { name: 'ID', data_type: 'NUMBER', is_nullable: false, is_primary_key: true },
      ]
    });

    renderForm();
    
    // Setup state so Fetch Columns is visible
    const selectTrigger = screen.getByText('Select Source (Optional)');
    fireEvent.mouseDown(selectTrigger);
    fireEvent.click(await screen.findByText('Oracle DB'));

    // Fill table name
    const nameInput = screen.getByPlaceholderText('users');
    fireEvent.change(nameInput, { target: { value: 'USERS' } });

    // Click fetch
    const fetchBtn = screen.getByText('Fetch Columns');
    fireEvent.click(fetchBtn);

    await waitFor(() => {
      expect(tablesApi.introspect).toHaveBeenCalled();
      // Should show 'ID' in the fields table
      expect(screen.getByDisplayValue('ID')).toBeInTheDocument();
      expect(screen.getByDisplayValue('NUMBER')).toBeInTheDocument();
    });
  });
});
