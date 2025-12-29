# SQL Lineage Sub-Agent 设计文档

## 1. 背景与问题

### 业务背景
- 部门批处理任务主要使用 **Oracle 存储过程**（PL/SQL）
- 存储过程包含复杂逻辑：游标、动态SQL、临时表、异常处理
- 传统解析器（sqlglot）对 PL/SQL 支持有限

### 技术挑战
| 挑战 | 说明 | 示例 |
|------|------|------|
| **PL/SQL 语法复杂** | 包含过程式编程元素 | `FOR...LOOP`, `CURSOR`, `EXCEPTION` |
| **动态 SQL** | 运行时拼接的 SQL 字符串 | `EXECUTE IMMEDIATE 'SELECT * FROM ' \|\| v_table_name` |
| **临时表** | 会话级临时表，名称可能重复 | `CREATE GLOBAL TEMPORARY TABLE tmp_...` |
| **包依赖** | 跨包调用，需要解析包头 | `pkg_utils.get_user_data(p_id)` |
| **隐式转换** | Oracle 特有的类型转换 | `TO_DATE`, `TO_CHAR` |

### 为什么不用传统解析器
- **sqlglot**: 主要支持 ANSI SQL，PL/SQL 支持不完整
- **sqlparse**: 只做分词，不构建语法树
- **Oracle SQL Developer**: 闭源，无法集成

### 为什么 Sub-Agent 是最佳方案
1. ✅ **专业化分工**：主助手负责交互，SQL 专家负责解析
2. ✅ **上下文隔离**：SQL 专家有独立的工具集和提示词
3. ✅ **可扩展性**：未来可添加其他专家（Python 专家、Java 专家）
4. ✅ **错误隔离**：SQL 解析失败不影响主助手

---

## 2. 架构设计

### 2.1 Multi-Agent 架构

```
┌─────────────────────────────────────────────────────────────┐
│                    用户 (User)                               │
└─────────────────────────────────────────────────────────────┘
                            ↕
┌─────────────────────────────────────────────────────────────┐
│           主 AI 助手 (Main Assistant)                        │
│  - 角色: 元数据助手                                          │
│  - 职责: 用户交互、任务分发、结果整合                        │
│  - Tools: search_tables, get_lineage, calculate_blast_radius│
└─────────────────────────────────────────────────────────────┘
                ↓ 委托 SQL 解析任务
┌─────────────────────────────────────────────────────────────┐
│           SQL 专家 Sub-Agent (SQL Expert)                    │
│  - 角色: Oracle PL/SQL 专家                                  │
│  - 职责: SQL 解析、血缘提取、置信度评估                      │
│  - Tools: parse_sql, extract_lineage, validate_tables       │
│  - Strategies: AST → Regex → LLM (fallback chain)           │
└─────────────────────────────────────────────────────────────┘
                ↓ 调用工具
┌─────────────────────────────────────────────────────────────┐
│              SQL 解析工具链 (Tool Chain)                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ AST Parser   │  │ Regex Parser │  │ LLM Parser   │      │
│  │ (sqlglot)    │  │ (patterns)   │  │ (GPT-4)      │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└─────────────────────────────────────────────────────────────┘
                ↓
┌─────────────────────────────────────────────────────────────┐
│              血缘验证与持久化 (Validation & Storage)         │
│  - Catalog 映射 (fuzzy match table names)                   │
│  - 置信度评分 (confidence scoring)                           │
│  - 审阅队列 (review queue for low confidence)                │
│  - Neo4j 存储 (lineageSource: "inferred_sql")               │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 工作流设计

#### Workflow 1: 用户上传存储过程

```
User: "帮我分析这个存储过程的血缘关系"
      [上传 procedure.sql]
      ↓
Main Assistant:
  1. 识别任务类型: "SQL 解析"
  2. 调用 SQL Expert Sub-Agent
  3. 传递上下文: {sql_code, catalog_tables, current_schema}
      ↓
SQL Expert Sub-Agent:
  1. 选择解析策略:
     - 尝试 AST Parser (sqlglot)
     - 失败 → Regex Parser (自定义规则)
     - 失败 → LLM Parser (GPT-4)
  2. 提取血缘关系:
     - Source tables: [TABLE_A, TABLE_B]
     - Target tables: [TABLE_C]
     - Transformations: [JOIN, AGGREGATE]
  3. 映射到 Catalog:
     - TABLE_A → uuid_123 (confidence: 0.95)
     - TABLE_B → uuid_456 (confidence: 0.90)
  4. 返回结构化结果
      ↓
