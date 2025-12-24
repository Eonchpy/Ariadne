# Phase 2 验收检查清单 (Acceptance Checklist)

**阶段**: Phase 2 - Data Source Connection + Manual Lineage
**验收人**: 用户 (手动操作验证)
**验收时间**: Week 8 结束后
**前置条件**: Codex 和 Gemini 均完成 Phase 2 开发任务

---

## 验收流程

### 准备工作
1. ✅ 确认后端服务启动成功 (`uvicorn` 运行在 8000 端口)
2. ✅ 确认前端服务启动成功 (`npm run dev` 运行在 5173 端口)
3. ✅ 确认数据库服务正常 (PostgreSQL, Neo4j, Redis)
4. ✅ 确认测试环境可访问 (Oracle: 192.168.144.143)

---

## 第一部分: 数据源管理 (Data Sources)

### 1.1 创建 Oracle 数据源
**操作步骤**:
1. 打开前端页面 `http://localhost:5173`
2. 导航到 "Data Sources" 页面
3. 点击 "Add Data Source" 按钮
4. 填写表单:
   - Name: `Oracle Test`
   - Type: `Oracle`
   - Host: `192.168.144.143`
   - Port: `1521`
   - Service Name: `pdb1`
   - Username: `f10app`
   - Password: `oracle`
5. 点击 "Test Connection" 按钮

**预期结果**:
- ✅ 表单验证通过 (所有必填字段已填写)
- ✅ "Test Connection" 显示加载状态 (spinner)
- ✅ 连接测试成功,显示绿色成功提示 "✅ Connection successful"
- ✅ "Save" 按钮变为可用状态
- ✅ 点击 "Save" 后跳转到数据源列表页面
- ✅ 列表中显示新创建的 `Oracle Test` 数据源,状态为 🟢 Connected

**验证点**:
- [x] 前端表单验证正常 (必填字段、端口范围 1-65535)
- [x] 连接测试 API 调用成功 (`POST /api/v1/sources/{id}/test`)
- [x] 后端成功连接到 Oracle 数据库
- [x] 数据源保存到 PostgreSQL 数据库
- [x] 密码在数据库中已加密 (Fernet 格式,以 `gAAAAA` 开头)
- [x] API 响应中密码已脱敏 (显示为 `******`)

---

### 1.2 查看数据源详情
**操作步骤**:
1. 在数据源列表页面,点击 `Oracle Test` 数据源的 "View" 按钮
2. 查看数据源详情页面

**预期结果**:
- ✅ 显示数据源基本信息 (Name, Type, Status)
- ✅ 显示连接配置 (Host, Port, Service Name, Username)
- ✅ 密码字段显示为 `******` (已脱敏)
- ✅ 显示最后测试时间 (Last Tested)

**验证点**:
- [ ] 数据源详情正确显示
- [ ] 敏感信息已脱敏
- [ ] 页面布局美观,符合 Ant Design 规范

---

### 1.3 编辑数据源
**操作步骤**:
1. 点击 "Edit" 按钮
2. 修改 Name 为 `Oracle Production`
3. 修改 Description 为 `公司生产环境 Oracle 数据库`
4. 点击 "Test Connection" (验证修改后仍可连接)
5. 点击 "Save"

**预期结果**:
- ✅ 表单预填充原有数据 (密码显示为 `******`)
- ✅ 修改后连接测试仍然成功
- ✅ 保存成功,跳转回详情页面
- ✅ 详情页面显示更新后的信息

**验证点**:
- [ ] 编辑表单正确预填充数据
- [ ] 修改后保存成功
- [ ] 数据库中数据已更新

---

### 1.4 删除数据源
**操作步骤**:
1. 创建一个临时数据源 `Oracle Temp`
2. 在列表页面点击 "Delete" 按钮
3. 确认删除操作

**预期结果**:
- ✅ 显示确认对话框 "Are you sure you want to delete this data source?"
- ✅ 点击 "Confirm" 后数据源从列表中消失
- ✅ 显示成功提示 "Data source deleted successfully"

**验证点**:
- [x] 删除确认对话框正常显示
- [x] 删除操作成功
- [ ] 数据库中数据已删除 (级联删除相关表和字段)

---

### 1.5 连接测试失败场景
**操作步骤**:
1. 创建新数据源,故意填写错误密码 `wrong_password`
2. 点击 "Test Connection"

**预期结果**:
- ✅ 连接测试失败,显示红色错误提示 "❌ Connection failed: Invalid credentials"
- ✅ "Save" 按钮保持禁用状态
- ✅ 错误信息清晰易懂

