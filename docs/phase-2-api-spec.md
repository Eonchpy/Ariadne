# Phase 2 API Specification

**Version**: v0.2.0
**Base URL**: `/api/v1`
**Authentication**: JWT Bearer Token

---

## New Endpoints Summary

### Data Sources
- `POST /sources` - Create data source
- `GET /sources` - List data sources
- `GET /sources/{id}` - Get data source
- `PUT /sources/{id}` - Update data source
- `DELETE /sources/{id}` - Delete data source
- `POST /sources/{id}/test` - Test connection

### Smart Metadata Assist
- `POST /sources/{source_id}/introspect/table` - Introspect table/collection/index

### Tables (Updated)
- `POST /tables` - Create table (source_id now optional)
- `GET /tables` - List tables (add filter by source_id)
- `GET /tables/{id}` - Get table
- `PUT /tables/{id}` - Update table
- `DELETE /tables/{id}` - Delete table

### Fields (New)
- `POST /tables/{table_id}/fields` - Create field
- `POST /tables/{table_id}/fields/batch` - Batch create fields
- `GET /tables/{table_id}/fields` - List fields
- `PUT /fields/{id}` - Update field
- `DELETE /fields/{id}` - Delete field

### Lineage (New)
- `POST /lineage/table` - Create table-level lineage
- `POST /lineage/field` - Create field-level lineage
- `GET /lineage/table/{table_id}/upstream` - Get upstream lineage
- `GET /lineage/table/{table_id}/downstream` - Get downstream lineage
- `DELETE /lineage/{id}` - Delete lineage

### Bulk Operations (New)
- `POST /bulk/import` - Import data from file
- `GET /bulk/export` - Export data to file

---

## Detailed API Specifications

### 1. Data Sources

#### POST /sources
Create a new data source.

**Request**:
```json
{
  "name": "Oracle Production",
  "type": "oracle",
  "description": "Production Oracle database",
  "connection_config": {
    "host": "oracle.example.com",
    "port": 1521,
    "service_name": "ORCL",
    "username": "admin",
    "password": "secret123"
  },
  "is_active": true
}
```

