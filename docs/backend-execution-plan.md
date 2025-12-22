# Ariadne Backend Execution Plan (Backend Architecture Agent)

## Technology Stack

- **Language**: Python 3.11+
- **Web Framework**: FastAPI 0.104+
- **ORM**: SQLAlchemy 2.0 (async)
- **Database Drivers**:
  - `asyncpg` (PostgreSQL)
  - `neo4j` (Neo4j Python Driver)
  - `redis` (Redis)
- **Task Queue**: Celery + Redis
- **AI Framework**: LangChain + OpenAI API
- **Data Source Drivers**:
  - `oracledb` (Oracle)
  - `pymongo` (MongoDB)
  - `elasticsearch` (Elasticsearch)
- **Testing**: pytest + pytest-asyncio
- **Code Quality**: ruff (linter), black (formatter), mypy (type checker)

## Special Focus Areas (PRIORITY GUIDANCE)

  ### 🎯 Priority 1: Manual & Bulk Lineage Management

  This is the HIGHEST PRIORITY feature. Most enterprise users will rely on manual
  declaration and bulk import rather than automatic inference.

  **Implementation Focus**:
  1. Robust validation engine (syntax, semantics, business rules)
  2. User-friendly error reporting (row-level, actionable messages)
  3. Transaction support (all-or-nothing or configurable)
  4. Preview functionality (what-if analysis before commit)

  **Quality Bar**:
  - Must handle 10,000+ rows without errors
  - Validation must catch 100% of schema violations
  - Error messages must be understandable by non-technical users

  ### 🎯 Priority 2: Lineage Source Distinction

  Every lineage relationship MUST have a clear source attribution:
  - `inferred`: System-generated (low confidence, requires review)
  - `manual`: User-declared (high confidence)
  - `approved`: Data steward verified (highest confidence)

  **Implementation Requirements**:
  - Database schema includes `lineage_source` enum field
  - API always returns lineage source
  - Approval workflow implemented
  - Audit trail for all changes

  ### ⚠️ Priority 3: Automatic Lineage Inference (EXPERIMENTAL)

  Automatic inference is a "nice-to-have" feature, not a core requirement.

  **Implementation Approach**:
  - Mark as experimental/beta
  - Provide confidence scores
  - Always require manual review
  - Do not block core functionality

## Project Structure

```
backend/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── dependencies.py
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── sources.py
│   │   │   ├── tables.py
│   │   │   ├── fields.py
│   │   │   ├── lineage.py
│   │   │   ├── import_export.py
│   │   │   ├── ai.py
│   │   │   └── search.py
│   │   └── deps.py
│   │
│   ├── services/
│   │   ├── metadata_service.py
│   │   ├── lineage_service.py
│   │   ├── connector_service.py
│   │   ├── import_service.py
│   │   ├── export_service.py
│   │   ├── ai_service.py
│   │   ├── embedding_service.py
│   │   └── search_service.py
│   │
│   ├── connectors/
│   │   ├── base.py
│   │   ├── oracle_connector.py
│   │   ├── mongodb_connector.py
│   │   └── elasticsearch_connector.py
│   │
│   ├── models/
│   │   ├── data_source.py
│   │   ├── metadata_table.py
│   │   ├── metadata_field.py
│   │   ├── metadata_history.py
│   │   └── embedding.py
│   │
│   ├── schemas/
│   │   ├── source.py
│   │   ├── table.py
│   │   ├── field.py
│   │   ├── lineage.py
│   │   ├── import_export.py
│   │   └── ai.py
│   │
│   ├── repositories/
│   │   ├── base.py
│   │   ├── source_repo.py
│   │   ├── table_repo.py
│   │   ├── field_repo.py
│   │   ├── history_repo.py
│   │   └── embedding_repo.py
│   │
│   ├── graph/
│   │   ├── client.py
│   │   ├── queries.py
│   │   └── models.py
│   │
│   ├── core/
│   │   ├── security.py
│   │   ├── cache.py
│   │   ├── exceptions.py
│   │   └── logging.py
│   │
│   └── utils/
│       ├── validators.py
│       ├── parsers.py
│       └── crypto.py
│
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   └── conftest.py
├── requirements.txt
├── pyproject.toml
└── README.md
```