**验证点**:
- [x] 错误处理正常
- [x] 错误信息友好
- [ ] 不允许保存未测试成功的数据源

---

## 第二部分: 智能元数据辅助 (Smart Metadata Assist)

### 2.1 使用智能元数据辅助创建表
**操作步骤**:
1. 导航到 "Tables" 页面
2. 点击 "Add Table" 按钮
3. 填写表单:
   - Table Name: `CUSTOMERS`
   - Data Source: 选择 `Oracle Production`
   - Schema Name: `HR` (或根据实际情况填写)
   - Type: `Table`
4. 点击 "Fetch Columns" 按钮

**预期结果**:
- ✅ "Fetch Columns" 显示加载状态
- ✅ 成功获取列信息,自动填充 Fields 区域
- ✅ 显示列信息:
   - Field Name (例如: `CUSTOMER_ID`, `NAME`, `EMAIL`)
   - Data Type (例如: `NUMBER`, `VARCHAR2`, `DATE`)
   - Nullable (例如: `NO`, `YES`)
   - Primary Key (例如: `CUSTOMER_ID` 标记为 PK)
- ✅ 用户可以手动编辑、添加或删除字段
- ✅ 点击 "Save" 后表创建成功

**验证点**:
- [x] 智能元数据辅助 API 调用成功 (`POST /api/v1/sources/{id}/introspect/table`)
- [x] 后端成功连接到 Oracle 并查询 `ALL_TAB_COLUMNS`
- [x] 列信息正确解析并返回
- [x] 前端正确渲染列信息
- [x] 用户可以手动编辑获取的列信息
- [x] 表和字段保存到 PostgreSQL 数据库

---

### 2.2 手动创建表 (不绑定数据源)
**操作步骤**:
1. 点击 "Add Table" 按钮
2. 填写表单:
   - Table Name: `Manual Table 1`
   - Data Source: 留空 (不选择)
   - Type: `Table`
   - Description: `手动创建的测试表`
3. 手动添加字段:
   - Field 1: `id`, `INTEGER`, Not Nullable, Primary Key
   - Field 2: `name`, `VARCHAR`, Nullable
   - Field 3: `created_at`, `TIMESTAMP`, Not Nullable
4. 点击 "Save"

**预期结果**:
- ✅ 表单允许不选择数据源 (source_id 为 null)
- ✅ "Fetch Columns" 按钮禁用 (因为未选择数据源)
- ✅ 用户可以手动添加字段
- ✅ 保存成功,跳转到表列表页面
- ✅ 列表中显示 `Manual Table 1`,Source 列显示 "Manual"

**验证点**:
- [ ] 支持创建不绑定数据源的表 (source_id nullable)
- [ ] 手动添加字段功能正常
- [ ] 表和字段保存成功

---

### 2.3 智能元数据辅助失败场景
**操作步骤**:
1. 创建新表,选择数据源 `Oracle Production`
2. 填写不存在的表名 `NONEXISTENT_TABLE`
3. 点击 "Fetch Columns"

**预期结果**:
- ✅ 显示错误提示 "❌ Table not found: NONEXISTENT_TABLE"
- ✅ Fields 区域保持空白
- ✅ 用户可以选择手动添加字段或修改表名重试

**验证点**:
- [ ] 错误处理正常
- [ ] 错误信息清晰
- [ ] 不影响后续操作

---

## 第三部分: 血缘关系管理 (Lineage Management)

### 3.1 创建表级血缘关系
**操作步骤**:
1. 导航到 "Lineage" 页面
2. 点击 "Create Lineage" 按钮
3. 填写表单:
   - Lineage Type: `Table-level`
   - Source Table: 选择 `CUSTOMERS`
   - Target Table: 选择 `Manual Table 1`
   - Lineage Source: `Manual`
   - Description: `测试表级血缘关系`
4. 点击 "Save"

**预期结果**:
- ✅ 血缘关系创建成功
- ✅ 血缘图自动刷新,显示新关系
- ✅ 图中显示:
   - `CUSTOMERS` 节点 (带 Oracle 图标)
   - `Manual Table 1` 节点 (带 Manual 标签)
   - 蓝色实线连接两个节点 (Manual 血缘)

**验证点**:
- [ ] 血缘关系保存到 Neo4j 数据库
- [ ] 血缘图正确渲染
- [ ] 节点和边样式符合设计规范

---