**Response** (201):
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "name": "Oracle Production",
  "type": "oracle",
  "description": "Production Oracle database",
  "connection_config": {
    "host": "oracle.example.com",
    "port": 1521,
    "service_name": "ORCL",
    "username": "admin"
    // password is encrypted and not returned
  },
  "is_active": true,
  "created_at": "2025-12-23T10:00:00Z",
  "updated_at": "2025-12-23T10:00:00Z"
}
```

#### GET /sources
List all data sources with pagination.

**Query Parameters**:
- `page` (int, default: 1)
- `size` (int, default: 20)
- `type` (string, optional): Filter by type (oracle/mongodb/elasticsearch)
- `is_active` (boolean, optional): Filter by active status

**Response** (200):
```json
{
  "total": 15,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "name": "Oracle Production",
      "type": "oracle",
      "description": "Production Oracle database",
      "is_active": true,
      "last_tested_at": "2025-12-23T09:30:00Z",
      "last_test_status": "success",
      "created_at": "2025-12-23T10:00:00Z",
      "updated_at": "2025-12-23T10:00:00Z"
    }
  ]
}
```

#### POST /sources/{id}/test
Test connection to data source.

**Response** (200):
```json
{
  "status": "success",
  "message": "Connection successful",
  "tested_at": "2025-12-23T10:05:00Z",
  "latency_ms": 45
}
```

**Response** (400) - Connection Failed:
```json
{
  "error": {
    "code": "CONNECTION_FAILED",
    "message": "Failed to connect to Oracle database",
    "details": "ORA-12154: TNS:could not resolve the connect identifier specified"
  }
}
```

---

### 2. Smart Metadata Assist

#### POST /sources/{source_id}/introspect/table
Introspect a single table/collection/index from the data source.

**Request**:
```json
{
  "table_name": "CUSTOMERS",
  "schema_name": "HR"  // Optional, for Oracle/PostgreSQL
}
```

**Response** (200) - Oracle Example:
```json
{
  "table": {
    "name": "CUSTOMERS",
    "schema_name": "HR",
    "qualified_name": "HR.CUSTOMERS",
    "type": "TABLE",
    "row_count": 15000,
    "description": null
  },
  "fields": [
    {
      "name": "CUSTOMER_ID",
      "data_type": "NUMBER",
      "is_nullable": false,
      "is_primary_key": true,
      "description": null,
      "ordinal_position": 1
    },
    {
      "name": "FIRST_NAME",
      "data_type": "VARCHAR2(50)",
      "is_nullable": true,
      "is_primary_key": false,
      "description": null,
      "ordinal_position": 2
    },
    {
      "name": "EMAIL",
      "data_type": "VARCHAR2(100)",
      "is_nullable": false,
      "is_primary_key": false,
      "description": null,
      "ordinal_position": 3
    }
  ]
}
```

**Response** (200) - MongoDB Example:
```json
{
  "table": {
    "name": "customers",
    "type": "COLLECTION",
    "row_count": 12500,
    "description": null
  },
  "fields": [
    {
      "name": "_id",
      "data_type": "ObjectId",
      "is_nullable": false,
      "is_primary_key": true,
      "ordinal_position": 1
    },
    {
      "name": "firstName",
      "data_type": "String",
      "is_nullable": true,
      "is_primary_key": false,
      "ordinal_position": 2
    },
    {
      "name": "email",
      "data_type": "String",
      "is_nullable": true,
      "is_primary_key": false,
      "ordinal_position": 3
    }
  ]
}
```

**Response** (404) - Table Not Found:
```json
{
  "error": {
    "code": "TABLE_NOT_FOUND",
    "message": "Table 'CUSTOMERS' not found in schema 'HR'"
  }
}
```

**Response** (403) - Permission Denied:
```json
{
  "error": {
    "code": "PERMISSION_DENIED",
    "message": "User does not have permission to access table 'HR.CUSTOMERS'"
  }
}
```

---

### 3. Tables (Updated)

#### POST /tables
Create a new table (source_id is now optional).

**Request** (Manual Table):
```json
{
  "name": "users",
  "type": "table",
  "description": "User accounts table",
  "source_id": null,  // Manual table, not bound to any source
  "schema_name": null,
  "tags": ["core", "authentication"]
}
```

**Request** (Table Bound to Source):
```json
{
  "name": "CUSTOMERS",
  "type": "table",
  "description": "Customer data",
  "source_id": "550e8400-e29b-41d4-a716-446655440000",
  "schema_name": "HR",
  "qualified_name": "HR.CUSTOMERS",
  "tags": ["sales", "crm"]
}
```

**Response** (201):
```json
{
  "id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "CUSTOMERS",
  "type": "table",
  "description": "Customer data",
  "source_id": "550e8400-e29b-41d4-a716-446655440000",
  "schema_name": "HR",
  "qualified_name": "HR.CUSTOMERS",
  "tags": ["sales", "crm"],
  "row_count": null,
  "field_count": 0,
  "created_at": "2025-12-23T10:10:00Z",
  "updated_at": "2025-12-23T10:10:00Z"
}
```

#### GET /tables
List tables with filtering.

**Query Parameters**:
- `page` (int, default: 1)
- `size` (int, default: 20)
- `source_id` (uuid, optional): Filter by data source
- `source_type` (string, optional): "manual" (source_id is null) or "connected" (source_id is not null)
- `search` (string, optional): Search by table name

**Response** (200):
```json
{
  "total": 50,
  "page": 1,
  "size": 20,
  "items": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "CUSTOMERS",
      "type": "table",
      "source_id": "550e8400-e29b-41d4-a716-446655440000",
      "source_name": "Oracle Production",
      "schema_name": "HR",
      "field_count": 15,
      "created_at": "2025-12-23T10:10:00Z"
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440002",
      "name": "users",
      "type": "table",
      "source_id": null,
      "source_name": null,  // Manual table
      "schema_name": null,
      "field_count": 8,
      "created_at": "2025-12-23T10:15:00Z"
    }
  ]
}
```

---

### 4. Fields (New)

#### POST /tables/{table_id}/fields
Create a single field.

**Request**:
```json
{
  "name": "email",
  "data_type": "VARCHAR(100)",
  "is_nullable": false,
  "is_primary_key": false,
  "description": "User email address",
  "ordinal_position": 3
}
```

**Response** (201):
```json
{
  "id": "770e8400-e29b-41d4-a716-446655440003",
  "table_id": "660e8400-e29b-41d4-a716-446655440001",
  "name": "email",
  "data_type": "VARCHAR(100)",
  "is_nullable": false,
  "is_primary_key": false,
  "description": "User email address",
  "ordinal_position": 3,
  "created_at": "2025-12-23T10:20:00Z",
  "updated_at": "2025-12-23T10:20:00Z"
}
```

#### POST /tables/{table_id}/fields/batch
Batch create multiple fields (used after smart metadata assist).

**Request**:
```json
{
  "fields": [
    {
      "name": "CUSTOMER_ID",
      "data_type": "NUMBER",
      "is_nullable": false,
      "is_primary_key": true,
      "ordinal_position": 1
    },
    {
      "name": "FIRST_NAME",
      "data_type": "VARCHAR2(50)",
      "is_nullable": true,
      "is_primary_key": false,
      "ordinal_position": 2
    }
  ]
}
```

**Response** (201):
```json
{
  "created_count": 2,
  "fields": [
    {
      "id": "770e8400-e29b-41d4-a716-446655440003",
      "name": "CUSTOMER_ID",
      "data_type": "NUMBER",
      "is_nullable": false,
      "is_primary_key": true,
      "ordinal_position": 1
    },
    {
      "id": "770e8400-e29b-41d4-a716-446655440004",
      "name": "FIRST_NAME",
      "data_type": "VARCHAR2(50)",
      "is_nullable": true,
      "is_primary_key": false,
      "ordinal_position": 2
    }
  ]
}
```

---

### 5. Lineage (New)

#### POST /lineage/table
Create table-level lineage relationship.

**Request**:
```json
{
  "source_table_id": "660e8400-e29b-41d4-a716-446655440001",
  "target_table_id": "660e8400-e29b-41d4-a716-446655440002",
  "lineage_source": "manual",  // manual | approved | inferred
  "description": "ETL job copies customer data to analytics table"
}
```

**Response** (201):
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440005",
  "source_table_id": "660e8400-e29b-41d4-a716-446655440001",
  "target_table_id": "660e8400-e29b-41d4-a716-446655440002",
  "lineage_source": "manual",
  "description": "ETL job copies customer data to analytics table",
  "created_at": "2025-12-23T10:30:00Z"
}
```