## API Route Design

### 1. Data Source Management API

#### List Data Sources
```python
GET /api/v1/sources
Query Parameters:
  - page: int = 1
  - size: int = 20
  - type: Optional[str] = None
  - is_active: Optional[bool] = None

Response: SourceListResponse
{
  "total": 50,
  "page": 1,
  "size": 20,
  "items": [...]
}
```

#### Create Data Source
```python
POST /api/v1/sources
Request Body: SourceCreateRequest
{
  "name": "Production Oracle",
  "type": "oracle",
  "description": "Main production database",
  "connection_config": {
    "host": "oracle.example.com",
    "port": 1521,
    "service_name": "PRODDB",
    "username": "metadata_reader",
    "password": "encrypted_password"
  }
}

Response: SourceResponse (201 Created)
```

#### Test Connection
```python
POST /api/v1/sources/test-connection
Request Body: SourceCreateRequest

Response: ConnectionTestResponse
{
  "success": true,
  "message": "Connection successful",
  "latency_ms": 45
}
```

#### Sync Metadata
```python
POST /api/v1/sources/{source_id}/sync
Query Parameters:
  - full_sync: bool = false

Response: SyncJobResponse
{
  "job_id": "uuid",
  "status": "running",
  "started_at": "2024-01-15T10:00:00Z"
}
```

### 2. Table Metadata API

#### List Tables
```python
GET /api/v1/tables
Query Parameters:
  - page: int = 1
  - size: int = 20
  - source_id: Optional[UUID] = None
  - search: Optional[str] = None
  - tags: Optional[List[str]] = None
  - type: Optional[str] = None

Response: TableListResponse
```

#### Get Table Details
```python
GET /api/v1/tables/{table_id}

Response: TableDetailResponse
```

#### Create Table (Manual)
```python
POST /api/v1/tables
Request Body: TableCreateRequest

Response: TableResponse (201 Created)
```

#### Update Table
```python
PUT /api/v1/tables/{table_id}
Request Body: TableUpdateRequest

Response: TableResponse
```

#### Delete Table
```python
DELETE /api/v1/tables/{table_id}

Response: 204 No Content
```

#### Get Change History
```python
GET /api/v1/tables/{table_id}/history
Query Parameters:
  - page: int = 1
  - size: int = 20

Response: HistoryListResponse
```

### 3. Field Metadata API

#### Get Table Fields
```python
GET /api/v1/tables/{table_id}/fields

Response: FieldListResponse
```

#### Create Field
```python
POST /api/v1/fields
Request Body: FieldCreateRequest

Response: FieldResponse (201 Created)
```

#### Update Field
```python
PUT /api/v1/fields/{field_id}
Request Body: FieldUpdateRequest

Response: FieldResponse
```

#### Delete Field
```python
DELETE /api/v1/fields/{field_id}

Response: 204 No Content
```

### 4. Lineage Management API

#### Get Upstream Lineage
```python
GET /api/v1/lineage/table/{table_id}/upstream
Query Parameters:
  - depth: int = 3
  - source_filter: Optional[str] = None

Response: LineageGraphResponse
{
  "root_id": "uuid",
  "nodes": [...],
  "edges": [...]
}
```

#### Get Downstream Lineage
```python
GET /api/v1/lineage/table/{table_id}/downstream
Query Parameters:
  - depth: int = 3

Response: LineageGraphResponse
```

#### Create Table Lineage
```python
POST /api/v1/lineage/table
Request Body: TableLineageCreateRequest
{
  "source_table_id": "uuid",
  "target_table_id": "uuid",
  "transformation_type": "ETL",
  "transformation_logic": "INSERT INTO target SELECT * FROM source WHERE ...",
  "lineage_source": "manual",
  "metadata": {}
}

Response: LineageResponse (201 Created)
```

#### Create Field Lineage
```python
POST /api/v1/lineage/field
Request Body: FieldLineageCreateRequest

Response: LineageResponse (201 Created)
```

#### Approve Lineage
```python
POST /api/v1/lineage/{lineage_id}/approve
Request Body: LineageApprovalRequest
{
  "approved": true,
  "comment": "Verified, lineage is correct"
}

Response: LineageResponse
```