### 3.2 创建字段级血缘关系
**操作步骤**:
1. 点击 "Create Lineage" 按钮
2. 填写表单:
   - Lineage Type: `Field-level`
   - Source Table: `CUSTOMERS`
   - Source Field: `CUSTOMER_ID`
   - Target Table: `Manual Table 1`
   - Target Field: `id`
   - Lineage Source: `Manual`
3. 点击 "Save"

**预期结果**:
- ✅ 字段级血缘关系创建成功
- ✅ 血缘图显示细线连接两个字段节点

**验证点**:
- [ ] 字段级血缘关系保存成功
- [ ] 血缘图正确显示字段级关系

---

### 3.3 血缘图交互功能
**操作步骤**:
1. 在血缘图页面:
   - 使用鼠标滚轮缩放图形
   - 拖拽节点移动位置
   - 点击节点查看详情
   - 使用搜索框搜索表名
   - 调整深度控制 (1-5 hops)
   - 切换方向 (upstream/downstream/both)
2. 点击 "Export as PNG" 按钮

**预期结果**:
- ✅ 缩放功能正常
- ✅ 拖拽功能正常
- ✅ 节点点击显示详情面板
- ✅ 搜索功能正常,自动聚焦到匹配节点
- ✅ 深度控制正常,图形根据深度更新
- ✅ 方向切换正常
- ✅ 导出 PNG 成功,图片清晰

**验证点**:
- [ ] ReactFlow 交互功能正常
- [ ] 所有控制按钮功能正常
- [ ] 导出功能正常

---

### 3.4 删除血缘关系
**操作步骤**:
1. 在血缘图中右键点击边 (或点击边后点击删除按钮)
2. 确认删除操作

**预期结果**:
- ✅ 显示确认对话框
- ✅ 删除成功,边从图中消失
- ✅ Neo4j 中关系已删除

**验证点**:
- [ ] 删除功能正常
- [ ] 数据库中关系已删除

---

## 第四部分: 批量导入导出 (Bulk Operations)

### 4.1 批量导出
**操作步骤**:
1. 导航到 "Bulk Operations" 页面
2. 选择导出范围:
   - Export Scope: `All tables + lineage`
   - Format: `CSV`
3. 点击 "Export" 按钮

**预期结果**:
- ✅ 浏览器下载 CSV 文件 (例如: `ariadne_export_2025-12-23.csv`)
- ✅ 打开 CSV 文件,包含:
   - 所有表信息 (name, type, source, description)
   - 所有字段信息 (field_name, data_type, nullable, primary_key)
   - 所有血缘关系 (source_table, target_table, lineage_source)

**验证点**:
- [ ] 导出 API 调用成功 (`GET /api/v1/bulk/export?format=csv`)
- [ ] CSV 文件格式正确
- [ ] 数据完整无遗漏

---

### 4.2 批量导入
**操作步骤**:
1. 准备测试 CSV 文件 (包含 10 个表 + 50 个字段 + 5 个血缘关系)
2. 在 "Bulk Operations" 页面:
   - 选择 Format: `CSV`
   - 拖拽 CSV 文件到上传区域 (或点击选择文件)
3. 点击 "Preview" 按钮
4. 查看预览结果 (显示前 10 行)
5. 点击 "Import" 按钮

**预期结果**:
- ✅ 文件上传成功
- ✅ 预览显示前 10 行数据
- ✅ 点击 "Import" 后显示进度条
- ✅ 导入成功,显示成功提示 "✅ Imported 10 tables, 50 fields, 5 lineage relationships"
- ✅ 如果有错误,显示错误报告 (例如: "Row 5: Duplicate table name")

**验证点**:
- [ ] 文件上传功能正常
- [ ] 预览功能正常
- [ ] 导入 API 调用成功 (`POST /api/v1/bulk/import`)
- [ ] 数据正确保存到数据库
- [ ] 进度跟踪正常
- [ ] 错误报告清晰

---

### 4.3 批量导入错误处理
**操作步骤**:
1. 准备包含错误的 CSV 文件:
   - Row 3: 缺少必填字段 `table_name`
   - Row 7: 无效的数据类型 `INVALID_TYPE`
2. 上传并导入文件

**预期结果**:
- ✅ 导入部分成功,部分失败
- ✅ 显示错误报告:
   - "Row 3: Missing required field 'table_name'"
   - "Row 7: Invalid data type 'INVALID_TYPE'"
- ✅ 成功导入的数据已保存
- ✅ 失败的行未保存 (事务回滚)

**验证点**:
- [ ] 错误处理正常
- [ ] 错误报告详细
- [ ] 事务支持正常 (部分失败不影响成功的行)

