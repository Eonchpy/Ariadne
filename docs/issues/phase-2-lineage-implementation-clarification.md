# Phase 2 血缘关系实现澄清

**Issue ID**: P2-LINEAGE-001
**Priority**: High
**Status**: Needs Clarification
**Created**: 2025-12-23
**Reporter**: QC Agent (Claude)

---

## 问题描述

在 Phase 2 验收审查中，发现血缘关系的查询和展示可能存在理解偏差。需要 Codex 和 Gemini 确认当前实现是否符合预期设计。

---

## 预期设计（正确理解）

### API 行为

当用户查询某个表的血缘关系时，**应该一次性返回**：
- 该表的上游/下游表（表级血缘）
- 该表的字段的上游/下游字段（字段级血缘）

**示例**：

```http
GET /api/v1/lineage/table/{table_id}/upstream?depth=3
```

**预期响应**：
```json
{
  "root_id": "table-123",
  "nodes": [
    {
      "id": "table-456",
      "label": "orders",
      "type": "table",
      "source_id": "source-1"
    },
    {
      "id": "field-789",
      "label": "order_id",
      "type": "field",
      "source_id": null
    },
    {
      "id": "field-101",
      "label": "customer_id",
      "type": "field",
      "source_id": null
    }
  ],
  "edges": [
    {
      "id": "edge-1",
      "from": "table-456",
      "to": "table-123",
      "lineage_source": "manual"
    },
    {
      "id": "edge-2",
      "from": "field-789",
      "to": "field-999",
      "lineage_source": "manual"
    }
  ]
}
```

**关键点**：
- ✅ `nodes` 数组同时包含 `type: "table"` 和 `type: "field"` 的节点
- ✅ `edges` 数组同时包含表级和字段级的血缘关系
- ✅ 一次查询返回完整的血缘图（表 + 字段）

---

### UI 展示

**预期行为**：
- 用户在血缘图页面选择一个表
- 选择方向（upstream/downstream/both）和深度（1-5 hops）
- **一个统一的图**同时显示：
  - 表节点（大节点，带图标）
  - 字段节点（小节点，嵌套在表节点下或独立显示）
  - 表级血缘（粗线）
  - 字段级血缘（细线）

**不应该有**：
- ❌ "Table Level / Field Level" 切换器
- ❌ 两个独立的图分别显示表血缘和字段血缘

---

## 问题 1: 给 Codex（后端）

### 需要确认

**Q1**: 当前 `GET /lineage/table/{table_id}/upstream` 的实现是否同时返回了表节点和字段节点？

**Q2**: Neo4j 查询是否同时遍历了 `[:LINEAGE]` 关系（表级）和 `[:FIELD_LINEAGE]` 关系（字段级）？

**Q3**: 如果当前只返回表节点，是否需要修改实现？

### 预期实现（如果需要修正）

```python
# app/services/lineage_service.py

async def get_upstream_lineage(self, table_id: str, depth: int = 3) -> Dict:
    """
    获取表的上游血缘关系（同时包含表级和字段级）
    """
    async with self.neo4j.session() as session:
        result = await session.run(
            """
            // 查询表级血缘
            MATCH table_path = (upstream_table:Table)-[:LINEAGE*1..{depth}]->(target:Table {id: $table_id})

            // 查询字段级血缘
            OPTIONAL MATCH field_path = (upstream_field:Field)-[:FIELD_LINEAGE*1..{depth}]->(target_field:Field)
            WHERE target_field.table_id = $table_id

            // 返回所有节点和边
            RETURN
                collect(DISTINCT upstream_table) AS table_nodes,
                collect(DISTINCT upstream_field) AS field_nodes,
                relationships(table_path) AS table_edges,
                relationships(field_path) AS field_edges
            """,
            table_id=table_id,
            depth=depth
        )

        # 组装成 LineageGraphResponse 格式
        return self._build_graph_response(result)
```

**关键**：一次查询同时获取表和字段的血缘关系。

---

## 问题 2: 给 Gemini（前端）

### 需要确认

**Q1**: 当前是否实现了 "Table Level / Field Level" 切换器？

**Q2**: 如果有切换器，是否意味着表血缘和字段血缘是分开展示的？

**Q3**: 是否实现了删除血缘关系的 UI（右键菜单或删除按钮）？

### 预期实现（如果需要修正）

**移除切换器，统一展示**：

```typescript
// src/pages/Lineage/LineageGraph.tsx

// ❌ 不应该有这个
const [lineageLevel, setLineageLevel] = useState<'table' | 'field'>('table');

// ✅ 应该是统一的图
const { nodes, edges } = useLineageGraph(selectedTableId, direction, depth);

// nodes 包含 table 和 field 两种类型
// edges 包含表级和字段级血缘
```

**添加删除功能**：

```typescript
// 右键菜单或删除按钮
const handleDeleteLineage = async (edgeId: string) => {
  if (confirm('确定要删除这条血缘关系吗？')) {
    await lineageApi.deleteLineage(edgeId);
    // 刷新图
    refetchLineage();
  }
};
```

---

## 影响评估

### 如果确认有偏差

**严重程度**: 🔴 High
- 影响核心功能（血缘可视化）
- 用户体验不符合预期
- 需要修改后端查询和前端展示逻辑

**修复工作量**：
- **Codex**: 1-2 天（修改 Neo4j 查询，更新 API 响应）
- **Gemini**: 1-2 天（移除切换器，统一图展示，添加删除功能）

### 如果当前实现正确

**需要确认**：
- 当前实现已经是统一的图
- 只是文档描述不清晰

---

## 验证方法

### 测试步骤

1. **创建测试数据**：
   - 创建表 A 和表 B
   - 创建表级血缘：A → B
   - 创建字段级血缘：A.field1 → B.field2

2. **测试 API**：
   ```bash
   curl http://localhost:8000/api/v1/lineage/table/{B的ID}/upstream
   ```

3. **检查响应**：
   - `nodes` 数组是否包含 4 个节点（表 A、表 B、field1、field2）？
   - `edges` 数组是否包含 2 条边（表级 + 字段级）？

4. **测试前端**：
   - 打开血缘图页面
   - 选择表 B
   - 查看 upstream
   - 是否同时显示表节点和字段节点？
   - 是否有删除按钮？

---

## 请求回复

### Codex 请回答：

1. 当前 `get_upstream_lineage()` 是否同时返回表和字段节点？
2. 如果不是，是否需要修改实现？
3. 预计修复时间？

### Gemini 请回答：

1. 当前是否有 "Table Level / Field Level" 切换器？
2. 如果有，是否需要移除并改为统一展示？
3. 删除血缘功能是否已实现？
4. 预计修复时间？

---

**Document Version**: v1.0
**Status**: Awaiting Response
**Next Action**: Codex 和 Gemini 确认当前实现
