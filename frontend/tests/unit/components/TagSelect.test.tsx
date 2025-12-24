import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import TagSelect from '@/components/TagSelect/TagSelect';
import { tagsApi } from '@/api/endpoints/tags';

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

// Mock ResizeObserver
window.ResizeObserver = vi.fn().mockImplementation(() => ({
  observe: vi.fn(),
  unobserve: vi.fn(),
  disconnect: vi.fn(),
}));

vi.mock('@/api/endpoints/tags', () => ({
  tagsApi: {
    list: vi.fn(),
  },
}));

describe('TagSelect', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render and load tags', async () => {
    (tagsApi.list as any).mockResolvedValue({
      items: [
        { id: '1', name: 'Root Tag', level: 1, children: [] }
      ]
    });

    render(<TagSelect />);
    
    expect(screen.getByRole('combobox')).toBeInTheDocument();
    
    await waitFor(() => {
      expect(tagsApi.list).toHaveBeenCalled();
    });
  });

  it('should display selected values', async () => {
    (tagsApi.list as any).mockResolvedValue({
      items: [
        { id: '1', name: 'Tag 1', level: 1, children: [] }
      ]
    });

    const { container } = render(<TagSelect value={['1']} />);
    
    await waitFor(() => {
      // Antd TreeSelect renders selected items as content within selection-item
      expect(container.querySelector('.ant-select-selection-item-content')).toHaveTextContent('Tag 1');
    });
  });
});