#### POST /lineage/field
Create field-level lineage relationship.

**Request**:
```json
{
  "source_field_id": "770e8400-e29b-41d4-a716-446655440003",
  "target_field_id": "770e8400-e29b-41d4-a716-446655440006",
  "lineage_source": "manual",
  "transformation": "UPPER(email)",
  "description": "Email is uppercased during ETL"
}
```

**Response** (201):
```json
{
  "id": "880e8400-e29b-41d4-a716-446655440007",
  "source_field_id": "770e8400-e29b-41d4-a716-446655440003",
  "target_field_id": "770e8400-e29b-41d4-a716-446655440006",
  "lineage_source": "manual",
  "transformation": "UPPER(email)",
  "description": "Email is uppercased during ETL",
  "created_at": "2025-12-23T10:35:00Z"
}
```

#### GET /lineage/table/{table_id}/upstream
Get upstream lineage (tables that feed into this table).

**Query Parameters**:
- `depth` (int, default: 3, max: 5): How many hops to traverse
- `lineage_source` (string, optional): Filter by lineage source (manual/approved/inferred)

**Response** (200):
```json
{
  "table_id": "660e8400-e29b-41d4-a716-446655440002",
  "depth": 3,
  "nodes": [
    {
      "id": "660e8400-e29b-41d4-a716-446655440001",
      "name": "CUSTOMERS",
      "type": "table",
      "source_name": "Oracle Production",
      "level": 1
    },
    {
      "id": "660e8400-e29b-41d4-a716-446655440008",
      "name": "RAW_CUSTOMERS",
      "type": "table",
      "source_name": "MongoDB Staging",
      "level": 2
    }
  ],
  "edges": [
    {
      "id": "880e8400-e29b-41d4-a716-446655440005",
      "source_id": "660e8400-e29b-41d4-a716-446655440001",
      "target_id": "660e8400-e29b-41d4-a716-446655440002",
      "lineage_source": "manual",
      "description": "ETL job copies customer data"
    }
  ]
}
```

---

### 6. Bulk Operations (New)

#### POST /bulk/import
Import tables, fields, and lineage from file.

**Request** (multipart/form-data):
- `file`: File upload (CSV/Excel/JSON/YAML)
- `format`: "csv" | "excel" | "json" | "yaml"
- `preview`: boolean (if true, return preview without importing)

**Response** (200) - Preview:
```json
{
  "preview": true,
  "tables_count": 50,
  "fields_count": 350,
  "lineage_count": 75,
  "sample_tables": [
    {
      "name": "customers",
      "fields_count": 8,
      "source_name": "Oracle Production"
    }
  ]
}
```

**Response** (201) - Import Success:
```json
{
  "status": "success",
  "tables_created": 50,
  "fields_created": 350,
  "lineage_created": 75,
  "errors": []
}
```

**Response** (207) - Partial Success:
```json
{
  "status": "partial_success",
  "tables_created": 48,
  "fields_created": 340,
  "lineage_created": 70,
  "errors": [
    {
      "row": 15,
      "table": "invalid_table",
      "error": "Table name contains invalid characters"
    }
  ]
}
```

#### GET /bulk/export
Export tables, fields, and lineage to file.

**Query Parameters**:
- `format`: "csv" | "excel" | "json" | "yaml"
- `scope`: "all" | "source:{source_id}" | "tables:{table_ids}"
- `include_lineage`: boolean (default: true)

**Response** (200):
- Content-Type: application/octet-stream
- Content-Disposition: attachment; filename="ariadne_export_2025-12-23.xlsx"
- Body: File content

---

## Error Responses

All error responses follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable error message",
    "details": "Additional technical details (optional)"
  }
}
```

### Common Error Codes
- `VALIDATION_ERROR` (400): Request validation failed
- `UNAUTHORIZED` (401): Authentication required
- `FORBIDDEN` (403): Insufficient permissions
- `NOT_FOUND` (404): Resource not found
- `CONFLICT` (409): Resource already exists
- `CONNECTION_FAILED` (400): Data source connection failed
- `TABLE_NOT_FOUND` (404): Table not found in data source
- `PERMISSION_DENIED` (403): No permission to access resource
- `INTERNAL_ERROR` (500): Server error

---

## Performance Requirements

- API response time (P95): < 200ms (regular endpoints)
- Connection testing: < 5s timeout
- Smart metadata assist: < 10s timeout
- Lineage query (3-hop): < 500ms
- Bulk import (1000 rows): < 30s

---

**Document Version**: v1.0
**Last Updated**: 2025-12-23
**Maintainer**: QC Agent (Claude)
