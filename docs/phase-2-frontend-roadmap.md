# Phase 2 Frontend Roadmap (Gemini)

**Agent**: Frontend Agent (Gemini)
**Timeline**: Week 6-8 (3 weeks)
**Dependencies**: Phase 1 Complete ✅

---

## Week 6: Data Sources Management UI

### Day 1: Mock API Layer Setup (NEW - Gemini Suggestion Adopted, Priority Elevated)
**Tasks**:
1. Install dependencies:
   ```bash
   npm install --save-dev msw
   ```
2. Create mock API infrastructure:
   - Create `src/api/mocks/` directory structure
   - Create `src/api/mocks/handlers.ts` - Mock API handlers
   - Create `src/api/mocks/data/` - Mock data generators
   - Create `src/api/mocks/browser.ts` - MSW browser setup
3. Implement `VITE_USE_MOCKS` environment variable:
   - Update `vite.config.ts` to read environment variable
   - Conditionally enable MSW based on flag
4. Create mock data for Phase 2 APIs:
   - Data sources mock data (Oracle, MongoDB, ES)
   - Tables mock data
   - Fields mock data
   - Lineage mock data
5. Update API client to support mock mode
6. Document usage in README

**Deliverables**:
- Mock API infrastructure complete
- `VITE_USE_MOCKS=true` enables mock mode
- `VITE_USE_MOCKS=false` connects to real backend
- Mock data for all Phase 2 APIs
- Documentation for developers

**Usage**:
```bash
# Pure frontend development (no backend needed)
VITE_USE_MOCKS=true npm run dev

# Connect to real backend
VITE_USE_MOCKS=false npm run dev
```

**Rationale**: Enables parallel frontend/backend development, reduces dependency on backend availability

---

### Day 2-3: Data Sources List Page
**Tasks**:
1. Create data sources list page (`src/pages/DataSources/DataSourcesList.tsx`):
   - Table with columns: Name, Type, Status, Last Tested, Actions
   - Status indicator: 🟢 Connected / 🔴 Failed / ⚪ Not Tested
   - Search and filter by type (Oracle/MongoDB/ES)
   - Pagination support
2. Implement data sources API client (`src/api/endpoints/dataSources.ts`):
   - `getDataSources(page, size, filters)`
   - `getDataSource(id)`
   - `deleteDataSource(id)`
3. Create Zustand store (`src/stores/dataSourceStore.ts`):
   - State: sources list, loading, error
   - Actions: fetchSources, deleteSource

**Deliverables**:
- Data sources list page with search/filter
- API client for data sources
- Zustand store for state management
- Unit tests for store (≥70% coverage)
- Works with both mock and real API

### Day 4-5: Add/Edit Data Source Form
**Tasks**:
1. Create data source form (`src/pages/DataSources/DataSourceForm.tsx`):
   - Form fields: Name, Type (dropdown), Description
   - Connection config fields (dynamic based on type):
     - Oracle: Host, Port, Service Name, Username, Password
     - MongoDB: Connection String, Database
     - Elasticsearch: Host, Port, Username, Password, Use SSL
   - "Test Connection" button with loading state
   - Save button (disabled until connection tested successfully)

2. Implement connection testing:
   - API call: `POST /api/v1/sources/{id}/test`
   - Show result: ✅ Success / ❌ Failed with error message
   - Visual feedback: loading spinner, success/error alerts

3. Form validation:
   - Required fields validation
   - Connection string format validation (MongoDB)
   - Port number validation (1-65535)

**Deliverables**:
- Add/Edit data source form with dynamic fields
- Connection testing UI with visual feedback
- Form validation with React Hook Form
- Unit tests for form component

---

## Week 7: Manual Table Management + Smart Metadata Assist

### Day 1-2: Tables List Page
**Tasks**:
1. Create tables list page (`src/pages/Tables/TablesList.tsx`):
   - Table with columns: Name, Type, Source, Fields Count, Created At, Actions
   - Source column: Show "Manual" or data source name
   - Filter by source (dropdown with all sources + "Manual")
   - Search by table name
   - Pagination support
2. Implement tables API client (`src/api/endpoints/tables.ts`):
   - `getTables(page, size, filters)`
   - `getTable(id)`
   - `deleteTable(id)`
3. Add navigation link in sidebar

**Deliverables**:
- Tables list page with search/filter
- API client for tables
- Navigation integration
- Unit tests

### Day 3: Zod Validation Integration (NEW - Gemini Suggestion Adopted)
**Tasks**:
1. Install dependencies:
   ```bash
   npm install zod @hookform/resolvers
   ```
