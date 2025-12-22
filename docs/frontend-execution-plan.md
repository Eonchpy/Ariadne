# Ariadne Frontend Execution Plan (Frontend Experience & Visualization Agent)

## Technology Stack

- **Framework**: React 18.2+ with TypeScript 5.0+
- **Build Tool**: Vite 5.0+
- **State Management**: Zustand 4.4+
- **Routing**: React Router 6.20+
- **UI Library**: Ant Design 5.12+
- **Graph Visualization**: ReactFlow 11.10+
- **HTTP Client**: Axios 1.6+
- **Form Handling**: React Hook Form 7.48+
- **Data Tables**: Ant Design Table (built-in)
- **Charts**: Recharts 2.10+ (optional)
- **Styling**: CSS Modules / Tailwind CSS
- **Code Standards**: ESLint + Prettier
- **Testing**: Vitest + React Testing Library + Playwright

## Project Structure

```
frontend/
├── public/
│   └── favicon.ico
├── src/
│   ├── main.tsx
│   ├── App.tsx
│   ├── vite-env.d.ts
│   │
│   ├── api/
│   │   ├── client.ts
│   │   ├── endpoints/
│   │   │   ├── sources.ts
│   │   │   ├── tables.ts
│   │   │   ├── fields.ts
│   │   │   ├── lineage.ts
│   │   │   ├── import.ts
│   │   │   ├── export.ts
│   │   │   └── ai.ts
│   │   └── types.ts
│   │
│   ├── components/
│   │   ├── common/
│   │   │   ├── PageHeader.tsx
│   │   │   ├── Loading.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   └── EmptyState.tsx
│   │   ├── metadata/
│   │   │   ├── TableCard.tsx
│   │   │   ├── FieldList.tsx
│   │   │   ├── TagManager.tsx
│   │   │   └── HistoryTimeline.tsx
│   │   ├── lineage/
│   │   │   ├── LineageGraph.tsx
│   │   │   ├── LineageNode.tsx
│   │   │   ├── LineageEdge.tsx
│   │   │   ├── GraphControls.tsx
│   │   │   └── GraphLegend.tsx
│   │   ├── forms/
│   │   │   ├── TableForm.tsx
│   │   │   ├── FieldForm.tsx
│   │   │   ├── LineageForm.tsx
│   │   │   └── SourceConnectionForm.tsx
│   │   └── import/
│   │       ├── ImportWizard.tsx
│   │       ├── FileUpload.tsx
│   │       ├── ValidationResults.tsx
│   │       └── PreviewDiff.tsx
│   │
│   ├── pages/
│   │   ├── auth/
│   │   │   └── LoginPage.tsx
│   │   ├── sources/
│   │   │   ├── SourceListPage.tsx
│   │   │   └── SourceDetailPage.tsx
│   │   ├── metadata/
│   │   │   ├── TableListPage.tsx
│   │   │   ├── TableDetailPage.tsx
│   │   │   └── FieldDetailPage.tsx
│   │   ├── lineage/
│   │   │   ├── LineageViewerPage.tsx
│   │   │   └── ImpactAnalysisPage.tsx
│   │   ├── import/
│   │   │   └── ImportPage.tsx
│   │   ├── ai/
│   │   │   └── AIAssistantPage.tsx
│   │   └── NotFoundPage.tsx
│   │
│   ├── layouts/
│   │   ├── MainLayout.tsx
│   │   └── AuthLayout.tsx
│   │
│   ├── stores/
│   │   ├── authStore.ts
│   │   ├── metadataStore.ts
│   │   ├── lineageStore.ts
│   │   └── uiStore.ts
│   │
│   ├── hooks/
│   │   ├── useAuth.ts
│   │   ├── useTables.ts
│   │   ├── useLineage.ts
│   │   ├── useImport.ts
│   │   └── useDebounce.ts
│   │
│   ├── utils/
│   │   ├── format.ts
│   │   ├── validation.ts
│   │   └── download.ts
│   │
│   ├── constants/
│   │   ├── routes.ts
│   │   └── config.ts
│   │
│   └── types/
│       ├── models.ts
│       └── api.ts
│
├── tests/
│   ├── unit/
│   └── e2e/
├── .env.development
├── .env.production
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## API Client Design

### Axios Instance Configuration

```typescript
// src/api/client.ts
import axios from 'axios';
import { message } from 'antd';
import { useAuthStore } from '@/stores/authStore';