---

## 第五部分: 审计日志 (Audit Logging)

### 5.1 查看连接测试日志
**操作步骤**:
1. 执行多次连接测试 (成功和失败各几次)
2. 使用 SQL 查询审计日志:
```sql
SELECT * FROM connection_test_logs
WHERE source_id = '<Oracle Production ID>'
ORDER BY created_at DESC
LIMIT 10;
```

**预期结果**:
- ✅ 日志表包含所有连接测试记录
- ✅ 每条记录包含:
   - `source_id`: 数据源 ID
   - `operation`: `connection_test`
   - `tested_by`: 用户名 (如果有认证)
   - `result`: `success` 或 `failure`
   - `error_message`: 失败时的错误信息
   - `created_at`: 测试时间

**验证点**:
- [ ] 审计日志表已创建
- [ ] 连接测试自动记录日志
- [ ] 日志信息完整

---

### 5.2 查看智能元数据辅助日志
**操作步骤**:
1. 执行多次 "Fetch Columns" 操作
2. 查询审计日志:
```sql
SELECT * FROM connection_test_logs
WHERE operation = 'introspection'
ORDER BY created_at DESC
LIMIT 10;
```

**预期结果**:
- ✅ 日志表包含所有智能元数据辅助记录
- ✅ 每条记录包含:
   - `source_id`: 数据源 ID
   - `operation`: `introspection`
   - `table_name`: 查询的表名
   - `tested_by`: 用户名
   - `result`: `success` 或 `failure`
   - `created_at`: 操作时间

**验证点**:
- [ ] 智能元数据辅助操作自动记录日志
- [ ] 日志信息完整

---

## 第六部分: Mock API 模式 (Frontend Only)

### 6.1 启用 Mock API 模式
**操作步骤**:
1. 停止后端服务
2. 设置环境变量:
```bash
VITE_USE_MOCKS=true npm run dev
```
3. 打开前端页面 `http://localhost:5173`
4. 执行以下操作:
   - 查看数据源列表
   - 创建新数据源
   - 测试连接
   - 查看表列表
   - 创建新表
   - 查看血缘图

**预期结果**:
- ✅ 所有页面正常显示
- ✅ 所有操作返回模拟数据
- ✅ 无需后端服务即可开发和测试前端功能
- ✅ 模拟数据符合真实 API 响应格式

**验证点**:
- [ ] Mock API 模式正常工作
- [ ] 模拟数据完整
- [ ] 前端功能不受影响

---

### 6.2 切换回真实 API
**操作步骤**:
1. 启动后端服务
2. 设置环境变量:
```bash
VITE_USE_MOCKS=false npm run dev
```
3. 刷新页面,验证连接到真实后端

**预期结果**:
- ✅ 前端连接到真实后端 API
- ✅ 数据来自真实数据库
- ✅ 所有功能正常

**验证点**:
- [ ] 环境变量切换正常
- [ ] 真实 API 连接正常

---

## 第七部分: 表单验证 (Zod Validation)

### 7.1 数据源表单验证
**操作步骤**:
1. 打开 "Add Data Source" 表单
2. 测试以下验证场景:
   - 留空 Name 字段,点击 "Save"
   - 输入无效端口号 `99999`,点击 "Test Connection"
   - 输入无效 MongoDB 连接字符串,点击 "Test Connection"

**预期结果**:
- ✅ Name 为空时显示错误 "Name is required"
- ✅ 端口号超出范围时显示错误 "Port must be between 1 and 65535"
- ✅ MongoDB 连接字符串格式错误时显示错误 "Invalid connection string format"
- ✅ 所有错误信息清晰易懂

**验证点**:
- [ ] Zod 验证正常工作
- [ ] 错误信息友好
- [ ] 表单验证覆盖所有必填字段

---

### 7.2 表表单验证
**操作步骤**:
1. 打开 "Add Table" 表单
2. 测试以下验证场景:
   - 留空 Table Name,点击 "Save"
   - 不添加任何字段,点击 "Save"

**预期结果**:
- ✅ Table Name 为空时显示错误 "Table name is required"
- ✅ 字段为空时显示错误 "At least one field is required"

**验证点**:
- [ ] 表表单验证正常
- [ ] 字段验证正常

---

## 第八部分: 错误边界 (ErrorBoundary)

### 8.1 触发 LineageGraph 错误
**操作步骤**:
1. 创建 100+ 个表和血缘关系 (使用批量导入)
2. 打开血缘图页面
3. 如果渲染失败,观察错误处理