2. Create Zod schemas for forms:
   - Create `src/schemas/dataSourceSchema.ts` - Data source form validation
   - Create `src/schemas/tableSchema.ts` - Table form validation
   - Define validation rules (required fields, formats, ranges)
3. Integrate with react-hook-form:
   - Update DataSource form to use Zod resolver
   - Update Table form to use Zod resolver
   - Configure error messages
4. Add custom validation rules:
   - Connection string format (MongoDB)
   - Port number range (1-65535)
   - Table name format
5. Unit tests for schemas

**Deliverables**:
- Zod schemas for all forms
- Type-safe form validation
- Better error messages
- Unit tests for validation logic

**Example**:
```typescript
// src/schemas/dataSourceSchema.ts
import { z } from 'zod';

export const dataSourceSchema = z.object({
  name: z.string().min(1, 'Name is required'),
  type: z.enum(['oracle', 'mongodb', 'elasticsearch']),
  connection_config: z.object({
    host: z.string().min(1, 'Host is required'),
    port: z.number().min(1).max(65535),
    // ... other fields
  })
});
```

**Rationale**: Type-safe validation, reusable schemas, better error messages

---

### Day 4-5: Add/Edit Table Form with Smart Metadata Assist
**Tasks**:
1. Create table form (`src/pages/Tables/TableForm.tsx`):
   - Basic info section:
     - Table Name (required)
     - Data Source (optional dropdown)
     - Schema Name (optional, shown only for Oracle/PostgreSQL)
     - Type (dropdown: table/view/collection/index)
     - Description (textarea)

   - **Smart Metadata Assist section** (shown only if data source selected):
     - "Fetch Columns" button
     - Loading state during fetch
     - Success: Auto-populate fields section
     - Error: Show error message (table not found, permission denied)

   - Fields section:
     - Dynamic field rows (add/remove)
     - Columns: Field Name, Data Type, Nullable, Primary Key, Description
     - "Add Field" button
     - Pre-populated if "Fetch Columns" was used
     - User can edit/add/remove fields after fetch

2. Implement introspection API call:
   - `POST /api/v1/sources/{source_id}/introspect/table`
   - Request: `{ table_name, schema_name }`
   - Response: Parse and populate fields array

3. Form state management:
   - Track if columns were fetched
   - Track manual edits after fetch
   - Validation: at least 1 field required

**Deliverables**:
- Table form with smart metadata assist
- "Fetch Columns" feature working for all 3 database types
- Dynamic fields section with add/remove
- Form validation
- Unit tests for form logic

---

## Week 8: Lineage Visualization + Bulk Operations

### Day 1: Lineage Visualization Page (Part 1)
**Tasks**:
1. Install ReactFlow:
   ```bash
   npm install reactflow
   ```

2. Create lineage graph page (`src/pages/Lineage/LineageGraph.tsx`):
   - ReactFlow canvas with custom nodes
   - Node types:
     - Table node (with icon, name, source badge)
     - Field node (smaller, nested under table)
   - Edge types:
     - Table-level lineage (thick line)
     - Field-level lineage (thin line)
   - Edge colors by lineage source:
     - Manual: Blue solid line
     - Approved: Green solid line
     - Inferred: Gray dashed line (Phase 5)

3. Implement lineage API client (`src/api/endpoints/lineage.ts`):
   - `getTableLineage(tableId, direction, depth)`
   - `createTableLineage(sourceId, targetId, lineageSource)`
   - `createFieldLineage(sourceId, targetId, lineageSource)`
   - `deleteLineage(id)`

**Deliverables**:
- Basic lineage graph rendering
- Custom nodes and edges
- API client for lineage

### Day 2: ErrorBoundary + Lineage Controls (NEW - Gemini Suggestion Adopted)
**Tasks**:
1. Create LineageGraph ErrorBoundary (Gemini suggestion):
   - Create `src/components/Lineage/LineageGraphErrorBoundary.tsx`
   - Catch rendering errors from ReactFlow
   - Display user-friendly error message
   - Add "Retry" button to reload graph
   - Log errors to console for debugging

2. Implement lineage controls:
   - Search table to focus
   - Depth control (1-5 hops)
   - Direction toggle (upstream/downstream/both)
   - Zoom controls
   - Mini-map
   - Export as PNG

**Deliverables**:
- `LineageGraphErrorBoundary` component
- Error recovery UI (retry button, error message)
- Interactive controls for lineage graph
- Unit tests for ErrorBoundary

**Example**:
```typescript
// src/components/Lineage/LineageGraphErrorBoundary.tsx
class LineageGraphErrorBoundary extends React.Component {
  state = { hasError: false, error: null };

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('LineageGraph Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div>
          <h3>Failed to render lineage graph</h3>
          <p>{this.state.error?.message}</p>
          <button onClick={() => this.setState({ hasError: false })}>
            Retry
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
```