const client = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor - add auth token
client.interceptors.request.use(
  (config) => {
    const token = useAuthStore.getState().token;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - unified error handling
client.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const { response } = error;

    if (response) {
      switch (response.status) {
        case 401:
          message.error('Not logged in or session expired');
          useAuthStore.getState().logout();
          window.location.href = '/login';
          break;
        case 403:
          message.error('No permission to access');
          break;
        case 404:
          message.error('Resource not found');
          break;
        case 422:
          message.error(response.data?.error?.message || 'Validation failed');
          break;
        case 500:
          message.error('Server error, please try again later');
          break;
        default:
          message.error(response.data?.error?.message || 'Request failed');
      }
    } else {
      message.error('Network error, please check connection');
    }

    return Promise.reject(error);
  }
);

export default client;
```

### API Endpoint Wrappers

```typescript
// src/api/endpoints/tables.ts
import client from '../client';
import type {
  TableListResponse,
  TableDetailResponse,
  TableCreateRequest,
  TableUpdateRequest
} from '../types';

export const tablesApi = {
  list: (params: {
    page?: number;
    size?: number;
    source_id?: string;
    search?: string;
    tags?: string[];
  }) => client.get<TableListResponse>('/tables', { params }),

  get: (id: string) =>
    client.get<TableDetailResponse>(`/tables/${id}`),

  create: (data: TableCreateRequest) =>
    client.post<TableDetailResponse>('/tables', data),

  update: (id: string, data: TableUpdateRequest) =>
    client.put<TableDetailResponse>(`/tables/${id}`, data),

  delete: (id: string) =>
    client.delete(`/tables/${id}`),

  history: (id: string, page: number = 1) =>
    client.get(`/tables/${id}/history`, { params: { page } }),

  fields: (id: string) =>
    client.get(`/tables/${id}/fields`),
};
```

```typescript
// src/api/endpoints/lineage.ts
import client from '../client';
import type {
  LineageGraphResponse,
  TableLineageCreateRequest
} from '../types';

export const lineageApi = {
  getUpstream: (tableId: string, depth: number = 3, sourceFilter?: string) =>
    client.get<LineageGraphResponse>(`/lineage/table/${tableId}/upstream`, {
      params: { depth, source_filter: sourceFilter },
    }),

  getDownstream: (tableId: string, depth: number = 3) =>
    client.get<LineageGraphResponse>(`/lineage/table/${tableId}/downstream`, {
      params: { depth },
    }),

  createTableLineage: (data: TableLineageCreateRequest) =>
    client.post('/lineage/table', data),

  approve: (lineageId: string, approved: boolean, comment?: string) =>
    client.post(`/lineage/${lineageId}/approve`, { approved, comment }),

  impactAnalysis: (tableId: string, changeType: string) =>
    client.get(`/lineage/impact/${tableId}`, { params: { change_type: changeType } }),
};
```

## Core Page Designs

### 1. Table Metadata List Page

**Route**: `/metadata/tables`

**Features**:
- Paginated table display
- Search (table name, description)
- Filtering (data source, tags, type)
- Sorting (name, row count, update time)
- Quick actions (view details, view lineage, edit, delete)

### 2. Table Detail Page

**Route**: `/metadata/tables/:id`

**Features**:
- Display complete table metadata
- Tab switching: Basic Info, Fields, Lineage, Change History
- Edit table information
- Manage tags
- View statistics

### 3. Lineage Visualization Page

**Route**: `/lineage/:tableId`

**Features**:
- Interactive lineage graph
- Upstream/downstream toggle
- Depth control (1-5 layers)
- Lineage source filtering (inferred/manual/approved)
- Node click shows detail panel
- Edge click shows transformation logic
- Graph layout switching (hierarchical, force-directed)
- Export graph (PNG/SVG)

**Core Component**:
```typescript
// src/components/lineage/LineageGraph.tsx
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { useLineage } from '@/hooks/useLineage';