#### Impact Analysis
```python
GET /api/v1/lineage/impact/{table_id}
Query Parameters:
  - change_type: str

Response: ImpactAnalysisResponse
```

### 5. Bulk Import/Export API

#### Validate Import File
```python
POST /api/v1/import/validate
Request: multipart/form-data
  - file: UploadFile
  - import_type: str

Response: ValidationResponse
```

#### Execute Import
```python
POST /api/v1/import/execute
Request: multipart/form-data
  - file: UploadFile
  - import_type: str
  - mode: str
  - skip_errors: bool = false

Response: ImportJobResponse
```

#### Get Import Job Status
```python
GET /api/v1/import/jobs/{job_id}

Response: ImportJobStatusResponse
```

#### Export Metadata
```python
GET /api/v1/export/metadata
Query Parameters:
  - source_ids: Optional[List[UUID]] = None
  - tags: Optional[List[str]] = None
  - format: str = 'csv'

Response: File download
```

### 6. AI Assistant API

#### Natural Language Query
```python
POST /api/v1/ai/query
Request Body: AIQueryRequest
{
  "question": "Find all tables containing user information",
  "conversation_id": "optional_uuid",
  "filters": {}
}

Response: AIQueryResponse
```

#### Semantic Search
```python
POST /api/v1/ai/search
Request Body: SemanticSearchRequest
{
  "query": "customer order data",
  "limit": 10,
  "threshold": 0.7
}

Response: SemanticSearchResponse
```

#### Explain Lineage
```python
POST /api/v1/ai/explain-lineage
Request Body: ExplainLineageRequest
{
  "table_id": "uuid",
  "direction": "upstream"
}

Response: LineageExplanationResponse
```

### 7. Search API

#### Full-Text Search
```python
GET /api/v1/search
Query Parameters:
  - q: str
  - type: Optional[str] = None
  - source_ids: Optional[List[UUID]] = None
  - page: int = 1
  - size: int = 20

Response: SearchResponse
```

## Phase Implementation Plan

### Phase 0: Foundation (Week 1-2)

**Tasks**:
- [ ] Project structure setup
- [ ] FastAPI basic app configuration
- [ ] PostgreSQL + pgvector installation
- [ ] Neo4j installation
- [ ] Redis installation
- [ ] SQLAlchemy model definitions
- [ ] Alembic migration scripts
- [ ] Neo4j initialization scripts
- [ ] OpenAPI specification
- [ ] Docker Compose dev environment

**Deliverables**:
- `docs/api/openapi.yaml`
- `migrations/`
- `docker-compose.dev.yml`
- `README.md`

### Phase 1: Core Infrastructure (Week 3-5)

**Tasks**:
- [ ] Authentication & Authorization
  - JWT token generation/validation
  - Dependency injection: `get_current_user()`
  - RBAC implementation
- [ ] Data Source Management API
  - CRUD operations
  - Connection config encryption (AES-256)
- [ ] Table Metadata API
  - CRUD operations
  - Pagination, filtering, sorting
  - Full-text search (PostgreSQL FTS)
- [ ] Field Metadata API
  - CRUD operations
- [ ] Change History Recording
  - SQLAlchemy event listeners
  - Auto-record CREATE/UPDATE/DELETE
- [ ] Unit Tests
  - Repository layer tests (>80% coverage)
  - Service layer tests
  - API tests (TestClient)

**Deliverables**:
- Running API service
- Unit test suite
- Swagger documentation

### Phase 2: Connector Framework (Week 6-8)

**Tasks**:
- [ ] Connector Abstract Base Class
- [ ] Oracle Connector
  - Use `oracledb` library
  - Extract from `all_tables`, `all_tab_columns`
  - Connection pool management
- [ ] MongoDB Connector
  - Use `pymongo` library
  - List collections
  - Schema inference
- [ ] Elasticsearch Connector
  - Use `elasticsearch` library
  - List indices
  - Extract mapping
- [ ] Metadata Sync Service
  - Celery async tasks
  - Incremental sync logic
  - Error handling & retry
