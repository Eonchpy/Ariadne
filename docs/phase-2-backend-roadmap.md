# Phase 2 Backend Roadmap (Codex)

**Agent**: Backend Agent (Codex)
**Timeline**: Week 6-8 (3 weeks)
**Dependencies**: Phase 1 Complete ✅

---

## Week 6: Data Source Connection Management

### Day 1-2: Connection Service Implementation
**Tasks**:
1. Install database drivers:
   ```bash
   pip install oracledb pymongo elasticsearch
   ```
2. Create connection service (`app/services/connection_service.py`):
   - `test_oracle_connection(config: dict) -> ConnectionTestResult`
   - `test_mongodb_connection(config: dict) -> ConnectionTestResult`
   - `test_elasticsearch_connection(config: dict) -> ConnectionTestResult`
3. Implement connection pooling and timeout handling
4. Add connection encryption (SSL/TLS support)

**Deliverables**:
- Connection service with 3 database types
- Unit tests for each connection type
- Error handling for common connection failures

### Day 3: Credential Encryption (NEW - Codex Suggestion Adopted)
**Tasks**:
1. Install encryption library:
   ```bash
   pip install cryptography
   ```
2. Create encryption service (`app/core/encryption.py`):
   - Implement Fernet encryption/decryption
   - `encrypt(plaintext: str) -> str`
   - `decrypt(ciphertext: str) -> str`
   - `encrypt_dict(data: dict, fields: list) -> dict`
   - `decrypt_dict(data: dict, fields: list) -> dict`
3. Update config to load `ENCRYPTION_KEY` from environment
4. Unit tests for encryption service

**Deliverables**:
- Fernet encryption service implemented
- Unit tests with 100% coverage
- See `/docs/guides/fernet-encryption-guide.md` for implementation details

**Reference**: QC Agent provided implementation guide

---

### Day 4: Data Source CRUD APIs + Encryption Integration
**Tasks**:
1. Implement API endpoints:
   - `POST /api/v1/sources` - Create data source
   - `GET /api/v1/sources` - List data sources (with pagination)
   - `GET /api/v1/sources/{id}` - Get data source details
   - `PUT /api/v1/sources/{id}` - Update data source
   - `DELETE /api/v1/sources/{id}` - Delete data source
   - `POST /api/v1/sources/{id}/test` - Test connection
2. Add validation for connection configs
3. **Integrate encryption**: Encrypt sensitive fields before saving to database
4. **Mask passwords**: Update response schemas to return `"******"` for passwords
5. Configure company test environment (Oracle: f10app@192.168.144.143/pdb1)

**Deliverables**:
- 6 API endpoints implemented
- Credentials encrypted in database (Fernet)
- Passwords masked in API responses
- Request/response validation with Pydantic
- Integration tests for CRUD operations
- Connection test to company Oracle environment successful

### Day 5: Database Migration
**Tasks**:
1. Create Alembic migration to make `source_id` nullable:
   ```python
   # migrations/versions/0002_make_source_id_nullable.py
   op.alter_column('tables', 'source_id', nullable=True)
   ```
2. Update SQLAlchemy model:
   ```python
   source_id: Mapped[uuid.UUID | None] = mapped_column(
       UUID(as_uuid=True), ForeignKey("sources.id", ondelete="CASCADE"),
       nullable=True
   )
   ```
3. Test migration up/down

**Deliverables**:
- Migration file created and tested
- Model updated
- No data loss in migration

---

## Week 7: Smart Metadata Assist + Manual Table CRUD

### Day 1-3: Smart Metadata Introspection Service
**Tasks**:
1. Create introspection service (`app/services/introspection_service.py`):

   **Oracle**:
   ```python
   async def introspect_oracle_table(
       connection_config: dict,
       table_name: str,
       schema_name: str
   ) -> TableIntrospectionResult:
       # Query ALL_TABLES, ALL_TAB_COLUMNS, ALL_CONSTRAINTS
       # Return table metadata + columns with data types and PKs
   ```

   **MongoDB**:
   ```python
   async def introspect_mongodb_collection(
       connection_config: dict,
       collection_name: str
   ) -> TableIntrospectionResult:
       # Get collection stats
       # Sample documents to infer schema
       # Return collection metadata + inferred fields
   ```

   **Elasticsearch**:
   ```python
   async def introspect_elasticsearch_index(
       connection_config: dict,
       index_name: str
   ) -> TableIntrospectionResult:
       # Get index mapping
       # Parse mapping to extract fields
       # Return index metadata + fields
   ```

2. Implement API endpoint:
   - `POST /api/v1/sources/{source_id}/introspect/table`
   - Request: `{ "table_name": "CUSTOMERS", "schema_name": "HR" }`
   - Response: Table metadata + columns array

**Deliverables**:
- Introspection service for 3 database types
- API endpoint implemented
- Unit tests with mocked database connections
- Error handling (table not found, permission denied)

### Day 4-5: Manual Table/Field CRUD
**Tasks**:
1. Update table CRUD to support nullable `source_id`
2. Add field CRUD APIs:
   - `POST /api/v1/tables/{table_id}/fields` - Create field
   - `GET /api/v1/tables/{table_id}/fields` - List fields
   - `PUT /api/v1/fields/{id}` - Update field
   - `DELETE /api/v1/fields/{id}` - Delete field