interface LineageGraphProps {
  tableId: string;
  direction?: 'upstream' | 'downstream';
}

export const LineageGraph: React.FC<LineageGraphProps> = ({
  tableId,
  direction = 'upstream'
}) => {
  const { lineageData, loading } = useLineage(tableId, direction);
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  const [selectedNode, setSelectedNode] = useState(null);

  useEffect(() => {
    if (lineageData) {
      const flowNodes: Node[] = lineageData.nodes.map((node, index) => ({
        id: node.id,
        type: 'custom',
        position: calculatePosition(index),
        data: {
          label: node.qualified_name,
          type: node.type,
          source: node.source,
        },
      }));

      const flowEdges: Edge[] = lineageData.edges.map((edge) => ({
        id: edge.id,
        source: edge.source_id,
        target: edge.target_id,
        type: 'smoothstep',
        animated: edge.lineage_source === 'inferred',
        style: {
          stroke: getEdgeColor(edge.lineage_source),
          strokeWidth: 2,
        },
        label: edge.transformation_type,
        data: edge,
      }));

      setNodes(flowNodes);
      setEdges(flowEdges);
    }
  }, [lineageData]);

  const onNodeClick = (event, node) => {
    setSelectedNode(node.data);
  };

  const onEdgeClick = (event, edge) => {
    Modal.info({
      title: 'Transformation Logic',
      content: edge.data.transformation_logic,
      width: 600,
    });
  };

  return (
    <div style={{ height: '600px' }}>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        onEdgeClick={onEdgeClick}
        fitView
      >
        <Controls />
        <MiniMap />
        <Background />
        <GraphControls />
        <GraphLegend />
      </ReactFlow>

      {selectedNode && (
        <NodeDetailPanel node={selectedNode} onClose={() => setSelectedNode(null)} />
      )}
    </div>
  );
};

const getEdgeColor = (lineageSource: string) => {
  switch (lineageSource) {
    case 'inferred':
      return '#d9d9d9'; // Gray dashed
    case 'manual':
      return '#1890ff'; // Blue solid
    case 'approved':
      return '#52c41a'; // Green solid
    default:
      return '#000';
  }
};
```

### 4. Bulk Import Wizard

**Route**: `/import`

**Steps**:
1. File Upload
2. Format Mapping
3. Validation Results
4. Preview Changes
5. Execute Import
6. Results Report

### 5. AI Assistant Page

**Route**: `/ai`

**Features**:
- Chat interface
- Natural language queries
- AI response rendering (Markdown, tables, lineage graphs)
- Click metadata in responses to jump to detail pages
- Suggested questions quick buttons
- Conversation history

## State Management (Zustand)

### Authentication State

```typescript
// src/stores/authStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface AuthState {
  token: string | null;
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: () => boolean;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      token: null,
      user: null,

      login: async (email, password) => {
        const response = await authApi.login({ email, password });
        set({ token: response.access_token, user: response.user });
      },

      logout: () => {
        set({ token: null, user: null });
      },

      isAuthenticated: () => !!get().token,
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

### Metadata Cache

```typescript
// src/stores/metadataStore.ts
import { create } from 'zustand';

interface MetadataState {
  tables: Map<string, TableDetail>;
  sources: Map<string, DataSource>;
  cacheTable: (table: TableDetail) => void;
  getTable: (id: string) => TableDetail | undefined;
}

export const useMetadataStore = create<MetadataState>((set, get) => ({
  tables: new Map(),
  sources: new Map(),

  cacheTable: (table) => {
    set((state) => ({
      tables: new Map(state.tables).set(table.id, table),
    }));
  },

  getTable: (id) => get().tables.get(id),
}));
```

## Custom Hooks

### useTables Hook

