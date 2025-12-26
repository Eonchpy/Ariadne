# Phase 3: Lineage Engine Enhancement - Frontend Roadmap (Part 2/3)

**Agent**: Frontend Agent (Gemini)
**Phase Duration**: Week 9-12 (4 weeks)
**Status**: 🔴 Not Started
**Last Updated**: 2025-12-25

---

## Week 10: Impact Analysis & Root Cause UI

### Day 1-2: Impact Analysis Panel

**Task 4.1: Impact Analysis Trigger**

**UI Requirements**:
- Right-click context menu on table node
- "Analyze Impact" option
- Modal dialog for impact configuration
- Change type selection (schema change/data quality issue)

**Component Structure**:
```tsx
<ImpactAnalysisModal
  tableId={selectedTableId}
  tableName={selectedTableName}
  onAnalyze={(config) => runImpactAnalysis(config)}
  visible={showModal}
  onClose={() => setShowModal(false)}
/>
```

**Deliverables**:
- [ ] Context menu component
- [ ] Impact analysis modal
- [ ] Change type selector
- [ ] Loading state with progress indicator

---

**Task 4.2: Impact Visualization**

**UI Requirements**:
- Highlight affected nodes in different colors
- Severity indicators (direct/indirect impact)
- Impact metrics panel (total affected tables/fields)
- Expandable impact tree view

**Visual Design**:
- Direct impact: Red nodes
- Indirect impact: Orange nodes
- No impact: Gray (dimmed)
- Impact severity badge on nodes

**Deliverables**:
- [ ] Impact highlighting on graph
- [ ] Severity color coding
- [ ] Impact metrics summary card
- [ ] Impact tree view component

---

### Day 3-4: Root Cause Analysis UI

**Task 5.1: Root Cause Tracer**

**UI Requirements**:
- "Trace Root Cause" button on table node
- Issue type selection (data quality/missing data)
- Interactive investigation flow
- Highlight critical path

**Component Structure**:
```tsx
<RootCauseTracer
  tableId={issueTableId}
  issueType={selectedIssueType}
  onTrace={(result) => displayRootCausePath(result)}
/>
```

**Deliverables**:
- [ ] Root cause modal dialog
- [ ] Issue type selector
- [ ] Critical path highlighting
- [ ] Source table identification

---

**Task 5.2: Investigation Checklist**

**UI Requirements**:
- Auto-generated investigation steps
- Checkable task list
- Low-confidence relationship warnings
- Export investigation report

**Deliverables**:
- [ ] Investigation checklist component
- [ ] Task completion tracking
- [ ] Warning indicators for low-confidence links
- [ ] Export to PDF/Markdown

---

### Day 5: Circular Dependency Detection

**Task 6.1: Cycle Detection UI**

**UI Requirements**:
- "Detect Cycles" button in toolbar
- Visual cycle highlighting on graph
- Cycle path list panel
- Resolution suggestions

**Visual Design**:
- Cycle nodes: Purple border
- Cycle edges: Dashed purple lines
- Cycle badge on affected nodes

**Deliverables**:
- [ ] Cycle detection trigger button
- [ ] Cycle highlighting on graph
- [ ] Cycle details panel
- [ ] Resolution suggestions UI

---

## Week 10 Deliverables Summary

- ✅ Impact analysis modal
- ✅ Impact visualization with severity colors
- ✅ Root cause tracer UI
- ✅ Investigation checklist
- ✅ Circular dependency detection
- ✅ Export investigation reports

---

**Next**: Week 11-12 - Performance & Workflow UI (Part 3/3)