Main Assistant:
  1. 接收 Sub-Agent 结果
  2. 标记低置信度项需要审阅
  3. 生成用户友好的报告:
     "我分析了这个存储过程，发现以下血缘关系：
      - 源表: TABLE_A, TABLE_B
      - 目标表: TABLE_C
      - 转换逻辑: 关联后聚合
      - 置信度: 92% (建议审阅)"
  4. 提供操作按钮: [保存血缘] [审阅] [修改]
```

#### Workflow 2: 批量解析任务

```
User: "批量解析 prod_etl 下所有存储过程"
      ↓
Main Assistant:
  1. 查询存储过程列表 (从 Oracle 系统表)
  2. 创建批量任务
  3. 循环调用 SQL Expert Sub-Agent
      ↓
SQL Expert Sub-Agent:
  - 并发处理多个存储过程
  - 汇总结果
  - 生成批量报告
      ↓
Main Assistant:
  "批量解析完成:
   - 总计: 45 个存储过程
   - 成功: 38 个 (84%)
   - 需审阅: 7 个 (16%)
   - 失败: 0 个"
```

---

## 3. SQL Expert Sub-Agent 详细设计

### 3.1 Agent 定义

```python
SQL_EXPERT_SYSTEM_PROMPT = """You are an Oracle PL/SQL expert specializing in data lineage extraction.

## Your Role
- Analyze Oracle stored procedures, PL/SQL blocks, and SQL scripts
- Extract table-level and field-level lineage relationships
- Handle complex scenarios: dynamic SQL, temporary tables, cursors, packages

## Your Tools
1. **parse_sql_ast**: Use sqlglot to parse standard SQL (try this first)
2. **parse_sql_regex**: Use regex patterns for PL/SQL-specific constructs
3. **parse_sql_llm**: Use LLM reasoning for complex/non-standard cases
4. **validate_tables**: Verify extracted table names against catalog
5. **map_to_catalog**: Fuzzy match table names to UUIDs

## Parsing Strategy (Fallback Chain)
1. Try AST parser (fast, deterministic)
   - If successful and confidence > 0.9: return result
2. Try Regex parser (handles PL/SQL keywords)
   - If successful and confidence > 0.7: return result
3. Use LLM parser (slow but comprehensive)
   - Always succeeds, but mark confidence appropriately

## Output Format
Return JSON with:
{
  "source_tables": [
    {"name": "TABLE_A", "schema": "PROD", "uuid": "...", "confidence": 0.95}
  ],
  "target_tables": [...],
  "field_mappings": [
    {"source": "TABLE_A.USER_ID", "target": "TABLE_C.USER_KEY", "transformation": "direct"}
  ],
  "transformations": ["JOIN", "AGGREGATE", "FILTER"],
  "dynamic_sql_detected": true,
  "temp_tables": ["TMP_STAGING"],
  "overall_confidence": 0.85,
  "parsing_method": "regex",
  "needs_review": false
}

## Critical Rules
1. NEVER fabricate table names - only extract names explicitly in SQL
2. ALWAYS validate against catalog before returning UUIDs
3. ALWAYS calculate realistic confidence scores
4. ALWAYS mark dynamic SQL sections for review
5. If uncertain, set needs_review: true
"""
```

### 3.2 工具定义

#### Tool 1: parse_sql_ast
```python
@mcp.tool(description="Parse SQL using AST (sqlglot). Fast and deterministic for standard SQL.")
async def parse_sql_ast(sql_code: str, dialect: str = "oracle"):
    """
    Uses sqlglot to parse SQL into AST and extract table references.
    Returns: {tables: [...], confidence: 0.95, method: "ast"}
    """
    try:
        parsed = sqlglot.parse_one(sql_code, dialect=dialect)
        tables = extract_tables_from_ast(parsed)
        return {
            "tables": tables,
            "confidence": 0.95,
            "method": "ast",
            "success": True
        }
    except Exception as e:
        return {
            "tables": [],
            "confidence": 0.0,
            "method": "ast",
            "success": False,
            "error": str(e)
        }
```

#### Tool 2: parse_sql_regex
```python
@mcp.tool(description="Parse PL/SQL using regex patterns. Handles Oracle-specific syntax.")
async def parse_sql_regex(sql_code: str):
    """
    Uses regex to extract:
    - INSERT INTO ... SELECT FROM ...
    - CREATE TABLE ... AS SELECT ...
    - MERGE INTO ... USING ...
    - Dynamic SQL patterns
    """
    patterns = {
        "insert_select": r"INSERT\s+INTO\s+(\w+).*?SELECT.*?FROM\s+([\w,\s]+)",
        "create_as_select": r"CREATE\s+TABLE\s+(\w+).*?AS\s+SELECT.*?FROM\s+([\w,\s]+)",
        "merge": r"MERGE\s+INTO\s+(\w+).*?USING\s+(\w+)",
        "dynamic_sql": r"EXECUTE\s+IMMEDIATE\s+['\"]([^'\"]+)['\"]",
    }

    results = {
        "source_tables": [],
        "target_tables": [],
        "dynamic_sql": [],
        "confidence": 0.8,
        "method": "regex"
    }

    for pattern_name, pattern in patterns.items():
        matches = re.findall(pattern, sql_code, re.IGNORECASE | re.DOTALL)
        # Process matches...

    return results