```typescript
// src/hooks/useTables.ts
import { useState, useEffect } from 'react';
import { tablesApi } from '@/api/endpoints/tables';
import { useDebounce } from './useDebounce';

export const useTables = () => {
  const [tables, setTables] = useState([]);
  const [loading, setLoading] = useState(false);
  const [pagination, setPagination] = useState({ current: 1, pageSize: 20, total: 0 });
  const [filters, setFilters] = useState({});
  const [searchTerm, setSearchTerm] = useState('');

  const debouncedSearch = useDebounce(searchTerm, 500);

  const fetchTables = async () => {
    setLoading(true);
    try {
      const response = await tablesApi.list({
        page: pagination.current,
        size: pagination.pageSize,
        search: debouncedSearch,
        ...filters,
      });
      setTables(response.items);
      setPagination((prev) => ({ ...prev, total: response.total }));
    } catch (error) {
      console.error('Failed to fetch tables:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTables();
  }, [pagination.current, pagination.pageSize, debouncedSearch, filters]);

  return {
    tables,
    loading,
    pagination,
    filters,
    onSearch: setSearchTerm,
    onFilter: setFilters,
    onPageChange: (page, pageSize) =>
      setPagination({ ...pagination, current: page, pageSize }),
    refresh: fetchTables,
  };
};
```

## Phase Implementation Plan

### Phase 0: Project Setup (Week 1-2)

**Tasks**:
- [ ] Vite + React + TypeScript project initialization
- [ ] Install dependencies (Ant Design, ReactFlow, Zustand, Axios, etc.)
- [ ] Configure ESLint + Prettier
- [ ] Configure environment variables (.env.development, .env.production)
- [ ] Setup routing structure
- [ ] Create base layout components (MainLayout, AuthLayout)
- [ ] Axios client configuration (interceptors, error handling)
- [ ] Authentication state management (Zustand)

**Deliverables**:
- Running React application
- Login/logout functionality
- Basic routing navigation

### Phase 1: Core Pages (Week 3-5)

**Tasks**:
- [ ] Data Source Management
  - Data source list page
  - Create data source form
  - Connection test functionality
- [ ] Table Metadata Browsing
  - Table list page (pagination, search, filtering)
  - Table detail page (Basic Info tab)
  - Field list component
- [ ] Manual Create/Edit
  - Create table form
  - Edit table form
  - Create field form
  - Tag management component
- [ ] Change History
  - Timeline component for history display

**Deliverables**:
- Complete metadata browsing functionality
- Manual CRUD operations

### Phase 2: Forms & Validation (Week 6-8)

**Tasks**:
- [ ] React Hook Form integration
- [ ] Form validation rules
- [ ] Custom form components
  - TagInput
  - KeyValueEditor
  - RichTextEditor
- [ ] Form submission error handling
- [ ] Optimistic UI updates

**Deliverables**:
- Polished form experience
- Real-time validation feedback

### Phase 3: Lineage Visualization (Week 9-12)

**Tasks**:
- [ ] ReactFlow Integration
  - Custom node styles
  - Custom edge styles
  - Auto-layout algorithm (Dagre)
- [ ] Lineage Graph Component
  - Upstream/downstream toggle
  - Depth control slider
  - Lineage source filtering
  - Node detail panel
  - Edge detail modal
- [ ] Graph Control Component
  - Zoom controls
  - Fit to screen
  - Layout switching
  - Export graph
- [ ] Performance Optimization
  - Virtualized rendering (large graphs)
  - Lazy loading nodes
  - Throttling/debouncing

**Deliverables**:
- Interactive lineage graph
- Support 1000+ nodes

### Phase 4: Bulk Import (Week 13-15)

**Tasks**:
- [ ] Import Wizard Component
  - 5-step flow
  - File upload
  - Validation results display
  - Preview diff component
  - Progress bar
- [ ] Error Reporting
  - Error list table
  - Download error report
- [ ] Export Functionality
  - Export configuration form
  - File download

**Deliverables**:
- Complete import wizard
- Export functionality

### Phase 5: AI Assistant (Week 16-19)

**Tasks**:
- [ ] Chat Interface
  - Message list
  - Input box
  - Suggested questions
- [ ] AI Response Rendering
  - Markdown support
  - Metadata reference clicking
  - Lineage graph embedding
- [ ] Conversation History
  - History list sidebar
  - Switch conversations
- [ ] Feedback Mechanism
  - Thumbs up/down buttons

