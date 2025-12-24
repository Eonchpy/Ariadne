# Phase 2: Data Source Connection + Manual Lineage Management

**Timeline**: Week 6-8 (3 weeks)
**Status**: Ready to Begin
**Previous Phase**: Phase 1 (Core Infrastructure) ✅ Complete

---

## Overview

Phase 2 introduces a **hybrid approach** that combines:
1. **Data Source Connection Management** - Connect to Oracle, MongoDB, Elasticsearch
2. **Smart Metadata Assist** - On-demand column retrieval for manual tables
3. **Manual Lineage Management** - User-driven lineage documentation
4. **Bulk Operations** - Import/export lineage data

This phase delivers immediate value while deferring complex bulk metadata extraction to Phase 5.

---

## Key Innovation: Smart Metadata Assist

**Problem Solved**: Users want to manually document tables but don't want to type every column name.

**Solution**: On-demand, single-table metadata introspection using active connections.

**User Workflow**:
1. User adds Oracle data source → Test connection ✅
2. User creates new table, enters table name "CUSTOMERS"
3. User clicks "Fetch Columns" button
4. System queries Oracle system catalog for that specific table
5. System auto-populates column names, data types, primary keys
6. User reviews, adjusts, and saves

**Benefits**:
- ✅ Reduces manual data entry
- ✅ Validates table existence
- ✅ Eliminates typos
- ✅ Much simpler than full metadata extraction (no permissions complexity)

---

## Phase Comparison

### Phase 2: Smart Metadata Assist (This Phase)
- User-initiated, on-demand
- Single table at a time
- Synchronous API (immediate feedback)
- No background jobs
- Simple permission model

### Phase 5: Full Metadata Extraction (Later)
- System-initiated, scheduled
- Bulk extraction (all tables)
- Asynchronous jobs (Celery)
- Background processing
- Complex permission handling
- Conflict resolution

---

## Architecture Decisions

### ADR-004: Make source_id Nullable
**Decision**: Change `MetadataTable.source_id` from `nullable=False` to `nullable=True`

**Rationale**:
- Allows manual table creation without binding to data source
- `source_id = NULL` indicates "manually documented table"
- `source_id = UUID` indicates "connected to real source"
- Enables flexible workflow: manual first, connect later

**Migration Required**: Yes (Alembic migration to alter column)

### ADR-005: Split Connector Framework into Two Phases
**Decision**: Phase 2 = Connection + Testing, Phase 5 = Metadata Extraction

**Rationale**:
- Connection testing is simple (ping/health check)
- Metadata extraction is complex (system catalogs, permissions, bulk sync)
- Early connection validation provides immediate value
- Defers complexity to later phase when core lineage is proven

---

## Success Criteria

### Backend
- ✅ All 3 data source types can connect and test successfully
- ✅ Smart metadata assist works for Oracle, MongoDB, Elasticsearch
- ✅ Manual table/field CRUD with optional source binding
- ✅ Neo4j lineage graph operational
- ✅ Lineage relationship CRUD APIs working
- ✅ Bulk import/export functional
- ✅ Test coverage ≥ 80%

### Frontend
- ✅ Data sources management page with connection testing
- ✅ Manual table creation with "Fetch Columns" feature
- ✅ Lineage visualization with ReactFlow
- ✅ Bulk import/export UI
- ✅ Test coverage ≥ 70%

### Integration
- ✅ End-to-end flow: Add source → Test → Create table → Fetch columns → Create lineage
- ✅ Bulk import creates tables + lineage relationships
- ✅ Lineage graph renders correctly

---

## Deliverables

See detailed roadmaps:
- [Backend Roadmap](./phase-2-backend-roadmap.md)
- [Frontend Roadmap](./phase-2-frontend-roadmap.md)
- [API Specification](./phase-2-api-spec.md)

---

**Document Version**: v1.0
**Last Updated**: 2025-12-23
**Maintainer**: QC Agent (Claude)
**Next Phase**: Phase 3 - Lineage Engine Enhancement
