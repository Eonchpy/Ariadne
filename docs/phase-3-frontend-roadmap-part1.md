# Phase 3: Lineage Engine Enhancement - Frontend Roadmap (Part 1/3)

**Agent**: Frontend Agent (Gemini)
**Phase Duration**: Week 9-12 (4 weeks)
**Status**: 🔴 Not Started
**Last Updated**: 2025-12-26

---

## Overview

Enhance the lineage visualization with path analysis, impact assessment, and performance optimization.

### Scope Changes
- ❌ Multi-hop traversal controls (already in Phase 2)
- ❌ Approval workflow UI (deferred)
- ❌ Confidence score display (removed)

### Core UI Components

1. **Path Finding UI**: Select nodes and find paths between them
2. **Impact Analysis Panel**: Visual impact assessment
3. **Root Cause Tracer**: Interactive investigation tool
4. **Performance Optimization**: Support 1000+ nodes

---

## Week 9: Path Finding & Filtering

### Day 1-2: Path Finding UI

**Task 1.1: Node Selection Mode**

**UI Requirements**:
- "Find Path" button in toolbar
- Click to select source node (blue highlight)
- Click to select target node (green highlight)
- Display all paths in side panel

**Component Structure**:
```tsx
<PathFindingMode
  active={isPathFindingMode}
  sourceNode={selectedSource}
  targetNode={selectedTarget}
  onPathsFound={(paths) => highlightPaths(paths)}
/>
```

**Deliverables**:
- [ ] Path finding mode toggle
- [ ] Node selection state management
- [ ] Path highlighting on graph
- [ ] Path details side panel

---

### Day 3-4: Enhanced Filtering

**Task 1.2: Filter Panel Enhancement**

**Filter Options**:
- Source type (Oracle/MongoDB/Elasticsearch)
- Lineage source (Manual/Inferred)
- Date range picker

**Deliverables**:
- [ ] Enhanced filter panel
- [ ] Multi-select for source types
- [ ] Date range picker integration
- [ ] Active filter tags display

---

### Day 5: Circular Dependency Detection UI

**Task 1.3: Cycle Detection**

**UI Requirements**:
- "Detect Cycles" button in toolbar
- Visual cycle highlighting (purple border)
- Cycle path list panel

**Deliverables**:
- [ ] Cycle detection trigger button
- [ ] Cycle highlighting on graph
- [ ] Cycle details panel

---

## Week 9 Deliverables Summary

- ✅ Path finding UI
- ✅ Enhanced filter panel
- ✅ Circular dependency detection
- ✅ Path details side panel

---

**Next**: Week 10 - Impact Analysis & Root Cause UI (Part 2/3)
