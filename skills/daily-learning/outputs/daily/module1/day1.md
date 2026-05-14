# 📚 Daily Learning | Day 1
**Module 1: AI Applications (AI应用入门)**
Day 1/7 in module | Files 1-76 of 532

---

## 📄 1. knowledge_base_usage_guide.md
**File**: `aianswer/2025-12-26/knowledge_base_usage_guide.md` | **Type**: 文档
**Preview**: 该文档已移动到 local_knowledge_model/knowledge_base_usage_guide.md 请访问新位置查看完整内容。...

```
该文档已移动到 local_knowledge_model/knowledge_base_usage_guide.md

请访问新位置查看完整内容。

```

## 📄 2. dwd_hr_sys_user_display_df_validation_report.md
**File**: `aianswer/2025-12-26/dwd_hr_sys_user_display_df_validation_report.md` | **Type**: 文档
**Preview**: 该报告已移动到 aianswer/2025-12-25/dwd_hr_sys_user_display_df_validation_report.md 请访问新位置查看完整内容。...

```
该报告已移动到 aianswer/2025-12-25/dwd_hr_sys_user_display_df_validation_report.md

请访问新位置查看完整内容。

```

## 📄 3. Excel 全量读取输出
**File**: `audits/dwd/2026-03-13/dwd_fin_expense_detail_xlsx_read/README.md` | **Type**: 文档
**Preview**: - 源文件：`D:\zmproject\model_project\docs\dwd_费用明细模型.xlsx` - 工作表数量：1 - 最低扫描边界：`120` 行、`AT` 列 - `summary.json`：工作簿总览 - `*_rows.md`：按行展开后的可读文本，已过滤删除线 - `*_...

```
# Excel 全量读取输出

- 源文件：`D:\zmproject\model_project\docs\dwd_费用明细模型.xlsx`
- 工作表数量：1
- 最低扫描边界：`120` 行、`AT` 列

## 输出说明

- `summary.json`：工作簿总览
- `*_rows.md`：按行展开后的可读文本，已过滤删除线
- `*_grid.tsv`：按网格导出的扫描结果，至少覆盖到指定行列
- `*_deleted_cells.json`：被删除线过滤掉的单元格
- `*_images.json`：图片锚点与上下文
- `images/`：导出的嵌入图片文件
```

## 📄 4. Agent5：部署导入 Agent
**File**: `帆软报表自动化项目/02_Agent配置/Agent5_部署导入Agent/使用说明.md` | **Type**: 文档
**Preview**: 把 `{报表名称}.cpt` 的导入与发布过程整理成可执行的 Windows 操作步骤（Markdown），用于上线前部署。 - `03_报表模板库/{页签文件夹}/{报表名称}.cpt` - 远程服务器信息（URL/端口/webroot/decision） - `03_报表模板库/{页签文件夹}/...

```
# Agent5：部署导入 Agent

## 作用

把 `{报表名称}.cpt` 的导入与发布过程整理成可执行的 Windows 操作步骤（Markdown），用于上线前部署。

## 输入

- `03_报表模板库/{页签文件夹}/{报表名称}.cpt`
- 远程服务器信息（URL/端口/webroot/decision）

## 输出

- `03_报表模板库/{页签文件夹}/{报表名称}_部署指南.md`

## 注意事项

- 文档中不要出现任何明文密码
- 离线模式仅生成步骤与命令模板，不做实际连接验证

```

## 📄 5. Agent4：cpt 生成 Agent
**File**: `帆软报表自动化项目/02_Agent配置/Agent4_cpt生成Agent/使用说明.md` | **Type**: 文档
**Preview**: 根据需求文档与 SQL 文件，生成 FineReport 10.x 可直接导入的 `.cpt` 模板文件（XML）。 - `03_报表模板库/{页签文件夹}/{报表名称}_需求.md` - `03_报表模板库/{页签文件夹}/{报表名称}_SQL.sql` - `03_报表模板库/{页签文件夹}/{...

```
# Agent4：cpt 生成 Agent

## 作用

根据需求文档与 SQL 文件，生成 FineReport 10.x 可直接导入的 `.cpt` 模板文件（XML）。

## 输入

- `03_报表模板库/{页签文件夹}/{报表名称}_需求.md`
- `03_报表模板库/{页签文件夹}/{报表名称}_SQL.sql`

## 输出

- `03_报表模板库/{页签文件夹}/{报表名称}.cpt`

## 注意事项

- 字段顺序与控件类型必须与需求文档一致
- 离线模式下不验证数据库连通性，但必须在模板中定义数据集与参数

```

## 📄 6. Task: Update dwd_co_mat_miss_price_df
**File**: `共享文档/知识库/knowledges/history/task.md` | **Type**: 文档
**Preview**: - [x] Analyze existing `dwd_co_mat_miss_price_df` files (SQL, MD, DDL) <!-- id: 0 --> - [x] Create implementation plan <!-- id: 1 --> - [x] Initial up...

```
# Task: Update dwd_co_mat_miss_price_df

- [x] Analyze existing `dwd_co_mat_miss_price_df` files (SQL, MD, DDL) <!-- id: 0 -->
- [x] Create implementation plan <!-- id: 1 -->
- [x] Initial update of `dwd_co_mat_miss_price_df.sql` with UNION <!-- id: 2 -->
- [x] Refine `dwd_co_mat_miss_price_df.sql` for doc alignment (filters, specific columns) <!-- id: 6 -->
- [/] Final alignment with detailed design checklist <!-- id: 7 -->
- [x] Update documentation (`dwd_co_mat_miss_price_df_readme.md`) <!-- id: 3 -->
- [x] Update DDL if schema changes <!-- id: 4 -->
- [x] Verify changes <!-- id: 5 -->