3. Add batch field creation endpoint:
   - `POST /api/v1/tables/{table_id}/fields/batch` - Create multiple fields at once

**Deliverables**:
- Table CRUD updated for nullable source_id
- Field CRUD APIs implemented
- Batch field creation endpoint
- Integration tests

---

## Week 8: Neo4j Lineage + Bulk Operations

### Day 1-2: Neo4j Lineage Graph Setup
**Tasks**:
1. Create Neo4j node models:
   ```cypher
   CREATE CONSTRAINT table_id IF NOT EXISTS FOR (t:Table) REQUIRE t.id IS UNIQUE;
   CREATE CONSTRAINT field_id IF NOT EXISTS FOR (f:Field) REQUIRE f.id IS UNIQUE;
   ```
2. Implement lineage service (`app/services/lineage_service.py`):
   - `create_table_lineage(source_table_id, target_table_id, lineage_source='manual')`
   - `create_field_lineage(source_field_id, target_field_id, lineage_source='manual')`
   - `get_upstream_lineage(table_id, depth=3)`
   - `get_downstream_lineage(table_id, depth=3)`
3. Sync PostgreSQL tables/fields to Neo4j nodes

**Deliverables**:
- Neo4j constraints and indexes
- Lineage service with CRUD operations
- Sync mechanism (PostgreSQL → Neo4j)

### Day 3: Lineage CRUD APIs
**Tasks**:
1. Implement API endpoints:
   - `POST /api/v1/lineage/table` - Create table-level lineage
   - `POST /api/v1/lineage/field` - Create field-level lineage
   - `GET /api/v1/lineage/table/{table_id}/upstream` - Get upstream lineage
   - `GET /api/v1/lineage/table/{table_id}/downstream` - Get downstream lineage
   - `DELETE /api/v1/lineage/{id}` - Delete lineage relationship
2. Add lineage source classification (manual/approved/inferred)

**Deliverables**:
- 5 lineage API endpoints
- Lineage source classification
- Integration tests with Neo4j

### Day 4: Bulk Import/Export
**Tasks**:
1. Implement bulk import service:
   - Support CSV, Excel, JSON, YAML formats
   - Parse file and validate schema
   - Batch insert tables + fields + lineage relationships
   - Transaction support (rollback on error)
2. Implement bulk export service:
   - Export tables + fields + lineage to CSV/Excel/JSON/YAML
   - Include metadata (created_at, updated_at, lineage_source)
3. API endpoints:
   - `POST /api/v1/bulk/import` - Upload file and import
   - `GET /api/v1/bulk/export?format=csv` - Export data

**Deliverables**:
- Bulk import for 4 file formats
- Bulk export for 4 file formats
- Validation and error reporting
- Transaction support

### Day 5: Simplified Audit Logging (NEW - Codex Suggestion Adopted)
**Tasks**:
1. Create audit log table (Alembic migration):
   ```sql
   CREATE TABLE connection_test_logs (
       id UUID PRIMARY KEY,
       source_id UUID REFERENCES sources(id),
       operation VARCHAR(50),  -- 'connection_test' or 'introspection'
       table_name VARCHAR(255),  -- For introspection operations
       tested_by VARCHAR(100),
       result VARCHAR(20),  -- 'success' or 'failure'
       error_message TEXT,
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   ```
2. Update connection test service to log operations:
   - Log every connection test (source_id, user, result, timestamp)
   - Log every introspection operation (source_id, table_name, user, timestamp)
3. Optional: Basic audit query API
   - `GET /api/v1/audit/connection-tests?source_id={id}` - Query audit logs

**Deliverables**:
- `connection_test_logs` table created
- Connection tests logged automatically
- Introspection operations logged automatically
- Basic audit query API (optional)

**Note**: This is simplified audit logging for Phase 2. Full audit system will be implemented in Phase 6.

---

## Testing Requirements

### Unit Tests
- Connection service tests (mocked connections)
- Introspection service tests (mocked database queries)
- Lineage service tests (mocked Neo4j)
- Bulk import/export tests (sample files)

### Integration Tests
- End-to-end data source CRUD
- Connection testing with real databases (Docker containers)
- Smart metadata assist with real databases
- Lineage creation and querying
- Bulk import/export round-trip

### Target Coverage
- **≥ 80%** overall coverage
- **100%** coverage for critical paths (connection testing, lineage CRUD)

---

## Dependencies

### Python Packages
```txt
oracledb>=1.4.0
pymongo>=4.6.0
elasticsearch>=8.11.0
neo4j>=5.14.0
openpyxl>=3.1.0  # Excel support
pyyaml>=6.0.1    # YAML support
```

### Docker Services
- Oracle Database (for testing)
- MongoDB (for testing)
- Elasticsearch (for testing)
- Neo4j (production + testing)

---

## Success Metrics

- ✅ All 3 database types connect successfully
- ✅ Smart metadata assist retrieves columns correctly
- ✅ Manual tables can be created with/without source binding
- ✅ Lineage relationships stored in Neo4j
- ✅ Bulk import handles 1000+ tables without errors
- ✅ Test coverage ≥ 80%
- ✅ API response time < 200ms (P95)

---

**Document Version**: v1.0
**Last Updated**: 2025-12-23
**Maintainer**: QC Agent (Claude)
**Agent**: Backend Agent (Codex)
