# Phase 2 血缘关系修复方案

**Issue ID**: P2-LINEAGE-001
**Priority**: High
**Status**: Fix Plan Approved
**Created**: 2025-12-23
**Estimated Time**: 2-3 天

---

## 问题确认

### Codex（后端）确认
✅ **当前实现有偏差**：
- API 只返回表级节点和边
- Neo4j 查询只遍历 `FEEDS_INTO` 关系
- 没有包含字段节点和 `FIELD_LINEAGE` 关系

### Gemini（前端）确认
✅ **当前实现有偏差**：
1. 实现了 "Table/Field" 切换器
2. 表血缘和字段血缘分开展示
3. 删除血缘的 UI 触发器缺失

---

## 修复方案

### Phase 1: 后端修复（Codex）- 1-2 天

#### 任务 1.1: 修改 Neo4j 查询
**文件**: `app/services/lineage_service.py`

**修改点**：
- 扩展 `get_upstream_lineage()` 同时查询表和字段
- 扩展 `get_downstream_lineage()` 同时查询表和字段
- 返回混合图（表节点 + 字段节点）

#### 任务 1.2: 更新响应组装
**修改点**：
- 将表节点和字段节点合并到 `nodes` 数组
- 将表级边和字段级边合并到 `edges` 数组
- 确保节点 `type` 字段正确（"table" 或 "field"）

#### 任务 1.3: 测试验证
- 单元测试：验证返回的节点包含两种类型
- 集成测试：验证 Neo4j 查询正确
- API 测试：验证响应格式符合 OpenAPI 规范

---

### Phase 2: 前端修复（Gemini）- 1 天

**依赖**: 后端修复完成

#### 任务 2.1: 移除切换器
**文件**: `src/pages/Lineage/LineageGraph.tsx`

**修改点**：
- 移除 "Table/Field" 切换器组件
- 移除 `granularity` 参数
- 统一调用 `fetchLineage()` 获取混合图

#### 任务 2.2: 统一图渲染
**修改点**：
- 更新 ReactFlow 配置支持混合节点
- 调整节点样式（表节点大，字段节点小）
- 调整边样式（表级粗线，字段级细线）

#### 任务 2.3: 添加删除功能
**修改点**：
- 实现 `onEdgeClick` 处理器
- 添加删除确认对话框（Ant Design Modal）
- 调用 `deleteLineage()` API
- 删除后刷新图

---

## 验收标准

### 后端验收
- [ ] API 返回包含表和字段两种节点
- [ ] API 返回包含表级和字段级两种边
- [ ] 单元测试通过
- [ ] 集成测试通过

### 前端验收
- [ ] 移除了切换器
- [ ] 统一图同时显示表和字段
- [ ] 可以删除血缘关系
- [ ] 删除后图正确刷新

---

## 时间表

| 阶段 | 负责人 | 时间 | 状态 |
|------|--------|------|------|
| 后端修复 | Codex | 1-2 天 | Pending |
| 前端修复 | Gemini | 1 天 | Pending |
| 联调测试 | 用户 | 0.5 天 | Pending |
| **总计** | | **2.5-3.5 天** | |

---

**Document Version**: v1.0
**Status**: Approved - Ready to Start
