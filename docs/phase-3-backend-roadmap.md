# Phase 3: Lineage Engine Enhancement - Backend Roadmap

**Agent**: Backend Agent (Codex)
**Phase Duration**: Week 9-12 (4 weeks)
**Status**: 🔴 Not Started
**Last Updated**: 2025-12-25

---

## Week 9: Graph Traversal Algorithms

### Day 1-2: Multi-hop Traversal Implementation

**Task 1.1: Upstream Traversal API**
```python
# Endpoint: GET /api/v1/lineage/table/{id}/upstream?depth=3&include_fields=true
# Response: Nested graph structure with all upstream dependencies
```

**Deliverables**:
- [ ] Implement configurable depth traversal (1-10 hops)
- [ ] Support field-level traversal option
- [ ] Add filtering by lineage source (manual/inferred/approved)
- [ ] Return graph in both tree and flat formats

**Neo4j Query Example**:
```cypher
MATCH path = (target:Table {id: $tableId})<-[:FEEDS_INTO*1..3]-(source:Table)
WHERE ALL(r IN relationships(path) WHERE r.lineageSource IN $sources)
RETURN path
```

**Task 1.2: Downstream Traversal API**
```python
# Endpoint: GET /api/v1/lineage/table/{id}/downstream?depth=3
```

**Deliverables**:
- [ ] Mirror upstream traversal functionality
- [ ] Add impact scope metrics (total affected tables/fields)
- [ ] Support pagination for large result sets

---

### Day 3-4: Bidirectional & Path Finding

**Task 2.1: Find All Paths Between Nodes**
```python
# Endpoint: GET /api/v1/lineage/paths?from={id}&to={id}&max_depth=5
```

**Deliverables**:
- [ ] Find all paths between two tables
- [ ] Shortest path algorithm
- [ ] Path ranking by confidence score
- [ ] Circular dependency detection

**Neo4j Query**:
```cypher
MATCH path = allShortestPaths(
  (source:Table {id: $fromId})-[:FEEDS_INTO*..5]->(target:Table {id: $toId})
)
RETURN path
```

**Task 2.2: Graph Filtering**

**Deliverables**:
- [ ] Filter by source type (oracle/mongodb/elasticsearch)
- [ ] Filter by confidence threshold
- [ ] Filter by approval status
- [ ] Filter by date range

---

### Day 5: Testing & Documentation

**Deliverables**:
- [ ] Unit tests for all traversal functions (coverage ≥ 80%)
- [ ] Integration tests with sample graphs
- [ ] API documentation (OpenAPI spec)
- [ ] Performance baseline measurements

---

## Week 10: Impact & Root Cause Analysis

### Day 1-2: Impact Analysis

**Task 3.1: Impact Analysis API**
```python
# Endpoint: POST /api/v1/lineage/impact
# Body: { "table_id": "uuid", "change_type": "schema_change|data_quality" }
```

**Deliverables**:
- [ ] Calculate full downstream impact
- [ ] Categorize impact by severity (direct/indirect)
- [ ] Estimate affected row counts
- [ ] Generate impact report

**Algorithm**:
```python
def analyze_impact(table_id, change_type):
    # 1. Get all downstream tables (unlimited depth)
    # 2. Calculate distance from source
    # 3. Estimate impact severity based on:
    #    - Distance (closer = higher impact)
    #    - Relationship confidence
    #    - Table importance (row count, usage frequency)
    # 4. Return ranked list
```

---

### Day 3-4: Root Cause Analysis

**Task 4.1: Root Cause Tracing API**
```python
# Endpoint: POST /api/v1/lineage/root-cause
# Body: { "table_id": "uuid", "issue_type": "data_quality|missing_data" }
```

**Deliverables**:
- [ ] Trace back to all source tables
- [ ] Identify critical path (most likely cause)
- [ ] Highlight low-confidence relationships
- [ ] Generate investigation checklist

**Task 4.2: Circular Dependency Detection**

**Deliverables**:
- [ ] Detect cycles in lineage graph
- [ ] Report cycle paths
- [ ] Suggest resolution strategies

**Neo4j Query**:
```cypher
MATCH path = (t:Table)-[:FEEDS_INTO*]->(t)
RETURN path
```

---

### Day 5: Metrics & Reporting

**Task 5.1: Dependency Metrics**

**Deliverables**:
- [ ] Calculate in-degree (number of upstream dependencies)
- [ ] Calculate out-degree (number of downstream consumers)
- [ ] Identify hub tables (high degree centrality)
- [ ] Generate dependency matrix

---

## Week 11: Performance Optimization

### Day 1-2: Neo4j Optimization

**Task 6.1: Index Optimization**

**Deliverables**:
- [ ] Create composite indexes for frequent queries
- [ ] Analyze query execution plans
- [ ] Optimize Cypher queries
- [ ] Configure Neo4j memory settings

**Indexes to Create**:
```cypher
CREATE INDEX table_id_source FOR (t:Table) ON (t.id, t.source);
CREATE INDEX lineage_source_confidence FOR ()-[r:FEEDS_INTO]-()
  ON (r.lineageSource, r.confidence);
```