**Rationale**: Prevents app crashes from complex graph rendering with 100+ nodes

### Day 3: Manual Lineage Creation UI
**Tasks**:
1. Create lineage creation modal (`src/components/Lineage/CreateLineageModal.tsx`):
   - Source table selector (searchable dropdown)
   - Target table selector (searchable dropdown)
   - Lineage type: Table-level / Field-level
   - If field-level: Show field selectors for both tables
   - Lineage source: Manual / Approved (default: Manual)
   - Description (optional)

2. Add "Create Lineage" button on lineage graph page
3. After creation, refresh graph to show new relationship

**Deliverables**:
- Lineage creation modal
- Integration with lineage graph
- Form validation
- Unit tests

### Day 5: Bulk Import/Export UI
**Tasks**:
1. Create bulk operations page (`src/pages/Bulk/BulkOperations.tsx`):

   **Import Section**:
   - File upload (drag & drop or click)
   - Format selector: CSV / Excel / JSON / YAML
   - "Preview" button (show first 10 rows)
   - "Import" button with progress bar
   - Error reporting (show which rows failed)

   **Export Section**:
   - Export scope selector:
     - All tables + lineage
     - Selected tables only
     - Specific data source
   - Format selector: CSV / Excel / JSON / YAML
   - "Export" button (download file)

2. Implement bulk API client (`src/api/endpoints/bulk.ts`):
   - `importData(file, format)`
   - `exportData(scope, format)`

3. Add progress tracking for large imports

**Deliverables**:
- Bulk import UI with preview
- Bulk export UI with scope selection
- Progress tracking
- Error reporting
- Unit tests

---

## Testing Requirements

### Unit Tests
- Component tests for all forms (React Testing Library)
- Store tests (Zustand state management)
- API client tests (mocked axios)
- Form validation tests

### E2E Tests (Playwright)
- Data source CRUD flow
- Connection testing flow
- Table creation with smart metadata assist
- Manual lineage creation
- Bulk import/export flow

### Target Coverage
- **≥ 70%** overall coverage
- **100%** coverage for critical stores (dataSourceStore, tableStore, lineageStore)

---

## UI/UX Requirements

### Design System
- Continue using Ant Design 5.x
- Consistent color scheme:
  - Primary: Blue (#1890ff)
  - Success: Green (#52c41a)
  - Warning: Orange (#faad14)
  - Error: Red (#ff4d4f)
  - Manual: Blue badge
  - Connected: Green badge

### Responsive Design
- Desktop-first (1920x1080 primary)
- Support tablet (1024x768)
- Lineage graph: Minimum 1280px width recommended

### Loading States
- Skeleton screens for list pages
- Spinners for button actions
- Progress bars for bulk operations

### Error Handling
- Toast notifications for errors (Ant Design message)
- Inline validation errors in forms
- Detailed error messages from API

---

## Dependencies

### NPM Packages
```json
{
  "reactflow": "^11.10.0",
  "react-hook-form": "^7.49.0",
  "zustand": "^4.4.7",
  "antd": "^5.12.0",
  "axios": "^1.6.0"
}
```

---

## Success Metrics

- ✅ Data sources can be added and connection tested
- ✅ Smart metadata assist fetches columns correctly
- ✅ Tables can be created manually or with fetched columns
- ✅ Lineage graph renders 100+ nodes without lag
- ✅ Bulk import handles 1000+ rows successfully
- ✅ Test coverage ≥ 70%
- ✅ E2E tests cover all critical flows

---

## Integration Checkpoints

### Week 6 Day 5: Data Source Integration
- Backend: Data source APIs ready
- Frontend: Data sources list + form working
- Test: Create Oracle source → Test connection → Success

### Week 7 Day 5: Smart Metadata Assist Integration
- Backend: Introspection API ready
- Frontend: Table form with "Fetch Columns" working
- Test: Select Oracle source → Enter table name → Fetch columns → Auto-populate

### Week 8 Day 3: Lineage Integration
- Backend: Lineage APIs ready
- Frontend: Lineage graph rendering
- Test: Create table lineage → View in graph → Correct visualization

### Week 8 Day 5: Bulk Operations Integration
- Backend: Bulk import/export APIs ready
- Frontend: Bulk operations UI working
- Test: Import CSV with 100 tables → All imported → Export to Excel → Match

---

**Document Version**: v1.0
**Last Updated**: 2025-12-23
**Maintainer**: QC Agent (Claude)
**Agent**: Frontend Agent (Gemini)