**预期结果**:
- ✅ 如果 ReactFlow 渲染失败,显示友好错误页面:
   - "Failed to render lineage graph"
   - 错误信息 (例如: "Maximum call stack size exceeded")
   - "Retry" 按钮
- ✅ 点击 "Retry" 按钮重新加载图形
- ✅ 应用其他部分不受影响 (不会整个应用崩溃)

**验证点**:
- [ ] ErrorBoundary 正常捕获错误
- [ ] 错误恢复 UI 正常
- [ ] 应用不会崩溃

---

## 第九部分: 性能测试

### 9.1 大数据量测试
**操作步骤**:
1. 使用批量导入功能导入 1000 个表
2. 观察导入时间和性能
3. 在表列表页面测试分页和搜索功能
4. 在血缘图页面测试渲染性能

**预期结果**:
- ✅ 批量导入 1000 个表在 30 秒内完成
- ✅ 表列表页面加载时间 < 2 秒
- ✅ 分页和搜索功能流畅
- ✅ 血缘图渲染 100+ 节点无明显卡顿

**验证点**:
- [ ] 批量导入性能达标
- [ ] 列表页面性能达标
- [ ] 血缘图性能达标

---

## 第十部分: 安全性测试

### 10.1 密码加密验证
**操作步骤**:
1. 创建数据源,填写密码 `test_password_123`
2. 使用 SQL 查询数据库:
```sql
SELECT connection_config FROM sources WHERE name = 'Oracle Production';
```
3. 检查密码字段

**预期结果**:
- ✅ 数据库中密码已加密,格式为 Fernet 密文 (以 `gAAAAA` 开头)
- ✅ 密文长度远大于原始密码长度
- ✅ 无法直接读取明文密码

**验证点**:
- [ ] 密码加密正常
- [ ] 加密格式正确 (Fernet)

---

### 10.2 API 响应脱敏验证
**操作步骤**:
1. 使用浏览器开发者工具 (Network 标签)
2. 查看数据源详情 API 响应 (`GET /api/v1/sources/{id}`)
3. 检查 `connection_config.password` 字段

**预期结果**:
- ✅ API 响应中密码显示为 `******`
- ✅ 其他敏感字段 (如 `api_key`, `secret`) 也已脱敏

**验证点**:
- [ ] API 响应脱敏正常
- [ ] 所有敏感字段已脱敏

---

## 验收标准

### 必须通过 (Must Pass)
- [ ] 所有数据源 CRUD 操作正常
- [ ] 连接测试功能正常 (成功和失败场景)
- [ ] 智能元数据辅助功能正常
- [ ] 手动创建表功能正常
- [ ] 血缘关系创建和查询正常
- [ ] 血缘图渲染正常
- [ ] 批量导入导出功能正常
- [ ] 密码加密和脱敏正常
- [ ] 审计日志记录正常

### 应该通过 (Should Pass)
- [ ] Mock API 模式正常工作
- [ ] Zod 表单验证正常
- [ ] ErrorBoundary 错误处理正常
- [ ] 性能测试达标 (1000 表导入 < 30 秒)
- [ ] UI/UX 符合设计规范

### 可选通过 (Nice to Have)
- [ ] 血缘图导出 PNG 功能正常
- [ ] 所有交互动画流畅
- [ ] 移动端响应式布局正常

---

## 验收结果

### 通过项统计
- 必须通过: __ / 9
- 应该通过: __ / 5
- 可选通过: __ / 3

### 总体评分
- **优秀 (Excellent)**: 必须通过 9/9, 应该通过 ≥ 4/5
- **良好 (Good)**: 必须通过 9/9, 应该通过 ≥ 3/5
- **合格 (Pass)**: 必须通过 ≥ 8/9
- **不合格 (Fail)**: 必须通过 < 8/9

### 发现的问题
| 问题编号 | 问题描述 | 严重程度 | 负责人 | 状态 |
|---------|---------|---------|--------|------|
| P2-001  | (示例) 连接测试超时未处理 | High | Codex | Open |
| P2-002  | (示例) 血缘图缩放卡顿 | Medium | Gemini | Open |

---

## 验收签字

- **验收人**: _______________
- **验收日期**: _______________
- **验收结果**: ☐ 通过 ☐ 有条件通过 ☐ 不通过
- **备注**: _______________

---

**文档版本**: v1.0
**创建日期**: 2025-12-23
**维护者**: QC Agent (Claude)
**状态**: Ready for Use