```

## 📄 7. Agent3：SQL 生成 Agent
**File**: `帆软报表自动化项目/02_Agent配置/Agent3_SQL生成Agent/使用说明.md` | **Type**: 文档
**Preview**: 根据 `{报表名称}_需求.md` 与依赖表结构文档，生成帆软数据集 SQL（MySQL 5.7+）。 - 需求文档：`03_报表模板库/{页签文件夹}/{报表名称}_需求.md` - 表结构：`01_数据源配置/表结构清单/*.md` - SQL 文件：`03_报表模板库/{页签文件夹}/{报表名...

```
# Agent3：SQL 生成 Agent

## 作用

根据 `{报表名称}_需求.md` 与依赖表结构文档，生成帆软数据集 SQL（MySQL 5.7+）。

## 输入

- 需求文档：`03_报表模板库/{页签文件夹}/{报表名称}_需求.md`
- 表结构：`01_数据源配置/表结构清单/*.md`

## 输出

- SQL 文件：`03_报表模板库/{页签文件夹}/{报表名称}_SQL.sql`
- 校验清单：`03_报表模板库/{页签文件夹}/{报表名称}_SQL校验.md`

## 约束

- 不允许 `SELECT *`
- 字段别名必须与需求文档一致
- 参数必须使用 `${param}` 占位符，并在 WHERE 中落地

```

## 📄 8. 交付登记（审计采购_202509）
**File**: `共享文档/知识库/projects/审计采购_202509/03_delivery/README.md` | **Type**: 文档
**Preview**: 实施完成后在此登记帆软与中台产物，便于联调与交接。无内容则保留占位，后续补齐。 | 项 | 内容 | |----|------| | 报表路径/模板名 | （待填） | | 数据集名称 | （待填） | | 连接数据源 | （待填：直连 SRM / 中台 ODS 等） | | 项 | 内容 | |-...

```
# 交付登记（审计采购_202509）

实施完成后在此登记帆软与中台产物，便于联调与交接。无内容则保留占位，后续补齐。

## 帆软 FineReport

| 项 | 内容 |
|----|------|
| 报表路径/模板名 | （待填） |
| 数据集名称 | （待填） |
| 连接数据源 | （待填：直连 SRM / 中台 ODS 等） |

## 中台 StarRocks（若已落表）

| 项 | 内容 |
|----|------|
| ODS 表 | （待填，例：`ods_*_purchase_order_item_*`） |
| DWD/DM 表 | （待填） |
| 与 SRM 伪 SQL 对齐说明 | （待填：或链接到 `02_source_sql/`） |

## 验收与比对

- 与源系统比对记录：（待填：差异率、截图或链接）
- 业务验收人 / 日期：（待填）

```

## 📄 9. dt 分区 + leaf_flag 变更记录
**File**: `共享文档/知识库/knowledges/history/task_20260302.md` | **Type**: 文档
**Preview**: - [x] 修改 dwd_co_customize_material_unit_cost_df_ddl.sql - 添加 dt 字段和分区 - [x] 修改 dwd_co_customize_material_unit_cost_df.py - 添加 dt 写入逻辑 - [x] 更新 dwd_co_...

```
# dt 分区 + leaf_flag 变更记录

## DWD 成本计算表
- [x] 修改 dwd_co_customize_material_unit_cost_df_ddl.sql - 添加 dt 字段和分区
- [x] 修改 dwd_co_customize_material_unit_cost_df.py - 添加 dt 写入逻辑
- [x] 更新 dwd_co_customize_material_unit_cost_df_readme.md

## DWD BOM 表（无需改代码）
- [x] 更新 dwd_co_customize_quotation_bom_df_readme.md - 更新 leaf_flag 说明

## DWS 层
- [x] 修改 dws_co_customize_product_predict_cost_df_ddl.sql - 改为分区表
- [x] 修改 dws_co_customize_product_predict_cost_df.sql - 添加 dt 字段
- [x] 更新 dws_co_customize_product_predict_cost_df_readme.md

## DM 层（无需改代码）
- [x] 更新 dm_co_max_customize_product_predict_cost_df_readme.md - 更新 leaf_flag 说明

```

## 📄 10. 字段差异报告：dwd_hr_sys_user_display_df
**File**: `aianswer/2025-12-18/dwd_hr_sys_user_display_df_validation_report.md` | **Type**: 文档
**Preview**: **生成时间**: 2025-12-18 15:20:32 | 来源 | 字段数 | |------|--------| | 数据字典CSV | 22 | | DDL文件 | 24 | | Excel设计 | 22 | - DDL有，数据字典缺失: DROP - DDL有，数据字典缺失: CREAT...

```
# 字段差异报告：dwd_hr_sys_user_display_df

**生成时间**: 2025-12-18 15:20:32

## 统计信息

| 来源 | 字段数 |
|------|--------|
| 数据字典CSV | 22 |
| DDL文件 | 24 |
| Excel设计 | 22 |

## ⚠️ 差异列表（共4项）

- DDL有，数据字典缺失: DROP
- DDL有，数据字典缺失: CREATE
- 数据字典有，Excel缺失: company_slw_account
- Excel有，数据字典缺失: slw_acct_srm

## 💡 建议

[WARN] 存在差异，建议先解决差异再修改SQL

         原则：以数据字典为准（已落地）

## 📋 数据字典字段列表

1. `sys_code`
2. `acct_id`
3. `company_slw_account`
4. `data_source_mes`
5. `acct_name`
6. `acct_status`
7. `acct_type`
8. `emp_code`
9. `orig_emp_code`
10. `emp_name`
11. `org_full_name`
12. `job_title_name`
13. `emp_status`
14. `emp_status_hly`
15. `supplier_flag_mes`
16. `emp_status_mes`
17. `emp_status_eam`
18. `sap_user_name`
19. `start_time`
20. `end_time`
21. `remark`
22. `insert_dt`

```

## 📄 11. Agent1：数据库解析 Agent（离线优先）
**File**: `帆软报表自动化项目/02_Agent配置/Agent1_数据库解析Agent/使用说明.md` | **Type**: 文档
**Preview**: 把“目标表”的结构信息整理成标准化 Markdown 字段说明文档，供后续 Agent2/3/4 使用。 - `fr_费用科目映射表`带fr是bi数据库HONE_IMPORT的表，无法连接，只能从文档或者图片看表结构，并生成ddl,如帆软报表自动化项目\03_报表模板库\页签1_成本中心归属映射表\...

```
# Agent1：数据库解析 Agent（离线优先）

## 作用

把“目标表”的结构信息整理成标准化 Markdown 字段说明文档，供后续 Agent2/3/4 使用。

## 输入

- `fr_费用科目映射表`带fr是bi数据库HONE_IMPORT的表，无法连接，只能从文档或者图片看表结构，并生成ddl,如帆软报表自动化项目\03_报表模板库\页签1_成本中心归属映射表\fr_cost_center_mapping_ddl.sql
- 表名：例如 `dim_成本中心维表`、`dim_account_info_df`
- 可用离线资料：
  - `d:\zmproject\model_project\docs\model_csv\`
  - `d:\zmproject\model_project\docs\dim_data_dictionary_df.csv`

## 输出

- 输出路径：`01_数据源配置/表结构清单/`
- 文件名：`{表名}_结构.md`

## 推荐操作

1. 优先从 `model_csv` 找到对应 `{表名}.csv`，生成结构文档
2. 若 `dim_data_dictionary_df.csv` 存在对应表，则补齐字段类型/字段注释
3. 办公网环境可连库后，再用 `DESC`/`SHOW CREATE TABLE` 完善主键与精确类型

```

## 📄 12. Agent2：需求转换 Agent 使用说明
**File**: `帆软报表自动化项目/02_Agent配置/Agent2_需求转换Agent/使用说明.md` | **Type**: 文档
**Preview**: 把 Excel 页签（截图/设计表）转成可直接用于开发的结构化需求文档（Markdown）。 **本 Agent 已升级**：具备深度视觉理解能力，能解析表格样式、颜色、尺寸，并能理解图片中的抽象逻辑定义。 1. **视觉解析**：识别行高、列宽、字体颜色、对齐方式。 2. **逻辑提取**：自动提...

```
# Agent2：需求转换 Agent 使用说明

## 作用
把 Excel 页签（截图/设计表）转成可直接用于开发的结构化需求文档（Markdown）。
**本 Agent 已升级**：具备深度视觉理解能力，能解析表格样式、颜色、尺寸，并能理解图片中的抽象逻辑定义。

## 核心能力
1. **视觉解析**：识别行高、列宽、字体颜色、对齐方式。
2. **逻辑提取**：自动提取图片中表格下方/周围的文字定义作为业务逻辑。
3. **知识库融合**：结合 `ai_applications` 知识库和 `报表详细方案设计_V1.xlsx` 确保需求准确。

## 输入要求
- **截图（必须）**：`03_报表模板库/{页签文件夹}/{报表名称}.png`
  - *注意：截图需清晰包含表格主体及下方的逻辑说明文字。*
- **设计文档（必须）**：`03_报表模板库/报表详细方案设计_V1.xlsx`
- **表结构文档**：`01_数据源配置/表结构清单/*.md`

## 输出
- 文件：`{报表名称}_需求.md`
- 路径：`03_报表模板库/{页签文件夹}/`

## 运行提示
当发现 Agent 对样式或逻辑理解不到位时，请检查截图是否完整包含说明区域，或在提示词中强调“关注图片下方的定义”。

```

## 📄 13. Walkthrough - Standards Update
**File**: `共享文档/知识库/knowledges/history/walkthrough.md` | **Type**: 文档
**Preview**: I have updated the `模型开发规范.md` document with a new section designed for direct copy-paste usage in development. Added **"七、核心场景跨表交互SQL通用模板"** section ...

```
# Walkthrough - Standards Update

I have updated the `模型开发规范.md` document with a new section designed for direct copy-paste usage in development.

## Changes

### [MODIFY] [模型开发规范.md](file:///D:/zmproject/model_project/docs/%E6%A8%A1%E5%9E%8B%E5%BC%80%E5%8F%91%E8%A7%84%E8%8C%83.md)

Added **"七、核心场景跨表交互SQL通用模板"** section containing:

1.  **Universal SQL Template**: 
    - **Compatibility Layer (`target_compat`)**: Automatically handles `NULLIF` for all fields from the target table to ensure standard `NULL`s.
    - **Standard Layer (`source_standard`)**: Base selection for the source table.
    - **Logic Layer**: Demonstrates safe `LEFT JOIN` and robust `COALESCE(s.field, t.field)` fallback logic.
    - **Core Principle**: Prevents empty strings from bypassing fallback logic and ensures data consistency.

2.  **Verification SQLs**:
    - Pre-written queries to check for successful NULL conversion, residual empty strings, and join cardinality (row counts).

## Verification Results

### Manual Verification
- Verified that the new section is correctly inserted before the appendix ("无公司规范...").
- The SQL template follows the standard `NULLIF` + `COALESCE` pattern defined in the document.

```

## 📄 14. dwd_sd_shipment_detail_df（出货明细）
**File**: `model_project/src/prod/dwd/dwd_sd_shipment_detail_df_readme.md` | **Type**: 文档
**Preview**: 实物/虚拟交货合并，关联 `dwd_sd_order_detail_df` 补全订单维度；源含 `ods_sap_erp_lips`/`likp`/`vbap`/`vbak` 等。 - **销售订单号 `order_num`**（`lips.VGBEL` / `vbap`/`vbak`）：`COAL...

```
# dwd_sd_shipment_detail_df（出货明细）

## 概述

实物/虚拟交货合并，关联 `dwd_sd_order_detail_df` 补全订单维度；源含 `ods_sap_erp_lips`/`likp`/`vbap`/`vbak` 等。

## SAP 键与锚表对齐（`dwd_sd_order_detail_df`）

- **销售订单号 `order_num`**（`lips.VGBEL` / `vbap`/`vbak`）：`COALESCE(CASE WHEN col IS NULL OR col = '' OR TRIM(col) = '' THEN '' ELSE col END, '')`；`JOIN vbap`/`vbak` 使用同式两侧相等。
- **交货单号 `delivery_order_num`**（`lips.VBELN`）：同上 **CASE** 模板。
- **行号**：与锚表一致使用 **`COALESCE(vbap.POSNR, '')`**（实物路径）；虚拟路径仍来自明细。
- **客户**（`likp.KUNNR` / `vbak.KUNNR`）：`COALESCE(NULLIF(col, ' '), '')`。
- **合同号 `BSTNK`**：与应收/画像 T4 一致，按值 `CASE`（空/单空格/整段空白 → NULL，否则原值）。
- **长文本 / 国际存量 / 验收子查询 / vbfa 国际量 / setleaf 关联方 / zsd_sub 康利**：与主表键比较时，对侧 `vbeln`/`vgbel`/`aubel` 等使用与上相同的 **CASE** 归一；**setleaf** `VALFROM`/`VALTO` 使用 **CASE** 区间逻辑，与 `dwd_fin_ar_aging_daily_summary` 关联方一致。

## 更新方式

全量：`TRUNCATE` + `INSERT`；脚本见 `dwd_sd_shipment_detail_df.sql`。

```

## 📄 15. User Guide: Coze StarRocks Agent
**File**: `共享文档/知识库/knowledge_base/coze_agent_guide.md` | **Type**: 文档
**Preview**: The Coze StarRocks Agent is an AI assistant designed to help developers generate and optimize StarRocks SQL queries. It is integrated into the project...

```
# User Guide: Coze StarRocks Agent

## Overview
The Coze StarRocks Agent is an AI assistant designed to help developers generate and optimize StarRocks SQL queries. It is integrated into the project as a Python tool.

## Credentials Configuration
The agent requires a `COZE_KEY` and `COZE_BOT_ID`. These are configured in:
- Environment Variables (`COZE_KEY`, `COZE_BOT_ID`)
- `ai_applications/kb_qa_mvp/app/core/config.py`

## Usage Methods

### 1. Command Line / Script
You can use the `tools/coze_agent.py` module in your scripts:
```python
from tools.coze_agent import generate_sql_quick

sql = generate_sql_quick(
    requirement="Apply nullif wrappers to problematic fields",
    context="DWD SQL content and field list..."
)
```

### 2. Testing Connection
Run the following script to verify connectivity:
```bash
.\venv\Scripts\python.exe tools/tests/test_coze_connection.py
```

## Environment Setup
Ensure the project virtual environment is used and `cozepy` is installed:
```bash
.\venv\Scripts\Activate.ps1
pip install cozepy
```

## Best Practices
- **Provide Context**: Always include table schemas or existing SQL snippets when asking for modifications.
- **Verify Syntax**: Always check the generated SQL against the StarRocks version (currently 3.3.19).
- **Token Awareness**: Be mindful of token usage for large SQL blocks.

```

## 📄 16. SRM 伪 SQL 清单（审计采购相关）
**File**: `共享文档/知识库/projects/审计采购_202509/02_source_sql/README_manifest.md` | **Type**: 文档
**Preview**: **权威正文位置**（避免双份维护）：`帆软报表自动化项目/03_报表模板库/审计采购销售/src/伪sql/` 本目录登记文件名与用途；若 SRM 更新 SQL，请更新伪 SQL 文件并在 `../00_meta.md` 更新 `last_confirmed_with_srm`。 | 文件名 | ...

```
# SRM 伪 SQL 清单（审计采购相关）

**权威正文位置**（避免双份维护）：`帆软报表自动化项目/03_报表模板库/审计采购销售/src/伪sql/`

本目录登记文件名与用途；若 SRM 更新 SQL，请更新伪 SQL 文件并在 `../00_meta.md` 更新 `last_confirmed_with_srm`。

| 文件名 | 用途摘要 |
|--------|----------|
| `独家采购.md.txt` | 独家采购多段统计 SQL，大量复用 `purchase_order_item` 基础过滤（见 `srm_purchase_order_item_base_filter.md`） |
| `询价有报价供应商小于3家.md.txt` | 询比价供应商不足 |
| `竞价有报价供应商小于3家.md.txt` | 竞价供应商不足 |
| `询价有报价供应商价差大于等于50%.md.txt` | 询比价价差 ≥50% |
| `竞价有报价供应商价差大于等于50%.md.txt` | 竞价价差 ≥50% |
| `订单份额（供应商来料良率变化与采购份额变化成反比）.MD.txt` | 良率与份额反比 |
| `订单份额（供应商季度份额增长100%以上或减少50%以上）.txt` | 季度份额大幅变动 |
| `sql参考.md.txt` | 通用写法（期间、最低价、窗口函数等），非单一指标 |

## 与中台 MCP 的关系

当前 Cursor 工程内 MCP 为 **StarRocks**，可用于核对中台表结构与抽样数据；**不能**直接读写飞书/企微。源库仍为 SRM 业务库时，以上伪 SQL 需在 SRM 或同步后的 ODS 上执行验证。

```

## 📄 17. ZM AI Knowledge Base MVP 优化设计方案
**File**: `ai_applications/kb_qa_mvp/design_notes.md` | **Type**: 文档
**Preview**: - **路径处理**：统一使用 `pathlib.Path` 处理所有文件路径，避免硬编码 `/` 或 `\`。 - **环境变量**：使用 `python-dotenv` 加载 `.env` 文件，并在 `app/core/config.py` 中定义配置类。 - **依赖管理**：确保 `req...

```
# ZM AI Knowledge Base MVP 优化设计方案

## 1. 跨平台适配方案 (Windows & Linux)
- **路径处理**：统一使用 `pathlib.Path` 处理所有文件路径，避免硬编码 `/` 或 `\`。
- **环境变量**：使用 `python-dotenv` 加载 `.env` 文件，并在 `app/core/config.py` 中定义配置类。
- **依赖管理**：确保 `requirements.txt` 中的包在两个平台上都可用。

## 2. 数据库切换机制
- **配置源**：支持从 `.env` 或用户指定的 `d:\zmproject\tools\config.py` (Windows) / `/home/ubuntu/zmproject/tools/config.py` (Linux) 加载配置。
- **动态加载**：在 `DatabaseService` 中实现逻辑，优先检查用户配置的数据库，若不可用则回退到 `sr_cache` 样例库。
- **数据库类型**：支持 SQLite (样例库) 和 StarRocks (生产库)。

## 3. 生产级功能增强
- **图表生成**：集成 `matplotlib` 或 `plotly`，在 Agent 识别到统计需求时生成图表，并在 Streamlit 中展示。
- **数据库归因**：增强 `analyze_margin_attribution` 工具，使其能够执行实际的 SQL 查询并进行多维分析。
- **知识库学习**：实现一个自动化的“学习”流程，将业务逻辑文档（如交付说明、财务规则）向量化并存入 FAISS。

## 4. 目录结构优化
- `app/core/config.py`: 增加对外部配置文件的支持。
- `app/services/database_service.py`: 实现多数据库适配器。
- `app/services/chart_service.py`: 新增图表生成服务。
- `app/services/knowledge_service.py`: 增强知识库管理。

```

## 📄 18. 帆软报表自动化 Agent 使用手册（离线优先）
**File**: `帆软报表自动化项目/05_项目文档/Agent使用手册.md` | **Type**: 文档
**Preview**: 所有对话与自动化串联 **默认遵守**：[AI_报表生成_执行规范.md](./AI_报表生成_执行规范.md)（阶段 A 先核查、阶段 B 再出 SQL/CPT；表字段须与 MCP/BI/离线结构证据对齐，禁止臆造）。 可复制提示词见该文档 **第五节**。 | Agent | 名称 | 输入 |...

```
# 帆软报表自动化 Agent 使用手册（离线优先）

## 必读：AI 执行门禁

所有对话与自动化串联 **默认遵守**：[AI_报表生成_执行规范.md](./AI_报表生成_执行规范.md)（阶段 A 先核查、阶段 B 再出 SQL/CPT；表字段须与 MCP/BI/离线结构证据对齐，禁止臆造）。

可复制提示词见该文档 **第五节**。

## Agent 清单

| Agent | 名称 | 输入 | 输出 | 备注 |
| --- | --- | --- | --- | --- |
| 1 | 数据库解析 Agent | 表名 / 表结构来源 | `{表名}_结构.md` | 当前环境离线整理为主 |
| 2 | 需求转换 Agent | 页签截图 + 表结构 | `{报表名称}_需求.md` | 输出固定结构 Markdown |
| 3 | SQL 生成 Agent | 需求文档 + 表结构 | `{报表名称}_SQL.sql` | MySQL 5.7+ 语法 |
| 4 | cpt 生成 Agent | SQL + 需求文档 | `{报表名称}.cpt` | FineReport 10.x 可导入 |
| 5 | 部署导入 Agent | cpt 路径 + 服务器信息 | `{报表名称}_部署指南.md` | 离线先生成步骤文档 |

## 通用约定（所有 Agent 共用）

- 输出目录：`03_报表模板库/{页签文件夹}/`
- 命名：与页签名称保持一致（避免后续导入混乱）
- 数据源：离线模式不连库，优先使用：
  - `d:\zmproject\model_project\docs\model_csv\`
  - `d:\zmproject\model_project\docs\dim_data_dictionary_df.csv`

## 推荐的单页签执行顺序

1. Agent1：补齐依赖表结构文档（放入 `01_数据源配置/表结构清单/`）
2. Agent2：生成 `{报表名称}_需求.md`
3. Agent3：生成 `{报表名称}_SQL.sql`
4. Agent4：生成 `{报表名称}.cpt`
5. Agent5：生成 `{报表名称}_部署指南.md`

```

## 📄 19. Knowledge Base: SAP ERP Data Cleaning (Space Treatment)
**File**: `共享文档/知识库/knowledge_base/sap_erp_data_cleaning.md` | **Type**: 文档
**Preview**: In the SAP ERP system (ECC/S4), certain fields may contain only single or multiple spaces instead of being truly NULL or containing character data. Th...

```
# Knowledge Base: SAP ERP Data Cleaning (Space Treatment)

## Overview
In the SAP ERP system (ECC/S4), certain fields may contain only single or multiple spaces instead of being truly NULL or containing character data. This often causes issues in downstream data analysis and BI reporting in the StarRocks Data Warehouse.

## Problem Identification
Fields with space issues are typically identified using the `SAP_字段值分析报告`. Common statuses include:
- `单个空格` (Single space)
- `多个空格(3个+)` (Multiple spaces 3+)

## Solution: `nullif` Transformation
To ensure these fields are treated as NULL (or as empty strings if needed) in the DWD layer, we apply the `nullif(col, ' ')` transformation.

### 1. Standard Fields
For standard character fields, wrap the source column:
```sql
nullif(vbrp.vrkme, ' ') AS sales_unit
```

### 2. Fields with `COALESCE`
If a field is already wrapped in a `COALESCE` for null-to-empty-string conversion, nest the `nullif` inside:
```sql
COALESCE(nullif(vbrk.bstnk_vf, ' '), '') AS order_remark
```

### 3. Fields in `CASE` or Joins
When fields are used in `CASE` statements or join conditions, ensure the `nullif` is applied to the source column to maintain consistency:
```sql
COALESCE(nullif(vbrk_cancel.stgrd, ' '), nullif(vbrk.stgrd, ' '), '') AS reverse_reason
```

## Impacted Tables & Models (Example)
- **Source Tables**: `VBRP`, `VBRK`, `BKPF`, `BSEG`
- **DWD Models**: `dwd_fin_acceptance_detail_df`, `dwd_fin_acc_voucher_detail_df`

## Tools
Use `tools/sap_erp_field_analyzer.py` to identify which fields in a specific DWD SQL model require this transformation based on the latest Excel analysis report.

... (内容过长，已截断)
```

## 📄 20. 业务洞察学习库
**File**: `ai_learning/business_insights/README.md` | **Type**: 文档
**Preview**: ``` business_insights/ ├── financial_theme/              # 财务主题 │   ├── gross_profit/             # 毛利分析 │   ├── revenue_cost/             # 收入成本 │   ...

```
# 业务洞察学习库

## 目录结构

```
business_insights/
├── financial_theme/              # 财务主题
│   ├── gross_profit/             # 毛利分析
│   ├── revenue_cost/             # 收入成本
│   └── expense_analysis/         # 费用分析
├── sales_theme/                  # 销售主题
├── supply_chain_theme/           # 供应链主题
└── methodology/                  # 学习方法论
```

## 使用说明

### 文件命名规范

| 文件类型 | 命名格式 | 示例 |
|---------|---------|------|
| 深度分析 | `{主题}_deep_analysis.md` | `gross_profit_deep_analysis.md` |
| 学习笔记 | `{主题}_learning_notes.md` | `gross_profit_learning_notes.md` |
| 问题记录 | `{主题}_questions.md` | `gross_profit_questions.md` |
| 模式提炼 | `{主题}_patterns.md` | `gross_profit_patterns.md` |

### 内容模板

每个主题目录下建议包含：

1. **deep_analysis.md** - 深度业务分析
   - 业务背景理解
   - 数据血缘梳理
   - 业务规则提炼
   - 异常点发现

2. **learning_notes.md** - 学习笔记
   - 学习过程记录
   - 关键收获
   - 关联知识点

3. **questions.md** - 问题记录
   - 待确认问题
   - 疑问解答
   - 后续跟进

4. **patterns.md** - 模式提炼
   - SQL模式总结
   - 业务规则模式
   - 反推方法论

## 与标准知识库的关系

```
个人学习沉淀 (ai_learning/business_insights/)
         ↓ 提炼总结
标准知识库 (ai_applications/kb_qa_mvp/knowledge_base/)
         ↓ 应用
AI Agent 查询
```

- **个人学习库**：自由书写、深度思考、过程记录
- **标准知识库**：结构化、标准化、便于检索

## 更新频率

- **学习笔记**：随时记录
- **深度分析**：完成一个主题后整理
- **模式提炼**：积累一定案例后总结

```

## 📄 21. 工作表：工作表1
**File**: `audits/dwd/2026-03-13/dwd_fin_expense_detail_xlsx_read/工作表1_rows.md` | **Type**: 文档
**Preview**: - 实际扫描范围：A1:AT120 - 原始 max_row/max_col：120/AT - 最低扫描要求：1:AT120 - 图片数量：0 - 删除线过滤单元格数：0 - R001: [空] - R002: [空] - R003: [空] - R004: [空] - R005: [空]...

```
# 工作表：工作表1

- 实际扫描范围：A1:AT120
- 原始 max_row/max_col：120/AT
- 最低扫描要求：1:AT120
- 图片数量：0
- 删除线过滤单元格数：0

## 按行展开
- R001: [空]
- R002: [空]
- R003: [空]
- R004: [空]
- R005: [空]
- R006: [空]
- R007: [空]
- R008: [空]
- R009: [空]
- R010: [空]
- R011: [空]
- R012: [空]
- R013: [空]
- R014: [空]
- R015: [空]
- R016: [空]
- R017: [空]
- R018: [空]
- R019: [空]
- R020: [空]
- R021: [空]
- R022: [空]
- R023: [空]
- R024: [空]
- R025: [空]
- R026: [空]
- R027: [空]
- R028: [空]
- R029: [空]
- R030: [空]
- R031: [空]
- R032: [空]
- R033: [空]
- R034: [空]
- R035: [空]
- R036: [空]
- R037: [空]
- R038: [空]
- R039: [空]
- R040: [空]
- R041: [空]
- R042: [空]
- R043: [空]
- R044: [空]
- R045: [空]
- R046: [空]
- R047: [空]
- R048: [空]
- R049: [空]
- R050: [空]
- R051: [空]
- R052: [空]
- R053: [空]
- R054: [空]
- R055: [空]
- R056: [空]
- R057: [空]
- R058: [空]
- R059: [空]
- R060: [空]
- R061: [空]
- R062: [空]
- R063: [空]
- R064: [空]
- R065: [空]
- R066: [空]
- R067: [空]
- R068: [空]
- R069: [空]
- R070: [空]
- R071: [空]
- R072: [空]
- R073: [空]
- R074: [空]
- R075: [空]
- R076: [空]
- R077: [空]
- R078: [空]
- R079: [空]
- R080: [空]
- R081: [空]
- R082: [空]
- R083: [空]
- R084: [空]
- R085: [空]
- R086: [空]
- R087: [空]
- R088: [空]
- R089: [空]
- R090: [空]
- R091: [空]
- R092: [空]
- R093: [空]
- R094: [空]
- R095: [空]
- R096: [空]
- R097: [空]
- R098: [空]
- R099: [空]
- R100: [空]
- R101: [空]
- R102: [空]
- R103: [空]
- R104: [空]
- R105: [空]
- R106: [空]
- R107: [空]
- R108: [空]
- R109: [空]
- R110: [空]
- R111: [空]
- R112: [空]
- R113: [空]
- R114: [空]
- R115: [空]
- R116: [空]
- R117: [空]

... (内容过长，已截断)
```

## 📄 22. dwd_sd_order_detail_df
**File**: `model_project/src/prod/dwd/dwd_sd_order_detail_df_readme.md` | **Type**: 文档
**Preview**: SAP 透明表在 GUI 显示为空的字段，在 DB2 中常为**单空格** `' '`（ECC 标准行为）。 **凭证号类**（`order_num`、`ref_order_num` 及与 ODS 等值关联的 `vbeln`/`vgbel`/`aubel` 等）约定： - **不对结果列整段 `TR...

```
# dwd_sd_order_detail_df

## SAP ECC / DB2 与凭证号归一

SAP 透明表在 GUI 显示为空的字段，在 DB2 中常为**单空格** `' '`（ECC 标准行为）。

**凭证号类**（`order_num`、`ref_order_num` 及与 ODS 等值关联的 `vbeln`/`vgbel`/`aubel` 等）约定：

- **不对结果列整段 `TRIM` 覆盖原值**；仅用 **`TRIM(col) = ''` 判断「整段是否仅空白」**（空串、`NULL`、单空格、多空格、整段空白均属此类）→ 落业务空串 `''`。
- **只要中间存在非空白字符**，则 **`ELSE col` 保留 SAP 原样**（**保留首尾空格**，与「有实质内容不动」一致）。

统一写为：

`COALESCE(CASE WHEN col IS NULL OR col = '' OR TRIM(col) = '' THEN '' ELSE col END, '')`

与 [`dwd_fin_ar_aging_daily_summary.sql`](dwd_fin_ar_aging_daily_summary.sql) 中 ZFI074 侧 `vbeln`/`zvbeln` 同式。

## setleaf 关联方（`in_customer_flag`）

与应收日汇总、出货明细同式：`valfrom` / `valto` 使用 CASE（`TRIM` 仅用于判断是否「全空白」，`ELSE` 保留原列）；`valto` 归一后为空时点匹配客户键，非空时按区间 `>= valfrom AND <= valto`；关联条件带 `mandt`；`setname` 为 `ZKUNNR_INNER_SUBCOM`、`ZKUNNR_OUTSIDE_SUBCOM`、`ZKUNNR_OUTSIDE_ZK`。客户键 `COALESCE(NULLIF(kunnr,' '), '')`；`KNA1` 关联侧与客户键同式。

## 主键与 NOT NULL

表模型为 `PRIMARY KEY(company_code, order_num, order_item_num)`，三列均为 NOT NULL。`INSERT` 投影使用 `COALESCE`/`CASE` 保证不落 `NULL`；归一后出现全空白键时值为 `''`（仍非 NULL）。若归一导致主键重复，须用源数据或过滤规则解决，不得为迁就 PK 擅自改锚口径。

## 其它

设计细节见同目录 `dwd_sd_order_detail_df.sql` 头部注释与 `model_project/docs/model_csv/` 对应模型说明。销售订单产品表等下游键字段已向本表口径对齐。

```

## 📄 23. 数仓扩展规范（按需查阅）
**File**: `docs/ai_guides/warehouse_on_demand.md` | **Type**: 文档
**Preview**: 本文档用于承接不需要每轮注入的长规范。默认先遵循 `AGENTS.md` 核心版，命中以下场景再查本文件。 - 先跑：`python tools/ensure_sap_erp_space_profile.py --from-model <模型名> --prod`。 - 报告以“字段详情”页签逐列判定...

```
# 数仓扩展规范（按需查阅）

本文档用于承接不需要每轮注入的长规范。默认先遵循 `AGENTS.md` 核心版，命中以下场景再查本文件。

## 1. SAP `ods_sap_erp_*` 空格清洗（命中即查）

- 先跑：`python tools/ensure_sap_erp_space_profile.py --from-model <模型名> --prod`。
- 报告以“字段详情”页签逐列判定，不只看摘要。
- 列按 T0~T4 定型后再选模板：
  - `T0`：无专项清洗要求。
  - `T1`：可用 `NULLIF(col, ' ')`。
  - `T2`：在确认无 T3/T4 时可用 `NULLIF(TRIM(col), '')`。
  - `T3`：保留原值，不做整列 `TRIM` 后回写。
  - `T4`：必须按值 `CASE`，禁止整列一刀切。
- 业务键/JOIN 键两侧必须同式，避免失配。

## 2. StarRocks 语法与写入细则（复杂 SQL 时查）

- 不支持 `QUALIFY`，用子查询 + `ROW_NUMBER()`。
- `INSERT OVERWRITE ... WITH ... SELECT ...` 时，`INSERT` 在前，`WITH` 在后。
- 禁止 `SELECT` 列表内子查询与 `CASE` 内子查询。
- 新建日快照表优先按 `dt` 日分区口径；避免无分区条件的整表覆盖写入历史数据。

## 3. 需求冲突处理（口径争议时查）

- 业务文档与 `model_csv` / 设计 Excel / 数据字典 / 源表样本冲突时，先列冲突项并暂停开发。
- 未确认前不得把任一口径写死到生产 SQL。
- “空/无/未填”默认兼指 `NULL` 与空串；数值 `0` 是否算空需单独确认。

## 4. Python ETL 细节（写 Python 时查）

- 递归父子匹配必须包含完整业务键，禁止单字段匹配。
- `Decimal` 参与浮点运算前先转型；递归累加防 `NaN`。
- 批量入库前将空值统一转 `None`：`df.astype(object).where(pd.notnull(df), None)`。

## 5. 收尾与质量

- 修改 SQL 后同步同目录 `readme.md`。
- 关键报表上线前做行数/金额/明细抽样核对并留痕。
- 需要更新本地知识库时执行：`python local_knowledge_model/scripts/build_knowledge_enhanced.py`。

```

## 📄 24. 字段映射问题分析
**File**: `aianswer/2025-12-22/field_mapping_fix.md` | **Type**: 文档
**Preview**: ```sql DESC dwd_co_external_purchase_product_df 结果： ✅ 存在的字段： - max_pur_cost       (不是 max_outbound_cost) - min_pur_cost       (不是 min_outbound_cost) -...

```
# 字段映射问题分析

## 📋 问题发现

### 外协表字段实际名称
```sql
DESC dwd_co_external_purchase_product_df 结果：

✅ 存在的字段：
  - max_pur_cost       (不是 max_outbound_cost)
  - min_pur_cost       (不是 min_outbound_cost)
  - latest_pur_cost    (不是 latest_outbound_cost)
  - s_pur_cost         (不是 s_outbound_cost)
  - v_pur_cost         (不是 v_outbound_cost)
  - supply_ratio
  - pci_bom_code

❌ SQL中引用但不存在的字段：
  - max_outbound_cost
  - min_outbound_cost
  - latest_outbound_cost
  - s_outbound_cost
  - v_outbound_cost
```

## 🎯 已修复
已更新 `wx` CTE 的字段映射，使用正确的源字段名称：
```sql
wx AS (
    SELECT
        pci_bom_code,
        COALESCE(max_pur_cost, 0) AS max_outbound_cost,
        COALESCE(min_pur_cost, 0) AS min_outbound_cost,
        COALESCE(latest_pur_cost, 0) AS latest_outbound_cost,
        COALESCE(s_pur_cost, 0) AS s_outbound_cost,
        COALESCE(v_pur_cost, 0) AS v_outbound_cost
    FROM dwd.dwd_co_external_purchase_product_df
    WHERE pci_bom_code IS NOT NULL
)
```

## 📊 成本表字段情况

成本表中存在**两套成本字段**：

### 第一套：源字段
```
max_unit_mat_cost
min_unit_mat_cost
latest_unit_mat_cost
s_unit_mat_cost
v_unit_mat_cost
```

### 第二套：映射字段
```
max_product_est_cost
min_product_est_cost
latest_product_est_cost
s_product_est_cost
v_product_est_cost
```

### 当前 SQL 的做法
在 `cost` CTE 中进行映射：
```sql
max_unit_mat_cost AS max_product_est_cost
min_unit_mat_cost AS min_product_est_cost
...
```

✅ **这个做法是正确的**，因为：
1. 源表中两套字段都存在
2. SQL中使用别名统一引用
3. 保持命名一致性

## ✅ 修复总结

| 问题 | 原因 | 修复方案 | 状态 |
|------|------|---------|------|
| wx 表字段名 | 外协表实际字段名是 `*_pur_cost` | 更新别名映射 | ✅ 已修复 |

... (内容过长，已截断)
```

## 📄 25. P1：SRM `purchase_order_item` 审计用基础过滤（公共片段）
**File**: `共享文档/知识库/projects/审计采购_202509/02_source_sql/srm_purchase_order_item_base_filter.md` | **Type**: 文档
**Preview**: 多份伪 SQL（如 `独家采购.md.txt`）在 `FROM purchase_order_item` 上使用相同或等价的 WHERE 条件。新指标若在同期、同工厂集合、同订单类型下分析，应**先引用本片段**，再只写增量条件，避免重复向 SRM 索要整包 SQL。 - 时间：业务要求为 `yyy...

```
# P1：SRM `purchase_order_item` 审计用基础过滤（公共片段）

## 用途

多份伪 SQL（如 `独家采购.md.txt`）在 `FROM purchase_order_item` 上使用相同或等价的 WHERE 条件。新指标若在同期、同工厂集合、同订单类型下分析，应**先引用本片段**，再只写增量条件，避免重复向 SRM 索要整包 SQL。

## 参数

- 时间：业务要求为 `yyyy-MM` 区间，**间隔不超过 1 年**。伪 SQL 中示例为 `DATE_FORMAT(create_time, '%Y-%m') BETWEEN '2025-01' AND '2026-12'`，落地时请改为参数或报表参数。
- 可选筛选项（由 BI 拼接）：
  - 供应商：`AND to_els_account = 'XX'`（名称字典：`supplier_master_data`，key=`to_els_account`，value=`supplier_name`）
  - 执行采购：`AND sub_account = 'XX'`（字典：`els_subaccount_info`，key=`sub_account`，value=`realname`；部分段落注释写 `create_by`，以 SRM 最新口径为准）

## 建议公共 WHERE（与当前伪 SQL 对齐）

下列从 `独家采购.md.txt` 等文件中归纳；`sap_order_number` 非空条件在源文中存在 `> ''` 与 `!= ''` 两种写法，**以 SRM 确认为准**，语义均为排除空单号。

```sql
-- P1: purchase_order_item 基础过滤（审计采购-当前批次）
WHERE
    DATE_FORMAT(create_time, '%Y-%m') BETWEEN :start_month AND :end_month
    AND sap_order_number > ''   -- 或与下等价: sap_order_number != ''
    AND factory IN (
        '1010', '1020', '1050', '2020',
        'B010', '8220', '9010', 'A000'
    )
    AND purchase_type = '0'
    AND material_number != ''
    AND sap_order_number NOT REGEXP '^5[1347]'
    AND is_deleted = 0
-- 可选：
-- AND to_els_account = :supplier_account
-- AND sub_account = :buyer_sub_account
```

## 常见下游粒度

- **订单物料金额子查询**：在 P1 结果上常做  
  `GROUP BY material_number, to_els_account, sap_order_number`，并对 `tax_amount` 等求和（见独家采购「基础数据」子查询）。

## 版本记录

| 版本 | 日期 | 说明 |
|------|------|------|
| v1 | 2026-03-20 | 根据 `src/伪sql/独家采购.md.txt` 归纳，供知识库复用 |

```

## 📄 26. SQL执行问题诊断报告
**File**: `aianswer/2025-12-18/SQL执行问题诊断报告.md` | **Type**: 文档
**Preview**: 执行 `dwd_hr_sys_user_display_df.sql` 时遇到两类问题： 只有5个系统的ODS表实际存在： - ✅ SRM: `ods.ods_srm_els_subaccount_info_df` - ✅ HLY: `ods.ods_hly_user_di` - ✅ SAP-ERP...

```
# SQL执行问题诊断报告

## 📋 问题总结

执行 `dwd_hr_sys_user_display_df.sql` 时遇到两类问题：

### 1. 源表不存在（9个系统）
只有5个系统的ODS表实际存在：
- ✅ SRM: `ods.ods_srm_els_subaccount_info_df`
- ✅ HLY: `ods.ods_hly_user_di`
- ✅ SAP-ERP: `ods.ods_sap_erp_usr02_df`
- ✅ SAP-BPC: `ods.ods_sap_bpc_usr02_df`
- ✅ BI: `ods.ods_bi_view_fine_user_hone_df`

缺失9个表：
- ❌ OA, PLM, MES-XSP, MES-ZM, MES-MINI, MES-XSPNC, WMS, EAM, QMS

### 2. SRM表字段名错误
SQL中使用的字段 vs 实际表字段：
- ❌ `enterprise_account` → ✅ `els_account`
- ❌ `sub_name` → ✅ `realname`

---

## 🎯 解决方案

### 方案1: 仅执行存在的5个系统（推荐）

**优点**: 
- 快速见效，先完成可用部分
- 避免等待其他ODS表创建
- 验证SQL逻辑是否正确

**缺点**:
- 数据不完整（只有5/14个系统）

**实施步骤**:
1. 修复SRM字段名
2. 注释掉9个缺失的系统
3. 执行简化版SQL

### 方案2: 等待所有ODS表创建后执行

**优点**:
- 一次性完成所有14个系统
- 数据完整

**缺点**:
- 需要等待9个ODS表创建
- 可能有更多字段名不匹配问题

---

## 🔧 需要修复的字段（SRM系统）

```sql
-- 第50行：修改字段引用
-- 错误:
COALESCE(srm.enterprise_account, '')  AS company_slw_account
-- 正确:
COALESCE(srm.els_account, '')  AS company_slw_account

-- 第51行：修改字段引用
-- 错误:
COALESCE(srm.sub_name, '')  AS acct_name
-- 正确:
COALESCE(srm.realname, '')  AS acct_name

-- 第85行：修改JOIN条件
-- 错误:
AND fill_srm.slw_acct_srm = srm.enterprise_account
-- 正确:
AND fill_srm.slw_acct_srm = srm.els_account
```

---

## 📝 建议

**立即执行（推荐方案1）**:

1. 我可以帮你创建一个修正后的SQL文件（只包含5个存在的系统）
2. 立即执行验证逻辑是否正确
3. 等其他ODS表创建后，再逐步添加剩余9个系统

**你的决定**:
- 选择方案1: 我立即创建修正版SQL并执行
- 选择方案2: 我修复SRM字段名，然后等你确认其他ODS表创建完成

请告诉我你的选择，或者你有其他想法也可以提出。

```

## 📄 27. 项目元数据：审计部 BI 采购与销售指标（2025-09）
**File**: `共享文档/知识库/projects/审计采购_202509/00_meta.md` | **Type**: 文档
**Preview**: | 字段 | 本次取值 | 说明 | |------|----------|------| | `project_id` | `审计采购_202509` | 知识库项目目录名 | | `source_type` | `xlsx` | 原始需求形态：`xlsx` / `word` / `image` ...

```
# 项目元数据：审计部 BI 采购与销售指标（2025-09）

## 固定登记字段（各类需求形态通用）

| 字段 | 本次取值 | 说明 |
|------|----------|------|
| `project_id` | `审计采购_202509` | 知识库项目目录名 |
| `source_type` | `xlsx` | 原始需求形态：`xlsx` / `word` / `image` / `mixed` |
| `source_location` | 见下「原始附件」 | 仓库内相对路径或飞书/企微链接 |
| `normalized_paths` | 见下「归一化产物」 | CSV / Markdown 等可检索正文位置 |
| `owner_platform` | 谭程俊 | 中台/BI 负责人 |
| `owner_source` | 龚晨 | SRM/业务口径确认人 |
| `last_confirmed_with_srm` | （ `2026-03-19`） | 与源系统开发最后一次对齐 SQL 的日期 |
| `feishu_doc_url` | （待填） | 飞书需求/评审文档链接 |
| `wework_doc_url` | （待填） | 企微文档或群公告中的需求链接 |

## 原始附件

- Excel：`帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）.xlsx`
- 切分 CSV 目录：`帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）_csv/`

## 归一化产物

- 需求索引与说明：`本目录/01_requirement/README.md`
- 源系统伪 SQL 清单与公共片段：`本目录/02_source_sql/`
- 交付登记：`本目录/03_delivery/README.md`
- 指标总索引：`本目录/INDEX.md`

## Word / 图片类需求时（补充约定）

在 `source_type` 填 `word` 或 `image`，并在 `01_requirement/` 下：

1. 增加 `需求摘录.md`（人工整理或 OCR 后的指标列表与口径）。
2. 若有原件，放入 `01_requirement/attachments/` 或仅在此文件「原始附件」中写网盘/飞书文件链接。

## 与数仓实施手册的对应

- 采购模块 9 项指标总览：`model_project/docs/审计_采购模块指标实施手册.md`（「监控指标清单」表格，约第 10–20 行）。

## 协作说明（飞书 / 企微）

请在飞书或企微需求置顶补充一行：**Git 知识库路径** `共享文档/知识库/projects/审计采购_202509/` 与 **最后同步日期**，避免在聊天记录中重复索要 SQL。

```

## 📄 28. 开票日期逻辑错误分析与修复
**File**: `ai_learning/lessons_learned/20260205_invoice_date_logic_error.md` | **Type**: 文档
**Preview**: 在 `dwd_sd_shipment_detail_df.sql` 文件中，无交货单情况下的开票日期逻辑错误： - 使用了 `MIN(v1.FKDAT)` 来获取开票日期，与文档要求的聚合逻辑不符 - 错误引用了 `vbrk.FKDAT`，但实际关联的是 `v1` 和 `v2` 别名 - 无交货单情...

```
# 开票日期逻辑错误分析与修复

## 一、错误现象

### 1. 错误描述
在 `dwd_sd_shipment_detail_df.sql` 文件中，无交货单情况下的开票日期逻辑错误：
- 使用了 `MIN(v1.FKDAT)` 来获取开票日期，与文档要求的聚合逻辑不符
- 错误引用了 `vbrk.FKDAT`，但实际关联的是 `v1` 和 `v2` 别名

### 2. 影响范围
- 无交货单情况下的出货日期不准确
- SQL 执行失败，StarRocks 无法解析 `vbrk.FKDAT` 列

## 二、根本原因分析

### 1. 文档理解不充分
- 文档明确要求使用 `GROUP_CONCAT` 聚合所有开票日期
- 代码却使用了 `MIN()` 函数，与文档要求不符

### 2. 代码结构设计不合理
- 创建了多余的 `invoice_dates` CTE，导致逻辑重复
- 与 `no_delivery_inspection` CTE 的逻辑不一致

### 3. 表别名管理混乱
- 关联了 `v1` 和 `v2` 别名，但错误引用了不存在的 `vbrk` 别名

## 三、修复方案

### 1. 移除多余的 CTE
- 删除 `invoice_dates` CTE，避免逻辑重复

### 2. 更新虚拟交货的出货日期逻辑
- 修改 `virtual_shipment_base` CTE 中的 `shipment_date` 字段为 NULL
- 后续由 `final_calculations` 统一使用 `no_delivery_inspection_invoice_date`

### 3. 验证 `no_delivery_inspection` CTE
- 确认关联条件：`VBRP.aubel = wi.order_num AND VBRP.aupos = wi.order_item_num`
- 确认筛选条件：排除过账状态为E、排除已取消的票据
- 确认聚合逻辑：使用 `ARRAY_JOIN(ARRAY_AGG(...))` 聚合所有开票日期

## 四、预防措施

### 1. 文档理解
- 实现前通读相关文档，标记关键要求
- 确认字段逻辑、关联条件、筛选条件与文档一致

### 2. 代码结构
- 避免创建多余的 CTE，确保逻辑清晰
- 确保数据流合理，避免逻辑重复

### 3. SQL 语法
- 使用 `GetDiagnostics` 工具检查语法错误
- 验证表别名使用一致，避免引用错误

### 4. 测试验证
- 执行 SQL 确保无语法错误
- 验证无交货单情况下的验收开票日期正确显示
- 验证出货日期与验收开票日期一致

## 五、参考文档
- `d:\zmproject\model_project\docs\model_csv\dwd_出货明细模型.csv`
- `d:\zmproject\model_project\src\dwd\dwd_sd_shipment_detail_df.sql`
```

## 📄 29. 需求归一化说明（审计采购_202509）
**File**: `共享文档/知识库/projects/审计采购_202509/01_requirement/README.md` | **Type**: 文档
**Preview**: | 类型 | 路径（相对仓库根） | |------|-------------------| | 原始 Excel | `帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）.xlsx` | | 切分后 CSV 目录 | `帆软报表自动化项目/03...

```
# 需求归一化说明（审计采购_202509）

## 原始与归一化路径

| 类型 | 路径（相对仓库根） |
|------|-------------------|
| 原始 Excel | `帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）.xlsx` |
| 切分后 CSV 目录 | `帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）_csv/` |

## 本目录副本

- `指标明细.csv`：从上述 `_csv/指标明细.csv` 复制，便于只打开 `共享文档/知识库` 即可浏览总清单。若源文件变更，请同步复制或改由 `00_meta.md` 仅保留路径说明。

## 分指标 CSV 文件列表（与源目录一致）

源目录内除 `指标明细.csv` 外，各指标对应独立 CSV 文件名如下（完整路径 = 上表「切分后 CSV 目录」+ 文件名）：

- `独家采购.csv`
- `采购价格（询比价、竞价且有报价的供应商＜3家，最大差≥50%）.csv`
- `采购价格（同物料不限供应商单次价涨或降≥20%）.csv`
- `采购价格（超1年未降价）.csv`
- `库存（库龄ZMM028A、ZMM028F）.csv`
- `采购人员（同一岗位任职3年以上）.csv`
- `订单份额（供应商来料良率变化与采购份额变化成反比）.csv`
- `订单份额（供应商季度份额增长100%以上或减少50%以上）.csv`
- `实际毛利率ZFI057订单汇总（10%） (国内).csv`
- `实际毛利率订单汇总（20%）国外.csv`
- `赊销比例（国内）.csv`
- `赊销比例(国际).csv`
- `客诉金额OA（≥50万元）.csv`
- `逾期应收（1年和50万元）.csv`
- `订单取消或退货OA（≥50万元）.csv`
- `居间服务费OA（不限金额）.csv`

## Excel 解析注意

合并单元格、删除线、隐藏行列等，见：`共享文档/知识库/knowledges/ki_excel_conversion_patterns.md`。

## Word / 图片类需求（模板）

当 `00_meta.md` 中 `source_type` 为 `word` 或 `image` 时，在本目录补充：

1. `需求摘录.md`：指标名称、口径、参数、负责人、确认日期。
2. `attachments/`（可选）：原 Word、截图；或仅在 `00_meta.md` 填写飞书/企微文件链接。

勿仅以图片作为唯一权威来源，须在 `需求摘录.md` 中有可检索文字。

```

## 📄 30. 低 Token 提问模板（ZM 数仓）
**File**: `docs/ai_guides/low_token_prompt_templates.md` | **Type**: 文档
**Preview**: 使用原则：每次只做 1 件事，限定路径，限定输出长度，默认不贴全量日志。 ```text 任务：为 <目标表名> 开发/修改 SQL（仅此任务）。 范围： - 只看这些文件：@model_project/src/prod/<layer>/<target>.sql @model_project/doc...

```
# 低 Token 提问模板（ZM 数仓）

使用原则：每次只做 1 件事，限定路径，限定输出长度，默认不贴全量日志。

## 模板 1：SQL 开发

```text
任务：为 <目标表名> 开发/修改 SQL（仅此任务）。

范围：
- 只看这些文件：@model_project/src/prod/<layer>/<target>.sql @model_project/docs/model_csv/<target>.csv
- 不要全仓搜索，不要展示全量 git status。

已知口径：
- 粒度：<如 订单行>
- 主键：<字段1,字段2>
- 业务过滤：<条件>
- 目标产出：<字段清单或指标>

约束：
- StarRocks 3.3.19；禁止 SELECT *；SELECT/CASE 禁子查询。
- 若与 model_csv/数据字典冲突，先列冲突，不要直接实现。

输出要求（精简）：
1) 先给 3 条结论（每条 <= 20 字）
2) 再给改动文件列表
3) 最后给待我确认项（若无写“无”）
```

## 模板 2：SQL 排错

```text
任务：定位并修复 <报错/异常现象>。

范围：
- 仅排查：@model_project/src/prod/<layer>/<job>.sql
- 可参考：@model_project/docs/model_csv/<job>.csv
- 不做无关重构。

现象：
- 报错信息：<粘贴关键 5~20 行>
- 预期结果：<一句话>
- 实际结果：<一句话>

排查要求（低 token）：
- 先给“最可能原因 Top3”（按概率排序）
- 每个原因给“最小验证 SQL/步骤”1 条
- 确认后再改代码

输出要求：
- 总字数控制在 200 字内
- 不复述大段日志
```

## 模板 3：口径确认（先对齐再开发）

```text
任务：只做口径确认，不改代码。

主题：<指标名/报表名>
范围：
- 只对照：@model_project/docs/model_csv/<sheet>.csv @model_project/docs/dim_data_dictionary_df.csv
- 必要时补充：@model_project/src/prod/<layer>/<related>.sql

我要你输出（固定格式）：
1) 口径定义（<= 80 字）
2) 计算公式（1 行）
3) 过滤条件（最多 5 条）
4) 粒度与主键
5) 冲突清单（业务文档 vs 设计/字典）
6) 待确认问题（最多 3 条）

要求：
- 只给结论，不展开背景。
- 若证据不足，直接写“证据不足 + 缺失项”。
```

## 可复用短指令（建议追加在每次提问末尾）

```text
请用低 token 模式：限制在指定路径内工作；不主动输出 git status；先给结论后细节；总字数尽量 <= 200。
```

```

## 📄 31. Implementation Plan - Update dwd_co_mat_miss_price_df
**File**: `共享文档/知识库/knowledges/history/implementation_plan.md` | **Type**: 文档
**Preview**: The goal is to update the `dwd_co_mat_miss_price_df` model to include `dwd_co_mat_price_df` in the main table union, as per the issue "Main table unio...

```
# Implementation Plan - Update dwd_co_mat_miss_price_df

The goal is to update the `dwd_co_mat_miss_price_df` model to include `dwd_co_mat_price_df` in the main table union, as per the issue "Main table union is missing `dwd_co_mat_price_df`". This ensures that materials identified with missing prices in `dwd_co_mat_price_df`, even if not present in the PLM BOM (`ods_plm_customize_bom_item_df`), are included in the report.

## Proposed Changes

### [dwd]

#### [MODIFY] [dwd_co_mat_miss_price_df.sql](file:///D:/zmproject/model_project/src/dwd/dwd_co_mat_miss_price_df.sql)

-   **UNION Logic**:
    -   Part 1: Select columns from `ods_plm_customize_bom_item_df`.
        -   Map `virtual_pci_code` to `pci_code` (Align with CSV line 38).
        -   Map `mat_desc` to a new `mat_desc` field for fallback (Align with CSV line 41).
    -   Part 2: Select columns from `dwd_co_mat_price_df`.
        -   Filter by `factory_code IN ('2020', 'B010')` and `mat_pur_type IN ('F', 'X')` (Align with CSV line 15).
        -   Ensure it only includes "price-missing" items to keep the source clean.
-   **Join/Selection Logic**:
    -   Update `price` CTE to include the same `factory_code` and `mat_pur_type` filters.
    -   Update main query `mat_name` to: `COALESCE(price.mat_name, cust.mat_desc, cust.mat_code)`.

#### [MODIFY] [dwd_co_mat_miss_price_df_readme.md](file:///D:/zmproject/model_project/src/dwd/dwd_co_mat_miss_price_df_readme.md)

-   Update "Data Source" section to reflect the Union logic.

... (内容过长，已截断)
```

## 📄 32. 标准业务知识库
**File**: `ai_applications/kb_qa_mvp/knowledge_base/README.md` | **Type**: 文档
**Preview**: ``` knowledge_base/ ├── financial_theme/              # 财务主题 │   ├── gross_profit/             # 毛利分析 │   │   ├── business_definition.md    # 业务定义 │  ...

```
# 标准业务知识库

## 目录结构

```
knowledge_base/
├── financial_theme/              # 财务主题
│   ├── gross_profit/             # 毛利分析
│   │   ├── business_definition.md    # 业务定义
│   │   ├── sql_patterns.md           # SQL模式
│   │   └── data_lineage.md           # 数据血缘
│   ├── revenue_cost/             # 收入成本
│   └── expense_analysis/         # 费用分析
├── sales_theme/                  # 销售主题
├── supply_chain_theme/           # 供应链主题
└── methodology/                  # 方法论
    ├── sql_analysis_checklist.md     # 分析检查清单
    └── business_glossary.md          # 业务术语表
```

## 文件规范

### business_definition.md 模板

```markdown
# {模型名称} - 业务定义

## 1. 模型基本信息
- **模型名称**: {英文名}
- **中文名称**: {中文名}
- **模型层级**: {ODS/DWD/DWS/DM}
- **更新方式**: {全量/增量}

## 2. 业务目的
{描述模型的业务用途}

## 3. 核心业务实体
| 实体 | 来源系统 | 业务含义 | 关键字段 |
|-----|---------|---------|---------|
| {实体1} | {系统} | {含义} | {字段} |

## 4. 业务规则提炼
{业务规则的结构化描述}

## 5. 数据血缘
{数据流向图}

## 6. 关键业务指标
| 指标 | 字段 | 计算逻辑 | 业务含义 |
|-----|------|---------|---------|
| {指标1} | {字段} | {逻辑} | {含义} |

## 7. 业务场景应用
{模型的应用场景}
```

### sql_patterns.md 模板

```markdown
# {模型名称} - SQL模式

## 1. CTE分层模式
{SQL结构 + 适用场景}

## 2. 特殊处理模式
{SQL结构 + 识别信号 + 业务含义}

## 3. 映射规则模式
{SQL结构 + 优先级设计}

## 4. 关联模式
{SQL结构 + 关联顺序原则}

## 5. 数据质量处理模式
{SQL结构 + 应用场景}
```

## 与个人学习库的关系

```
ai_learning/business_insights/          # 个人学习沉淀
         ↓ 提炼总结
ai_applications/kb_qa_mvp/knowledge_base/   # 标准知识库
         ↓ 应用
AI Agent 检索查询
```

- 个人学习库 → 过程性、思考性、探索性
- 标准知识库 → 结论性、规范性、检索性

## 更新流程

1. 在 `ai_learning/` 中积累学习笔记

... (内容过长，已截断)
```

## 📄 33. 知识库：Excel 到 CSV 自动化解析最佳实践
**File**: `共享文档/知识库/knowledges/ki_excel_conversion_patterns.md` | **Type**: 文档
**Preview**: 业务提供的 Excel 往往包含以下非结构化特征，直接解析会导致数据丢失或包含“已删除”信息： - **合并单元格**：内容仅存储在左上角单元格。 - **删除线 (Strikethrough)**：表示业务上已废弃，但不删除物理内容。 - **富文本 (Rich Text)**：单单元格内不同字符...

```
# 知识库：Excel 到 CSV 自动化解析最佳实践

## 1. 核心挑战
业务提供的 Excel 往往包含以下非结构化特征，直接解析会导致数据丢失或包含“已删除”信息：
- **合并单元格**：内容仅存储在左上角单元格。
- **删除线 (Strikethrough)**：表示业务上已废弃，但不删除物理内容。
- **富文本 (Rich Text)**：单单元格内不同字符有不同格式（部分删除线）。
- **隐藏行/列**：表示临时隐藏，不应导出。

## 2. 模式与解决方案 (Python + openpyxl)

### 2.1 删除线过滤模式
逻辑必须穿透富文本片段。

```python
def get_filtered_value(cell):
    """
    过滤掉带删除线的内容。支持富文本部分过滤。
    """
    if cell.value is None:
        return ""
    
    # 情况 A: 富文本 (CellRichText)
    if isinstance(cell.value, CellRichText):
        valid_parts = []
        for part in cell.value:
            # 仅保留未设置 strike 的片段
            if isinstance(part, str):
                valid_parts.append(part)
            elif hasattr(part, 'font') and not part.font.strike:
                valid_parts.append(part.text)
        return "".join(valid_parts).strip()
    
    # 情况 B: 普通单元格
    if cell.font and cell.font.strike:
        return ""
        
    return str(cell.value).strip()
```

### 2.2 隐藏内容识别
解析前必须检查维度的 `hidden` 属性。

```python
# 过滤隐藏行
if sheet.row_dimensions[row_idx].hidden:
    continue

# 过滤隐藏列
if sheet.column_dimensions[get_column_letter(col_idx)].hidden:
    continue
```

### 2.3 合并单元格取值
始终取合并区域起始单元格的值，并应用过滤逻辑。

```python
def get_cell_value(sheet, row, col):
    cell = sheet.cell(row=row, column=col)
    for merged_range in sheet.merged_cells.ranges:
        if cell.coordinate in merged_range:
            # 取合并区域左上角
            start_cell = sheet.cell(row=merged_range.min_row, column=merged_range.min_col)
            return get_filtered_value(start_cell)

... (内容过长，已截断)
```

## 📄 34. 2026-01-28 知识归纳与总结
**File**: `共享文档/知识库/knowledge_base/daily_summary_20260128.md` | **Type**: 文档
**Preview**: - **去 DWS 化**：全天的工作重心之一是将原有的 `dws` 层表（汇总层）统一迁移/重命名为 `dwd` 层（明细层）或直接合并逻辑。 - **引用全局更新**： - 更新了 `dm_sd_weekly_actual_df.sql` 中的所有关联逻辑，将 `dws` 前缀统一修改为 `dw...

```
# 2026-01-28 知识归纳与总结

## 1. 架构演进：DWS 层向 DWD 层归并
### 核心变动
- **去 DWS 化**：全天的工作重心之一是将原有的 `dws` 层表（汇总层）统一迁移/重命名为 `dwd` 层（明细层）或直接合并逻辑。
- **引用全局更新**：
  - 更新了 `dm_sd_weekly_actual_df.sql` 中的所有关联逻辑，将 `dws` 前缀统一修改为 `dwd`。
  - 所有的业绩分配模型（Performance Allocation Models）现在统一归口在 `dwd` 层。

### 知识点
- **分层简化**：在特定业务场景下，过多的汇总层（DWS）可能会增加维护成本。通过将逻辑沉淀到更健壮的明细层（DWD），可以提高下游 DM 层的查询灵活性。

---

## 2. StarRocks 开发标准与 DDL 规范
### 核心细节
- **数据类型安全性**：
  - 在 StarRocks 中，`STRING` 类型不能作为 **Primary Key**。
  - **规范**：所有主键列统一使用 `VARCHAR(length)`。
  - **建议**：对于描述性字段，优先使用 `VARCHAR(100/255)`，对于超长字段（如拒绝原因）使用 `VARCHAR(1000)`。
- **模型一致性**：
  - `work_num` (EHR 工号) 在多个模型中丢失 DDL 定义，现已统一补全。
  - **强制要求**：DML 中的 `SELECT` 列表必须与 DDL 定义的列顺序和类型严格一致。

---

## 3. 元数据管理自动化：HONE 同步工具
### 核心工具：`fetch_hone_sql.py`
- **功能升级**：
  - **全量同步**：支持从 `xsql_sql_job` 表拉取所有 SQL 脚本。
  - **自动目录化**：根据脚本名前缀（`dim_`, `dwd_`, `dm_`）自动创建并归类到 `src/` 下的对应文件夹。
  - **DataX 支持**：新增从 `xdtx_datax_sync` 表拉取 DataX JSON 配置，并统一存放在 `src/sync` 目录。
- **配置优化**：
  - `config.py` 中增加了 HONE 生产与测试环境的独立配置。

---

## 4. 环境管理与安全性
- **多环境支持**：在 `config.py` 中明确区分了 `HONE_MYSQL8_CONFIG` (生产) 和 `HONE_MYSQL8_CONFIG_TEST` (测试)。
- **敏感信息脱敏**：注意在代码库中保留完整的连接信息（如 MySQL 高权限账户），应确保 `.gitignore` 或环境管理机制覆盖此类配置（后续优化建议）。

---

## 5. 今日产出总结
- **模型更新**：`dwd_sd_order_performance_df`, `dwd_sd_order_performance_alloc_df` 等。
- **关联修复**：`dwd_fin_acceptance_detail_df`, `dwd_fin_acceptance_with_perf_alloc_df` 等。
- **基础工具**：完善了 `tools/` 目录下的同步脚本与配置。

```

## 📄 35. DWD 会计凭证明细表开发文档
**File**: `model_project/src/test/dwd/dwd_fin_acc_voucher_detail_df_readme.md` | **Type**: 文档
**Preview**: - **表名**: `dwd.dwd_fin_acc_voucher_detail_df` - **中文名**: dwd_会计凭证明细表 - **开发日期**: 2025-12-31 - **责任人**: AI Assistant - **更新频率**: 每日全量 该表用于记录 SAP 系统的会计凭...

```
# DWD 会计凭证明细表开发文档

## 1. 表信息
- **表名**: `dwd.dwd_fin_acc_voucher_detail_df`
- **中文名**: dwd_会计凭证明细表
- **开发日期**: 2025-12-31
- **责任人**: AI Assistant
- **更新频率**: 每日全量

## 2. 业务背景
该表用于记录 SAP 系统的会计凭证明细信息，整合了凭证抬头 (`BKPF`) 和凭证段 (`BSEG`) 的数据，并关联了公司信息 (`T001`) 和汇率信息 (`dim_exchange_rate_di`)，为财务分析提供基础明细数据。

## 3. 数据来源
| 源表 | 描述 | 关联条件 |
| :--- | :--- | :--- |
| `ods.ods_sap_erp_zhone_get_bseg_di` | 会计核算凭证段 (全量历史) | 主表，提供凭证明细 |
| `ods.ods_sap_erp_bkpf_df` | 会计核算凭证标题 | `BUKRS`, `GJAHR`, `BELNR` |
| `ods.ods_sap_erp_t001_df` | 公司代码 | `BUKRS` |
| `dim.dim_exchange_rate_di` | 汇率表 | `FROM_CCY` (原币), `TO_CCY` (CNY/USD), `RATE_TYPE` ('M'), `DT` (过账日期) |

## 4. 核心逻辑说明

### 4.1 基础过滤
- `BSEG` (`ods_sap_erp_zhone_get_bseg_di`) 和 `BKPF` 的 `MANDT` 均过滤为 '800'。
- 关联条件严格匹配公司代码 (`BUKRS`)、会计年度 (`GJAHR`) 和凭证编号 (`BELNR`)。

### 4.2 金额处理
- **借贷方向 (`SHKZG`)**:
  - 当 `SHKZG = 'H'` (贷方) 时，金额 (`WRBTR`, `DMBTR`) 乘以 -1。
  - 其他情况保持原值。

### 4.3 汇率计算 (逻辑已修正)
- **汇率匹配规则**:
  - 汇率类型固定为 'M'。
  - 匹配日期为凭证过账日期 (`BUDAT`)。
  - 原币 (`FROM_CCY`) 取自 `BKPF.PSWSL`。
- **特殊处理**:
  - **TO_CNY**: 若原币为 'CNY'，汇率直接置为 1；否则关联汇率表 (to_ccy='CNY')。
  - **TO_USD**: 若原币为 'USD'，汇率直接置为 1；否则关联汇率表 (to_ccy='USD')。
  - *注：修正了设计文档中关于 TO_USD 逻辑的笔误（原文档误写为原币=CNY赋值1）。*
  - 若未匹配到汇率，默认为 0。

### 4.4 衍生金额计算
- **人民币金额_不含税**: `ccy_notax_amt` * `cny_exchange_rate`
- **美元金额_不含税**: `ccy_notax_amt` * `usd_exchange_rate`

### 4.5 字段映射说明
- **开票凭证 (`invoice_num`)**: 映射自 `BSEG.BELNR` (会计凭证号)，已确认两者在业务上一致。
- **销售凭证 (`sales_invoice_num`)**: 映射自 `BSEG.VBEL2`。

## 5. 变更记录
- **2025-12-30**: 初始开发。

... (内容过长，已截断)
```

## 📄 36. DWD 会计凭证明细表开发文档
**File**: `model_project/src/prod/dwd/dwd_fin_acc_voucher_detail_df_readme.md` | **Type**: 文档
**Preview**: - **表名**: `dwd.dwd_fin_acc_voucher_detail_df` - **中文名**: dwd_会计凭证明细表 - **开发日期**: 2025-12-31 - **责任人**: AI Assistant - **更新频率**: 每日全量 该表用于记录 SAP 系统的会计凭...

```
# DWD 会计凭证明细表开发文档

## 1. 表信息
- **表名**: `dwd.dwd_fin_acc_voucher_detail_df`
- **中文名**: dwd_会计凭证明细表
- **开发日期**: 2025-12-31
- **责任人**: AI Assistant
- **更新频率**: 每日全量

## 2. 业务背景
该表用于记录 SAP 系统的会计凭证明细信息，整合了凭证抬头 (`BKPF`) 和凭证段 (`BSEG`) 的数据，并关联了公司信息 (`T001`) 和汇率信息 (`dim_exchange_rate_di`)，为财务分析提供基础明细数据。

## 3. 数据来源
| 源表 | 描述 | 关联条件 |
| :--- | :--- | :--- |
| `ods.ods_sap_erp_zhone_get_bseg_di` | 会计核算凭证段 (全量历史) | 主表，提供凭证明细 |
| `ods.ods_sap_erp_bkpf_df` | 会计核算凭证标题 | `BUKRS`, `GJAHR`, `BELNR` |
| `ods.ods_sap_erp_t001_df` | 公司代码 | `BUKRS` |
| `dim.dim_exchange_rate_di` | 汇率表 | `FROM_CCY` (原币), `TO_CCY` (CNY/USD), `RATE_TYPE` ('M'), `DT` (过账日期) |

## 4. 核心逻辑说明

### 4.1 基础过滤
- `BSEG` (`ods_sap_erp_zhone_get_bseg_di`) 和 `BKPF` 的 `MANDT` 均过滤为 '800'。
- 关联条件严格匹配公司代码 (`BUKRS`)、会计年度 (`GJAHR`) 和凭证编号 (`BELNR`)。

### 4.2 金额处理
- **借贷方向 (`SHKZG`)**:
  - 当 `SHKZG = 'H'` (贷方) 时，金额 (`WRBTR`, `DMBTR`) 乘以 -1。
  - 其他情况保持原值。

### 4.3 汇率计算 (逻辑已修正)
- **汇率匹配规则**:
  - 汇率类型固定为 'M'。
  - 匹配日期为凭证过账日期 (`BUDAT`)。
  - 原币 (`FROM_CCY`) 取自 `BKPF.PSWSL`。
- **特殊处理**:
  - **TO_CNY**: 若原币为 'CNY'，汇率直接置为 1；否则关联汇率表 (to_ccy='CNY')。
  - **TO_USD**: 若原币为 'USD'，汇率直接置为 1；否则关联汇率表 (to_ccy='USD')。
  - *注：修正了设计文档中关于 TO_USD 逻辑的笔误（原文档误写为原币=CNY赋值1）。*
  - 若未匹配到汇率，默认为 0。

### 4.4 衍生金额计算
- **人民币金额_不含税**: `ccy_notax_amt` * `cny_exchange_rate`
- **美元金额_不含税**: `ccy_notax_amt` * `usd_exchange_rate`

### 4.5 字段映射说明
- **开票凭证 (`invoice_num`)**: 映射自 `BSEG.BELNR` (会计凭证号)，已确认两者在业务上一致。
- **销售凭证 (`sales_invoice_num`)**: 映射自 `BSEG.VBEL2`。

## 5. 变更记录
- **2025-12-30**: 初始开发。

... (内容过长，已截断)
```

## 📄 37. ZM 数仓 AI 协作规范（核心版 / 低 token）
**File**: `AGENTS.md` | **Type**: 文档
**Preview**: 本文件为默认注入的核心规范。详细条款请按需查看：`docs/ai_guides/warehouse_on_demand.md`。 - 构建并维护洲明数据中台，保证 DWD/DWS/DM 口径正确、可追溯、可验证。 - 结论必须基于仓库证据，不凭经验臆造字段、口径和表关系。 - 设计依据：`model...

```
# ZM 数仓 AI 协作规范（核心版 / 低 token）

本文件为默认注入的核心规范。详细条款请按需查看：`docs/ai_guides/warehouse_on_demand.md`。

## 1) 核心目标

- 构建并维护洲明数据中台，保证 DWD/DWS/DM 口径正确、可追溯、可验证。
- 结论必须基于仓库证据，不凭经验臆造字段、口径和表关系。

## 2) 单一事实来源（强制）

- 设计依据：`model_project/docs/model_csv/` + `model_project/docs/模型设计清单-技术开发.xlsx`。
- 字段依据：`model_project/docs/dim_data_dictionary_df.csv` 与源表结构。
- `readme.md` 可滞后，只能作辅证，不可单独作为开发依据。

## 3) 开发前检查（强制）

- 进入虚拟环境后执行：`python load_project_context.py`。
- 改表前执行：`python tools/pre_dev_check.py <表名>`。
- SQL 引用 `ods_sap_erp_*` 时，先执行：
  `python tools/ensure_sap_erp_space_profile.py --from-model <模型名> --prod`。

## 4) SQL 编写红线（StarRocks 3.3.19）

- 禁止 `SELECT *`。
- 禁止在 `SELECT` 列表或 `CASE` 中写子查询，改为 `JOIN`/派生表。
- 不支持 `QUALIFY`，用子查询 + `ROW_NUMBER()` 改写。
- 全量模型默认 `INSERT OVERWRITE`，不写 `TRUNCATE`（除非明确要求）。
- **DML `UPDATE`（表类型）：** 仅**主键表**支持；`WHERE` 可用 Key 列或 Value 列过滤，**禁止更新主键列**。
- **明细表（Duplicate Key）** 不支持 DML `UPDATE`（与 StarRocks「数据变更」能力说明一致）；聚合表、更新表（Unique Key）同样不按主键表方式支持常规 DML `UPDATE`，改数用导入 UPSERT、重建分区等，勿对明细表写 `UPDATE`。

## 5) 需求冲突处理

- 业务需求若与设计文档、数据字典、源表样本冲突，先输出冲突点并待确认，禁止直接落库。
- 文档写“空/无/未填”且未特指时，默认同时覆盖 `NULL` 与空串 `''`。

## 6) 开发后收尾

- 修改 SQL 后同步更新同目录 `readme.md`。
- 关键结果需做可量化核对（行数、金额、关键明细抽样）。
- 需要同步知识库时执行：
  `python local_knowledge_model/scripts/build_knowledge_enhanced.py`。

## 7) 语言与协作

- 默认中文输出，结构简洁。
- 结论优先给“可执行下一步”，不做过度展开。

## 8) 按需扩展入口

- SAP 空格画像/T0~T4：`docs/ai_guides/warehouse_on_demand.md`
- StarRocks 细则：`aianswer/2025-12-19/StarRocks_3.3.19_开发规范.md`
- 本地检查与 CI：`scripts/ci/lint.ps1`、`scripts/ci/lint.sh`

... (内容过长，已截断)
```

## 📄 38. 维度关联稳定性规范
**File**: `ai_learning/lessons_learned/维度关联稳定性规范.md` | **Type**: 文档
**Preview**: 在数据仓库开发中，经常需要从明细表（DWD/DWS）中筛选特定的一行（如“最高金额”、“最新状态”）并关联维度属性。如果关联逻辑设计不当，极易导致筛选后的结果集维度信息大面积缺失。 1. **关联时机错误**：在 `ROW_NUMBER() = 1` 之后才进行 `LEFT JOIN`，导致维度关联...

```
# 维度关联稳定性规范

## 📋 概述
在数据仓库开发中，经常需要从明细表（DWD/DWS）中筛选特定的一行（如“最高金额”、“最新状态”）并关联维度属性。如果关联逻辑设计不当，极易导致筛选后的结果集维度信息大面积缺失。

## 🎯 核心风险点
1. **关联时机错误**：在 `ROW_NUMBER() = 1` 之后才进行 `LEFT JOIN`，导致维度关联强依赖于被选中的唯一行。
2. **排序字段不唯一**：排序字段（如成本、单价）存在大量重复值，导致 `rn=1` 的行可能恰好是维度信息缺失的那一行。
3. **关联键非严格匹配**：业务系统的编码（BOM编码、物料编码）可能带空格或大小写不一。

## 💡 最佳实践

### 1. “关联先行”原则
**原则**：尽可能在进行分区排序（Ranking）或聚合之前，先将维度表关联上。
这样可以确保每一条明细在参与竞争（排序）时，都已经携带了完整的维度属性。

### 2. 核心字段兜底 (COALESCE Fallback)
针对产品描述、Offering 等关键字段，应采用双源互补模式：
```sql
COALESCE(dim.offering, co.offering, '') AS offering
```
*优先取维度表标签值，若无则回退取明细表原始值。*

### 3. 排序键稳定性
当使用金额、成本等度量进行排序时，必须增加次要排序键（Secondary Order Key）：
```sql
ROW_NUMBER() OVER (
    PARTITION BY pci_code 
    ORDER BY calc_max_total_cost DESC, -- 业务逻辑
             dim.pci_label_start_date DESC, -- 次要排序：取最新维度的行
             co.insert_dt DESC -- 最终兜底：取最新入库的行
)
```

### 4. 维表子查询预处理
连接维表前，确保维表本身已去重并取最新。
```sql
WITH latest_dim AS (
    SELECT *, ROW_NUMBER() OVER(PARTITION BY pk ORDER BY version DESC) as rn
    FROM dim_table
)
...
LEFT JOIN latest_dim ON ... AND latest_dim.rn = 1
```

## ⚠️ 禁忌事项
- ❌ **严禁** 在不确定维度覆盖率的情况下，使用 `co.rn = 1` 强制过滤维表。
- ❌ **严禁** 忽略成本字段为 0 的极端情况。这些情况会触发隐式排序，导致维度丢失。
- ❌ **严禁** 相信业务系统输入的编码总是干净的，关联时应习惯性使用 `TRIM(UPPER(code))`。

## 📊 验证方法
1. **填充率检查**：开发后检查 `count(attr) / count(*)` 是否显著低于预期。
2. **边缘测试**：专门选取维度表中缺失或有多个版本的 PCI，验证 DM 输出是否稳健。

---
**所属主题**：SQL 质量规范 / 数据关联
**适用层级**：DWS, DM
**版本**：v1.0 (2026-01-19)

```

## 📄 39. AI喂料标准模板 - 使用说明
**File**: `业务需求/审计/项目方案二/AI喂料标准模板_说明.md` | **Type**: 文档
**Preview**: 本模板旨在建立**业务语义层**与**代码执行层**之间的标准化桥梁，让AI能够准确理解业务需求并生成对应的SQL代码。 | 字段名 | 填写要求 | 示例 | 注意事项 | |--------|----------|------|----------| | **指标名称** | 业务指标的中文名称...

```
# AI喂料标准模板 - 使用说明

## 🎯 模板设计理念

本模板旨在建立**业务语义层**与**代码执行层**之间的标准化桥梁，让AI能够准确理解业务需求并生成对应的SQL代码。

## 📊 模板字段说明

| 字段名 | 填写要求 | 示例 | 注意事项 |
|--------|----------|------|----------|
| **指标名称** | 业务指标的中文名称 | 采购节约率 | 简洁明了，避免歧义 |
| **业务含义/公式** | 指标的计算逻辑 | (基准价-实际价)/基准价 | 使用数学表达式，明确分子分母 |
| **对应SRM表名** | 数据来源表 | SRM_PURCHASE_ORDER | 必须是实际存在的表名 |
| **对应字段名** | 计算所需的字段 | PRICE, BASE_PRICE | 多个字段用逗号分隔 |
| **关联条件(Join)** | 多表关联条件 | ORDER_ID=... | 使用标准SQL语法 |
| **过滤条件(Where)** | 数据筛选条件 | STATUS='COMPLETED' | 确保数据质量 |
| **层级(明细/汇总)** | 数据聚合级别 | 汇总 | 明细/汇总二选一 |
| **备注** | 特殊说明 | 基准价需确认字段名 | 记录不确定因素 |

## 👥 填写责任分工

### 审计角色（业务定义者）
- **负责填写**：指标名称、业务含义/公式、层级
- **要求**：必须明确统计维度、计算公式、预警阈值
- **交付物**：《指标需求说明书》

### SRM业务/IT角色（数据源专家）
- **负责填写**：对应SRM表名、对应字段名、关联条件、过滤条件
- **要求**：不需要写SQL，只需标注数据来源
- **交付物**：《SRM业务字典/字段映射表》

### 中台管理员（AI编排者）
- **负责**：模板设计、数据验证、AI提示词优化
- **工具**：Cursor / Coze
- **操作**：将填好的模板喂给AI生成代码

## 🔄 使用流程

1. **模板分发**：将本模板发给相关责任人
2. **独立填写**：各角色按职责填写对应字段
3. **集中审核**：中台管理员验证数据准确性
4. **AI生成**：使用Cursor等工具生成SQL代码
5. **人工审核**：审核生成的代码逻辑

## ⚠️ 注意事项

1. **字段准确性**：SRM表名和字段名必须与实际系统一致
2. **业务逻辑**：计算公式要考虑到边界情况（除零、空值等）
3. **数据质量**：过滤条件要确保数据的有效性和完整性
4. **版本控制**：模板更新时要通知所有使用方

## 📈 预期效果

- **效率提升**：减少70%以上的手动开发时间
- **质量保证**：AI生成的SQL逻辑一致性更高
- **责任清晰**：谁填表谁负责业务准确性
- **可复用性**：模板可应用于其他业务模块
```

## 📄 40. 2026-02-28 定制产品成本测算全链路开发复盘报告
**File**: `ai_learning/lessons_learned/20260228_dws_customize_predict_cost_errors_and_standards.md` | **Type**: 文档
**Preview**: 针对定制产品（PCI）进行从报价 BOM 生成（DWD）到递归计算单位成本（DWD），再到最终产品测算汇总（DWS）的全链路开发与修复。涉及 SQL 与 Python 递归逻辑的深度整合。 - **现象**：DWD 宽表中成品数据（`bom_level = 0`）完全丢失。 - **根因**：开发中...

```
# 2026-02-28 定制产品成本测算全链路开发复盘报告

## 1. 案例背景
针对定制产品（PCI）进行从报价 BOM 生成（DWD）到递归计算单位成本（DWD），再到最终产品测算汇总（DWS）的全链路开发与修复。涉及 SQL 与 Python 递归逻辑的深度整合。

## 2. 核心错误案例与解决方案

### 2.1 NULLIF 盲目使用导致的根节点丢失 [核心避坑]
- **现象**：DWD 宽表中成品数据（`bom_level = 0`）完全丢失。
- **根因**：开发中盲目遵守“单空格清洗”规范，对 `parent_number` 施加了 `NULLIF(col, '')`。由于顶级成品的父节点为空字符串，被转为 `NULL`，直接被后续 `parent_number IS NOT NULL` 的主键过滤逻辑剔除。
- **规范建议**：**严禁在表示分层结构的主键/关联字段上盲目加 `NULLIF`**。必须分析“空字符串”是否具备“顶级节点”的业务含义。

### 2.2 StarRocks 5.1 (3.3.19) SQL 执行顺序错误
- **现象**：`INSERT OVERWRITE` 报错 `No viable statement for input 'WITH...`。
- **根因**：StarRocks 3.3.19 版本要求在 `INSERT OVERWRITE` 场景下，`WITH` 子句必须跟在 `INSERT` 语句之后。
- **修复写法**：
    ```sql
    INSERT OVERWRITE table (...) 
    WITH cte AS (...) 
    SELECT ... FROM cte;
    ```

### 2.3 Python 递归计算逻辑缺陷
- **现象**：成品层级（Level 0）计算结果未产出或被过滤。
- **根因**：
    1.  **匹配条件过松**：仅凭 `parent_number` 匹配子节点，未限制 `pci_bom_code`，导致跨 PCI 的数据污染。
    2.  **NaN 污染**：Pandas 中 `NaN + Numeric = NaN`。递归时若子节点价格缺失为 `NaN`，会污染整条父节点链路。
- **改进方案**：引入 `pd.notna` 检查，或在递归前全量填充 0，并使用独立的 `cost_miss_flag` 向上传递状态。

### 2.4 Decimal 数据类型转换陷阱
- **现象**：Python 报错 `unsupported operand type(s) for *: 'decimal.Decimal' and 'float'`。
- **根因**：StarRocks 库返回的金额是 `Decimal`，与脚本中的 `1.0` 等浮点常量运算不兼容。
- **规范**：在运算前统一强制转换：`float(row['cost']) * factor`。

## 3. 规范化操作流程总结
1.  **基础层（ODS/DWD）**：保留层级关联字段的原始表现形式（空串 vs NULL），谨慎过滤。
2.  **计算层（Python）**：统一 Decimal 转换，严防 NaN 污染，入库前 `pd.notnull` 替换为 `None`。
3.  **汇总层（DWS）**：严格按照 StarRocks 语法顺序编写 SQL，聚合维度必须涵盖所有 PCI 标识。
4.  **验证层**：坚持“行数比对 + 随机案例手工复核”模式。

... (内容过长，已截断)
```

## 📄 41. 费用明细模型 (dwd_fin_expense_detail_df) 逻辑复盘与规范
**File**: `model_project/src/test/dwd/dwd_fin_expense_detail_df_review.md` | **Type**: 文档
**Preview**: **时间**: 2026-02-28 **主题**: 针对业务需求文档 (`dwd_费用明细模型.csv`) 到 SQL 代码落地的逻辑实现与规范审查。 当把复杂的多系统业务规则映射到 SQL 代码时，必须确保“不遗漏”、“不越界”。 *   **表别名关联**: 业务文档通常使用类似 `a-实际费...

```
# 费用明细模型 (dwd_fin_expense_detail_df) 逻辑复盘与规范

**时间**: 2026-02-28
**主题**: 针对业务需求文档 (`dwd_费用明细模型.csv`) 到 SQL 代码落地的逻辑实现与规范审查。

## 1. 业务逻辑映射规范
当把复杂的多系统业务规则映射到 SQL 代码时，必须确保“不遗漏”、“不越界”。

*   **表别名关联**: 业务文档通常使用类似 `a-实际费用query`， `b-BPC实际调整` 以及 `b~j`、`b~k` 等别名代号来指代复杂的维度表。在 SQL 中翻译这些别名时，需要清晰地使用 `INNER JOIN` 替代 `LEFT JOIN + IS NOT NULL` 来实现强制过滤，这既能提高可读性，也能提升数据库优化器的执行效率。
    *   *案例*: BPC调整表与成本中心维表和科目维表的关联过滤。

## 2. 核心底表的数据约束边界
多表 `UNION ALL` 的模型中，每一个基础抽取层 (CTE) 必须独立完成其独有的业务限制，切忌把不同底表的过滤逻辑混淆或遗漏在最终的最外层。

*   **全融合范围过滤**: 对于 `实际费用query表`，文档中要求的“根据 `bic_zbukrs` (`bukrs`) 筛选 `dim_company_info_df` 限制为全融合公司”，必须在基础抽取层使用 `INNER JOIN dim.dim_company_info_df` 实现。单纯依赖其他辅表 (`dim_entity_info_mf` 的 GBG01) 无法达成精准的业务口径（实际验证可排除掉约30万条不合规数据）。

## 3. 字段映射值的“兜底”(Fallback) 设计规范
**【严重提醒】: 字段类型、业务含义完全不同的字段，严禁进行相互兜底 (Fallback)！**

*   **背景**: 在处理缺失映射时，开发人员往往会习惯性地使用 `COALESCE(map.field1, base.field2)` 以防止查出 `NULL` 值。
*   **错误案例**: 在处理销服费用一级科目属性 `fee_subject_l1_sales` 时，原代码写成了 `COALESCE(acc_map.fee_subject_l1_sales, acc.account_name)`。
*   **规范要求**: 
    1.  `fee_subject_l1_sales` (例如：人工成本、差旅费等) 是**部门级别/科目的统称（一级归类）**。
    2.  `account_name` (例如：应付职工薪酬-基本工资) 是直接的**底层总账科目名称**。
    3.  这两者属于**完全不同的业务概念与层级**。如果映射表中找不到对应的归类，宁可让其为 `NULL` (暴露出映射不全的数据质量问题，让业务及时补录)，也**绝对不能**用底层的 `account_name` 去顶替高级别的统称字段。这种“好心办坏事”的兜底会严重破坏下游报表针对 `fee_subject_l1_sales` 字段的 SELECT 和 GROUP BY 统计维度。
    4.  **结论**: 严格按照数据字典和配置表取数，对于分析层、聚合层字段，**无映射即为空**，倒逼前端源系统维护数据质量。

```

## 📄 42. 费用明细模型 (dwd_fin_expense_detail_df) 逻辑复盘与规范
**File**: `model_project/src/prod/dwd/dwd_fin_expense_detail_df_review.md` | **Type**: 文档
**Preview**: **时间**: 2026-02-28 **主题**: 针对业务需求文档 (`dwd_费用明细模型.csv`) 到 SQL 代码落地的逻辑实现与规范审查。 当把复杂的多系统业务规则映射到 SQL 代码时，必须确保“不遗漏”、“不越界”。 *   **表别名关联**: 业务文档通常使用类似 `a-实际费...

```
# 费用明细模型 (dwd_fin_expense_detail_df) 逻辑复盘与规范

**时间**: 2026-02-28
**主题**: 针对业务需求文档 (`dwd_费用明细模型.csv`) 到 SQL 代码落地的逻辑实现与规范审查。

## 1. 业务逻辑映射规范
当把复杂的多系统业务规则映射到 SQL 代码时，必须确保“不遗漏”、“不越界”。

*   **表别名关联**: 业务文档通常使用类似 `a-实际费用query`， `b-BPC实际调整` 以及 `b~j`、`b~k` 等别名代号来指代复杂的维度表。在 SQL 中翻译这些别名时，需要清晰地使用 `INNER JOIN` 替代 `LEFT JOIN + IS NOT NULL` 来实现强制过滤，这既能提高可读性，也能提升数据库优化器的执行效率。
    *   *案例*: BPC调整表与成本中心维表和科目维表的关联过滤。

## 2. 核心底表的数据约束边界
多表 `UNION ALL` 的模型中，每一个基础抽取层 (CTE) 必须独立完成其独有的业务限制，切忌把不同底表的过滤逻辑混淆或遗漏在最终的最外层。

*   **全融合范围过滤**: 对于 `实际费用query表`，文档中要求的“根据 `bic_zbukrs` (`bukrs`) 筛选 `dim_company_info_df` 限制为全融合公司”，必须在基础抽取层使用 `INNER JOIN dim.dim_company_info_df` 实现。单纯依赖其他辅表 (`dim_entity_info_mf` 的 GBG01) 无法达成精准的业务口径（实际验证可排除掉约30万条不合规数据）。

## 3. 字段映射值的“兜底”(Fallback) 设计规范
**【严重提醒】: 字段类型、业务含义完全不同的字段，严禁进行相互兜底 (Fallback)！**

*   **背景**: 在处理缺失映射时，开发人员往往会习惯性地使用 `COALESCE(map.field1, base.field2)` 以防止查出 `NULL` 值。
*   **错误案例**: 在处理销服费用一级科目属性 `fee_subject_l1_sales` 时，原代码写成了 `COALESCE(acc_map.fee_subject_l1_sales, acc.account_name)`。
*   **规范要求**: 
    1.  `fee_subject_l1_sales` (例如：人工成本、差旅费等) 是**部门级别/科目的统称（一级归类）**。
    2.  `account_name` (例如：应付职工薪酬-基本工资) 是直接的**底层总账科目名称**。
    3.  这两者属于**完全不同的业务概念与层级**。如果映射表中找不到对应的归类，宁可让其为 `NULL` (暴露出映射不全的数据质量问题，让业务及时补录)，也**绝对不能**用底层的 `account_name` 去顶替高级别的统称字段。这种“好心办坏事”的兜底会严重破坏下游报表针对 `fee_subject_l1_sales` 字段的 SELECT 和 GROUP BY 统计维度。
    4.  **结论**: 严格按照数据字典和配置表取数，对于分析层、聚合层字段，**无映射即为空**，倒逼前端源系统维护数据质量。

```

## 📄 43. ⚡ dwd_co_product_predict_cost_df 快速修复指南
**File**: `aianswer/2025-12-22/dwd_co_product_predict_cost_df_quick_fix.md` | **Type**: 文档
**Preview**: ``` 错误: Column 'pci_bom_code' cannot be resolved 原因: SQL 试图查询源表中不存在的字段 ``` | 错误的字段 | 正确的字段 | 来源 | |-----------|-----------|------| | `max_product_est_...

```
# ⚡ dwd_co_product_predict_cost_df 快速修复指南

## 🎯 问题

```
错误: Column 'pci_bom_code' cannot be resolved
原因: SQL 试图查询源表中不存在的字段
```

## 🔧 核心修复（3 个关键改动）

### 1️⃣ 字段名映射

| 错误的字段 | 正确的字段 | 来源 |
|-----------|-----------|------|
| `max_product_est_cost` | `max_unit_mat_cost` | dwd_co_product_unit_cost_df |
| `min_product_est_cost` | `min_unit_mat_cost` | dwd_co_product_unit_cost_df |
| `latest_product_est_cost` | `latest_unit_mat_cost` | dwd_co_product_unit_cost_df |
| `s_product_est_cost` | `s_unit_mat_cost` | dwd_co_product_unit_cost_df |
| `v_product_est_cost` | `v_unit_mat_cost` | dwd_co_product_unit_cost_df |

### 2️⃣ 供货比例来源修正

```diff
# 错误的方式
- param.supply_ratio      # 从参数表获取
+ cost.supply_ratio       # 直接从源表获取
```

### 3️⃣ 移除不需要的 param CTE

```diff
- LEFT JOIN dwd_co_product_cost_param_df   # 移除
+ LEFT JOIN dwd_co_external_purchase_product_df  # 保留
```

---

## 📝 修改后的 SQL 框架

### CTE 结构
```sql
WITH cost AS (
    SELECT
        pci_code, pci_bom_code, replace_rule_code,
        supply_ratio,                               -- ✅ 直接来自源表
        max_unit_mat_cost AS max_product_est_cost, -- ✅ 字段映射
        ...
    FROM dwd.dwd_co_product_unit_cost_df
    WHERE pci_bom_code IS NOT NULL AND mat_code IS NOT NULL
),
wx AS (
    SELECT pci_bom_code, max_outbound_cost, ...
    FROM dwd.dwd_co_external_purchase_product_df
)
SELECT ... FROM cost LEFT JOIN wx ON ...
```

---

## ✅ 验证命令

在 StarRocks 中执行：

```sql
-- 1. 检查源表结构
DESC dwd.dwd_co_product_unit_cost_df;

-- 2. 执行 SQL
TRUNCATE TABLE dwd.dwd_co_product_predict_cost_df;

... (内容过长，已截断)
```

## 📄 44. 帆软报表自动化：页签1闭环（成本中心归属映射表）
**File**: `ai_learning/lessons_learned/帆软报表自动化_页签1闭环_成本中心归属映射表.md` | **Type**: 文档
**Preview**: 以“成本中心归属映射表”做一次完整闭环：截图→需求→SQL→cpt→验收清单→知识沉淀。后续新增页签不再从头摸索。 - 可自动化生成/可维护的模板：`com.fr.data.impl.DBTableData`（SQL 在 `<Query><![CDATA[...]]></Query>`，参数在 `<...

```
# 帆软报表自动化：页签1闭环（成本中心归属映射表）

## 目标

以“成本中心归属映射表”做一次完整闭环：截图→需求→SQL→cpt→验收清单→知识沉淀。后续新增页签不再从头摸索。

## 关键结论（可复用）

### 1) 参考模板要选对：DBTableData vs EmbeddedTableData

- 可自动化生成/可维护的模板：`com.fr.data.impl.DBTableData`（SQL 在 `<Query><![CDATA[...]]></Query>`，参数在 `<Parameters>`）
- 不适合自动化改造的模板：`com.fr.data.impl.EmbeddedTableData`（RowData 是压缩/编码块，难以维护与替换）

### 2) 字段别名与需求必须 1:1

- SQL 输出字段别名必须与需求文档“字段名称”一致
- 禁止 `SELECT *`

### 3) 帆软参数写法（SQL 内动态条件）

- 推荐用帆软表达式拼接条件：
  - `${if(len(param) == 0, "", " AND xxx IN (" + param + ")")}`
- 多选参数建议传入“已带引号的逗号分隔”字符串，例如：
  - `'A','B','C'`

### 3.1) 多选下拉控件落地（ComboCheckBox）

- 参数面板要实现“事业部/成本中心多选下拉”，优先使用 `com.fr.form.ui.ComboCheckBox`
- 字典建议用 `TableDataDictionary` 绑定“筛选器数据集”（例如：事业部-筛选器、成本中心-筛选器）
- 关键点：`RAAttr delimiter="&apos;,&apos;" isArray="false"`，这样参数可直接拼进 `IN (${param})`，无需二次加工

### 4) 填报写回主键要与业务口径一致

成本中心归属映射表存在“版本有效期”概念（生效/失效日期）。

- 写回表：`fr_成本中心归属映射表`
- 建议主键：`成本中心 + 生效日期`
- 风险：如果只用“成本中心”做 key，会覆盖历史版本或引入重复行

### 5) 下拉控件的最低可用实现

不连库的离线阶段，下拉可以先用 `CustomDictionary` 固定枚举实现（例如：职能/研发/销服），待联通字典表后再替换为 `TableDataDictionary`。

### 6) 标题栏与报表区拆分（按第8节模板）

- 上半部分为“标题栏+筛选区”（建议放参数面板 ParameterUI 中），上面已经有页签名/表名
- 下半部分为“数据展示区”（报表网格），不再重复单独的标题行
- 数据展示区表头：行高约 10mm，白字加粗；边框色 dbdbdb；只读区背景色 ebebeb

## 页签1验收标准（精简版）

- cpt 可导入 FineReport 10.1.9
- 数据集 ds1 存在，SQL 可执行（字段正确、参数可替换）
- 归属部门为下拉（职能/研发/销服）
- 提交/校验/新增行可用
- 写回主键为“成本中心 + 生效日期”

## 对应项目产物

- 需求：帆软报表自动化项目/03_报表模板库/页签1_成本中心归属映射表/成本中心归属映射表_需求.md
- SQL：帆软报表自动化项目/03_报表模板库/页签1_成本中心归属映射表/成本中心归属映射表_SQL.sql
- cpt：帆软报表自动化项目/03_报表模板库/页签1_成本中心归属映射表/成本中心归属映射表.cpt

... (内容过长，已截断)
```

## 📄 45. dwd_sd_shipment_detail_df 表修复总结
**File**: `local_knowledge_model/docs/dwd_shipment_detail_fix_summary.md` | **Type**: 文档
**Preview**: **问题**：ZMCE（贷项凭证）和ZMDR类型的无交货单订单，由于order_qty为0，导致出货金额计算结果为0，度量值不合理。 **解决方案**：在amount_calculations CTE中添加特殊处理逻辑： - 对于无交货单的订单，直接使用订单金额作为出货金额，不进行比例分摊 - 对于...

```
# dwd_sd_shipment_detail_df 表修复总结

## 修复内容

### 1. 无交货单订单金额计算修复

**问题**：ZMCE（贷项凭证）和ZMDR类型的无交货单订单，由于order_qty为0，导致出货金额计算结果为0，度量值不合理。

**解决方案**：在amount_calculations CTE中添加特殊处理逻辑：
- 对于无交货单的订单，直接使用订单金额作为出货金额，不进行比例分摊
- 对于有交货单的订单，保持原有的比例分摊逻辑

**技术实现**：
```sql
-- 出货金额计算
CASE 
    -- 无交货单订单：直接使用订单金额作为出货金额
    WHEN sqc.delivery_order_num = '' THEN COALESCE(sqc.order_tax_amt, 0)
    -- 有交货单订单：按比例分摊
    WHEN COALESCE(sqc.order_qty, 0) = 0 THEN 0
    ELSE COALESCE(sqc.order_tax_amt, 0) * sqc.calculated_shipment_qty / sqc.order_qty
END AS shipment_tax_amt
```

### 2. 无交货单订单验收字段置空修复

**问题**：无交货单的借贷项凭证不需要验收信息，但验收相关字段未正确置空。

**解决方案**：在final_calculations CTE中添加字段置空逻辑：
- 对于无交货单的订单，将验收相关字段置空
- 对于有交货单的订单，保持原有逻辑

**技术实现**：
```sql
-- 无交货单订单验收字段置空处理
CASE 
    WHEN ac.delivery_order_num = '' THEN ''
    ELSE ac.is_inspected
END AS is_inspected_final
```

### 3. 筛选条件验证

**验证内容**：
- ✅ 订单类型限制：ZMCE、ZMDR
- ✅ 销售公司范围限制：关联dim_company_info_df，过滤不在公司维的公司代码
- ✅ 公司代码特殊处理：company_code in ('2000','B000')的订单，除客户代码等于'0000106034'外的订单外，其他的排除
- ✅ 订单状态限制：order_status=1
- ✅ 排除重复处理：确保不重复处理已有实物交货的订单行

## 数据验证结果

**修复后数据表现**：
- 无交货单订单正确标记为"I-借贷"场景
- ZMCE类型订单金额为负数（符合贷项凭证逻辑）
- ZMDR类型订单金额为正数
- 验收相关字段正确置空
- 所有筛选条件生效

## 技术要点

1. **多层CTE结构**：使用多个CTE进行逻辑分层，提高代码可读性和维护性
2. **条件判断**：通过CASE语句实现不同场景的差异化处理
3. **空值处理**：使用COALESCE函数处理可能的空值情况
4. **性能优化**：通过NOT EXISTS子查询避免重复数据处理

## 业务价值

1. **数据准确性**：确保无交货单订单的金额计算和字段处理正确
2. **业务逻辑一致性**：符合借贷项凭证的业务处理逻辑
3. **报表可靠性**：提高基于该表的报表数据质量
4. **系统稳定性**：增强了SQL的健壮性，能处理各种边缘场景

## 适用场景

此修复方案适用于：
- 无交货单的借贷项凭证处理

... (内容过长，已截断)
```

## 📄 46. dwd_fin_expense_detail_df 生产数据检查清单
**File**: `audits/dwd/2026-03-11/dwd_fin_expense_detail_df_production_checklist.md` | **Type**: 文档
**Preview**: **检查日期**：_____ **执行人**：_____ **环境**：生产 dwd 库 在 DBeaver 或 Trae 中连接生产 **dwd** 库，打开 `queries/verify_dwd_fin_expense_detail_df.sql`，按段执行并记录结果。 - **预期**：仅 ...

```
# dwd_fin_expense_detail_df 生产数据检查清单

**检查日期**：_____  
**执行人**：_____  
**环境**：生产 dwd 库  

在 DBeaver 或 Trae 中连接生产 **dwd** 库，打开 `queries/verify_dwd_fin_expense_detail_df.sql`，按段执行并记录结果。

---

## 1. 版本 × 来源分布（第 1 段）

- **预期**：仅 `version` ∈ {V1, V2}，`source_mark` ∈ {BPC费用, 手工调整, BPC调整}。
- **记录**：总行数 total ≈ _____，V1 与 V2 行数是否接近（可有一定差异，因 alloc 取一条逻辑）。

---

## 2. 值域校验（第 2～3 段）

- **第 2 段**：version 非法值 → 应为 0 行。
- **第 3 段**：source_mark 非法值 → 应为 0 行。

---

## 3. fee_attribute / fee_type / process_tag（第 4～6 段）

- **fee_attribute**：应为 研发费用/销售费用/管理费用/制造费用 及少量 NULL。
- **fee_type**：主要为 经营/战投/经营不含，按 belong_dept 分布合理。
- **process_tag**：D-销服-*、D-研发-* 或 NULL。

---

## 4. 关键非空（第 7 段）

- **预期**：null_ym、null_version、null_cost_center_code、null_source_mark 均为 0。

---

## 5. 金额与分摊（第 8 段）

- **fee_percent**：null 数应为 0（未关联 i 表时脚本赋 1）。
- **alloc_cny_mismatch**：alloc_cny_amt 与 cny_amt × fee_percent 的误差 >0.01 的行数，预期为 0 或极少。

---

## 6. 归属域与区域抽样（第 9 段）

- **预期**：fee_belongs 与 belong_dept 在未关联 g 表时一致；sales_area_name、sales_region_name、continent_name 有合理取值（国内/国际、华南等、亚洲等）。

---

## 7. 新增字段非空率（第 9b 段）★

- **检查**：V1/V2 下 total、has_region_code、has_region_name、has_continent、has_area_code、has_area_name、has_unit_code、has_unit_name。
- **预期**：关联上 g 表且 g 表有配置的成本中心，上述字段应有数；未关联 g 时可为空。国内销服线 has_* 比例相对较高。

---

## 8. V1/V2 行数（第 9c 段）

- **预期**：两版本行数相同或非常接近（脚本已按 _rid 取一条 alloc，避免膨胀）。若差异大，需排查 alloc 或 scope 关联。

---

## 9. 数据时效（第 10 段）

- **latest_insert_dt**：应为本次跑批时间。
- **min_ym / max_ym**：符合业务年月范围。

---

## 快速单条总览（可选）

可在库中执行下面一条，用于快速看行数、新增字段有数率（排除 NULL 与空串）、金额一致性：

... (内容过长，已截断)
```

## 📄 47. 洲明AI知识库问答MVP (kb_qa_mvp) - 生产增强版
**File**: `ai_applications/洲明AI知识库问答MVP (kb_qa_mvp) - 生产增强版.md` | **Type**: 文档
**Preview**: 本项目是洲明科技AI知识库问答系统的最小可行产品（MVP），旨在通过整合企业内部的结构化数据（如CRM客户信息、SAP订单数据），结合检索增强生成（RAG）技术和大语言模型（LLM），为用户提供一个智能、高效的自然语言问答界面。 **核心优化功能：** *   **跨平台适配**：完美支持 Wind...

```
# 洲明AI知识库问答MVP (kb_qa_mvp) - 生产增强版

## 项目简介

本项目是洲明科技AI知识库问答系统的最小可行产品（MVP），旨在通过整合企业内部的结构化数据（如CRM客户信息、SAP订单数据），结合检索增强生成（RAG）技术和大语言模型（LLM），为用户提供一个智能、高效的自然语言问答界面。

**核心优化功能：**

*   **跨平台适配**：完美支持 Windows 和 Linux 环境，自动处理路径差异，统一使用 `pathlib`。
*   **多数据库切换**：
    -   默认使用 `sr_cache` 样例库 (SQLite)。
    -   支持通过外部配置文件 `config.py` 切换至生产级数据库 (如 StarRocks)。
*   **智能图表生成**：Agent 可根据数据查询结果自动生成销售趋势图、对比图等可视化图表。
*   **深度归因分析**：集成财务归因逻辑，支持从毛利波动到成本因子的多维下钻分析。
*   **知识库持续学习**：支持上传业务逻辑文档 (.txt, .pdf)，系统自动向量化并存入知识库。

## 项目结构

```
kb_qa_mvp/
├── app/                    # FastAPI后端应用
│   ├── api/                # API路由定义
│   ├── core/               # 核心配置 (支持外部 config.py 加载)
│   ├── services/           # 核心业务逻辑服务
│   │   ├── rag_service.py  # RAG问答服务
│   │   ├── agent_service.py# Agent 调度服务
│   │   ├── agent_tools.py  # Agent 工具集 (图表、归因、查询)
│   │   ├── database_service.py # 多数据库适配服务
│   │   ├── chart_service.py # 图表生成服务
│   │   └── knowledge_service.py # 知识库学习服务
│   └── main.py             # FastAPI应用主入口
├── data/                   # 模拟数据与归因数据
├── scripts/                # 辅助脚本
├── vector_store/           # 向量数据库存储目录
├── .env                    # 环境变量配置文件
├── requirements.txt        # Python依赖列表
└── web_ui.py               # Streamlit网页问答界面 (增强版)
```

## 环境准备

1.  **克隆仓库**：
    ```bash
    git clone https://github.com/eninem123/zmproject.git
    cd zmproject/ai_applications/kb_qa_mvp
    ```

2.  **安装依赖**：
    ```bash
    pip install -r requirements.txt
    ```

3.  **配置环境变量**：
    在 `kb_qa_mvp` 目录下创建 `.env` 文件：

... (内容过长，已截断)
```

## 📄 48. 审计采购_202509：指标索引
**File**: `共享文档/知识库/projects/审计采购_202509/INDEX.md` | **Type**: 文档
**Preview**: 本表建立 **实施手册序号**、**需求 CSV**、**SRM 伪 SQL 文件** 之间的对应关系。路径均为相对仓库根目录 `zmproject/`。 | 手册序号 | 指标名称（实施手册） | 需求 CSV（`_csv` 目录下） | 伪 SQL 文件（`src/伪sql/`） | 备注 | ...

```
# 审计采购_202509：指标索引

本表建立 **实施手册序号**、**需求 CSV**、**SRM 伪 SQL 文件** 之间的对应关系。路径均为相对仓库根目录 `zmproject/`。

## 采购模块（SRM 伪 SQL 已提供部分）

| 手册序号 | 指标名称（实施手册） | 需求 CSV（`_csv` 目录下） | 伪 SQL 文件（`src/伪sql/`） | 备注 |
|----------|----------------------|---------------------------|-----------------------------|------|
| 1 | 独家采购 | `…_csv/独家采购.csv` | `独家采购.md.txt` | 多段 SQL，含公共 `purchase_order_item` 过滤；见 P1 |
| 2 | 采购价格-询比价供应商不足 | `…_csv/采购价格（询比价、竞价且有报价的供应商＜3家，最大差≥50%）.csv` | `询价有报价供应商小于3家.md.txt` | 与同 CSV 内「竞价不足」等指标共用展现文档 |
| 3 | 采购价格-竞价供应商不足 | 同上 | `竞价有报价供应商小于3家.md.txt` | 同上 |
| 4 | 采购价格-价差过大 | 同上 | `询价有报价供应商价差大于等于50%.md.txt`、`竞价有报价供应商价差大于等于50%.md.txt` | 询/竞两路各一份伪 SQL |
| 5 | 采购价格-长期未降价 | `…_csv/采购价格（超1年未降价）.csv` | *（本目录未收录伪 SQL，请向 SRM 索取后补 `02_source_sql/`）* | |
| 6 | 订单份额-良率与份额反比 | `…_csv/订单份额（供应商来料良率变化与采购份额变化成反比）.csv` | `订单份额（供应商来料良率变化与采购份额变化成反比）.MD.txt` | |
| 7 | 订单份额-份额大幅变动 | `…_csv/订单份额（供应商季度份额增长100%以上或减少50%以上）.csv` | `订单份额（供应商季度份额增长100%以上或减少50%以上）.txt` | |
| 8 | 采购人员-同一岗位任职3年以上 | `…_csv/采购人员（同一岗位任职3年以上）.csv` | *（HR 域，伪 SQL 待调研）* | 手册标注数据来源 HR |
| 9 | 定位考勤（占位） | *见指标明细* | *待定* | |

`_csv` 完整路径前缀：`帆软报表自动化项目/03_报表模板库/审计采购销售/BI系统-指标设置展现（审计部202509010）_csv/`

## 销售及其他模块（本需求包 CSV 索引）

以下 CSV 与 `指标明细.csv` 中销售端等指标对应，**当前 `src/伪sql/` 无独立文件**（若后续补充 SRM/SAP 伪 SQL，在 `02_source_sql/README_manifest.md` 登记）。

| 需求 CSV 文件名 |
|-----------------|
| `实际毛利率ZFI057订单汇总（10%） (国内).csv` |
| `实际毛利率订单汇总（20%）国外.csv` |
| `赊销比例(国际).csv` |
| `赊销比例（国内）.csv` |
| `客诉金额OA（≥50万元）.csv` |
| `逾期应收（1年和50万元）.csv` |
| `订单取消或退货OA（≥50万元）.csv` |

... (内容过长，已截断)
```

## 📄 49. 核心优化功能测试用例与预期结果
**File**: `ai_applications/核心优化功能测试用例与预期结果.md` | **Type**: 文档
**Preview**: 以下是针对您优化后的项目中两个核心功能——**问答生成图表**和**查询数据库进行归因**——的详细测试用例和预期结果。 请确保后端 API 和 Streamlit UI 均已成功启动，并在 Streamlit 界面中进行测试。 此功能验证 Agent 是否能正确识别图表生成意图，调用相应的工具，并...

```
# 核心优化功能测试用例与预期结果

以下是针对您优化后的项目中两个核心功能——**问答生成图表**和**查询数据库进行归因**——的详细测试用例和预期结果。

请确保后端 API 和 Streamlit UI 均已成功启动，并在 Streamlit 界面中进行测试。

## 1. 问答生成图表功能测试

此功能验证 Agent 是否能正确识别图表生成意图，调用相应的工具，并成功生成和展示图表。

| 测试用例 (输入问题) | 预期 Agent 动作 | 预期结果 (Streamlit UI) |
| :--- | :--- | :--- |
| **分析 LED 显示屏的销售趋势并生成图表** | 1. Agent 识别意图，调用 `analyze_sales_trend_with_chart` 工具。 <br> 2. 工具执行 SQL 查询，获取销售数据。 <br> 3. 调用 `chart_service.generate_line_chart` 生成折线图 (PNG)。 | **文本输出:** 应包含类似 "已生成 LED 显示屏 的销售趋势图表，路径为: /home/ubuntu/zmproject/ai_applications/kb_qa_mvp/static/charts/sales_trend_LED显示屏.png。分析显示销售额平稳。" 的信息。 <br> **图表展示:** 在文本回答下方，应直接显示一张标题为 "LED 显示屏 销售趋势" 的折线图。 |
| **统计一下最近的订单数量并用柱状图展示** | 1. Agent 识别意图，调用 `analyze_sales_trend_with_chart` 或类似工具（取决于 Agent 决策）。 <br> 2. **如果 Agent 决策正确:** 成功生成并展示图表。 <br> 3. **如果 Agent 决策失败:** 可能会退回到 RAG 检索或 SQL 查询，但不会生成图表。 | **文本输出:** 成功时，应包含图表路径和分析结果。 <br> **图表展示:** 成功时，应显示生成的图表。 |

## 2. 查询数据库进行归因功能测试

此功能验证 Agent 是否能正确识别归因分析意图，调用增强后的归因工具，并实现**模拟数据分析**与**实时数据库查询**的结合。

| 测试用例 (输入问题) | 预期 Agent 动作 | 预期结果 (Streamlit UI) |
| :--- | :--- | :--- |
| **为什么最近三个月 LED 显示屏的毛利下降了？** | 1. Agent 识别意图，调用 `analyze_margin_attribution` 工具。 <br> 2. 工具读取 `attribution_data.json` 进行模拟分析。 <br> 3. 工具执行实时 SQL 查询 (`SELECT COUNT(*) ...`) 获取当前销售凭证数量。 | **文本输出:** 应返回一份详细的 **【LED 显示屏 归因分析报告】**，内容包括：<br> - 毛利变动情况（基于模拟数据）。<br> - 成本异常项分析（基于模拟数据）。<br> - **关键验证点:** 报告末尾应包含类似 "**实时业务关联：当前系统内共有 [一个数字] 条相关销售凭证记录。**" 的语句，证明工具成功连接并查询了数据库。 |
| **分析一下产品线 A 的成本波动原因** | 1. Agent 识别意图，调用 `analyze_margin_attribution` 工具。 <br> 2. 工具尝试查找 "产品线 A" 的模拟数据。 <br> 3. 工具执行实时 SQL 查询。 | **文本输出:** 如果模拟数据中没有 "产品线 A" 的数据，则返回 "未找到产品线 A 的毛利趋势数据。" 但仍应尝试执行数据库查询，并可能在日志中显示查询结果。 |

... (内容过长，已截断)
```

## 📄 50. dt 分区新增 + 叶子节点标识逻辑变更
**File**: `共享文档/知识库/knowledges/history/implementation_plan_20260302.md` | **Type**: 文档
**Preview**: 1. `dwd_co_customize_material_unit_cost_df` 和 `dws_co_customize_product_predict_cost_df` 需要新增 `dt` 日期分区字段。 2. `dwd_定制-产品单位成本计算.csv` 需求变更：叶子节点 `leaf_fl...

```
# dt 分区新增 + 叶子节点标识逻辑变更

## 背景

1. `dwd_co_customize_material_unit_cost_df` 和 `dws_co_customize_product_predict_cost_df` 需要新增 `dt` 日期分区字段。
2. `dwd_定制-产品单位成本计算.csv` 需求变更：叶子节点 `leaf_flag` 改为 PLM 提供，`1`=叶子节点，`0`=非叶子节点。

## 分析结论

| 层级 | 文件 | 现状 | 变更 |
|------|------|------|------|
| DWD BOM | `dwd_co_customize_quotation_bom_df_ddl.sql` | 有 `leaf_flag` 字段 | **无需修改** |
| DWD BOM | `dwd_co_customize_quotation_bom_df.sql` | 直接从PLM源传递 `leaf_flag` | **无需修改** |
| DWD BOM | `dwd_co_customize_quotation_bom_df_readme.md` | 描述正确 | **更新 leaf_flag 说明** |
| DWD 成本 | `dwd_co_customize_material_unit_cost_df_ddl.sql` | 缺少 `dt` 字段 | **添加 `dt` 字段+分区** |
| DWD 成本 | `dwd_co_customize_material_unit_cost_df.py` | `leaf_flag='1'` 判断正确，缺少 `dt` | **添加 `dt=当日` 写入逻辑** |
| DWD 成本 | `dwd_co_customize_material_unit_cost_df_readme.md` | 无 dt 描述 | **更新说明** |
| DWS | `dws_co_customize_product_predict_cost_df_ddl.sql` | 有 `dt` 列但无分区 | **改为 PARTITION BY RANGE** |
| DWS | `dws_co_customize_product_predict_cost_df.sql` | INSERT 列表无 `dt` | **添加 `dt` 字段** |
| DWS | `dws_co_customize_product_predict_cost_df_readme.md` | 无 dt 描述 | **更新说明** |
| DM | `dm_co_max_customize_product_predict_cost_df_ddl.sql` | 已有 dt 分区 ✅ | **无需修改** |
| DM | `dm_co_max_customize_product_predict_cost_df.sql` | 已有 `dt` ✅ | **无需修改** |
| DM | `dm_co_max_customize_product_predict_cost_df_readme.md` | 无 dt 描述 | **更新说明** |

## 变更详情

### DWD 成本 DDL - 添加 dt 分区

#### [MODIFY] [dwd_co_customize_material_unit_cost_df_ddl.sql](file:///D:/zmproject/model_project/src/dwd/dwd_co_customize_material_unit_cost_df_ddl.sql)

... (内容过长，已截断)
```

## 📄 51. dwd_fin_expense_bud_detail_df
**File**: `model_project/src/test/dwd/dwd_fin_expense_bud_detail_df_readme.md` | **Type**: 文档
**Preview**: **中文名**：dwd_销服预算费用-明细表 **用途**：将 BPC 费用预算数据与费用分摊范围配置表打标，输出年度/年月/版本、组织/科目/项目、归属域与分摊粒度、国内国际/区域/省份战区、平台/直接费用等明细，供下游汇总使用。 | 来源系统 | 表名 | 说明 | |----------|--...

```
# dwd_fin_expense_bud_detail_df

## 表说明

**中文名**：dwd_销服预算费用-明细表  
**用途**：将 BPC 费用预算数据与费用分摊范围配置表打标，输出年度/年月/版本、组织/科目/项目、归属域与分摊粒度、国内国际/区域/省份战区、平台/直接费用等明细，供下游汇总使用。

## 数据来源

| 来源系统 | 表名 | 说明 |
|----------|------|------|
| BPC | ods_sap_bpc_zhone_get_model_data_02_u_002_b00_di | 费用预算查看（B0101），按成本中心/科目/项目/期间 |
| 填报 | ods_bi_fr_fee_alloc_scope_entry_df | fr_费用分摊范围配置表，是否预算、分摊粒度、国内国际、区域、省份战区、费用类型 |
| 数仓 | dim_account_info_df | 科目维，限制 account_type_code='08'（费用科目） |
| 数仓 | dim_entity_info_mf | 实体维表，成本中心描述、版本化取对应年/全局最新 ym |
| BPC | ods_sap_bpc_zhone_get_dimension_attribute_u_project_df | 预算项目维，项目名称 |
| 数仓 | dim_sales_area_info_df | 销售大区，区域名称 |
| 数仓 | dim_sales_unit_info_df | 销售战区，省份/战区名称 |

## 模型逻辑概述

- **a 表**：BPC 费用预算，筛选 `signeddata <> 0` 且 `u_project = 'NOPROJECT'`；`u_time` 转为 `ym`，年度取 `yr=LEFT(ym,4)`。
- **a inner join c**：先按文档口径关联科目维 `dim_account_info_df`，条件 `SUBSTRING(a.u_account, 2) = c.account_code AND c.account_type_code = '08'`，仅保留费用科目。
- **a left join b**：按版本对应最新年月关联 `ods_bi_fr_fee_alloc_scope_entry_df`。条件为：
  - `b.ym` = 版本对应最新年月（V1：按年度最新 ym；V2：全局最新 ym）
  - `b.entity_code = a.u_entity`
  - `b.is_budget = 'Y'`
  - 若 `b.account_type` 非空，则取 BPC 原始科目编码 `a.u_account` 首位判断是否命中 `b.account_type`；命中后同步带出 `belong_domain`、`alloc_granularity`
- **a left join d**：实体维 `dim_entity_info_mf` 按版本取 V1=年度最新 ym、V2=全局最新 ym；实体编码关联口径为 `SUBSTRING_INDEX(a.u_entity, '_', 1) = d.entity_raw_code`。
- **a left join 预算项目维**：`a.u_project = 预算项目维.id`，取项目名称。
- **a left join dim_销售大区**：按 `sales_area_code` 取区域名称，并按 `sales_region_code`补齐国内国际名称。

... (内容过长，已截断)
```

## 📄 52. 财务主题 - 个人学习笔记
**File**: `ai_learning/business_insights/financial_theme/README.md` | **Type**: 文档
**Preview**: 本目录记录我在学习洲明科技财务主题SQL模型过程中的深度分析、业务理解和学习心得。 | 模型 | 学习状态 | 深度分析 | 问题记录 | |-----|---------|---------|---------| | dwd_fin_actual_gross_profit_df (实际毛利模型) ...

```
# 财务主题 - 个人学习笔记

## 学习概览

本目录记录我在学习洲明科技财务主题SQL模型过程中的深度分析、业务理解和学习心得。

## 学习模型

### 收入成本类

| 模型 | 学习状态 | 深度分析 | 问题记录 |
|-----|---------|---------|---------|
| dwd_fin_actual_gross_profit_df (实际毛利模型) | ✅ 已完成 | [深度分析](gross_profit/gross_profit_deep_analysis.md) | [问题记录](gross_profit/gross_profit_questions.md) |
| dwd_fin_revenue_cost_df (标准收入成本模型) | ✅ 已完成 | [深度分析](revenue_cost/revenue_cost_deep_analysis.md) | - |

### 费用类

| 模型 | 学习状态 | 深度分析 | 问题记录 |
|-----|---------|---------|---------|
| dwd_fin_expense_detail_df (费用明细模型) | ✅ 已完成 | - | - |
| dws_fin_expense_budget_actual_analysis_df (费用预实分析) | ✅ 已完成 | [深度分析](expense_budget_actual/expense_budget_actual_deep_analysis.md) | - |

## 核心发现

### 发现1: 双口径设计

同一业务（收入成本）有两个模型：
- **实际毛利模型**: 财务导入视角，用于经营分析
- **标准收入成本模型**: 会计凭证视角，用于财务对账

**学习价值**: 理解不同用户群体的需求差异

### 发现2: 客户 0000106034 的特殊处理

该客户在多个模型中都有特殊处理：
- 实际毛利模型: 硬编码修改组织架构
- 标准收入成本模型: 只保留该客户，排除其他销售公司订单

**待确认**: 该客户的业务背景是什么？

### 发现3: 维度骨架解决断月问题

费用预实分析模型使用维度骨架(Spine)解决断月问题：
- 强制每个维度组合都有12个月数据
- 缺失月份填充0
- 保证累计计算连续

**学习价值**: 掌握时间序列数据处理的通用模式

## 学习方法论

### SQL反推5步法

```
Step 1: 读注释 → 了解业务背景
Step 2: 看来源 → 理解数据血缘
Step 3: 析条件 → 提炼业务规则
Step 4: 找特殊 → 识别硬编码
Step 5: 理口径 → 理解指标定义
```

[详细方法论](../methodology/sql_to_business_framework.md)

### 学习记录模板

每个模型的学习记录包含：
1. **深度分析**: 业务理解、数据血缘、关键发现
2. **问题记录**: 待确认问题、已解答问题
3. **学习收获**: 技术层面、业务层面、方法论层面
4. **关联学习**: 相关模型、相关主题

## 待学习主题

### 高优先级

- [ ] 费用明细模型的分摊逻辑
- [ ] 预算编制和调整流程
- [ ] 内部交易结算规则

### 中优先级

- [ ] 会计科目体系详解
- [ ] 汇率换算逻辑
- [ ] 组织架构层级设计

### 低优先级

... (内容过长，已截断)
```

## 📄 53. 📊 当前修改状态总结 - 2025-12-22
**File**: `aianswer/2025-12-22/current_status_checkpoint.md` | **Type**: 文档
**Preview**: **状态**：完成 - [x] DDL 中添加 `offering` 字段（第 4 列，replace_rule_code 之后） - [x] SQL 的 cost CTE 中添加 `offering` 字段 - [x] SQL 的 SELECT 中添加 `offering` 字段映射 **代码示例...

```
# 📊 当前修改状态总结 - 2025-12-22

## ✅ 已完成的修改

### 1. 新增 Offering 字段 ✅
**状态**：完成
- [x] DDL 中添加 `offering` 字段（第 4 列，replace_rule_code 之后）
- [x] SQL 的 cost CTE 中添加 `offering` 字段
- [x] SQL 的 SELECT 中添加 `offering` 字段映射

**代码示例**：
```sql
-- DDL
`offering` VARCHAR(100) NULL COMMENT '产品代码（Offering）',

-- CTE
offering,  -- 4. 产品代码（Offering）

-- SELECT
COALESCE(cost.offering, '') AS offering,  -- 4. 产品代码（Offering）
```

---

### 2. 实现委外加工费 ✅
**状态**：完成
- [x] DDL 中更新 `subcon_max_amt` 注释（委外最高金额合计（物料委外））
- [x] SQL 中将 `subcon_max_amt` 从 NULL 改为 `max_product_manu_fee`

**代码示例**：
```sql
-- DDL
`subcon_max_amt` DECIMAL(27,8) NULL COMMENT '最高价委外加工费',

-- SELECT
COALESCE(cost.max_product_manu_fee, 0) AS subcon_max_amt,  -- 21. 最高价委外加工费
```

**数据来源**：成本表的 `max_product_manu_fee` 字段

---

### 3. 表结构调整 ✅
**状态**：完成
- [x] 字段总数从 26 列增加到 27 列
- [x] 所有列的序号注释已更新
- [x] DDL 和 SQL 的列顺序一致

**新的字段顺序**：
```
1.  pci_code
2.  pci_bom_code
3.  replace_rule_code
4.  offering              ← 新增
5.  pci_name
...
21. subcon_max_amt        ← 改为实现加工费
22. max_est_cost
...
27. insert_dt
```

---

## ❓ 还需要确认的问题

### 问题 1：供货比例来源逻辑 🔴
**当前状态**：未改动
- 仍然从成本表获取 `supply_ratio`
- 参数表的逻辑未采用

**需要确认**：
- [ ] 是否应该从参数表获取 supply_ratio？
- [ ] 参数表是否需要重新设计（添加 pci_bom_code, calc_month）？
- [ ] 还是保持现有逻辑（从成本表获取）？

### 问题 2：其他加工费字段 🟡
**当前实现**：仅 `max_product_manu_fee`（最高价）

**可选需求**：
- [ ] 是否需要添加其他 4 种价格的加工费？
  - min_product_manu_fee（最低价）
  - latest_product_manu_fee（最近价）
  - s_product_manu_fee（S价）
  - v_product_manu_fee（V价）
- [ ] 如果需要，是否：
  - A. 新增多个字段到表中？

... (内容过长，已截断)
```

## 📄 54. 实际毛利模型 - 问题记录
**File**: `ai_learning/business_insights/financial_theme/gross_profit/gross_profit_questions.md` | **Type**: 文档
**Preview**: **问题描述**: SQL中发现对客户 0000106034 有硬编码处理，强制指定销售组织/部门/销售组。 **疑问**: 1. 这个客户是什么背景？为什么需要特殊处理？ 2. 是SAP主数据录入错误，还是特殊业务场景？ 3. 是否可以推动业务部门修正源头数据？ **跟进状态**: ⬜ 待确认 *...

```
# 实际毛利模型 - 问题记录

## 待确认问题

### 问题1: 客户 0000106034 的背景

**问题描述**:
SQL中发现对客户 0000106034 有硬编码处理，强制指定销售组织/部门/销售组。

**疑问**:
1. 这个客户是什么背景？为什么需要特殊处理？
2. 是SAP主数据录入错误，还是特殊业务场景？
3. 是否可以推动业务部门修正源头数据？

**跟进状态**: ⬜ 待确认

**可能答案推测**:
- 历史遗留客户，SAP主数据未清理
- 关联交易客户，需要单独标识
- 组织架构变更导致的历史数据问题

---

### 问题2: 产品线映射规则的变更频率

**问题描述**:
产品线通过映射表 `ods_bi_fr_product_line_mapping_df` 维护，区分ZM01/ZM02。

**疑问**:
1. 产品线映射规则多久变更一次？
2. 历史数据如何追溯？是否需要时点查询？
3. 映射失效后，历史数据是否重新计算？

**跟进状态**: ⬜ 待确认

**影响分析**:
- 如果频繁变更，需要设计版本控制
- 如果历史追溯，需要生失效日期
- 目前使用 `invalid_flag = 'N'`，可能不支持历史追溯

---

### 问题3: 财务导入数据的时效性

**问题描述**:
模型依赖财务导入表 `ods_bi_fr_income_gross_profit_import_df`。

**疑问**:
1. 财务数据是T+几导入？
2. 导入是自动还是手工？
3. 如果导入延迟，如何影响下游报表？

**跟进状态**: ⬜ 待确认

---

### 问题4: 业务员跨部门变动的处理

**问题描述**:
业务员信息从VBPA和PA0002获取，但人员可能跨部门变动。

**疑问**:
1. 人员跨部门变动时，历史订单的业绩如何归属？
2. 是按订单创建时的部门，还是按查询时的部门？
3. 是否有人员变动历史表？

**跟进状态**: ⬜ 待确认

**相关发现**:
- 发现 `ods_bi_fr_emp_dept_change_df` 表，可能是处理人员变动的
- 需要进一步分析该表的使用逻辑

---

### 问题5: EHR工号生成规则

**问题描述**:
SQL中工号生成逻辑：`COALESCE(p2.rufnm, CONCAT('U', RIGHT(vbpa.pernr, 7)))`

**疑问**:
1. 为什么有些员工没有rufnm？
2. U+后7位的规则是业务要求吗？
3. 这种生成方式是否唯一？

**跟进状态**: ⬜ 待确认

---

## 已解答问题

### 问题: 为什么照明渠道直接标记，不走映射表？

**答案**:
照明是特殊业务线，渠道编码20-25直接标记为"照明"，不通过映射表。

**业务原因**:
- 照明业务有独立的渠道体系
- 需要快速识别照明业务
- 避免映射表过于复杂

**解答日期**: 2026-03-24

---

## 疑问澄清记录

### 澄清1: 财务数据 vs SAP订单数据的关系

**原始疑问**: 财务导入表和SAP订单表是什么关系？

**澄清结果**:
- 财务导入表: 财务核算的实际入账数据
- SAP订单表: 销售订单的基础信息
- 关联目的: 为财务数据补充业务维度

**澄清日期**: 2026-03-24

---

## 后续跟进计划

| 序号 | 问题 | 跟进方式 | 计划时间 |
|-----|------|---------|---------|

... (内容过长，已截断)
```

## 📄 55. 检查结果速查表
**File**: `aianswer/2025-12-11/quick_reference.md` | **Type**: 文档
**Preview**: | 检查项 | 结果 | 详情 | |-------|------|------| | 字段完整性 | ✅ 29/29 | 所有29个字段完全符合需求 | | 单位换算 | ✅✅✅ | 3级降级方案完美实现 | | 委外金额 | ✅✅✅ | 0级行选择性关联，设计精妙 | | 替代料标志 | ✅ |...

```
# 检查结果速查表

## dwd_co_quotation_bom_df（报价BOM生成）

### ✅ 符合情况
| 检查项 | 结果 | 详情 |
|-------|------|------|
| 字段完整性 | ✅ 29/29 | 所有29个字段完全符合需求 |
| 单位换算 | ✅✅✅ | 3级降级方案完美实现 |
| 委外金额 | ✅✅✅ | 0级行选择性关联，设计精妙 |
| 替代料标志 | ✅ | 逻辑正确 |
| 基础物料标志 | ✅ | 按工厂隔离，强化设计 |
| 维表关联 | ✅ | 产品维表、三级分类都正确 |
| 数据质量处理 | ✅ | COALESCE兜底、过滤完善 |

### ❌ 需要修正
| 问题 | 类型 | 优先级 | 修正方案 |
|------|------|--------|---------|
| 缺少MANDT='800' | 硬性规则违反 | 🔴 第1优先 | 在2处SAP表关联添加mandt='800'条件 |
| 工厂不一致 | 数据治理问题 | 🔴 第2优先 | 业务确认B010/1010与werks='2020'映射 |

---

## dwd_co_bottom_bom_df（单层BOM替换明细）

### ✅ 符合情况
| 检查项 | 结果 | 详情 |
|-------|------|------|
| 业务筛选条件 | ✅✅✅ | (base_mat_flag='Y' OR bom_level='0') ✓ |
| 字段完整性 | ✅ 20/20 | 所有20个字段完全符合需求 |
| 关联条件 | ✅ | LEFT JOIN逻辑正确 |
| 替代物料处理 | ✅✅✅ | 替代逻辑+原始物料标志完善 |
| 数量聚合 | ✅✅✅ | SUM(amount_count)正确 |
| 金额聚合 | ✅✅ | SUM(subcon_max_amt)正确 |
| 防膨胀机制 | ✅ | GROUP BY严格按业务主键 |
| 代码规范 | ✅ | SQL编码规范符合 |

### ⚠️ 建议补充
| 项目 | 类型 | 建议 |
|------|------|------|
| 临时表管理 | 架构配置 | 补充dwd_tmp_alt_mapping生命周期说明 |
| 工作流参数 | 参数配置 | 确认参数定义和默认值 |

---

## 📊 综合评估

### dwd_co_quotation_bom_df
```
规范符合度：90%  (95%满分，扣除MANDT缺失)
需求符合度：90%  (95%满分，扣除工厂数据问题)
上线状态：  条件性 (需修正MANDT+业务确认工厂)
```

### dwd_co_bottom_bom_df
```
规范符合度：95%  (关键修正已完成)
需求符合度：95%  (所有需求字段完全符合)
上线状态：  基本可以 (补充架构文档即可)
```

---

## 🎯 立即行动清单

### 必须修正（今天）
1. [ ] 添加MANDT='800'到dwd_co_quotation_bom_df的2处SAP表关联
   - 位置1：sap_unit_conversion CTE的WHERE子句
   - 位置2：subcon_price_calculation CTE的LEFT JOIN ON子句

### 需要确认（1-2天）
2. [ ] 业务确认：B010/1010与werks='2020'的对应关系
3. [ ] SAP确认：采购价格表是否需要补充多工厂数据

... (内容过长，已截断)
```

## 📄 56. 项目周报任务清单
**File**: `aianswer/2025-12-17/项目周报任务清单_20251212.md` | **Type**: 文档
**Preview**: **周报日期**: 20251212 **导出时间**: 2025-12-17 17:01:17 **任务总数**: 28 条 - **其他**: 28 条任务 | 编号 | 任务名称 | 本周工作总结 | 本周工作目标 | 完成状态 | |------|---------|------------...

```
# 项目周报任务清单

**周报日期**: 20251212  
**导出时间**: 2025-12-17 17:01:17  
**任务总数**: 28 条  

## 任务分类统计

- **其他**: 28 条任务

---

## 任务明细

### 其他

| 编号 | 任务名称 | 本周工作总结 | 本周工作目标 | 完成状态 |
|------|---------|------------|------------|----------|
| 1 | 蓝图方案 | 蓝图方案确认签核 | 完成 | 进行 |
| 2 | 功能设计-HR主数据 | 虚拟组织方案设计 | 完成 | 完成 |
| 3 | 功能设计-基准价测算 | 标品-模型更新-事实表：产品单位成本计算 | 完成 | 完成 |
| 4 | 详细方案设计-指标分析 | 周报整体方案汇报 | 完成 | 完成 |
| 5 | 开发任务-主数据 | 主数据管理组织模型设计及维护 | 进行 | 完成 |
| 6 | 开发任务-基准价测算 | 已确认的数据源同步 | 进行 | 进行 |
| 7 | 开发任务-指标 | 已确认的数据源同步 | 进行 | 进行 |
| 8 | 工作事项 | 下周工作计划 | 目标 | 当前状态 |
| 9 | 蓝图方案 | 蓝图方案确认签核 |  |  |
| 10 | 功能设计-HR主数据 | 用户账号数据清洗梳理核对 | 进行 | 进行 |
| 11 | 功能设计-基准价测算 | 标品-模型更新-事实表：产品测算成本计算 | 完成 | 进行 |
| 12 | 详细方案设计-指标分析 | 报表设计：接单/出货/收入目标录入表 | 完成 | 进行 |
| 13 | 开发任务-主数据 | 已确认的数据源同步 | 进行 | 进行 |
| 14 | 开发任务-基准价测算 | 已确认的数据源同步 | 进行 | 进行 |
| 15 | 开发任务-指标 | 已确认的数据源同步 | 进行 | 进行 |
| 16 | 主题事项 | 描述 | 责任人 | 期望解决时间 |
| 17 | HR主数据-方案设计 | 洲明后续主数据管理组织人员确认 | 秦丽宏&吴娜 | 2025.12.5 |
| 18 | HR主数据-方案设计 | 系统账号数据清理 | 吴娜&熊生压 | 2025.12.17 |
| 19 | 基准价测算-开发细节 | 以下内容待沟通确认：
委外、外购的产品要如何区分 | 吴娜、万庚、研发同事 | 2025.12.15 |
| 20 | 指标分析 | CRM与SAP梳理订单信息对接字段，如行业类型、产品领域等字段的明确定义和字段对应关系，梳理SAP对接改造点 | CRM
熊生压、林佳鸿 | 2025.12.19 |
| 21 | 指标分析 | CRM与SAP确认业绩拆分后数据传输方式，梳理SAP对接改造点 | CRM
熊生压、林佳鸿 | 2025.12.19 |
| 22 | 指标分析 | CRM与SAP确认【提前备料订单】标签与业绩统计所需信息的传输方式。 | CRM
熊生压、林佳鸿 | 2025.12.19 |
| 23 | 主题事项 | 问题详述及影响 | 建议解决方案 | 责任人 |
| 24 | 开发任务安排 | 指标主题域范围扩大，需额外时间梳理框架和指标体系。 | 分批次确认需求，同时尽可能收敛控制需求范围 | 秦丽宏、王群斌、吴娜、万庚、孙拓 |
| 25 | 项目总体方案设计 | 总体方案签字确认延迟，项目开发实施不可控性和回款风险性增大 | 基于目前部分较明确的指标优先进行梳理和开发；同步推进指标签字确认事项 | 秦丽宏、王群斌、吴娜、万庚、孙拓 |

... (内容过长，已截断)
```

## 📄 57. dwd_fin_expense_bud_detail_df
**File**: `model_project/src/prod/dwd/dwd_fin_expense_bud_detail_df_readme.md` | **Type**: 文档
**Preview**: **中文名**：dwd_销服预算费用-明细表 **用途**：将 BPC 费用预算数据与费用分摊范围配置表打标，输出年度/年月/版本、组织/科目/项目、归属域与分摊粒度、国内国际/区域/省份战区、平台/直接费用等明细，供下游汇总使用。 - 2026-04-10：新增字段 `fee_subject_l1...

```
# dwd_fin_expense_bud_detail_df

## 表说明

**中文名**：dwd_销服预算费用-明细表  
**用途**：将 BPC 费用预算数据与费用分摊范围配置表打标，输出年度/年月/版本、组织/科目/项目、归属域与分摊粒度、国内国际/区域/省份战区、平台/直接费用等明细，供下游汇总使用。

## 变更记录

- 2026-04-10：新增字段 `fee_subject_l1_2_sales`（费用科目1.5级-销服），取值与 `fee_subject_l1_sales` 保持一致。

## 数据来源

| 来源系统 | 表名 | 说明 |
|----------|------|------|
| BPC | ods_sap_bpc_zhone_get_model_data_02_u_002_b00_di | 费用预算查看（B0101），按成本中心/科目/项目/期间 |
| 填报 | ods_bi_fr_fee_alloc_scope_entry_df | fr_费用分摊范围配置表，是否预算、分摊粒度、国内国际、区域、省份战区、费用类型 |
| 数仓 | dim_account_info_df | 科目维，限制 account_type_code='08'（费用科目） |
| 数仓 | dim_entity_info_mf | 实体维表，成本中心描述、版本化取对应年/全局最新 ym |
| BPC | ods_sap_bpc_zhone_get_dimension_attribute_u_project_df | 预算项目维，项目名称 |
| 数仓 | dim_sales_area_info_df | 销售大区，区域名称 |
| 数仓 | dim_sales_unit_info_df | 销售战区，省份/战区名称 |

## 模型逻辑概述

- **a 表**：BPC 费用预算，筛选 `signeddata <> 0` 且 `u_project = 'NOPROJECT'`；`u_time` 转为 `ym`，年度取 `yr=LEFT(ym,4)`。
- **a inner join c**：先按文档口径关联科目维 `dim_account_info_df`，条件 `SUBSTRING(a.u_account, 2) = c.account_code AND c.account_type_code = '08'`，仅保留费用科目。
- **a left join b**：按版本对应最新年月关联 `ods_bi_fr_fee_alloc_scope_entry_df`。条件为：
  - `b.ym` = 版本对应最新年月（V1：按年度最新 ym；V2：全局最新 ym）
  - `b.entity_code = a.u_entity`
  - `b.is_budget = 'Y'`
  - 若 `b.account_type` 非空，则取 BPC 原始科目编码 `a.u_account` 首位判断是否命中 `b.account_type`；命中后同步带出 `belong_domain`、`alloc_granularity`
- **a left join d**：实体维 `dim_entity_info_mf` 按版本取 V1=年度最新 ym、V2=全局最新 ym；实体编码关联口径为 `SUBSTRING_INDEX(a.u_entity, '_', 1) = d.entity_raw_code`。
- **a left join 预算项目维**：`a.u_project = 预算项目维.id`，取项目名称。

... (内容过长，已截断)
```

## 📄 58. DWD Order Detail Model Validation Report
**File**: `model_project/src/test/dwd/dwd_sd_order_detail_df_readme.md` | **Type**: 文档
**Preview**: This section compares the SQL implementation against the requirements in `模型设计清单-技术开发.xlsx` (Sheet: `dwd_订单明细模型`). | Field | Design Logic | Current SQ...

```
# DWD Order Detail Model Validation Report

## 1. Design Consistency Check

This section compares the SQL implementation against the requirements in `模型设计清单-技术开发.xlsx` (Sheet: `dwd_订单明细模型`).

| Field | Design Logic | Current SQL Implementation | Status | Recommendation |
| :--- | :--- | :--- | :--- | :--- |
| **`newest_date`**<br>(订单最新日期) | 1. `ZB2B`/`ZMRE` → `create_date`<br>2. `ZMCE`/`ZMDR` → `invoice_header_date`<br>3. Other → **`approval_date`** (if null then `create_date`) | 1. `ZMCE`/`ZMDR` → `invoice_header_date`<br>2. Other → **`create_date`**<br>*(Misses approval_date logic)* | ❌ **Mismatch** | Update SQL to prioritize `approval_date` for standard orders. |
| **`contract_need_date`**<br>(合同需求日期) | `newest_date` + `contract_need_days` | **`create_date`** + `contract_need_days` | ❌ **Mismatch** | Update logic to use `newest_date` as the base. |
| **`pmc_review_del_date`**<br>(PMC评审交期) | Logic depends on `newest_date` | Logic depends on **`create_date`** | ❌ **Mismatch** | Update logic to use `newest_date` as the base. |
| **`need_accept_flag`**<br>(是否需要验收) | If `ZSFYS` = '是' THEN 'Y' ELSE 'N' | If `ZSFYS` = '否' THEN 'N' ELSE 'Y' | ❌ **Logic Inverted** | Change to `CASE WHEN zf.need_accept_flag = '是' THEN 'Y' ELSE 'N' END`. |
| **Mapping Table Schema** | Referenced as `ods` in design context | Referenced as **`test`** in SQL code | ❌ **Schema Error** | Change `test.ods_fr_product_line_mapping_df` to `ods.ods_bi_fr_product_line_mapping_df`. |
| **`piz_line_name`**<br>(业务产品线) | 优先渠道20-25为'照明'，其次区域映射 | 仅进行区域映射 | ❌ **Mismatch** | Added priority check for channel 20-25. |

... (内容过长，已截断)
```

## 📄 59. SQL 反推业务分析检查清单
**File**: `ai_applications/kb_qa_mvp/knowledge_base/methodology/sql_analysis_checklist.md` | **Type**: 文档
**Preview**: - [ ] 确认模型设计文档位置 - [ ] 获取模型对应的SQL文件 - [ ] 了解模型的业务背景（从注释、文档获取） - [ ] 表名、中文名是否清晰 - [ ] 模型层级（ODS/DWD/DWS/DM） - [ ] 更新方式（全量/增量） - [ ] 作者、日期、版本历史 **输出**: 模...

```
# SQL 反推业务分析检查清单

## 分析前准备

- [ ] 确认模型设计文档位置
- [ ] 获取模型对应的SQL文件
- [ ] 了解模型的业务背景（从注释、文档获取）

## 分析流程

### Step 1: 读注释

- [ ] 表名、中文名是否清晰
- [ ] 模型层级（ODS/DWD/DWS/DM）
- [ ] 更新方式（全量/增量）
- [ ] 作者、日期、版本历史

**输出**: 模型基本信息记录

---

### Step 2: 看来源

- [ ] 主表是什么？业务含义？
- [ ] 关联了哪些表？关联关系？
- [ ] 数据来源系统？（SAP/BI/CRM等）
- [ ] 数据粒度？（订单级/明细级/汇总级）

**输出**: 数据血缘图

---

### Step 3: 析条件

- [ ] WHERE 条件有哪些？
- [ ] 业务过滤逻辑？
- [ ] 数据范围限定？
- [ ] 异常数据处理？

**输出**: 业务规则列表

---

### Step 4: 找特殊

- [ ] 是否有硬编码？（CASE WHEN 固定值）
- [ ] 是否有特殊处理？（特定客户/特定场景）
- [ ] 是否有数据修正？（NULL处理、空格清洗）
- [ ] 是否有临时方案？（TODO、FIXME标记）

**输出**: 特殊处理清单及原因分析

---

### Step 5: 理口径

- [ ] 关键指标有哪些？
- [ ] 指标计算公式？
- [ ] 统计维度？
- [ ] 时间口径？

**输出**: 指标口径定义

---

## 深度分析清单

### 数据质量分析

- [ ] NULL值如何处理？
- [ ] 空字符串如何清洗？
- [ ] 编码是否统一？（大小写、全半角）
- [ ] 重复数据如何处理？

### 业务规则分析

- [ ] 业务过滤条件的原因是什么？
- [ ] 映射规则的优先级设计？
- [ ] 默认/兜底规则是什么？
- [ ] 特殊场景如何处理？

### 组织架构分析

- [ ] 组织架构的层级关系？
- [ ] 历史变更如何处理？
- [ ] 人员变动如何处理？
- [ ] 部门归属如何判定？

### 口径一致性分析

- [ ] 与相关模型的口径是否一致？
- [ ] 财务口径 vs 业务口径的差异？
- [ ] 时间口径是否统一？
- [ ] 金额口径（含税/不含税）？

---

## 输出物检查

### 业务定义文档

- [ ] 模型基本信息完整
- [ ] 业务目的清晰
- [ ] 核心实体描述准确
- [ ] 业务规则结构化
- [ ] 数据血缘图清晰
- [ ] 关键指标定义完整

### SQL模式文档

- [ ] CTE分层模式提炼
- [ ] 特殊处理模式识别
- [ ] 映射规则模式总结
- [ ] 关联模式归纳
- [ ] 数据质量处理模式

### 个人学习笔记

- [ ] 深度分析记录
- [ ] 关键发现总结
- [ ] 疑问记录
- [ ] 学习收获
- [ ] 关联学习规划

---

## 常见模式识别

### 硬编码模式

```sql
-- 识别特征
CASE WHEN 特定条件 THEN '固定值' ELSE ... END

-- 业务含义
数据质量问题 / 历史遗留问题 / 特殊业务场景
```

### 映射表模式

```sql
-- 识别特征
LEFT JOIN mapping_table ON ... AND mapping_table.isvalid = 'Y'

... (内容过长，已截断)
```

## 📄 60. ✅ 外协表字段修复完成
**File**: `aianswer/2025-12-22/external_purchase_table_field_fix.md` | **Type**: 文档
**Preview**: **错误的字段名**： ```sql max_outbound_cost, min_outbound_cost, latest_outbound_cost, s_outbound_cost, v_outbound_cost ``` **实际存在的字段名**： ```sql max_pur_cost,...

```
# ✅ 外协表字段修复完成

## 📋 问题汇总

### 问题1：外协表字段名称不匹配
**错误的字段名**：
```sql
max_outbound_cost, min_outbound_cost, latest_outbound_cost, 
s_outbound_cost, v_outbound_cost
```

**实际存在的字段名**：
```sql
max_pur_cost, min_pur_cost, latest_pur_cost, 
s_pur_cost, v_pur_cost
```

## ✅ 修复方案

已更新 SQL 文件中的 `wx` CTE，使用正确的字段名称并通过别名映射：

```sql
wx AS (
    SELECT
        pci_bom_code,              -- 关联键
        COALESCE(max_pur_cost, 0) AS max_outbound_cost,           -- ✅ 正确
        COALESCE(min_pur_cost, 0) AS min_outbound_cost,           -- ✅ 正确
        COALESCE(latest_pur_cost, 0) AS latest_outbound_cost,     -- ✅ 正确
        COALESCE(s_pur_cost, 0) AS s_outbound_cost,               -- ✅ 正确
        COALESCE(v_pur_cost, 0) AS v_outbound_cost                -- ✅ 正确
    FROM
        dwd.dwd_co_external_purchase_product_df
    WHERE
        pci_bom_code IS NOT NULL
)
```

## 📊 字段验证结果

### 外协表字段映射
| 源表字段 | 别名字段 | 数据样本 | 状态 |
|---------|---------|---------|------|
| max_pur_cost | max_outbound_cost | 0E-8 ~ 0.xx | ✅ |
| min_pur_cost | min_outbound_cost | 0E-8 ~ 0.xx | ✅ |
| latest_pur_cost | latest_outbound_cost | 0E-8 ~ 0.xx | ✅ |
| s_pur_cost | s_outbound_cost | 0E-8 ~ 0.xx | ✅ |
| v_pur_cost | v_outbound_cost | 0E-8 ~ 0.xx | ✅ |
| pci_bom_code | pci_bom_code | CIP-xxx, CVP-xxx | ✅ |

### 成本表字段

成本表中包含两套成本字段：

**第一套：源字段** (来自上游系统)
```
max_unit_mat_cost
min_unit_mat_cost
latest_unit_mat_cost
s_unit_mat_cost
v_unit_mat_cost
```

**第二套：映射字段** (已预处理)
```
max_product_est_cost
min_product_est_cost
latest_product_est_cost

... (内容过长，已截断)
```

## 📄 61. 飞书文档工具配置说明
**File**: `aianswer/2025-12-17/feishu_配置说明.md` | **Type**: 文档
**Preview**: 当前遇到的 **404 错误** 表明飞书 API 凭证无效或应用配置不正确。 ``` Trying: https://open.feishu.cn/open-api/auth/v3/tenant_access_token/internal Status: 404 Trying: https://o...

```
# 飞书文档工具配置说明

## 问题诊断

当前遇到的 **404 错误** 表明飞书 API 凭证无效或应用配置不正确。

### 错误信息
```
Trying: https://open.feishu.cn/open-api/auth/v3/tenant_access_token/internal
Status: 404
Trying: https://open.larksuite.com/open-api/auth/v3/tenant_access_token/internal
Status: 404
```

## 解决方案

### 方案1: 使用有效的飞书企业自建应用凭证

1. **访问飞书开放平台**
   - 国内版: https://open.feishu.cn/
   - 国际版: https://open.larksuite.com/

2. **创建企业自建应用**
   - 登录飞书开放平台
   - 进入【开发者后台】
   - 点击【创建企业自建应用】
   - 填写应用名称和描述

3. **获取凭证**
   - 在应用详情页面找到：
     - **App ID** (应用ID)
     - **App Secret** (应用密钥)
   - 复制这两个值

4. **配置权限**
   
   必须为应用开通以下权限：
   
   **云文档权限**:
   - `docx:document` - 查看、评论和编辑文档
   - `docx:document:readonly` - 查看文档（只读）
   
   **多维表格权限**（如果需要）:
   - `bitable:app` - 查看、评论和编辑多维表格
   - `bitable:app:readonly` - 查看多维表格（只读）

5. **更新代码中的凭证**
   
   修改 `tools/feishu.py` 中的配置：
   ```python
   APP_ID = "你的真实App ID"
   APP_SECRET = "你的真实App Secret"
   ```

6. **将文档分享给应用**
   
   在飞书文档中：
   - 打开目标文档
   - 点击右上角【分享】
   - 添加你创建的应用为协作者
   - 授予【可阅读】或【可编辑】权限

---

### 方案2: 使用已有的 feishu_export.py 工具 ✅

**如果无法获取有效的 API 凭证**，建议使用已经成功运行的 `feishu_export.py` 工具：

#### 特点
- ✅ 无需 API 凭证
- ✅ 已验证可用
- ✅ 支持从本地 Excel 导出

#### 使用方法
```powershell
python tools/feishu_export.py
```

#### 生成文件
1. **Markdown 格式**: `项目周报任务清单_20251212.md`
2. **CSV 格式**: `项目周报任务清单_20251212.csv`
3. **飞书导入格式**: `项目周报任务清单_20251212_飞书导入.csv`

#### 导入到飞书
1. 打开飞书多维表格
2. 点击【导入】按钮
3. 选择【从 CSV 文件导入】
4. 上传 `项目周报任务清单_20251212_飞书导入.csv`
5. 映射字段并确认导入

---

### 方案3: 检查文档ID格式

您的文档链接: `https://ycnji7ld7p2q.feishu.cn/docx/EywEdzPLFoDQSzxyu2Vc80T0nCV`

... (内容过长，已截断)
```

## 📄 62. dwd_sd_shipment_detail_df (dwd_出货明细模型)
**File**: `model_project/src/test/dwd/dwd_sd_shipment_detail_df.md` | **Type**: 文档
**Preview**: - **2026-02-03 (Agent)**: - **架构调整**: 采用 "Innermost Union" 策略，将 "实物交货单" (LIPS) 与 "虚拟交货单" (无交货单) 在基础层 `base_shipment` 进行合并。 - **新增逻辑**: 增加 `virtual_shi...

```
# dwd_sd_shipment_detail_df (dwd_出货明细模型)

## 1. 变更记录
- **2026-02-03 (Agent)**:  
  - **架构调整**: 采用 "Innermost Union" 策略，将 "实物交货单" (LIPS) 与 "虚拟交货单" (无交货单) 在基础层 `base_shipment` 进行合并。
  - **新增逻辑**: 增加 `virtual_shipment_base` CTE，从 `dwd_sd_order_detail_df` 获取无交货单订单数据作为虚拟出货记录。
  - **字段修正**: 
    - 虚拟出货数量取 `ABS(order_qty)`，后续统一根据订单类型 (ZMCE/ZMRE) 处理正负号。
    - 虚拟出货日期取自 `invoice_post_date` (开票日期)。
    - 场景标签 `scenario_tag` 调整为 'I-借贷' 标识。
  - **范围扩展**: 虚拟交货订单类型扩展为 `ZMCE`, `ZMDR`, `ZMRE`, `ZMHH`。
- **2026-02-03 (Agent)**:  
  - **验收逻辑更新**: 增加 `no_delivery_inspection` CTE，处理无交货单情况下的验收逻辑。
  - **字段新增**: 
    - `no_delivery_inspection_order_num`: 无交货单情况下的验收单号。
    - `no_delivery_inspection_invoice_date`: 无交货单情况下的验收开票日期。
  - **逻辑优化**: 
    - 验收判断逻辑：若【是否需要验收】=Y，关联上开票数据则为'Y'，否则为'N'。
    - 无交货单情况下，出货日期使用验收开票日期。
    - 开票数据筛选：排除过账状态为'E'和已取消的票据。
- **2026-02-05 (Agent)**:  
  - **开票日期逻辑修复**: 移除 `invoice_dates` CTE，不再使用 `MIN()` 函数获取最小开票日期。
  - **逻辑调整**: 无交货单情况下，直接使用 `no_delivery_inspection` CTE 中聚合的开票日期，与文档要求一致。
  - **字段更新**: `virtual_shipment_base` 中的 `shipment_date` 改为 NULL，后续由 `final_calculations` 统一处理。

## 2. 模型逻辑概述
本模型整合了实物交货（基于 SAP LIKP/LIPS）和虚拟交货（基于 SAP 订单），提供统一的出货明细视图。

### 核心处理流程
1.  **Invoice Dates**: 预先获取订单对应的最早开票日期。
2.  **Real Shipment**: 提取 LIPS/LIKP 实物交货数据，关联 VBAK/VBAP 筛选有效订单。
3.  **Virtual Shipment**: 
    - 来源: `dwd_sd_order_detail_df`
    - 筛选: 订单类型为 `ZMCE`, `ZMDR`, `ZMRE`, `ZMHH`; 订单状态正常; 无对应实物交货记录。
    - 逻辑: `delivery_order_num` 为空; `shipment_qty` 取订单数量绝对值; `shipment_date` 取开票日期。
4.  **Base Union**: 合并 Real 与 Virtual 数据。

... (内容过长，已截断)
```

## 📄 63. dwd_sd_shipment_detail_df (dwd_出货明细模型)
**File**: `model_project/src/prod/dwd/dwd_sd_shipment_detail_df.md` | **Type**: 文档
**Preview**: - **2026-02-03 (Agent)**: - **架构调整**: 采用 "Innermost Union" 策略，将 "实物交货单" (LIPS) 与 "虚拟交货单" (无交货单) 在基础层 `base_shipment` 进行合并。 - **新增逻辑**: 增加 `virtual_shi...

```
# dwd_sd_shipment_detail_df (dwd_出货明细模型)

## 1. 变更记录
- **2026-02-03 (Agent)**:  
  - **架构调整**: 采用 "Innermost Union" 策略，将 "实物交货单" (LIPS) 与 "虚拟交货单" (无交货单) 在基础层 `base_shipment` 进行合并。
  - **新增逻辑**: 增加 `virtual_shipment_base` CTE，从 `dwd_sd_order_detail_df` 获取无交货单订单数据作为虚拟出货记录。
  - **字段修正**: 
    - 虚拟出货数量取 `ABS(order_qty)`，后续统一根据订单类型 (ZMCE/ZMRE) 处理正负号。
    - 虚拟出货日期取自 `invoice_post_date` (开票日期)。
    - 场景标签 `scenario_tag` 调整为 'I-借贷' 标识。
  - **范围扩展**: 虚拟交货订单类型扩展为 `ZMCE`, `ZMDR`, `ZMRE`, `ZMHH`。
- **2026-02-03 (Agent)**:  
  - **验收逻辑更新**: 增加 `no_delivery_inspection` CTE，处理无交货单情况下的验收逻辑。
  - **字段新增**: 
    - `no_delivery_inspection_order_num`: 无交货单情况下的验收单号。
    - `no_delivery_inspection_invoice_date`: 无交货单情况下的验收开票日期。
  - **逻辑优化**: 
    - 验收判断逻辑：若【是否需要验收】=Y，关联上开票数据则为'Y'，否则为'N'。
    - 无交货单情况下，出货日期使用验收开票日期。
    - 开票数据筛选：排除过账状态为'E'和已取消的票据。
- **2026-02-05 (Agent)**:  
  - **开票日期逻辑修复**: 移除 `invoice_dates` CTE，不再使用 `MIN()` 函数获取最小开票日期。
  - **逻辑调整**: 无交货单情况下，直接使用 `no_delivery_inspection` CTE 中聚合的开票日期，与文档要求一致。
  - **字段更新**: `virtual_shipment_base` 中的 `shipment_date` 改为 NULL，后续由 `final_calculations` 统一处理。

## 2. 模型逻辑概述
本模型整合了实物交货（基于 SAP LIKP/LIPS）和虚拟交货（基于 SAP 订单），提供统一的出货明细视图。

### 核心处理流程
1.  **Invoice Dates**: 预先获取订单对应的最早开票日期。
2.  **Real Shipment**: 提取 LIPS/LIKP 实物交货数据，关联 VBAK/VBAP 筛选有效订单。
3.  **Virtual Shipment**: 
    - 来源: `dwd_sd_order_detail_df`
    - 筛选: 订单类型为 `ZMCE`, `ZMDR`, `ZMRE`, `ZMHH`; 订单状态正常; 无对应实物交货记录。
    - 逻辑: `delivery_order_num` 为空; `shipment_qty` 取订单数量绝对值; `shipment_date` 取开票日期。
4.  **Base Union**: 合并 Real 与 Virtual 数据。

... (内容过长，已截断)
```

## 📄 64. ZM AI 知识库 MVP 部署与测试指南 (跨平台)
**File**: `ai_applications/ZM AI 知识库 MVP 部署与测试指南 (跨平台).md` | **Type**: 文档
**Preview**: 本文档提供了在 **Windows** 和 **Linux** 操作系统上部署和测试优化后的 ZM AI 知识库 MVP 项目的详细步骤。 无论您使用 Windows 还是 Linux，都需要确保以下环境已安装： | 软件 | 推荐版本 | 备注 | | :--- | :--- | :--- | |...

```
# ZM AI 知识库 MVP 部署与测试指南 (跨平台)

本文档提供了在 **Windows** 和 **Linux** 操作系统上部署和测试优化后的 ZM AI 知识库 MVP 项目的详细步骤。

## 1. 环境准备

无论您使用 Windows 还是 Linux，都需要确保以下环境已安装：

| 软件 | 推荐版本 | 备注 |
| :--- | :--- | :--- |
| **Python** | 3.9+ | 建议使用虚拟环境进行项目隔离。 |
| **Git** | 最新稳定版 | 用于克隆项目仓库。 |
| **OpenAI API Key** | 有效密钥 | 用于 LLM 和 Embedding 服务。 |

## 2. 项目设置

### 2.1. 克隆仓库

```bash
# 克隆您的仓库
git clone https://github.com/eninem123/zmproject.git
cd zmproject/ai_applications/kb_qa_mvp
```

### 2.2. 创建并激活虚拟环境

**Windows (PowerShell/CMD):**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**Linux/macOS (Bash):**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2.3. 安装依赖

项目依赖已更新，请确保安装所有必要的库，包括用于图表生成的 `matplotlib` 和用于 StarRocks 适配的 `pymysql`。

```bash
pip install -r requirements.txt
```

## 3. 配置说明

### 3.1. 基础配置 (`.env`)

在项目根目录 (`kb_qa_mvp/`) 下找到 `.env` 文件，并配置您的 OpenAI API Key。

```ini
OPENAI_API_KEY="sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# 外部配置文件路径，用于切换到生产数据库
# 默认留空则使用样例库 (sr_cache)
EXTERNAL_CONFIG_PATH=
```

### 3.2. 数据库切换配置 (可选)

如果您需要切换到自定义数据库（例如 StarRocks），请执行以下步骤：

1.  创建外部配置文件，例如 `d:\zmproject\tools\config.py` (Windows) 或 `/home/ubuntu/zmproject/tools/config.py` (Linux)。
2.  在 `config.py` 中定义 `DB_CONFIG` 字典。

**StarRocks 配置示例 (`config.py`):**
```python
DB_CONFIG = {
    "type": "starrocks",
    "config": {
        "host": "your_starrocks_host",
        "port": 9030,
        "user": "your_user",
        "password": "your_password",
        "database": "your_db"
    }
}
```

3.  在 `.env` 文件中设置 `EXTERNAL_CONFIG_PATH` 指向该文件。

... (内容过长，已截断)
```

## 📄 65. 上下文加载器整理说明
**File**: `aianswer/2025-12-19/上下文加载器整理说明.md` | **Type**: 文档
**Preview**: 项目根目录存在两个上下文加载器： - `load_project_context.py` (50KB, 840行) - 完整版本，直接读取所有文档 - `load_context_light.py` (7KB, 214行) - 轻量版，基于知识库智能检索 存在混淆和维护问题，需要整理。 **文件**...

```
# 上下文加载器整理说明

## 📋 问题背景

项目根目录存在两个上下文加载器：
- `load_project_context.py` (50KB, 840行) - 完整版本，直接读取所有文档
- `load_context_light.py` (7KB, 214行) - 轻量版，基于知识库智能检索

存在混淆和维护问题，需要整理。

## ✅ 整理决策

### 保留生产版本
**文件**: `D:\zmproject\load_project_context.py`  
**理由**:
- ✅ 功能完整，经过充分测试验证
- ✅ readme.md 中明确推荐使用
- ✅ 最近更新（2025-12-18），持续维护中
- ✅ 已集成所有核心功能：
  - Excel 设计文档详细读取（104个页签）
  - 数据库数据字典备份（8817条记录）
  - AI 学习知识库加载（错误案例+教训总结+最佳实践）
  - SQL 脚本扫描和预览
  - StarRocks 语法规范加载

### 归档轻量版本
**原路径**: `D:\zmproject\load_context_light.py`  
**新路径**: `D:\zmproject\aianswer\2025-12-19\load_context_light.py`  
**理由**:
- ⚠️ 引用路径错误：`query_knowledge.py` 应为 `query_knowledge_lite.py`
- ⚠️ 功能重叠：知识库查询功能可集成到主版本
- ✅ 设计思路有价值：基于知识库的智能检索（token消耗从50K降到5K）
- ✅ 保留备用：未来可能合并到主版本

## 📖 使用建议

### 当前阶段（2025-12）
```powershell
# 统一使用生产版本
cd D:\zmproject
.\venv\Scripts\Activate.ps1
python load_project_context.py
```

### 未来优化（可选）
考虑将 `load_context_light.py` 的知识库查询能力集成到 `load_project_context.py`：

```python
# 在 load_project_context.py 中增强
def load_context_smart(task_description: str = None):
    """智能加载上下文"""
    if task_description and KNOWLEDGE_BASE_AVAILABLE:
        # 使用知识库检索相关内容（5K tokens）
        return query_relevant_knowledge(task_description)
    else:
        # 使用完整加载方式（50K tokens）
        return load_full_context()
```

**优势**：
- 开发特定表时：使用知识库检索 → 仅5K tokens
- 全局理解项目：使用完整加载 → 获得所有上下文
- 一个入口文件，两种加载模式

## 📝 文件对比

| 特性 | load_project_context.py | load_context_light.py |
|------|-------------------------|----------------------|
| **文件大小** | 50KB (840行) | 7KB (214行) |

... (内容过长，已截断)
```

## 📄 66. dwd_sd_order_detail_df - mandt字段使用错误修正报告
**File**: `aianswer/2025-12-19/dwd_sd_order_detail_df_mandt_fix_report.md` | **Type**: 文档
**Preview**: **问题发现时间**: 2025-12-19 **问题类型**: 字段不存在但被引用 **严重程度**: ❌ P0（致命错误，会导致SQL执行失败） 在`dwd_sd_order_detail_df.sql`中，**CTE 23 (z008表)** 使用了`mandt`字段，但实际数据字典中`ods...

```
# dwd_sd_order_detail_df - mandt字段使用错误修正报告

**问题发现时间**: 2025-12-19  
**问题类型**: 字段不存在但被引用  
**严重程度**: ❌ P0（致命错误，会导致SQL执行失败）

---

## 问题描述

在`dwd_sd_order_detail_df.sql`中，**CTE 23 (z008表)** 使用了`mandt`字段，但实际数据字典中`ods_sap_erp_zhone_text_get_vbbk_di`表**没有mandt字段**。

### 表结构验证

**表名**: `ods_sap_erp_zhone_text_get_vbbk_di` (订单长文本表)  
**实际字段**: 
```
vbeln          -- 订单号
tdid           -- 文本ID
text           -- 文本内容
insert_dt      -- 插入时间
```

**❌ 缺失字段**: `mandt`

---

## 错误位置

### 1. CTE定义错误（第408-415行）

**错误代码**:
```sql
-- ========== CTE 23: 订单长文本（Z008） ==========
z008 AS (
    SELECT
        mandt,                       -- ❌ 字段不存在
        vbeln,                       -- 订单号
        _text                         -- 文本内容（质保期）
    FROM ods.ods_sap_erp_zhone_text_get_vbbk_di
    WHERE mandt = '800'              -- ❌ 字段不存在
),
```

### 2. JOIN条件错误（第744-746行）

**错误代码**:
```sql
LEFT JOIN z008
    ON vbak.mandt = z008.mandt       -- ❌ z008没有mandt字段
    AND vbak.vbeln = z008.vbeln
```

---

## 修正方案

### 修正1: CTE定义（✅ 已修正）

```sql
-- ========== CTE 23: 订单长文本（Z008） ==========
z008 AS (
    SELECT
        vbeln,                       -- 订单号
        text AS _text                -- 文本内容（质保期）
    FROM ods.ods_sap_erp_zhone_text_get_vbbk_di
),
```

**修改说明**:
- ✅ 删除了SELECT中的`mandt`字段
- ✅ 删除了WHERE中的`mandt = '800'`条件
- ✅ 将`_text`改为`text AS _text`（字段别名）

### 修正2: JOIN条件（✅ 已修正）

```sql
LEFT JOIN z008
    ON vbak.vbeln = z008.vbeln
```

**修改说明**:
- ✅ 删除了`vbak.mandt = z008.mandt`关联条件
- ✅ 保留`vbak.vbeln = z008.vbeln`（订单号关联）

... (内容过长，已截断)
```

## 📄 67. 错误案例：维度信息缺失问题
**File**: `ai_learning/errors/2026-01-19_维度信息缺失问题.md` | **Type**: 文档
**Preview**: - **日期**：2026-01-19 - **错误ID**：ERR-20260119-001 - **严重程度**：🔴严重 - **错误类型**：逻辑设计/数据关联 - **影响范围**： - `dm_co_max_product_predict_cost_df.sql`（主表关联缺失） - 面向...

```
# 错误案例：维度信息缺失问题

## 基本信息
- **日期**：2026-01-19
- **错误ID**：ERR-20260119-001
- **严重程度**：🔴严重
- **错误类型**：逻辑设计/数据关联
- **影响范围**：
  - `dm_co_max_product_predict_cost_df.sql`（主表关联缺失）
  - 面向应用层的产品最高成本展示（维度属性全为空）

---

## 问题描述

在开发 `dm_co_max_product_predict_cost_df` 时，尽管 DWD 明细表中有数据，但最终 DM 表中的维度属性（如产品线、物理尺寸、灯档次等）出现大面积为空的情况。

### 现象观察
- 成本指标 `max_total_cost` 计算正确。
- `pci_code` 和 `pci_bom_code` 存在。
- `product_line_name` 等从维度表关联获取的字段全为 `NULL` 或默认空值。

---

## 根本原因

经过深度分析，该问题主要由以下三个因素交织导致：

### 1. 维度关联与排序选择的顺序问题
**错误逻辑**：
1. 先在 DWD 层通过 `ROW_NUMBER() (rn=1)` 选出每个产品的最高成本行。
2. 将该“孤立”的行与维度表进行关联。

**风险点**：
如果 DWD 中成本最高的这一行（由特定的 `replace_rule_code` 决定）在维度表中没有对应的记录，或者关联键（`pci_bom_code`）存在细微差异（如大小写、空格、非严格匹配），则该行将无法获取任何维度属性。

### 2. 数据分布与隐式排序影响
**技术细节**：
使用 `ROW_NUMBER() OVER (PARTITION BY pci_code, pci_bom_code ORDER BY calc_max_total_cost DESC)` 时，如果有多个替代规则的成本相同（例如都为 0 或某个固定值），数据库会进行隐式排序。如果恰好选出的 `rn=1` 记录在维度表中缺失，而其他 `rn>1` 的记录在维度表中有值，则会导致维度信息被“抛弃”。

### 3. 数据完整性与关联健壮性不足
**具体表现**：
- DWD 的 `pci_bom_code` 可能源自业务系统输入，而 DIM 表的 `pci_bom_code` 可能源自 PLM 标签。两者在某些特殊产品上可能存在步调不一致。
- 采用 `LEFT JOIN dim ... ON dim.rn = 1` 的严格过滤，导致如果 DWD 选中的行在 DIM 中不是“最新标签”对应的记录，关联就会失效。

---

## 错误代码示例

### ❌ 错误做法：先筛选后关联（维度易丢失）

```sql
WITH dwd_ranked AS (
    SELECT *, 
           ROW_NUMBER() OVER (PARTITION BY pci_code, pci_bom_code ORDER BY calc_max_total_cost DESC) AS rn
    FROM dwd_table
)
SELECT co.*, dim.attr1, dim.attr2
FROM dwd_ranked co
LEFT JOIN dim_table dim ON co.pci_code = dim.pci_code AND co.rn = 1 -- ⚠️ 维度关联高度依赖于 DWD 筛选出的那唯一一行

... (内容过长，已截断)
```

## 📄 68. DWS Product Predict Cost Verification Report
**File**: `共享文档/知识库/knowledges/history/walkthrough_20260302.md` | **Type**: 文档
**Preview**: Successfully verified the requirement `dws_定制-产品测算成本计算.csv`, the SQL script `dws_co_customize_product_predict_cost_df.sql`, and the test environment d...

```
# DWS Product Predict Cost Verification Report

## Overview
Successfully verified the requirement `dws_定制-产品测算成本计算.csv`, the SQL script `dws_co_customize_product_predict_cost_df.sql`, and the test environment data in StarRocks.

## Verification Details

### 1. Requirements vs SQL Implementation
- **Grouping Logic**: Correct. The SQL groups by the 9 required fields.
- **Cost Calculations**:
    - M2 costs (`max`, `min`, `latest`, `s`, `v`) are calculated by summing `unit_cost * supply_ratio`.
    - Total M2 costs are calculated as `m2_cost * customize_total_square`.
    - Total Box costs are calculated as `m2_cost * customize_box_square`.
- **Supply Ratio Fallback**: 
    - **Requirement**: Default `factory_code=2020` to 1 if all ratios are empty.
    - **Implementation**: SQL uses `COALESCE(NULLIF(supply_ratio, 0), 1)` for all records.
    - **Status**: Currently, only `factory_code=2020` exists in the dataset, so the implementation effectively satisfies the requirement. However, if more factories are added, this logic might need to be refined to avoid overcounting.

### 2. Test Environment Data Verification (`starrocks-dev`)
- **Source Data**: `dwd.dwd_co_customize_material_unit_cost_df` contains 2 records at `bom_level = '0'`.
- **Target Data**: `dws.dws_co_customize_product_predict_cost_df` contains 2 matching records.
- **Accuracy Check**:
    - **Example PCI**: `202626020001L1078`
    - **M2 Cost**: 580.04984560
    - **Total M2 Cost**: 580.04984560 * 200 (Total Sq) = 116009.96912 (Verified ✅)

... (内容过长，已截断)
```

## 📄 69. ✅ 审查完成总结
**File**: `aianswer/2025-12-11/完成总结.md` | **Type**: 文档
**Preview**: 已对 `dwd_co_quotation_bom_df` 和 `dwd_co_bottom_bom_df` 两个数据仓库表进行了完整的合规性审查。 | 指标 | 结果 | |---|---| | **总体评分** | ⭐⭐⭐⭐⭐ 98/100 | | **代码质量** | ✅ Production-...

```
# ✅ 审查完成总结

## 检查完成

已对 `dwd_co_quotation_bom_df` 和 `dwd_co_bottom_bom_df` 两个数据仓库表进行了完整的合规性审查。

---

## 📊 核心结论

| 指标 | 结果 |
|---|---|
| **总体评分** | ⭐⭐⭐⭐⭐ 98/100 |
| **代码质量** | ✅ Production-Ready |
| **规范符合** | ✅ 100% 遵循项目标准 |
| **上线就绪** | ✅ 准予上线（需修复 1 个问题） |
| **修复时间** | 1-2 天业务确认 + 10 分钟实施 |

---

## 🔴 关键问题（必须修复）

### ✅ 问题 1：SAP MANDT='800' 过滤 - 已驳回
- **原问题**：采集任务是否需要过滤客户端数据？
- **结论**：✅ 无需处理
- **原因**：采集同步任务已在数据源侧完成 `mandt='800'` 过滤，DWD 层使用的 ODS 数据已经是纯 800 客户端数据

### 🔴 问题 2：工厂代码映射失效 ⏱️ 1-2天
- **文件**：`src/dwd/dwd_co_quotation_bom_df.sql`
- **原因**：PLM factory_code ≠ SAP werks
- **解决**：创建映射表或确认工厂对应关系

---

## 📚 生成文档（5 份）

所有文档已保存至 `docs/` 文件夹：

| 文档 | 内容 | 适合人群 |
|---|---|---|
| 📄 **README_审查文档导航.md** | 文档导航中心 | 所有人 |
| 📄 **executive_summary.md** | 3 页概览 | 项目经理 |
| 📄 **quick_fix_guide.md** | 修复指南 | 开发工程师 |
| 📘 **mat_code_data_driven_validation.md** | 15 页数据验证 | QA/开发 |
| 📗 **comprehensive_compliance_report.md** | 25 页完整报告 | 合规审计 |

### 快速阅读建议

**如果时间紧张** (5-10 分钟)：
```
→ executive_summary.md
```

**如果要立即修复** (15 分钟)：
```
→ quick_fix_guide.md
```

**如果要深入了解** (30-40 分钟)：
```
→ comprehensive_compliance_report.md
→ mat_code_data_driven_validation.md
```

---

## ✨ 亮点特色

### 1. 数据驱动的验证
- 使用实际项目数据样例进行追踪
- 完整展示数据流从源到最终结果
- 比纯代码审查更具说服力

### 2. 分层级报告
- 4 个文档满足不同读者需求
- 项目经理、开发、QA、审计都有适合的文档

### 3. 可立即执行的修复指南
- 代码片段复制即用
- 验证查询现成可用
- 测试清单完整

### 4. 深度业务逻辑分析
- 解释了为什么这样设计
- 分析了所有逻辑路径
- 覆盖了边界场景

---

## 🎯 后续行动

### 立即行动（今天）
1. ✅ 读 executive_summary.md（了解现状）
2. ⏳ 与业务确认工厂代码映射（1-2 小时）
3. ✅ 修复 SAP MANDT 过滤（5 分钟）

... (内容过长，已截断)
```

## 📄 70. dwd_co_mat_miss_price_df 模型更新记录
**File**: `aianswer/2025-12-25/dwd_co_mat_miss_price_df_更新记录.md` | **Type**: 文档
**Preview**: 2025-12-25 模型设计文档《模型设计清单-技术开发.xlsx》更新，需要同步代码以匹配最新设计规范。 - `2020_last_pur_currency` VARCHAR(100) - 上一次大亚湾采购币别 - `2020_last_pur_package_unit` VARCHAR(100...

```
# dwd_co_mat_miss_price_df 模型更新记录

## 更新日期
2025-12-25

## 更新原因
模型设计文档《模型设计清单-技术开发.xlsx》更新，需要同步代码以匹配最新设计规范。

## 主要变更

### 1. DDL结构调整（共22个字段）

#### 增加字段（4个）
- `2020_last_pur_currency` VARCHAR(100) - 上一次大亚湾采购币别
- `2020_last_pur_package_unit` VARCHAR(100) - 上一次大亚湾采购最小包装单位
- `2020_last_pur_moq` VARCHAR(100) - 上一次大亚湾采购MOQ
- `B010_last_pur_currency` VARCHAR(100) - 上一次南昌采购币别

#### 字段名调整
**旧字段名** → **新字段名**
- `last_pur_price_2020` → `2020_last_pur_price` (带反引号)
- `last_pur_price_b010` → `B010_last_pur_price`
- ~~`last_pur_package_unit`~~ → 拆分为 `2020_last_pur_package_unit` + `B010_last_pur_package_unit`
- ~~`last_pur_moq`~~ → 拆分为 `2020_last_pur_moq` + `B010_last_pur_moq`

#### 其他调整
- `part_level` 注释从"BOM对应行号"改为"结构级别"
- 产品系列/产品线字段注释去掉"所用的"前缀
- 表注释从"dwd_co_价格缺失物料信息表"改为"dwd_价格缺失物料信息表"
- 表模型从 DUPLICATE KEY 改为 PRIMARY KEY
- 分布键增加 pci_code, part_level（从单字段改为三字段组合）

### 2. 数据SQL调整

#### CTE结构变更
**原结构（8个CTE）**：
1. price_missing - 价格缺失物料基础表
2. cust_bom - PLM定制BOM信息
3. mat_info - 物料信息维表
4. marc - SAP物料工厂数据（**单个，不区分工厂**）
5. ekko - SAP采购订单抬头
6. ekpo - SAP采购订单行项目
7. ekpo_2020 - 大亚湾工厂采购价格
8. ekpo_b010 - 南昌工厂采购价格

**新结构（9个CTE）**：
1. price_missing - 价格缺失物料基础表
2. cust_bom - PLM定制BOM信息
3. mat_info - 物料信息维表
4. **marc_2020 - SAP物料工厂数据（大亚湾）** ✅ 新增
5. **marc_b010 - SAP物料工厂数据（南昌）** ✅ 新增
6. ekko - SAP采购订单抬头
7. ekpo - SAP采购订单行项目 (**增加waers币别字段**)
8. ekpo_2020 - 大亚湾工厂采购价格 (**增加currency字段**)
9. ekpo_b010 - 南昌工厂采购价格 (**增加currency字段**)

#### SELECT输出调整
**旧输出（18个字段）**：
- 14. last_pur_price_2020
- 15. last_pur_price_b010

... (内容过长，已截断)
```

## 📄 71. dwd_hr_sys_user_display_df.sql 修复完成报告
**File**: `aianswer/2025-12-18/dwd_hr_sys_user_display_df修复完成报告.md` | **Type**: 文档
**Preview**: **修复日期**: 2025-12-18 **修复人**: AI (在用户指导下) **修复原因**: 字段与数据字典不匹配 - ✅ 添加缺失的`sys_code`字段（第1个字段） - ✅ 将`slw_acct_srm`改为`company_slw_account`（与数据字典一致） - ✅ 调整...

```
# dwd_hr_sys_user_display_df.sql 修复完成报告

**修复日期**: 2025-12-18  
**修复人**: AI (在用户指导下)  
**修复原因**: 字段与数据字典不匹配

---

## 修复内容

### 1. INSERT语句修复
- ✅ 添加缺失的`sys_code`字段（第1个字段）
- ✅ 将`slw_acct_srm`改为`company_slw_account`（与数据字典一致）
- ✅ 调整字段顺序与数据字典完全一致（22个字段）

**修复前**:
```sql
INSERT INTO dwd.dwd_hr_sys_user_display_df (
    acct_id,                    -- 1. 账号
    slw_acct_srm,               -- 2. 企业slw账号（SRM专用）
    ...
)
```

**修复后**:
```sql
INSERT INTO dwd.dwd_hr_sys_user_display_df (
    sys_code,                   -- 1. 系统编码
    acct_id,                    -- 2. 账号
    company_slw_account,        -- 3. 企业slw账号（SRM专用）
    ...
)
```

### 2. SELECT语句修复（14个系统）
为所有14个系统的SELECT语句添加了`sys_code`字段：

| 系统编号 | 系统名称 | sys_code值 | 状态 |
|---------|---------|-----------|------|
| 1 | SRM | 'SRM' | ✅ 已添加 |
| 2 | HLY | 'HLY' | ✅ 已添加 |
| 3 | OA | 'OA' | ✅ 已修复 |
| 4 | PLM | 'PLM' | ✅ 已修复 |
| 5 | MES-XSP | 'MES' | ✅ 已修复 |
| 6 | MES-ZM | 'MES' | ✅ 已修复 |
| 7 | MES-MINI | 'MES' | ✅ 已修复 |
| 8 | MES-XSPNC | 'MES' | ✅ 已修复 |
| 9 | WMS | 'WMS' | ✅ 已修复 |
| 10 | EAM | 'EAM' | ✅ 已修复 |
| 11 | QMS | 'QMS' | ✅ 已修复 |
| 12 | SAP-ERP | 'SAP-ERP' | ✅ 已修复 |
| 13 | SAP-BPC | 'SAP-BPC' | ✅ 已修复 |
| 14 | BI | 'BI' | ✅ 已修复 |

**示例修复**（HLY系统）:
```sql
-- 修复前
SELECT
    COALESCE(hly.username, '')  AS acct_id,
    ''                          AS company_slw_account,
    ...

-- 修复后
SELECT
    'HLY'                                       AS sys_code,  -- ← 新增
    COALESCE(hly.username, '')                  AS acct_id,
    ''                                          AS company_slw_account,  -- ← 字段名已修正

... (内容过长，已截断)
```

## 📄 72. SQL 反推业务分析框架
**File**: `ai_learning/business_insights/methodology/sql_to_business_framework.md` | **Type**: 文档
**Preview**: ``` ┌─────────────────────────────────────────────────────────────┐ │  Step 1: 读注释                                               │ │  → 表名、中文名、描述、作者、日...

```
# SQL 反推业务分析框架

## 分析流程

```
┌─────────────────────────────────────────────────────────────┐
│  Step 1: 读注释                                               │
│  → 表名、中文名、描述、作者、日期 → 快速了解业务背景            │
├─────────────────────────────────────────────────────────────┤
│  Step 2: 看来源                                               │
│  → FROM/JOIN 了哪些表 → 理解业务实体和关联关系                 │
├─────────────────────────────────────────────────────────────┤
│  Step 3: 析条件                                               │
│  → WHERE 条件、CASE 语句 → 理解业务规则和过滤逻辑              │
├─────────────────────────────────────────────────────────────┤
│  Step 4: 找特殊                                               │
│  → 硬编码、特殊处理、异常分支 → 发现业务痛点和优化机会          │
├─────────────────────────────────────────────────────────────┤
│  Step 5: 理口径                                               │
│  → 计算字段、聚合逻辑 → 理解业务指标定义和统计口径              │
└─────────────────────────────────────────────────────────────┘
```

## SQL 元素 → 业务含义映射表

| SQL 元素 | 业务含义 | 关注重点 | 学习价值 |
|---------|---------|---------|---------|
| **注释头** | 业务目的、作者、日期 | 模型定位、更新方式 | ★★★★★ |
| **主表选择** | 核心业务实体 | 业务边界、数据粒度 | ★★★★★ |
| **JOIN 链** | 实体关系 | 业务流程、数据血缘 | ★★★★☆ |
| **WHERE 条件** | 业务规则 | 过滤逻辑、数据范围 | ★★★★☆ |
| **CASE WHEN** | 业务规则/异常处理 | 特殊场景、分支逻辑 | ★★★★★ |
| **硬编码** | 数据质量问题 | 优化机会、技术债 | ★★★★★ |
| **映射表** | 柔性规则 | 变更频率、维护成本 | ★★★☆☆ |
| **聚合函数** | 统计口径 | 指标定义、计算逻辑 | ★★★★☆ |
| **CTE 分层** | 业务处理步骤 | 处理流程、逻辑分层 | ★★★★☆ |

## 反推洞察清单

### 数据质量发现

- [ ] 是否存在硬编码？原因是什么？
- [ ] 是否有 NULL 值处理？处理逻辑是否合理？

... (内容过长，已截断)
```

## 📄 73. Windows系统安装并使用agent-browser完整指南
**File**: `ai_applications/Windows系统安装并使用agent-browser完整指南.md` | **Type**: 文档
**Preview**: 本文整理了Windows系统下agent-browser的完整安装流程、核心使用命令及常见问题解决方案，所有命令均经过实测验证。 1. 环境要求：Windows 10/11（64位），无需Node.js（最终使用原生exe文件） 2. 工具准备：Git（用于克隆源码） - 下载地址：https://...

```
# Windows系统安装并使用agent-browser完整指南

本文整理了Windows系统下agent-browser的完整安装流程、核心使用命令及常见问题解决方案，所有命令均经过实测验证。

## 一、安装准备

1. 环境要求：Windows 10/11（64位），无需Node.js（最终使用原生exe文件）

2. 工具准备：Git（用于克隆源码）
   
   - 下载地址：https://git-scm.com/download/win
     
     ## 二、完整安装步骤
     
     ### 步骤1：卸载残留的全局安装版本（可选）
     
     若之前全局安装过agent-browser，先清理残留：
     
     ```powershell
     # 卸载全局版本
     npm uninstall -g agent-browser
     # 清理npm缓存
     npm cache clean --force
     ```
     
     ### 步骤2：克隆官方源码（核心，避免npm包文件缺失）
     
     ```powershell
     # 新建本地目录并进入
     mkdir C:\Users\{当前用户}\Desktop\agent-browser-local
     cd C:\Users\{当前用户} \Desktop\agent-browser-local
     # 克隆源码
     git clone https://github.com/vercel-labs/agent-browser.git
     cd agent-browser
     ```
     
     ### 步骤3：安装依赖并构建项目
     
     ```powershell
     # 安装项目依赖
     npm install
     # 构建项目（生成可执行文件）
     npm run build
     # 
     npx playwright install chromium
     ```
     
     ### 步骤4：验证安装成功
     
     ```powershell
     # 查看版本（输出0.7.6即成功）
     .\bin\agent-browser-win32-x64.exe --version
     ```
     
     ## 三、核心使用命令
     
     ### 1. 基础命令清单
     
     | 命令                 | 作用                 | 示例                                                        |
     | ------------------ | ------------------ | --------------------------------------------------------- |
     | `open <网址>`        | 自动启动浏览器并打开指定网址     | `.\bin\agent-browser-win32-x64.exe open baidu.com`        |
     | `snapshot`         | 生成当前页面元素快照（获取操作标识） | `.\bin\agent-browser-win32-x64.exe snapshot`              |

... (内容过长，已截断)
```

## 📄 74. 📋 表结构与业务逻辑更新需求分析
**File**: `aianswer/2025-12-22/requirement_clarification.md` | **Type**: 文档
**Preview**: **说明**：文档最新新增，需要从成本表中获取 **当前状态**： - ✅ 成本表有 offering 字段 - ❌ 目标表 DDL 中没有此字段 - ❌ SQL 中也没有选择此字段 **需要的修改**： - 在 DDL 中添加 `offering` 字段 - 在 SQL SELECT 中添加 `o...

```
# 📋 表结构与业务逻辑更新需求分析

## 🔄 收到的新需求

### 1. 新增 Offering 字段
**说明**：文档最新新增，需要从成本表中获取

**当前状态**：
- ✅ 成本表有 offering 字段
- ❌ 目标表 DDL 中没有此字段
- ❌ SQL 中也没有选择此字段

**需要的修改**：
- 在 DDL 中添加 `offering` 字段
- 在 SQL SELECT 中添加 `offering` 列
- 确定字段位置（建议在 pci_bom_code 之后）

---

### 2. 取供货比例逻辑变更
**原有逻辑**：
```
从 dwd_co_product_unit_cost_df 直接取 supply_ratio
```

**新需求说明**：
- 文档提到要从参数表取供货比例
- 参数表关联键：offering + factory_code
- 按月份获取不同的比例

**当前问题**：
- 参数表缺 pci_bom_code 字段，无法按 BOM 关联
- 参数表缺 calc_month 字段，无法按月份过滤
- 参数表只有 2 条记录（supply_ratio=1.0）

**需要澄清**：
- [ ] 是否需要修改参数表结构？
- [ ] 是否需要添加 factory_code 字段到目标表？
- [ ] 成本表中的 supply_ratio 与参数表的逻辑关系是什么？

---

### 3. 委外加工费可以开发
**当前状态**：
```sql
NULL AS subcon_max_amt  -- 设置为空值
```

**新需求**：
- 不应该是 NULL
- 应该有具体的加工费数据

**可用的数据源**：
成本表中存在加工费字段：
```
✅ max_product_manu_fee     (DECIMAL(38,8))
✅ min_product_manu_fee     (DECIMAL(38,8))
✅ latest_product_manu_fee  (DECIMAL(38,8))
✅ s_product_manu_fee       (DECIMAL(38,8))
✅ v_product_manu_fee       (DECIMAL(38,8))
```

**需要澄清**：
- [ ] `subcon_max_amt` 对应的是哪个加工费字段？（max 还是其他？）
- [ ] 加工费是否需要乘以供货比例？
- [ ] 是否需要新增多个加工费字段（对应 5 种价格类型）？

---

## 📊 提议的表结构调整

### 当前表结构（26 列）
```
1. pci_code
2. pci_bom_code
3. replace_rule_code
4. pci_name
5. mat_code
6. mat_name
7. std_bom_mat_code
8. std_bom_mat_name
9. comp_base_cun_qty
10. mat_type
11. comp_unit
12. base_unit
13. alternative_flag
14. bom_level
15. max_product_est_cost      ← 产品成本
16. min_product_est_cost
17. latest_product_est_cost
18. s_product_est_cost
19. v_product_est_cost
20. subcon_max_amt            ← 暂时为 NULL

... (内容过长，已截断)
```

## 📄 75. 通用工具提取总结
**File**: `aianswer/2025-12-18/通用工具提取总结.md` | **Type**: 文档
**Preview**: 今天（2025-12-18）在 `D:\zmproject\aianswer\2025-12-18` 目录下创建了约**50个Python脚本**，用于开发和调试 `dwd_hr_sys_user_display_df` 表。 从这些脚本中提取了**3个通用工具**，已移至 `D:\zmprojec...

```
# 通用工具提取总结

## 📊 工作概况

今天（2025-12-18）在 `D:\zmproject\aianswer\2025-12-18` 目录下创建了约**50个Python脚本**，用于开发和调试 `dwd_hr_sys_user_display_df` 表。

从这些脚本中提取了**3个通用工具**，已移至 `D:\zmproject\tools` 目录。

---

## ✅ 已提取的通用工具

### 1. validate_table_fields.py - 字段验证工具
**源文件**: `aianswer/2025-12-18/validate_all_fields.py`（特定场景版）

**功能**:
- ✅ 验证表字段是否存在
- ✅ 检查字段大小写是否匹配
- ✅ 批量验证多个表的字段
- ✅ 返回详细的验证结果和建议

**通用化改进**:
- 从硬编码的14个系统改为通用的参数化接口
- 增加了详细的文档和示例
- 支持单表和批量验证两种模式

---

### 2. check_tables_exist.py - 表存在性检查工具
**源文件**: `aianswer/2025-12-18/check_all_14_systems.py`（特定场景版）

**功能**:
- ✅ 检查单个表是否存在
- ✅ 批量检查多个表
- ✅ 统计存在/缺失的表
- ✅ 生成详细的检查报告

**通用化改进**:
- 从固定的14个系统表改为任意表列表
- 增加了错误处理和详细返回值
- 提供了格式化打印函数

---

### 3. sql_executor.py - SQL执行和验证工具
**源文件**: `aianswer/2025-12-18/run_sql_with_hdap.py`（特定场景版）

**功能**:
- ✅ 执行SQL文件并验证结果
- ✅ 自动统计目标表数据
- ✅ 支持分组统计
- ✅ 详细的执行报告

**通用化改进**:
- 从固定的SQL文件改为参数化接口
- 增加了灵活的验证SQL支持
- 提供了两种执行模式（基本执行、带统计执行）

---

## 📋 未提取的脚本（特定场景）

以下脚本是针对特定开发任务的，不适合作为通用工具：

### 诊断和调试类（约15个）
- `check_latest_error.py` - 查看最新错误日志
- `check_job_log.py` - 查看job执行日志
- `check_load_logs.py` - 查看load日志
- `test_srm_insert.py` - 测试SRM系统插入
- `test_insert_srm_only.py` - 单独测试SRM插入
- ... 等

**特点**: 硬编码了特定的job_id、表名、SQL文件路径

---

### SQL修复类（约10个）
- `fix_column_alias.py` - 修复列别名
- `fix_join_conditions.py` - 修复JOIN条件
- `fix_org_full_name_length.py` - 修复字段长度
- `batch_fix_fields.py` - 批量修复字段
- ... 等

**特点**: 针对特定SQL文件的特定问题，不具备通用性

---

### 数据读取类（约8个）
- `read_excel_user_table.py` - 读取用户表Excel
- `read_excel_full_mapping.py` - 读取映射表Excel

... (内容过长，已截断)
```

## 📄 76. 财务主题知识库
**File**: `ai_applications/kb_qa_mvp/knowledge_base/financial_theme/README.md` | **Type**: 文档
**Preview**: 本知识库收录洲明科技数据中台财务主题的核心模型业务定义和SQL模式，支持财务分析、预算管理、成本核算等业务场景。 | 模型名称 | 中文名 | 层级 | 核心用途 | 文档 | |---------|-------|------|---------|------| | dwd_fin_actual_...

```
# 财务主题知识库

## 概述

本知识库收录洲明科技数据中台财务主题的核心模型业务定义和SQL模式，支持财务分析、预算管理、成本核算等业务场景。

## 模型清单

### 收入成本类

| 模型名称 | 中文名 | 层级 | 核心用途 | 文档 |
|---------|-------|------|---------|------|
| dwd_fin_actual_gross_profit_df | 实际毛利模型 | DWD | 经营分析、业务维度 | [业务定义](gross_profit/business_definition.md) / [SQL模式](gross_profit/sql_patterns.md) |
| dwd_fin_revenue_cost_df | 标准收入成本模型 | DWD | 财务对账、凭证追踪 | [业务定义](revenue_cost/business_definition.md) / [SQL模式](revenue_cost/sql_patterns.md) |

### 费用类

| 模型名称 | 中文名 | 层级 | 核心用途 | 文档 |
|---------|-------|------|---------|------|
| dwd_fin_expense_detail_df | 费用明细模型 | DWD | 费用明细、分摊计算 | [业务定义](expense_detail/business_definition.md) / [SQL模式](expense_detail/sql_patterns.md) |
| dws_fin_expense_budget_actual_analysis_df | 费用预实分析表 | DWS | 预算对比、累计分析 | [业务定义](expense_budget_actual/business_definition.md) / [SQL模式](expense_budget_actual/sql_patterns.md) |

## 核心概念

### 双口径设计

财务主题采用"双口径"设计，满足不同用户需求：

```
┌─────────────────────────────────────────────────────────────┐
│                    收入成本双口径                            │
├──────────────────────────┬──────────────────────────────────┤
│     实际毛利模型          │       标准收入成本模型            │
├──────────────────────────┼──────────────────────────────────┤
│ 数据来源: 财务导入         │ 数据来源: SAP会计凭证             │
│ 视角: 财务核算视角         │ 视角: 会计凭证视角                │
│ 精度: 订单级              │ 精度: 凭证级                      │
│ 用户: 业务人员            │ 用户: 财务人员                    │
│ 用途: 经营分析            │ 用途: 财务对账                    │
└──────────────────────────┴──────────────────────────────────┘

... (内容过长，已截断)
```

---

## 💡 Learning Tips
- 今天聚焦：理解 AI Agent 的核心逻辑（感知→推理→执行）
- 动手实验：运行 `kb_qa_mvp` 中的示例代码
- 思考：如何将知识库问答应用于你的业务场景？

---
*Generated: 2026-04-14 23:23 | HunterClaw Daily Learning*