```

#### Tool 3: parse_sql_llm
```python
@mcp.tool(description="Parse SQL using LLM reasoning. Handles complex/non-standard cases.")
async def parse_sql_llm(sql_code: str, catalog_tables: list[str]):
    """
    Uses GPT-4 to understand complex SQL logic.
    Provides catalog context to prevent hallucination.
    """
    prompt = f"""Analyze this Oracle PL/SQL code and extract data lineage.

Available tables in catalog:
{", ".join(catalog_tables[:50])}  # Limit context size

SQL Code:
```sql
{sql_code}
```

Extract:
1. Source tables (tables being READ from)
2. Target tables (tables being WRITTEN to)
3. Field-level mappings if clear
4. Transformation types (JOIN, AGGREGATE, etc.)

IMPORTANT: Only use table names from the catalog or explicitly in the SQL.
Return JSON format.
"""

    result = await llm.chat([{"role": "user", "content": prompt}])
    parsed = json.loads(result)

    # Validate against catalog
    parsed["confidence"] *= 0.85  # LLM results discounted
    parsed["method"] = "llm"

    return parsed
```

#### Tool 4: validate_tables
```python
@mcp.tool(description="Validate extracted table names against catalog.")
async def validate_tables(table_names: list[str]):
    """
    Fuzzy match table names to catalog.
    Returns: {matches: [{input: "user_info", matched: "USER_INFO", uuid: "...", score: 0.95}]}
    """
    from app.repositories.table_repo import TableRepository

    repo = TableRepository(session)
    results = []

    for name in table_names:
        # Try exact match first
        exact = await repo.find_by_name(name)
        if exact:
            results.append({
                "input": name,
                "matched": exact.name,
                "uuid": str(exact.id),
                "score": 1.0
            })
            continue

        # Fuzzy match
        candidates = await repo.search(name, limit=5)
        best_match = fuzzy_match(name, candidates)
        results.append({
            "input": name,
            "matched": best_match.name if best_match else None,
            "uuid": str(best_match.id) if best_match else None,
            "score": best_match.score if best_match else 0.0
        })

    return {"matches": results}
```

### 3.3 Sub-Agent 调用机制

#### 方式1: 通过 MCP Tool (推荐)
```python
# 在主助手的 MCP Server 中新增工具
@mcp.tool(description="Delegate SQL parsing to SQL Expert Sub-Agent. Use when user uploads SQL/PL-SQL code for lineage extraction.")
async def analyze_sql_lineage(sql_code: str, context: dict = None):
    """
    Spawns SQL Expert Sub-Agent to analyze SQL lineage.

    Args:
        sql_code: The SQL/PL-SQL code to analyze
        context: Optional context (catalog_tables, current_schema, etc.)

    Returns:
        Structured lineage result with confidence scores
    """
    # 创建 Sub-Agent
    sql_expert = create_sql_expert_agent(
        system_prompt=SQL_EXPERT_SYSTEM_PROMPT,
        tools=[parse_sql_ast, parse_sql_regex, parse_sql_llm, validate_tables]
    )

    # 构造任务
    task = f"""Analyze this SQL code and extract data lineage:

SQL Code:
```sql
{sql_code}
```

Context:
- Catalog tables: {context.get('catalog_tables', [])[:50]}
- Current schema: {context.get('current_schema', 'UNKNOWN')}

Use the fallback chain strategy: AST → Regex → LLM
Return structured JSON result.
"""

    # 执行 Sub-Agent
    result = await sql_expert.run(task)

    return result
```

#### 方式2: 直接在 AIService 中实现
```python
class AIService:
    async def analyze_sql_with_subagent(self, sql_code: str, user_id: uuid.UUID):
        # 获取 catalog 上下文
        tables = await self.table_repo.list_all()
        catalog_tables = [t.name for t in tables]

        # 调用 SQL Expert Sub-Agent
        expert_prompt = SQL_EXPERT_SYSTEM_PROMPT
        expert_tools = [
            # MCP tools for SQL parsing
        ]

        expert_messages = [
            {"role": "system", "content": expert_prompt},
            {"role": "user", "content": f"Analyze this SQL:\n\n{sql_code}"}
        ]

        # 使用独立的 LLM 实例
        expert_llm = LLMClient(temperature=0.1)  # Lower temp for deterministic output
        result = await expert_llm.achat(expert_messages, tools=expert_tools)

        # 解析 Sub-Agent 结果
        lineage_data = parse_subagent_result(result)

        # 主助手整合结果
        return {
            "lineage": lineage_data,
            "confidence": lineage_data["overall_confidence"],
            "needs_review": lineage_data["needs_review"],
            "summary": self._generate_summary(lineage_data)
        }