**Deliverables**:
- AI chat interface
- Natural language queries

### Phase 6: Optimization & Testing (Week 20-22)

**Tasks**:
- [ ] Performance Optimization
  - Code splitting (React.lazy)
  - Image lazy loading
  - Virtual lists (large tables)
  - Bundle size optimization
- [ ] Responsive Design
  - Mobile adaptation
  - Tablet adaptation
- [ ] Accessibility
  - ARIA labels
  - Keyboard navigation
  - Screen reader support
- [ ] E2E Testing
  - Playwright test suite
  - Core flow coverage
- [ ] Browser Compatibility
  - Chrome, Firefox, Safari, Edge testing
- [ ] Error Boundaries
  - Global error catching
  - Friendly error pages

**Deliverables**:
- Production-ready frontend application
- E2E test suite

## Backend API Dependencies

Frontend depends on the following backend API endpoints:

### Authentication API
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/refresh`

### Data Source API
- `GET /api/v1/sources`
- `POST /api/v1/sources`
- `POST /api/v1/sources/test-connection`
- `POST /api/v1/sources/{id}/sync`

### Table Metadata API
- `GET /api/v1/tables`
- `GET /api/v1/tables/{id}`
- `POST /api/v1/tables`
- `PUT /api/v1/tables/{id}`
- `DELETE /api/v1/tables/{id}`
- `GET /api/v1/tables/{id}/history`

### Field API
- `GET /api/v1/tables/{id}/fields`
- `POST /api/v1/fields`
- `PUT /api/v1/fields/{id}`
- `DELETE /api/v1/fields/{id}`

### Lineage API
- `GET /api/v1/lineage/table/{id}/upstream`
- `GET /api/v1/lineage/table/{id}/downstream`
- `POST /api/v1/lineage/table`
- `POST /api/v1/lineage/{id}/approve`

### Import/Export API
- `POST /api/v1/import/validate`
- `POST /api/v1/import/execute`
- `GET /api/v1/import/jobs/{id}`
- `GET /api/v1/export/metadata`

### AI API
- `POST /api/v1/ai/query`
- `POST /api/v1/ai/search`

## Testing Strategy

### Unit Tests (Vitest)

```typescript
// tests/unit/components/TableCard.test.tsx
import { render, screen } from '@testing-library/react';
import { TableCard } from '@/components/metadata/TableCard';

describe('TableCard', () => {
  it('renders table name correctly', () => {
    const table = { name: 'users', qualified_name: 'public.users' };
    render(<TableCard table={table} />);
    expect(screen.getByText('public.users')).toBeInTheDocument();
  });
});
```

### E2E Tests (Playwright)

```typescript
// tests/e2e/metadata-flow.spec.ts
import { test, expect } from '@playwright/test';

test('create and view table metadata', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'test@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');

  await page.goto('/metadata/tables');
  await page.click('text=Manually Create Table');

  await page.fill('[name="name"]', 'test_table');
  await page.fill('[name="description"]', 'Test description');
  await page.click('button:has-text("Create")');

  await expect(page.locator('text=test_table')).toBeVisible();
});
```

## Configuration Files

### package.json

```json
{
  "name": "ariadne-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "test": "vitest",
    "test:e2e": "playwright test",
    "lint": "eslint src --ext ts,tsx",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\""
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.20.0",
    "antd": "^5.12.0",
    "reactflow": "^11.10.0",
    "zustand": "^4.4.0",
    "axios": "^1.6.0",
    "react-hook-form": "^7.48.0",
    "react-markdown": "^9.0.0",
    "recharts": "^2.10.0",
    "@ant-design/icons": "^5.2.6"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.0.0",
    "vite": "^5.0.0",
    "vitest": "^1.0.0",
    "@testing-library/react": "^14.1.0",
    "@playwright/test": "^1.40.0",
    "eslint": "^8.55.0",
    "prettier": "^3.1.0"
  }
}
```

### .env.development

```bash
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_URL=ws://localhost:8000/ws
```

---

**Document Version**: v1.0  
**Last Updated**: 2025-12-21  
**Maintainer**: Frontend Experience & Visualization Agent