- [ ] Integration Tests
  - Docker Compose test databases
  - Connector integration tests

**Deliverables**:
- 3 working connectors
- Metadata sync functionality
- Integration tests

### Phase 3: Lineage Engine (Week 9-12)

**Tasks**:
- [ ] Neo4j Client Wrapper
  - Connection pool management
  - Transaction handling
- [ ] Graph Models
  - Table nodes, Field nodes
  - FEEDS_INTO, DERIVES_FROM relationships
- [ ] Cypher Query Templates
  - Upstream/downstream queries
  - Impact analysis queries
- [ ] Lineage Service
  - Create table/field lineage
  - Upstream/downstream traversal (N-hop)
  - Impact analysis algorithm
  - Lineage source marking
  - Approval workflow
- [ ] Lineage API
  - All lineage endpoints
- [ ] Cache Layer
  - Redis cache hot lineage queries
  - TTL: 15 minutes
  - Cache invalidation on lineage changes
- [ ] Performance Optimization
  - Neo4j index optimization
  - Query depth limit (max 5 layers)
  - Large graph pagination
- [ ] Tests
  - Lineage traversal algorithm tests
  - Performance tests (1000+ node graphs)

**Deliverables**:
- Complete lineage management API
- High-performance lineage queries (3-hop < 500ms)
- Caching mechanism

### Phase 4: Bulk Operations (Week 13-15)

**Tasks**:
- [ ] File Parsers
  - CSV parser
  - Excel parser
  - JSON parser
  - YAML parser
- [ ] Validation Engine
  - Schema validation
  - Data type validation
  - Referential integrity validation
  - Duplicate detection
  - Business rule validation
- [ ] Import Service
  - Multi-stage processing
  - Celery async tasks
  - Progress tracking
  - Error report generation
- [ ] Export Service
  - Query builder
  - Format conversion
  - Stream large files
- [ ] Import/Export API
- [ ] Tests
  - 10,000+ row import tests
  - Error handling tests
  - Transaction rollback tests

**Deliverables**:
- Bulk import functionality
- Bulk export functionality
- Validation & error reporting

### Phase 5: AI Integration (Week 16-19)

**Tasks**:
- [ ] Embedding Service
  - OpenAI Embeddings API integration
  - Auto-generate embeddings on create/update
- [ ] Vector Search
  - pgvector similarity search
- [ ] RAG Pipeline
  - Query understanding
  - Context retrieval
  - Prompt construction
  - LLM integration
  - Response generation
- [ ] LangChain Integration
  - Custom Retriever
  - Conversation memory
  - Tool calling
- [ ] AI API Implementation
- [ ] Caching Strategy
  - Same question cache (1 hour TTL)
  - Embedding cache
- [ ] Tests
  - Mock OpenAI API tests
  - RAG accuracy tests
  - Response time tests (<3s)

**Deliverables**:
- AI natural language query
- Semantic search
- Lineage explanation generation
- RAG pipeline

### Phase 6: Integration & Optimization (Week 20-22)

**Tasks**:
- [ ] End-to-end integration tests
- [ ] Performance Optimization
  - Database query optimization
  - Add missing indexes
  - Fix N+1 query issues
  - Connection pool tuning
- [ ] Security Hardening
  - SQL injection protection
  - XSS protection
  - CSRF protection
  - Rate limiting
  - Sensitive data encryption audit
- [ ] Monitoring Instrumentation
  - Prometheus metrics
  - Structured logging
- [ ] Error Handling
  - Unified error response format
  - Detailed error logging
  - User-friendly error messages
- [ ] API Documentation
  - Complete all endpoint examples
  - Error code documentation
  - Authentication documentation
- [ ] Deployment Preparation
  - Production environment config
  - Docker image optimization
  - Health check endpoint
  - Readiness probe

**Deliverables**:
- Production-ready backend service
- Complete API documentation
- Monitoring & logging system
- Deployment guide

## Frontend Integration Contract

### Authentication Flow

1. Frontend calls `POST /api/v1/auth/login` to get JWT token
2. Backend returns:
   ```json
   {
     "access_token": "eyJ...",
     "token_type": "bearer",
     "expires_in": 3600
   }
   ```