```

---

## 4. 实现路径

### Phase 5.1: SQL Expert Sub-Agent 基础 (Week 16)
- ✅ 设计 Sub-Agent 架构
- ✅ 实现 AST Parser (sqlglot)
- ✅ 实现 Regex Parser (PL/SQL patterns)
- ✅ 实现 Catalog 验证

### Phase 5.2: LLM Fallback + 批量处理 (Week 17)
- ✅ 实现 LLM Parser
- ✅ 实现 Fallback Chain 逻辑
- ✅ 批量解析接口
- ✅ 审阅队列机制

### Phase 5.3: 存储过程专项优化 (Week 18)
- ✅ 包依赖解析 (PKG.PROCEDURE)
- ✅ 游标处理
- ✅ 动态 SQL 检测
- ✅ 临时表追踪

### Phase 5.4: 集成与测试 (Week 19)
- ✅ 集成到主 AI 助手
- ✅ 端到端测试
- ✅ 性能优化
- ✅ 文档完善

---

## 5. 示例对话

### 示例1: 简单存储过程
```
User: "分析这个存储过程的血缘"
[上传 proc_daily_summary.sql]

Main Assistant:
"我来帮您分析这个存储过程的血缘关系。"
[调用 SQL Expert Sub-Agent]

SQL Expert Sub-Agent:
[使用 AST Parser 成功解析]
- Source: ORDERS, CUSTOMERS
- Target: DAILY_SUMMARY
- Confidence: 0.95

Main Assistant:
"分析完成！这个存储过程的血缘关系：

📥 源表 (2):
  - ORDERS (订单表)
  - CUSTOMERS (客户表)

📤 目标表 (1):
  - DAILY_SUMMARY (日汇总表)

🔄 转换逻辑:
  - 关联: ORDERS.CUSTOMER_ID = CUSTOMERS.ID
  - 聚合: SUM(ORDERS.AMOUNT) GROUP BY DATE

✅ 置信度: 95% (无需审阅)

[保存血缘] [查看图谱]"
```

### 示例2: 复杂动态 SQL
```
User: "这个存储过程用了动态SQL，能解析吗？"
[上传 proc_dynamic_etl.sql]

Main Assistant:
[调用 SQL Expert Sub-Agent]

SQL Expert Sub-Agent:
[AST Parser 失败 → Regex Parser 部分成功 → LLM Parser 补充]
- Source: USER_DATA, TRANSACTION_LOG, ${v_month_table}
- Target: ETL_RESULT
- Confidence: 0.75 (动态表名需确认)

Main Assistant:
"分析完成！这个存储过程较复杂：

📥 源表 (3):
  - USER_DATA (确定)
  - TRANSACTION_LOG (确定)
  - ${v_month_table} ⚠️ 动态表名，可能是:
    - TRANS_202401
    - TRANS_202402
    (需要手动确认)

📤 目标表 (1):
  - ETL_RESULT

⚠️ 置信度: 75% (建议审阅)
⚠️ 检测到动态 SQL，部分表名需人工确认

[保存血缘] [标记待审阅] [修改表名]"
```

---

## 6. 优势总结

| 特性 | 传统方案 | Sub-Agent 方案 |
|------|----------|----------------|
| **PL/SQL 支持** | 有限 | 优秀 (多策略) |
| **复杂 SQL** | 失败 | 可处理 (LLM fallback) |
| **置信度评估** | 无 | 有 (0-1 分数) |
| **审阅机制** | 无 | 有 (低置信度自动标记) |
| **可扩展性** | 差 | 好 (新增专家容易) |
| **成本** | 低 | 中 (AST 优先,LLM fallback) |
| **准确性** | 中 | 高 (验证+审阅) |

---

## 7. 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|----------|
| LLM 幻觉 | 编造表名 | Catalog 验证 + 降低置信度 |
| 解析失败 | 无法提取血缘 | Fallback chain + 人工审阅 |
| 性能问题 | 批量解析慢 | AST 优先 + 异步处理 |
| 成本过高 | LLM API 费用 | 优先用免费方法 + 缓存 |

---

**文档版本**: v1.0
**创建日期**: 2025-12-28
**作者**: QC Agent (Claude)
**状态**: 设计阶段
