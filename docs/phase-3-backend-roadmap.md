# Phase 3: Lineage Engine Enhancement - Backend Roadmap

**Agent**: Backend Agent (Codex)
**Phase Duration**: Week 9-12 (4 weeks)
**Status**: 🔴 Not Started
**Last Updated**: 2025-12-26

---

## Scope Changes

### Removed Features
- ❌ Multi-hop traversal (already in Phase 2 with depth 1-5)
- ❌ Approval workflow (deferred)
- ❌ Confidence scoring (over-engineering)

### Focus Areas
- ✅ Path finding between nodes
- ✅ Impact analysis
- ✅ Root cause analysis
- ✅ Performance optimization

---

## Week 9: Path Finding & Analysis

### Day 1-2: Find All Paths Between Nodes

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

**Task 1.2: Graph Filtering**

**Deliverables**:
- [ ] Filter by source type (oracle/mongodb/elasticsearch)
- [ ] Filter by lineage source (manual/inferred)
- [ ] Filter by date range

### Day 3-4: Circular Dependency Detection

**Task 1.3: Cycle Detection API**
```python
# Endpoint: GET /api/v1/lineage/cycles?table_id={id}
```

**Deliverables**:
- [ ] Detect cycles in lineage graph
- [ ] Report all cycle paths
- [ ] Calculate cycle length

**Neo4j Query**:
```cypher
MATCH path = (t:Table)-[:FEEDS_INTO*]->(t)
WHERE t.id = $tableId OR $tableId IS NULL
RETURN path
```

---

### Day 5: Testing & Documentation

**Deliverables**:
- [ ] Unit tests for path finding (coverage ≥ 80%)
- [ ] Integration tests with sample graphs
- [ ] API documentation (OpenAPI spec)
- [ ] Performance baseline measurements

---

## Week 10: Impact & Root Cause Analysis

### Day 1-2: Impact Analysis

**Task 2.1: Impact Analysis API**
```python
# Endpoint: POST /api/v1/lineage/impact
# Body: { "table_id": "uuid", "change_type": "schema_change|data_quality" }
```

**Deliverables**:
- [ ] Calculate full downstream impact
- [ ] Categorize impact by distance (direct/indirect)
- [ ] Estimate affected row counts
- [ ] Generate impact report

---

### Day 3-4: Root Cause Analysis

**Task 2.2: Root Cause Tracing API**
```python
# Endpoint: POST /api/v1/lineage/root-cause
# Body: { "table_id": "uuid", "issue_type": "data_quality|missing_data" }
```

**Deliverables**:
- [ ] Trace back to all source tables
- [ ] Identify critical path (most likely cause)
- [ ] Generate investigation checklist

---

### Day 5: Metrics & Reporting

**Task 2.3: Dependency Metrics**

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
CREATE INDEX lineage_source FOR ()-[r:FEEDS_INTO]-() ON (r.lineageSource);
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
- Path finding: < 1s (P95)
- Impact analysis (100 nodes): < 1s
- Cache hit rate: > 80%

---

## Week 12: Integration & Testing

### Day 1-2: API Integration

**Task 4.1: Frontend-Backend Integration**

**Deliverables**:
- [ ] Coordinate with Frontend Agent on API contracts
- [ ] Test all new endpoints
- [ ] Fix integration issues
- [ ] Update OpenAPI documentation

---

### Day 3-4: End-to-End Testing

**Task 4.2: Integration Testing**

**Deliverables**:
- [ ] Integration tests for all new APIs
- [ ] Test path finding with complex graphs
- [ ] Test impact analysis accuracy
- [ ] Performance regression tests

---

### Day 5: Documentation & Handoff

**Task 4.3: Documentation**

**Deliverables**:
- [ ] API documentation complete
- [ ] Algorithm documentation
- [ ] Deployment guide updates
- [ ] Handoff to QC Agent

---

## Deliverables Summary

### APIs (6 new endpoints)
- ✅ Find all paths between nodes
- ✅ Shortest path
- ✅ Circular dependency detection
- ✅ Impact analysis
- ✅ Root cause analysis
- ✅ Dependency metrics

### Database Changes
- ✅ Neo4j indexes optimization
- ✅ Redis cache configuration

### Performance Improvements
- ✅ Query optimization (<1s for path finding)
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
- Complex path finding algorithms → Mitigation: Use APOC library

---

**Next Steps**: Review with Frontend Agent to align on API contracts