3. Frontend adds header in subsequent requests:
   ```
   Authorization: Bearer eyJ...
   ```

### Error Response Format

Unified error response structure:
```json
{
  "error": {
    "code": "RESOURCE_NOT_FOUND",
    "message": "Table ID does not exist",
    "details": {
      "table_id": "invalid-uuid"
    }
  }
}
```

HTTP Status Codes:
- `200 OK` - Success
- `201 Created` - Created successfully
- `204 No Content` - Deleted successfully
- `400 Bad Request` - Request parameter error
- `401 Unauthorized` - Not authenticated
- `403 Forbidden` - No permission
- `404 Not Found` - Resource not found
- `409 Conflict` - Resource conflict
- `422 Unprocessable Entity` - Validation failed
- `500 Internal Server Error` - Server error

### Pagination Response Format

All paginated endpoints return:
```json
{
  "total": 1500,
  "page": 1,
  "size": 20,
  "pages": 75,
  "items": [...]
}
```

## Testing Strategy

### Unit Tests

- **Coverage Target**: ≥80%
- **Tools**: pytest + pytest-asyncio
- **Mock**: `unittest.mock` or `pytest-mock`
- **Database**: SQLite in-memory

Example:
```python
@pytest.mark.asyncio
async def test_create_table(mock_table_repo):
    service = MetadataService(repo=mock_table_repo)
    table_data = TableCreateRequest(name="test_table", ...)

    result = await service.create_table(table_data)

    assert result.name == "test_table"
    mock_table_repo.create.assert_called_once()
```

### Integration Tests

- **Database**: Docker containers (PostgreSQL, Neo4j)
- **Tools**: pytest + TestClient
- **Isolation**: Each test uses independent database schema

Example:
```python
def test_create_and_query_lineage(client, test_db):
    response = client.post("/api/v1/lineage/table", json={...})
    assert response.status_code == 201

    lineage_id = response.json()["id"]
    response = client.get(f"/api/v1/lineage/table/{lineage_id}/upstream")
    assert response.status_code == 200
```

### Performance Tests

- **Tools**: Locust or pytest-benchmark
- **Benchmarks**:
  - API response time (P95) < 200ms
  - Lineage query (3-hop) < 500ms
  - Bulk import 10,000 rows < 2 minutes

## Configuration Management

Using Pydantic Settings:

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Ariadne Metadata System"
    DEBUG: bool = False

    DATABASE_URL: str
    NEO4J_URI: str
    NEO4J_USER: str
    NEO4J_PASSWORD: str
    REDIS_URL: str

    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    OPENAI_API_KEY: str
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    LLM_MODEL: str = "gpt-4"

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    class Config:
        env_file = ".env"

settings = Settings()
```

## Logging Standards

Using structlog:

```python
import structlog

logger = structlog.get_logger()

logger.info(
    "table_created",
    table_id=str(table.id),
    table_name=table.name,
    user=current_user.email
)

logger.error(
    "connector_failed",
    source_id=str(source.id),
    error=str(e),
    exc_info=True
)
```

Log Levels:
- `DEBUG` - Development debugging
- `INFO` - Normal operations
- `WARNING` - Warnings
- `ERROR` - Operation failures
- `CRITICAL` - Critical errors

## Dependencies

```txt
# requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
alembic==1.12.1
asyncpg==0.29.0
psycopg2-binary==2.9.9
pgvector==0.2.3
neo4j==5.14.1
redis==5.0.1
celery==5.3.4

# AI/ML
openai==1.3.7
langchain==0.0.340
tiktoken==0.5.1

# Data source drivers
oracledb==1.4.2
pymongo==4.6.0
elasticsearch==8.11.0

# Utils
pydantic==2.5.0
pydantic-settings==2.1.0
python-multipart==0.0.6
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
structlog==23.2.0
openpyxl==3.1.2
pyyaml==6.0.1

# Testing
pytest==7.4.3
pytest-asyncio==0.21.1
pytest-cov==4.1.0
httpx==0.25.2
```

---

**Document Version**: v1.0  
**Last Updated**: 2025-12-21  
**Maintainer**: Backend Architecture Agent