**Task 6.2: Query Plan Analysis**

**Deliverables**:
- [ ] Profile slow queries (>500ms)
- [ ] Identify missing indexes
- [ ] Rewrite inefficient queries
- [ ] Document optimization decisions

---

### Day 3-4: Caching Layer

**Task 7.1: Redis Cache Implementation**

**Deliverables**:
- [ ] Cache frequent traversal queries
- [ ] Cache impact analysis results
- [ ] Implement cache invalidation strategy
- [ ] Configure TTL policies

**Cache Strategy**:
```python
# Cache key format: lineage:upstream:{table_id}:{depth}:{filters_hash}
# TTL: 1 hour for traversal queries
# Invalidation: On lineage create/update/delete
```

**Task 7.2: Incremental Loading**

**Deliverables**:
- [ ] Implement pagination for large graphs
- [ ] Support lazy loading of graph branches
- [ ] Add "load more" functionality
- [ ] Optimize initial page load

---

### Day 5: Performance Benchmarking

**Task 8.1: Benchmark Suite**

**Deliverables**:
- [ ] Create test graphs (100, 500, 1000, 5000 nodes)
- [ ] Measure query response times
- [ ] Measure cache hit rates
- [ ] Generate performance report

**Performance Targets**:
- 3-hop query: < 500ms (P95)
- 5-hop query: < 1s (P95)
- Impact analysis (100 nodes): < 1s
- Cache hit rate: > 80%

---

## Week 12: Workflow & Scoring

### Day 1-2: Approval Workflow

**Task 9.1: Workflow State Machine**

**States**: `draft` → `submitted` → `under_review` → `approved`/`rejected`

**Deliverables**:
- [ ] Create `lineage_approvals` table in PostgreSQL
- [ ] Implement state transition API
- [ ] Add role-based access control
- [ ] Create approval history tracking

**Database Schema**:
```sql
CREATE TABLE lineage_approvals (
    id UUID PRIMARY KEY,
    lineage_id VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL,
    submitted_by VARCHAR(100),
    submitted_at TIMESTAMP,
    reviewed_by VARCHAR(100),
    reviewed_at TIMESTAMP,
    comments TEXT,
    CONSTRAINT valid_status CHECK (status IN
      ('draft', 'submitted', 'under_review', 'approved', 'rejected'))
);
```

**Task 9.2: Approval API**

**Endpoints**:
```python
POST   /api/v1/lineage/{id}/submit
POST   /api/v1/lineage/{id}/approve
POST   /api/v1/lineage/{id}/reject
GET    /api/v1/lineage/pending-approvals
```

---

### Day 3-4: Confidence Scoring

**Task 10.1: Scoring Algorithm**

**Deliverables**:
- [ ] Implement confidence calculation
- [ ] Update confidence on lineage changes
- [ ] Add confidence decay over time
- [ ] Display confidence in API responses

**Scoring Factors**:
```python
confidence = (
    source_weight * 0.4 +      # manual=1.0, inferred=0.5
    approval_weight * 0.3 +     # approved=1.0, not_approved=0.7
    freshness_weight * 0.2 +    # decay over time
    usage_weight * 0.1          # based on query frequency
)
```

**Task 10.2: Quality Metrics**

**Deliverables**:
- [ ] Calculate lineage completeness (% of tables with lineage)
- [ ] Calculate approval rate
- [ ] Calculate average confidence score
- [ ] Generate quality dashboard data

---

### Day 5: Integration & Testing

**Task 11.1: End-to-End Testing**

**Deliverables**:
- [ ] Integration tests for all workflows
- [ ] Test approval workflow with multiple roles
- [ ] Test confidence score updates
- [ ] Performance regression tests

**Task 11.2: Documentation**

**Deliverables**:
- [ ] API documentation complete
- [ ] Algorithm documentation
- [ ] Deployment guide updates
- [ ] User guide for approval workflow

---

## Deliverables Summary

### APIs (12 new endpoints)
- ✅ Multi-hop traversal (upstream/downstream)
- ✅ Path finding & shortest path
- ✅ Impact analysis
- ✅ Root cause analysis
- ✅ Circular dependency detection
- ✅ Approval workflow (submit/approve/reject)
- ✅ Pending approvals list

### Database Changes
- ✅ `lineage_approvals` table
- ✅ Neo4j indexes optimization
- ✅ Redis cache configuration

### Performance Improvements
- ✅ Query optimization (3-hop < 500ms)
- ✅ Caching layer (>80% hit rate)
- ✅ Pagination support

### Testing
- ✅ Unit tests (≥80% coverage)
- ✅ Integration tests
- ✅ Performance benchmarks

---

## Dependencies & Blockers

### Prerequisites
- Phase 2 lineage graph complete
- Neo4j APOC plugin installed
- Redis configured

### Potential Blockers
- Neo4j performance issues → Mitigation: Early benchmarking
- Complex approval workflow → Mitigation: Start simple, iterate
- Cache invalidation bugs → Mitigation: Comprehensive testing

---

**Next Steps**: Review with Frontend Agent to align on API contracts
