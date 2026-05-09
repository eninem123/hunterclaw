# 📚 Daily Learning | Day 7
**Module 1: AI Applications (AI应用入门)**
Day 3/7 in module | Files 43-63 of 147

---

## 📄 43. 🔍 成本计算逻辑 - 关键问题清单
**File**: `aianswer/2025-12-22/cost_calculation_verification_checklist.md` | **Type**: 文档
**Preview**: 您指出SQL中的测算成本逻辑可能有问题。我发现了**数据字典与您的业务描述之间的差异**。 需要**立即确认**以下问题： - ✅ **cost 表（dwd_co_product_unit_cost_df）**有 supply_ratio（第18列） - ✅ **param 表（dwd_co_pro...

```
# 🔍 成本计算逻辑 - 关键问题清单

## 📌 核心问题

您指出SQL中的测算成本逻辑可能有问题。我发现了**数据字典与您的业务描述之间的差异**。

需要**立即确认**以下问题：

---

## ❓ 关键问题 1：supply_ratio 来源

### 现状
- ✅ **cost 表（dwd_co_product_unit_cost_df）**有 supply_ratio（第18列）
- ✅ **param 表（dwd_co_product_cost_param_df）**有 supply_ratio（第12列）

### 问题
| 来源 | 是否应该用？| 为什么？ |
|------|-----------|--------|
| cost.supply_ratio | ❓ | 已在成本表中 |
| param.supply_ratio | ❓ | 在参数表中 |

### 验证命令
```sql
-- 对比两个表的 supply_ratio 是否相同
SELECT DISTINCT 
    c.supply_ratio AS cost_supply_ratio,
    p.supply_ratio AS param_supply_ratio,
    COUNT(*) 
FROM dwd_co_product_unit_cost_df c
LEFT JOIN dwd_co_product_cost_param_df p 
  ON c.offering = p.offering
GROUP BY c.supply_ratio, p.supply_ratio;
```

---

## ❓ 关键问题 2：calc_month 字段

### 现状
数据字典显示 **param 表没有 calc_month 字段**。

### 问题
您说"取《dwd_产品成本计算参数》对应【PCI-BOM编码】的计算时对应月份的【供货比例】"

- ❓ param 表中是否实际有 calc_month 字段（但未在数据字典中记录）？
- ❓ 还是 param 表按 insert_dt 维度有多个版本？

### 验证命令
```sql
-- 查看 param 表的实际字段结构
DESC dwd.dwd_co_product_cost_param_df;

-- 查看是否有时间维度
SELECT * FROM dwd.dwd_co_product_cost_param_df LIMIT 5;
```

---

## ❓ 关键问题 3：关联键

### 现状
| 表 | 有的字段 | 
|----|----|
| cost | pci_bom_code, offering |
| param | offering, factory_code |

### 问题
您说"对应【PCI-BOM编码】"，但 param 表的主键是 offering + factory_code

- ❓ 应该用 **offering** 关联还是 **pci_bom_code** 关联？
- ❓ 还是需要通过某个维度表关联（如 dim_pci_offering_mapping）？

### 验证命令
```sql
-- 查看 cost 表的 pci_bom_code 和 offering 关系
SELECT DISTINCT pci_bom_code, offering FROM dwd_co_product_unit_cost_df 
ORDER BY pci_bom_code, offering;

... (内容过长，已截断)
```

## 📄 44. dwd_sd_order_detail_df 字段检查报告
**File**: `aianswer/2025-12-19/dwd_sd_order_detail_df_field_check_report.md` | **Type**: 文档
**Preview**: **生成时间**: 2025-12-19 **检查脚本**: check_order_tables.py **检查范围**: 23个源表，涉及82个字段映射 1. **vbap表 - `lameng`字段**: 已修正为`lsmeng`（需求交货数量） 2. **konv表名**: 已修正为`ods...

```
# dwd_sd_order_detail_df 字段检查报告

**生成时间**: 2025-12-19  
**检查脚本**: check_order_tables.py  
**检查范围**: 23个源表，涉及82个字段映射  

---

## 一、检查结果总结

### ✅ 已修正的问题（用户已修改）
1. **vbap表 - `lameng`字段**: 已修正为`lsmeng`（需求交货数量）
2. **konv表名**: 已修正为`ods_sap_erp_zhone_get_konv_so_di`

### ❌ 需要修正的问题（共4个）

| 序号 | 表名 | 问题类型 | 问题描述 | 修正方案 |
|------|------|---------|---------|---------|
| 1 | **ods_sap_erp_vbak_df** | 字段不存在 | CTE中有重复的`bstnk`字段（第148行），可能导致逻辑错误 | 检查第148行的`bstnk`注释是否正确（标注为"生产批次号"） |
| 2 | **ods_sap_erp_tvkot_df** | 表名正确 | **误报**：tvkot表存在且有vtext字段，SQL已正确使用 | ✅ 无需修改 |
| 3 | **ods_sap_erp_zpp019_h_df** | 字段不存在 | 数据字典中该表无`batnk`字段，SQL中使用的是`bstnk`（正确） | ✅ 无需修改 |
| 4 | **t148t表** | 表不存在 | CTE已注释但SELECT中仍引用`t148t.soext` | 修改第672行，将`t148t.soext`改为空字符串 |

---

## 二、详细分析

### 问题1: vbak表 - bstnk字段重复使用
**位置**: dwd_sd_order_detail_df.sql 第133行、第148行  
**问题**: 
```sql
-- 第133行
bstnk,                       -- 客户采购订单号（合同号）

-- 第148行
bstnk,                       -- 生产批次号（关联生产任务单）
```

**分析**: 同一个字段`bstnk`在CTE中被选择两次，但注释不同。需要确认：
- `bstnk`是否既是合同号又是生产批次号？
- 还是第148行应该去掉？

**建议**: 保留第133行（合同号），删除第148行（避免重复）

---

### 问题2: tvkot表 - vtext字段（✅ 已验证正确）
**位置**: dwd_sd_order_detail_df.sql 第273-279行  
**当前代码**:
```sql
-- ========== CTE 12: 销售组织（tvko） ==========
tvko AS (
    SELECT
        mandt,
        vkorg,                       -- 销售组织编码
        vtext                        -- 销售组织名称
    FROM ods.ods_sap_erp_tvkot_df
    WHERE mandt = '800'
      AND spras = '1'                -- 中文
),
```

**验证结果**: 
- ✅ 表`ods_sap_erp_tvkot_df`存在于数据字典

... (内容过长，已截断)
```

## 📄 45. dwd_sd_order_detail_df 字段检查完成报告
**File**: `aianswer/2025-12-19/dwd_sd_order_detail_df_final_check_report.md` | **Type**: 文档
**Preview**: **检查时间**: 2025-12-19 **检查工具**: check_order_tables.py + 手动验证 **检查范围**: 23个源表，82个字段映射 | 序号 | 问题描述 | 状态 | 修正方式 | |------|---------|------|---------| | 1 ...

```
# dwd_sd_order_detail_df 字段检查完成报告

**检查时间**: 2025-12-19  
**检查工具**: check_order_tables.py + 手动验证  
**检查范围**: 23个源表，82个字段映射  

---

## ✅ 检查结果：已全部修正

### 初始发现的6个问题

| 序号 | 问题描述 | 状态 | 修正方式 |
|------|---------|------|---------|
| 1 | vbap表 - `lameng`字段不存在 | ✅ 已修正 | 用户已改为`lsmeng` |
| 2 | vbak表 - `bstnk`字段重复 | ✅ 已修正 | AI删除了第148行重复字段 |
| 3 | tvko表 - `vtext`字段不存在 | ✅ 误报 | SQL正确使用`tvkot`表（带t后缀） |
| 4 | konv表 - 表名不存在 | ✅ 已修正 | 用户已改为`ods_sap_erp_zhone_get_konv_so_di` |
| 5 | t148t表 - 表不存在 | ✅ 已修正 | 用户已注释CTE并将引用改为空字符串 |
| 6 | zpp019_h表 - `batnk`字段不存在 | ✅ 误报 | SQL正确使用`bstnk`字段 |

---

## 修正详情

### 1. vbap表 - lsmeng字段（用户已修正）
**位置**: CTE 2, 第170行  
**修正**:
```sql
-- 修改前（错误）:
lameng,                      -- 需求交货数量

-- 修改后（正确）:
lsmeng,                      -- 需求交货数量
```

### 2. vbak表 - 删除重复的bstnk字段（AI已修正）
**位置**: CTE 1, 原第148行  
**修正**:
```sql
-- 删除了重复的字段选择
-- bstnk,                       -- 生产批次号（关联生产任务单）
```
**说明**: `bstnk`字段在第133行已经选择（作为合同号），第148行是重复选择，已删除。

### 3. tvko表 - vtext字段（无需修改，检查脚本误报）
**位置**: CTE 12, 第273-279行  
**验证结果**:
- SQL使用的是`ods_sap_erp_tvkot_df`（带t后缀，销售组织文本表）
- 数据字典中确实存在`ods_sap_erp_tvkot_df`表
- 该表包含`vtext`字段（销售组织名称）
- **结论**: SQL代码正确，初始检查脚本误报（因为检查的是`tvko`而非`tvkot`）

### 4. konv表 - 表名修正（用户已修正）
**位置**: CTE 18, 第351-360行  
**修正**:
```sql
-- 修改前（错误）:
FROM ods.ods_sap_erp_konv_df

-- 修改后（正确）:
FROM ods.ods_sap_erp_zhone_get_konv_so_di
```

### 5. t148t表 - 特殊库存表不存在（用户已修正）
**位置**: CTE 24 (第419-427行), SELECT子句 (第671行)  
**修正**:
```sql
-- CTE已注释:
-- t148t AS (
--     ...
-- )

-- SELECT子句已修改:

... (内容过长，已截断)
```

## 📄 46. 实际毛利模型 - SQL模式提炼
**File**: `ai_applications/kb_qa_mvp/knowledge_base/financial_theme/gross_profit/sql_patterns.md` | **Type**: 文档
**Preview**: ```sql WITH base_order AS ( -- 第1层CTE: 提取基础业务键 SELECT mandt, company_code, order_num, ... FROM ods.ods_sap_erp_vbak_df ),...

```
# 实际毛利模型 - SQL模式提炼

## 1. CTE分层模式

### 模式结构

```sql
WITH base_order AS (
    -- 第1层CTE: 提取基础业务键
    SELECT 
        mandt,
        company_code,
        order_num,
        ...
    FROM ods.ods_sap_erp_vbak_df
),
organization_info AS (
    -- 第2层CTE: 关联组织维度
    SELECT b.*, org_dim.*
    FROM base_order b
    LEFT JOIN org_dim ON b.key = org_dim.key
),
sales_mapping AS (
    -- 第3层CTE: 关联销售维度
    SELECT o.*, sales_dim.*
    FROM organization_info o
    LEFT JOIN sales_dim ON o.key = sales_dim.key
),
final_result AS (
    -- 第4层CTE: 计算派生维度
    SELECT *, 
           CASE WHEN ... THEN ... END AS derived_dim
    FROM sales_mapping
)
```

### 适用场景

- 多层级维度关联
- 逐步丰富数据
- 复杂逻辑分层处理

### 优势

- 每层职责单一，便于理解
- 方便调试，可单独验证每层结果
- 逻辑清晰，维护成本低

---

## 2. 硬编码修正模式

### 模式结构

```sql
CASE 
    WHEN 公司 = 'X' AND 客户 = 'Y' THEN '修正值'
    ELSE COALESCE(NULLIF(原字段, ''), '')
END AS 字段名
```

### 实际案例

```sql
-- 客户 0000106034 的组织架构修正
CASE 
    WHEN vbak.bukrs_vf = '2000' AND vbak.kunnr = '0000106034' THEN '1010'
    ELSE COALESCE(nullif(vbak.vkorg,' '), '')
END AS sales_org_code
```

### 识别信号

- CASE WHEN 条件固定且具体
- 涉及特定编码组合
- 无动态配置表关联

### 业务含义

- 源头数据质量问题
- 历史遗留数据处理
- 特殊业务场景处理

### 反推洞察

> 发现硬编码时，应记录并追踪：
> 1. 硬编码的原因是什么？
> 2. 是否可以推动源头修正？
> 3. 硬编码的维护成本如何？

---

## 3. 多分支映射模式

### 模式结构

```sql
CASE
    WHEN 条件A THEN 结果A           -- 优先规则（特殊场景）
    WHEN 条件B THEN 关联表B取值    -- 次要规则（一般场景1）
    WHEN 条件C THEN 关联表C取值    -- 第三规则（一般场景2）
    ELSE '默认值'                   -- 兜底规则
END
```

### 实际案例

```sql
-- 业务产品线映射
CASE

... (内容过长，已截断)
```

## 📄 47. 2025-12-16 开发文件索引
**File**: `aianswer/2025-12-16/README_文件索引.md` | **Type**: 文档
**Preview**: ``` model_project/src/dim/ ├── dim_data_dictionary_df_ddl.sql              # 主表DDL（v2.0增强版） ├── dim_data_dictionary_business_df_ddl.sql     # 业务表DDL ├...

```
# 2025-12-16 开发文件索引

## 📁 文件分类导航

### 🎯 核心开发文件

#### 数据字典增强（model_project/src/dim/）
```
model_project/src/dim/
├── dim_data_dictionary_df_ddl.sql              # 主表DDL（v2.0增强版）
├── dim_data_dictionary_business_df_ddl.sql     # 业务表DDL
├── init_data_dictionary_business.sql           # 业务表初始化（MySQL）
├── init_data_dictionary_business_starrocks.sql # 业务表初始化（StarRocks）
├── update_data_dictionary_stats.py             # 【核心】统计信息自动补充脚本
├── deploy_data_dictionary.py                   # 一键部署脚本
└── README_数据字典增强方案.md                  # 完整技术文档
```

**核心脚本说明**：
- `update_data_dictionary_stats.py`：统计信息自动补充（批量优化、大表跳过、连接监控）
- `deploy_data_dictionary.py`：一键部署（自动执行DDL、初始化、统计）

### 🛠️ 通用工具（根目录）

```
d:\zmproject\
├── check_connections.py           # 数据库连接数检查工具
├── check_tables.py                # 表存在性检查工具
├── cleanup_missing_tables.py      # 清理不存在的表记录
├── convert_sql_to_starrocks.py    # SQL语法转换工具（v1）
├── convert_sql_to_starrocks_v2.py # SQL语法转换工具（v2，优化版）
├── fix_sql_columns.py             # SQL字段修复工具
└── test_conn.py                   # 数据库连接测试
```

**工具分类**：
- 连接管理：`check_connections.py`、`test_conn.py`
- 表管理：`check_tables.py`、`cleanup_missing_tables.py`
- SQL转换：`convert_sql_to_starrocks.py`、`convert_sql_to_starrocks_v2.py`
- 字段修复：`fix_sql_columns.py`

### 📚 文档和日志（aianswer/2025-12-16/）

```
aianswer/2025-12-16/
├── 2025-12-16_开发总结.md                    # 【必读】今日开发完整总结
├── 数据字典业务信息补充完成报告.md           # 业务信息补充说明
├── 通用数据库工具升级完成报告.md             # 工具优化文档
├── README_文件索引.md                        # 本文件

... (内容过长，已截断)
```

## 📄 48. 中台开发需求-促销库存流程 产品经理需求梳理专用提示词
**File**: `业务需求/库存促销/产品经理agent提示词.md` | **Type**: 文档
**Preview**: 你现在作为**企业级中台产品经理**，聚焦**LED屏库存促销全流程中台开发需求**，基于提供的促销库存流程业务文档，严格按照**中台产品设计规范、业务流程落地性、系统对接兼容性、权限管控精细化**原则，完成全维度需求梳理与拆解，输出可直接指导中台研发、对接业务方的标准化需求成果，具体要求如下： 1...

```
# 中台开发需求-促销库存流程 产品经理需求梳理专用提示词

你现在作为**企业级中台产品经理**，聚焦**LED屏库存促销全流程中台开发需求**，基于提供的促销库存流程业务文档，严格按照**中台产品设计规范、业务流程落地性、系统对接兼容性、权限管控精细化**原则，完成全维度需求梳理与拆解，输出可直接指导中台研发、对接业务方的标准化需求成果，具体要求如下：

### 一、核心需求定调

1. 提炼本次中台开发的**核心业务目标**（清库存/标准化促销定价/自动化流程提效等）、**核心解决的业务痛点**（原流程手工操作多/系统数据不通/定价无标准/权限混乱等）；
2. 明确中台在整个促销库存流程中的**核心定位**、与SAP/OA/CRM/APS/ERP等外围系统的**角色边界**。
   
   ### 二、业务流程中台化拆解
3. 按S1-S6全步骤，梳理**每一步的中台核心操作节点**、**操作角色**（销服运营专员/产品经理/商设/质量总监/产品线总经理）、**角色操作权限**、**操作触发条件**、**操作输出结果**；
4. 识别每一步流程中**中台需要承接的上游数据来源**、**需要输出的下游数据内容**、**数据流转格式**（如CSV文件）；
5. 梳理流程中的**异常场景**（评审驳回/库存信息变更/定价错误/系统对接失败等），并明确中台对应的**异常处理逻辑**与**流程回退机制**。
   
   ### 三、中台功能模块需求梳理
   
   按业务流程拆解**中台核心功能模块**，明确每个模块的**核心功能点**、**操作流程**、**页面交互要求**，需覆盖但不限于：
6. 库存商品清单管理模块（SAP数据拉取/勾选/下推/库存锁定等）；
7. 促销定价管理模块（建议价录入/产品线定价权限隔离/定价标准配置/价格表生成等）；
8. 流程触发与对接模块（OA审批流程触发/CSV文件生成/审批结果回写等）；
9. 数据报表与状态管理模块（流程状态刷新/评审后价格上架表管理/数据可视化等）；
10. 系统对接模块（与SAP/OA/CRM的数据同步规则/轮询机制/接口对接要求等）。
    
    ### 四、中台数据层需求梳理
11. 梳理中台需要**存储的核心数据模型**，包括库存促销基础信息、定价信息、流程审批信息、系统对接日志等，明确**核心字段**（参考文档中的PCI编码、库龄、品质等级、促销价格等）、**字段类型**、**字段约束**、**数据来源**；
12. 明确**数据同步规则**（实时/定时/触发式）、**数据更新机制**（如OA归档后自动刷新中台报表状态、CRM轮询抓取价格表）、**数据一致性保障方案**；
13. 梳理**核心数据报表**（库存促销清单表/建议价申报表/评审后价格上架表等）的**展示维度**、**筛选条件**、**导出功能**要求。
    
    ### 五、权限与管控需求梳理
14. 按**角色+产品线**维度，梳理**精细化权限管控规则**（如商设/产品经理按固装/分销/租赁产品线区分定价表可视权限、运营专员仅可触发流程不可修改定价等）；
15. 明确**操作日志管控要求**（所有角色的中台操作行为留痕/关键操作可追溯）；
16. 梳理**数据权限范围**（如不同库存位置/产品线的数据可见范围、跨角色数据共享规则）。
    
    ### 六、系统对接需求梳理
    
    明确中台与SAP/OA/CRM/APS/ERP等外围系统的**对接细节**，包括：
17. **对接方式**（接口对接/数据导入导出/轮询抓取）；

... (内容过长，已截断)
```

## 📄 49. ✅ 业务逻辑修正方案 - 完整分析
**File**: `aianswer/2025-12-22/cost_calculation_logic_clarification.md` | **Type**: 文档
**Preview**: 根据数据字典的详细分析，我发现了**关键的真相**： | 列号 | 字段名 | 类型 | 说明 | 地位 | |------|--------|------|------|------| | 16 | `offering` | varchar | **Offering** | ✅ **关联键** |...

```
# ✅ 业务逻辑修正方案 - 完整分析

## 🎯 核心发现

根据数据字典的详细分析，我发现了**关键的真相**：

### 实际的表结构

#### 📊 dwd_co_product_unit_cost_df（产品单位成本表）
| 列号 | 字段名 | 类型 | 说明 | 地位 |
|------|--------|------|------|------|
| 16 | `offering` | varchar | **Offering** | ✅ **关联键** |
| 18 | `supply_ratio` | decimal | **供货比例** | ✅ **直接可用** |
| 24 | `max_product_est_cost` | decimal | 最高价产品成本 | ✅ **已计算** |
| 25 | `min_product_est_cost` | decimal | 最低价产品成本 | ✅ **已计算** |
| 26 | `latest_product_est_cost` | decimal | 最近价产品成本 | ✅ **已计算** |
| 27 | `s_product_est_cost` | decimal | S价产品成本 | ✅ **已计算** |
| 28 | `v_product_est_cost` | decimal | V价产品成本 | ✅ **已计算** |

#### 📊 dwd_co_product_cost_param_df（产品成本计算参数表）
| 列号 | 字段名 | 类型 | 说明 | 地位 |
|------|--------|------|------|------|
| 0 | `offering` | varchar | **Offering** | 🔑 **主键1** |
| 0 | `factory_code` | varchar | 工厂编码 | 🔑 **主键2** |
| 12 | `supply_ratio` | decimal | **供货比例** | 参考值 |

---

## 🤔 您指出的业务逻辑

您说：
> 供货比例：取《dwd_产品成本计算参数》对应【PCI-BOM编码】的计算时对应月份的【供货比例】

**但是**，根据数据字典：
- 参数表的**关联键是 Offering + Factory_Code**，**不是 PCI-BOM编码**
- 参数表中**没有 calc_month 字段**

---

## ❓ 需要确认的问题

### 问题 1：参数表是否真的有 calc_month？

数据字典显示参数表的字段：
```
1. offering (PK)
2. factory_code (PK)
3. product_line_code
4. product_line_name
5. product_group_code
6. product_group_name
7. product_series_code
8. product_series_name
9. factory_name
10. loss_rate
11. mfg_fee_rate
12. supply_ratio
13. insert_dt
```

**没有 calc_month 字段**。但您提到"对应月份"，这意味着：

- ❓ 是否参数表在实际系统中有其他字段未被记录在数据字典中？
- ❓ 还是说参数表按月份有多条记录（通过 insert_dt 或其他时间字段区分）？


... (内容过长，已截断)
```

## 📄 50. dwd_co_bottom_bom_df 中 mat_code 字段计算逻辑对标检查
**File**: `aianswer/2025-12-11/mat_code_logic_check.md` | **Type**: 文档
**Preview**: **字段说明**：物料编码 **获取方式**：**计算** **计算逻辑（需求原文）**： ``` 1、若是原始物料（bom.alternative_flag<>'Y'），则取本身bom.mat_code 2、若是替代物料（bom.alternative_flag='Y'），根据 【替代规则编码】a...

```
# dwd_co_bottom_bom_df 中 mat_code 字段计算逻辑对标检查

## 需求文档规范（摘自《模型设计清单-技术开发》"dwd_单层BOM替换明细"页签）

### 字段编号：6 - mat_code（物料编码）

**字段说明**：物料编码

**获取方式**：**计算**

**计算逻辑（需求原文）**：
```
1、若是原始物料（bom.alternative_flag<>'Y'），则取本身bom.mat_code

2、若是替代物料（bom.alternative_flag='Y'），根据 【替代规则编码】alt.replace_rule_code
   对应的【替代物料组合编码】alt.replace_mat_group_code物料信息获取替换后的物料
   
   例：推演过程参考单层bom替代情况推演
   若bom.mat_code=M07，alt.replace_mat_group_code=M03:M03#M07:M07-1
   则使用"#"分隔，找到alt.replace_mat_group_code中的":"前为M07的组合，
   将":"后的M07-1赋值给该字段
```

---

## 当前代码实现

### 位置：dwd_co_bottom_bom_df.sql 第54-60行

```sql
CASE 
    WHEN COALESCE(bom.alternative_flag, 'N') = 'Y' 
         AND COALESCE(tmp.replace_mat, '') != ''
    THEN tmp.replace_mat
    ELSE bom.mat_code
END AS mat_code,
```

---

## 符合性检查

### ✅ **完全符合**

#### 1. **原始物料处理逻辑** ✓

**需求**：若是原始物料（alternative_flag <> 'Y'），则取本身bom.mat_code

**当前代码**：
```sql
ELSE bom.mat_code
```

- 当 `alternative_flag != 'Y'`（包括'N'和其他值）时，直接返回 `bom.mat_code`
- ✅ **完全符合需求**

---

#### 2. **替代物料处理逻辑** ✓

**需求**：若是替代物料（alternative_flag='Y'），根据替代规则查找并赋值替换后的物料

**当前代码**：
```sql
WHEN COALESCE(bom.alternative_flag, 'N') = 'Y' 
     AND COALESCE(tmp.replace_mat, '') != ''
THEN tmp.replace_mat
```

**实现步骤分析**：

| 步骤 | 需求要求 | 当前实现 | 符合度 |
|------|---------|--------|-------|
| 1 | 识别替代物料（alternative_flag='Y'） | `COALESCE(bom.alternative_flag, 'N') = 'Y'` | ✅ |
| 2 | 根据replace_rule_code对应的replace_mat_group_code | 前置Step 4 SQL已展开：dwd_tmp_alt_mapping | ✅ |
| 3 | 找到"#"分隔中，":"前为原物料编码的组合 | 在Step 4中通过SUBSTRING_INDEX解析，original_mat匹配 | ✅ |

... (内容过长，已截断)
```

## 📄 51. StarRocks 3.3.19 子查询错误修复报告
**File**: `aianswer/2025-12-19/dwd_sd_order_detail_df_subquery_fix_report.md` | **Type**: 文档
**Preview**: ``` "Not support the subquery!" ``` **错误原因**: StarRocks 3.3.19 不支持在 SELECT 字段或 CASE 语句中使用子查询。 ```sql -- ❌ 错误：CASE 语句中包含子查询 CASE WHEN vbak.auart IN ('Z...

```
# StarRocks 3.3.19 子查询错误修复报告

## 📋 错误信息

```
"Not support the subquery!" 
```

**错误原因**: StarRocks 3.3.19 不支持在 SELECT 字段或 CASE 语句中使用子查询。

---

## 🔍 问题定位

### 原始问题代码（第 655-659 行）

```sql
-- ❌ 错误：CASE 语句中包含子查询
CASE 
    WHEN vbak.auart IN ('ZMCE', 'ZMDR') THEN 
        (SELECT _text FROM z008 WHERE z008.vbeln = vbak.vgbel LIMIT 1)
    ELSE z008._text
END AS warranty_period
```

**问题分析**:
- StarRocks 3.3.19 **不支持标量子查询**（Scalar Subquery）
- 子查询出现在 SELECT 字段中或 CASE 语句内部时会报错
- 该子查询试图从 `z008` 表查询**参考订单**（`vbak.vgbel`）的质保期信息

---

## ✅ 修复方案

### 方案说明

使用 **LEFT JOIN** 替代子查询：
1. 创建两个 CTE：`z008`（当前订单质保期）和 `z008_ref`（参考订单质保期）
2. 分别关联到主表：`z008` 关联当前订单号，`z008_ref` 关联参考订单号
3. 在 SELECT 中使用 CASE 语句选择正确的质保期字段

### 修复后代码

#### 1. CTE 部分（新增 z008_ref）

```sql
-- ========== CTE 23: 订单长文本（Z008） ==========
z008 AS (
    SELECT
        vbeln,                       -- 订单号
        _text                        -- 文本内容（质保期）
    FROM ods.ods_sap_erp_zhone_text_get_vbbk_di
),

-- ========== CTE 24: 参考订单长文本（Z008_REF，用于贷项/借项） ==========
z008_ref AS (
    SELECT
        vbeln,                       -- 订单号
        _text                        -- 文本内容（质保期）
    FROM ods.ods_sap_erp_zhone_text_get_vbbk_di
),
```

#### 2. JOIN 部分（新增 z008_ref 关联）

```sql
LEFT JOIN z008
    ON vbak.vbeln = z008.vbeln        -- 关联当前订单
LEFT JOIN z008_ref
    ON vbak.vgbel = z008_ref.vbeln    -- 关联参考原单（贷项/借项用）
```

#### 3. SELECT 部分（移除子查询）

```sql
-- 75. 质保期（贷项/借项从原单获取，其他从当前订单获取）
-- ⚠️ StarRocks 3.3.19 不支持 SELECT 中的子查询，使用 LEFT JOIN 替代
CASE 

... (内容过长，已截断)
```

## 📄 52. 标准收入成本模型 - 深度业务分析
**File**: `ai_learning/business_insights/financial_theme/revenue_cost/revenue_cost_deep_analysis.md` | **Type**: 文档
**Preview**: 2026-03-24 ``` ODS (贴源层) ├── ods_sap_erp_bkpf_df (会计凭证抬头) ├── ods_sap_erp_bseg_df (会计凭证行项目) └── ods_sap_erp_vbak_df (SAP订单) ↓ DWD (明细层) ├── dwd_fin_ac...

```
# 标准收入成本模型 - 深度业务分析

## 分析日期
2026-03-24

## 模型定位

### 在数仓架构中的位置
```
ODS (贴源层)
    ├── ods_sap_erp_bkpf_df (会计凭证抬头)
    ├── ods_sap_erp_bseg_df (会计凭证行项目)
    └── ods_sap_erp_vbak_df (SAP订单)
            ↓
DWD (明细层)
    ├── dwd_fin_acc_voucher_detail_df (会计凭证明细)
    ├── dwd_sd_order_detail_df (订单明细)
    └── dwd_fin_revenue_cost_df (本模型)
            ↓
DWS/DM (汇总/集市层)
    └── 财务对账、审计报表
```

### 与其他模型的关系
- **上游**: 会计凭证明细表、订单明细表
- **下游**: 财务对账、审计分析
- **关联**: 与实际毛利模型形成"双口径"对比

---

## 业务理解

### 核心业务问题

**问题1: 为什么要做两个收入成本模型？**

| 维度 | 标准收入成本模型 | 实际毛利模型 |
|-----|-----------------|-------------|
| 数据来源 | SAP会计凭证 | 财务系统导入 |
| 视角 | 会计凭证视角 | 财务核算视角 |
| 精度 | 凭证级 | 订单级 |
| 用途 | 财务对账、审计 | 经营分析、业务管理 |

**洞察**: 两个模型服务于不同用户群体
- 财务人员 → 标准收入成本模型（对账）
- 业务人员 → 实际毛利模型（分析）

**问题2: 借贷方向调整的业务含义**

```sql
-- 收入类科目 (600100, 605100)
-- 正常在贷方(S)，冲减在借方(H)
WHEN parent_acc_code IN ('600100','605100') AND dr_cr_tag='S' THEN -amount

-- 成本类科目 (630100, 640100)
-- 正常在借方(H)，冲减在贷方(S)
WHEN parent_acc_code IN ('630100','640100') AND dr_cr_tag='H' THEN -amount
```

**业务洞察**:
- SAP记账规则：收入贷方正数、成本借方正数
- 冲减业务：收入借方、成本贷方（红字）
- 调整目的：统一为正数表示增加，负数表示冲减

---

## 数据血缘深度分析

### 第一层: 会计凭证数据

**来源**: SAP-ERP (BKPF + BSEG)

**业务洞察**:
- BKPF: 凭证抬头（凭证号、日期、状态）
- BSEG: 凭证行项目（科目、金额、借贷方向）
- 一对多关系：一个凭证头对应多个行项目

**疑问**:
- [ ] 凭证的审核状态如何影响数据？
- [ ] 冲销凭证如何处理？
- [ ] 期末调整凭证是否包含？

### 第二层: 科目维度

**来源**: dim_account_info_df

**关键筛选**:
- `account_type_code = '06'` - 收入成本类科目
- `parent_acc_code IN ('600100','605100','630100','640100')`

**业务洞察**:
- 600100: 主营业务收入

... (内容过长，已截断)
```

## 📄 53. 实际毛利模型 - 深度业务分析
**File**: `ai_learning/business_insights/financial_theme/gross_profit/gross_profit_deep_analysis.md` | **Type**: 文档
**Preview**: 2026-03-24 ``` ODS (贴源层) ├── ods_bi_fr_income_gross_profit_import_df (财务导入) └── ods_sap_erp_vbak_df (SAP订单) ↓ DWD (明细层) └── dwd_fin_actual_gross_profi...

```
# 实际毛利模型 - 深度业务分析

## 分析日期
2026-03-24

## 模型定位

### 在数仓架构中的位置
```
ODS (贴源层)
    ├── ods_bi_fr_income_gross_profit_import_df (财务导入)
    └── ods_sap_erp_vbak_df (SAP订单)
            ↓
DWD (明细层)
    └── dwd_fin_actual_gross_profit_df (本模型)
            ↓
DWS/DM (汇总/集市层)
    └── 经营分析报表、财务报表
```

### 与其他模型的关系
- **上游**: 依赖财务导入表、SAP订单表
- **下游**: 支撑经营分析、财务报表
- **关联**: 与收入成本模型有重叠，但口径不同

---

## 业务理解

### 核心业务问题

**问题1: 为什么要做这个模型？**

财务部门每月会导入实际核算的收入成本数据，但这些数据：
- 缺少业务维度（产品线、销售区域、业务员等）
- 无法直接用于经营分析
- 需要与SAP订单关联，补充业务视角

**问题2: 财务数据 vs SAP数据的关系？**

| 对比维度 | 财务导入表 | SAP订单表 |
|---------|-----------|----------|
| 数据来源 | 财务核算系统 | SAP-ERP |
| 数据粒度 | 订单级汇总 | 订单明细 |
| 金额性质 | 实际入账金额 | 订单金额 |
| 时间口径 | 会计期间 | 订单日期 |
| 完整性 | 已入账订单 | 全部订单 |

**洞察**: 财务数据是"已发生"，SAP数据是"已签约"，两者口径不同

---

## 数据血缘深度分析

### 第一层: 财务导入数据

**来源**: 帆软填报 (`ods_bi_fr_income_gross_profit_import_df`)

**业务洞察**:
- 财务部门手工导入，存在滞后性
- 数据质量控制依赖财务部门
- 导入格式标准化程度影响数据质量

**疑问**:
- [ ] 导入频率是每月一次还是实时？
- [ ] 是否有数据校验机制？
- [ ] 历史数据如何追溯修正？

### 第二层: SAP订单数据

**来源**: SAP-ERP (`ods_sap_erp_vbak_df`)

**业务洞察**:
- 订单头是主数据，相对稳定
- 组织架构字段可能存在变更
- 客户主数据需要定期同步

### 第三层: 维度丰富

**组织架构维度**:
```
销售区域 (ZM01/ZM02)
    → 销售大区
        → 销售战区
            → 销售组
                → 业务员
```

**产品线维度**:
```
产品类型/行业类型
    → 产品线映射表
        → 业务产品线 (piz_line_name)
```

---

## 关键业务发现

### 发现1: 组织架构硬编码

**现象**: 客户 0000106034 的销售组织/部门/销售组被硬编码

**推测原因**:
1. 该客户在SAP中组织架构录入错误
2. 历史遗留客户，主数据未清理
3. 特殊业务场景（如关联交易）

**业务影响**:
- 硬编码增加了维护成本
- 如果客户组织架构变更，需要同步修改SQL
- 可能影响其他依赖该客户数据的模型

**建议**:

... (内容过长，已截断)
```

## 📄 54. 实际毛利模型 - 业务定义
**File**: `ai_applications/kb_qa_mvp/knowledge_base/financial_theme/gross_profit/business_definition.md` | **Type**: 文档
**Preview**: | 属性 | 内容 | |-----|------| | **模型名称** | dwd_fin_actual_gross_profit_df | | **中文名称** | 财务实际毛利明细模型 | | **模型层级** | DWD (明细层) | | **更新方式** | 全量更新 (TRUNCAT...

```
# 实际毛利模型 - 业务定义

## 1. 模型基本信息

| 属性 | 内容 |
|-----|------|
| **模型名称** | dwd_fin_actual_gross_profit_df |
| **中文名称** | 财务实际毛利明细模型 |
| **模型层级** | DWD (明细层) |
| **更新方式** | 全量更新 (TRUNCATE + INSERT) |
| **主键** | fiscal_year + fiscal_period + order_num + order_item_num |

## 2. 业务目的

整合财务部门导入的实际收入、成本、毛利数据，与 SAP 销售订单关联，形成完整的业绩维度分析体系，支撑：

- 经营分析（按产品线/区域/客户分析毛利贡献）
- 业绩考核（销售业绩达成分析）
- 财务报表（收入成本明细表、毛利分析表）
- 异常监控（毛利率波动预警）

## 3. 核心业务实体

### 3.1 主数据实体

| 实体 | 来源系统 | 业务含义 | 关键字段 |
|-----|---------|---------|---------|
| 财务导入表 | BI (帆软填报) | 财务核算的实际收入成本 | fiscal_year, fiscal_period, revenue, cost, gross_profit |
| SAP 订单头 | SAP-ERP | 销售订单基础信息 | VBELN(订单号), KUNNR(客户), 组织架构字段 |
| 产品线映射 | BI (帆软填报) | 业务产品线归集规则 | product_type/industry_type → piz_line_name |

### 3.2 关联实体

| 实体 | SAP表 | 业务含义 | 关联键 |
|-----|-------|---------|-------|
| 公司主数据 | T001 | 公司代码描述 | BUKRS |
| 订单类型描述 | TVAKT | 订单类型中文名 | AUART |
| 分销渠道描述 | TVTWT | 分销渠道中文名 | VTWEG |
| 销售组织描述 | TVKOT | 销售组织中文名 | VKORG |
| 雇员部门描述 | ZSDEMP | 雇员部门中文名 | ZEMPNO |
| 销售合作伙伴 | VBPA | 销售员信息 | VBELN + PARVW='VE' |
| HR人员主数据 | PA0002 | 业务员姓名/工号 | PERNR |

## 4. 业务规则提炼

### 4.1 收入分类体系

```
主营业务收入
├── 加工收入 (rev_process_amt)
├── 出口销售收入 (rev_export_amt)
├── 内销销售收入 (rev_domestic_amt)
├── 工程收入 (rev_project_amt)
├── 软件销售收入 (rev_software_amt)
├── EMC项目收入 (rev_emc_amt)
├── 修理修配收入 (rev_repair_amt)
└── 外销运费 (rev_freight_amt)

其他业务收入
├── 材料销售收入 (other_material_amt)
├── 服务费收入-6%税率 (other_service_amt)
├── 水电/维修收入-13%税率 (other_utility_maint_amt)
├── 固定资产出租收入 (other_fa_lease_amt)

... (内容过长，已截断)
```

## 📄 55. dwd_sd_inventory_detail_di (dwd_存量明细模型)
**File**: `model_project/src/prod/dwd/dwd_sd_inventory_detail_di.md` | **Type**: 文档
**Preview**: | 表名 | dwd_sd_inventory_detail_di | | :--- | :--- | | 中文名 | dwd_存量明细模型 | | 主题域 | DWD | | 负责人 | / | | 预估数据量 | / | | 备注 | 存量明细数据，包含订单、出货、库存、计划行等信息 | | 来...

```
# dwd_sd_inventory_detail_di (dwd_存量明细模型)

## BASIC INFO
| 表名 | dwd_sd_inventory_detail_di |
| :--- | :--- |
| 中文名 | dwd_存量明细模型 |
| 主题域 | DWD |
| 负责人 | / |
| 预估数据量 | / |
| 备注 | 存量明细数据，包含订单、出货、库存、计划行等信息 |

## SOURCE TABLES
| 来源系统 | 英文表名 | 中文含义 | 别名 | 备注 |
| :--- | :--- | :--- | :--- | :--- |
| 数仓 | dwd_sd_order_detail_df | dwd_订单明细模型 | b | 主表 |
| 数仓 | dwd_sd_shipment_detail_df | dwd_出货明细模型 | a | 关联前先排除场景标识为D开头的数据 |
| SAP | ZTSO_TRACE | 销售订单跟踪手工维护字段 | c | 国内存量手工维护 |
| SAP | MSKA | 销售订单库存 | mk | |
| SAP | MSEG | 凭证段_物料 | e | |
| SAP | ZSD_CLXX_GJ | 国际订单存量信息 | f | 国际存量手工维护 |
| SAP | ZSDFKFS | 付款方式表 | g | |
| SAP | dim_exchange_rate_di | dim_汇率表 | h | |
| SAP | VBEP | 销售凭证：计划行数据 | ve | |

## FIELD LIST
| 字段名称 | 字段类型 | 字段含义 | 备注 |
| :--- | :--- | :--- | :--- |
| dt | date | 日期(分区字段YYYYMMDD) | |
| order_num | varchar | 销售公司销售订单号 | |
| contract_num | varchar | 客户采购订单编号 | |
| order_item_num | varchar | 订单行项目号 | |
| order_type_code | varchar | 订单类型编码 | |
| manu_sales_order_num | varchar | 制造公司销售订单号 | |
| order_num_transfer | varchar | 销售订单号_含抛转 | |
| create_date | date | 订单创建日期 | |
| approval_date | date | 订单首次审批日期 | |
| newest_date | date | 订单最新日期 | |
| contract_need_days | bigint | 合同需求天数 | |
| contract_need_date | date | 合同需求日期 | |
| review_del_days | bigint | 评审交期（天数） | |
| pmc_review_del_date | date | PMC评审交期 | |
| predict_del_date | date | 预计出货日期 | |
| pmc_change_date | date | PMC变更日期 | |
| latest_warehousing_date | date | 最新入库日期 | 原 last_receipt_date |
| transport_method | varchar | 运输方式 | |

... (内容过长，已截断)
```

## 📄 56. 费用预实分析表 - 深度业务分析
**File**: `ai_learning/business_insights/financial_theme/expense_budget_actual/expense_budget_actual_deep_analysis.md` | **Type**: 文档
**Preview**: 2026-03-24 ``` DWD (明细层) ├── dwd_fin_expense_detail_df (费用实际明细) └── dwd_fin_expense_bud_detail_df (费用预算明细) ↓ DWS (汇总层) └── dws_fin_expense_budget_actu...

```
# 费用预实分析表 - 深度业务分析

## 分析日期
2026-03-24

## 模型定位

### 在数仓架构中的位置
```
DWD (明细层)
    ├── dwd_fin_expense_detail_df (费用实际明细)
    └── dwd_fin_expense_bud_detail_df (费用预算明细)
            ↓
DWS (汇总层)
    └── dws_fin_expense_budget_actual_analysis_df (本模型)
            ↓
DM/报表
    └── 费用预实对比报表、费用分析看板
```

### 与其他模型的关系
- **上游**: 费用明细模型、费用预算明细表
- **下游**: 费用分析报表、管理驾驶舱
- **核心功能**: 解决断月问题，实现完整对比

---

## 业务理解

### 核心业务问题

**问题1: 什么是"断月"问题？**

**场景**:
```
部门A的费用发生情况:
- 1月: 1000元
- 2月: 无发生（数据缺失）
- 3月: 1500元

直接计算累计:
- 1月累计: 1000
- 2月累计: NULL（错误！应该是1000）
- 3月累计: 2500
```

**问题**:
- 2月数据缺失导致累计断裂
- 预算vs实际对比时维度不对齐
- 趋势分析出现断点

**解决方案**: 维度骨架(Spine)
- 强制每个维度组合都有12个月
- 缺失月份填充0
- 累计计算连续

**问题2: 为什么要用窗口函数计算累计？**

**传统方式**:
```sql
-- 需要自关联或子查询，复杂且低效
SELECT a.*, 
    (SELECT SUM(amount) FROM t WHERE month <= a.month) AS cumulative
FROM t a
```

**窗口函数方式**:
```sql
-- 简洁高效
SUM(amount) OVER(PARTITION BY dept ORDER BY month) AS cumulative
```

**优势**:
- 代码简洁
- 性能更好
- 支持多种累计方式

---

## 数据血缘深度分析

### 第一层: 费用实际数据

**来源**: dwd_fin_expense_detail_df

**筛选条件**:
- `belong_dept IS NOT NULL` - 必须有部门归属
- `process_tag NOT LIKE 'D-%'` - 排除调整类数据

**业务洞察**:
- 费用明细经过复杂分摊计算
- 只取最终归属明确的费用
- 排除中间过程数据

### 第二层: 费用预算数据

**来源**: dwd_fin_expense_bud_detail_df

**筛选条件**:
- `belong_domain IS NOT NULL` - 必须有归属域
- `alloc_granularity = '整体'` - 只取整体粒度
- `entity_code NOT IN ('Y000000005_Total')` - 排除汇总行

**业务洞察**:
- 预算有多个粒度（整体/明细）
- 只取整体粒度用于对比
- 排除系统汇总行避免重复

### 第三层: 维度骨架构建

**核心逻辑**: CROSS JOIN生成完整时间序列

```sql
-- 所有维度组合
all_keys: version × belong_dept × dept_name × account_code

... (内容过长，已截断)
```

## 📄 57. DWD 层成本计算损耗率系数校验规范
**File**: `ai_learning/lessons_learned/DWD 层成本计算损耗率系数校验规范.md` | **Type**: 文档
**Preview**: - **规范编号**：DWD-STD-20260303-001 - **发布日期**：2026-03-03 - **适用范围**：所有涉及材料成本计算的 DWD 层脚本 - **强制级别**：🔴 强制性（必须遵守） - **关联错误案例**：`local_knowledge_model/docs/d...

```
# DWD 层成本计算损耗率系数校验规范

## 📋 规范元数据

- **规范编号**：DWD-STD-20260303-001
- **发布日期**：2026-03-03
- **适用范围**：所有涉及材料成本计算的 DWD 层脚本
- **强制级别**：🔴 强制性（必须遵守）
- **关联错误案例**：`local_knowledge_model/docs/dwd_customize_cost_loss_rate_fix.md`

---

## 1. 核心原则

**所有材料成本计算必须包含损耗率系数 `(1 + loss_rate)`**，除非设计文档明确说明不需要。

### 1.1 通用公式模板

```python
# 步骤 1：获取损耗率（必须处理 NULL 值）
loss_rate = float(row.get('loss_rate', 0) or 0)

# 步骤 2：计算含损耗的材料成本（必须应用系数）
material_cost_with_loss = material_cost * (1 + loss_rate)

# 步骤 3：在后续计算中使用 material_cost_with_loss（禁止使用原始 material_cost）
result = material_cost_with_loss / box_square + other_costs
```

---

## 2. 校验清单（强制执行）

### 2.1 开发阶段校验

在编写任何成本计算逻辑时，必须逐项确认：

- [ ] **损耗率字段确认**
  - [ ] 确认源表是否包含 `loss_rate` 或类似字段
  - [ ] 确认损耗率的取值范围（通常 0-1 之间）
  - [ ] 确认 NULL 值处理方式（默认 0 还是跳过）

- [ ] **计算公式确认**
  - [ ] 对照 Excel 设计文档，逐字段确认计算公式
  - [ ] 确认公式中是否包含 `(1 + loss_rate)` 系数
  - [ ] 确认系数应用位置（材料成本、委外成本等）

- [ ] **代码实现确认**
  - [ ] 是否正确获取 `loss_rate` 字段
  - [ ] 是否正确计算 `material_cost_with_loss`
  - [ ] 是否在后续计算中使用 `material_cost_with_loss` 而非 `material_cost`

### 2.2 测试阶段校验

必须运行专项校验脚本验证计算结果：

```powershell
# 激活虚拟环境
cd D:\zmproject
.\venv\Scripts\Activate.ps1

# 运行校验脚本（根据具体表名调整）
python tools\tests\validate_customize_cost_calculation.py
```

**关键校验点**：
- [ ] 第 0 层（`bom_level=0`）数据计算正确
- [ ] 非叶子节点递归累加正确
- [ ] 分支逻辑（分销模组 vs 非分销模组）正确
- [ ] 边界值场景（零成本、空值）处理正确

### 2.3 上线前校验

- [ ] 校验脚本输出全部通过（无 FAILED 项）
- [ ] 生成校验报告并保存至 `audits/[表名]/[日期]/`
- [ ] 校验报告经团队成员 Review 确认

---

## 3. 常见错误模式

### ❌ 错误模式 1：直接使用原始材料成本

... (内容过长，已截断)
```

## 📄 58. dwd_fin_expense_detail_df 性能评估
**File**: `audits/dwd/2026-03-11/dwd_fin_expense_detail_df_性能评估.md` | **Type**: 文档
**Preview**: | 项 | 当前 | 说明 | |----|------|------| | 表模型 | DUPLICATE KEY(ym, version, company_code) | 明细表，不去重，仅排序键 | | 分布方式 | DISTRIBUTED BY RANDOM | 随机分桶 | | 单桶大小 ...

```
# dwd_fin_expense_detail_df 性能评估

## 一、DDL 评估（dwd_fin_expense_detail_df_ddl.sql）

### 1.1 当前设计

| 项 | 当前 | 说明 |
|----|------|------|
| 表模型 | DUPLICATE KEY(ym, version, company_code) | 明细表，不去重，仅排序键 |
| 分布方式 | DISTRIBUTED BY RANDOM | 随机分桶 |
| 单桶大小 | bucket_size = 4294967296 (4GB) | 桶较大 |
| 压缩/副本 | LZ4, replication_num=3, replicated_storage | 常规配置 |

### 1.2 优点

- **DUPLICATE KEY** 与业务一致：保留 V1/V2 双版本，不触发去重，符合需求。
- **RANDOM 分布**：写入时数据均匀打散，无热点；全量 INSERT OVERWRITE 时各 BE 负载较均衡。
- 字段较多但均为业务必需，无冗余大字段。

### 1.3 可优化点

| 问题 | 建议 | 优先级 |
|------|------|--------|
| **RANDOM 无查询剪枝** | 若下游/BI 常按 `ym` 或 `ym+version` 过滤，可改为 `DISTRIBUTED BY HASH(ym)` 或 `HASH(ym, version)`，使按年月查询能剪枝部分分桶。 | 中（取决于查询模式） |
| **排序键仅 3 列** | 若常见过滤为 `ym, version, cost_center_code`，可考虑把 `cost_center_code` 加入 DUPLICATE KEY 以利前缀过滤（会拉长排序键、略增写入成本，需权衡）。 | 低 |
| **4GB 桶** | 表总数据量若在数十 GB 级，4GB 桶数较少；若达百 GB 以上，可适当调小 bucket_size 增加并行度（需重建表）。 | 低 |

---

## 二、SQL 逻辑评估（dwd_fin_expense_detail_df.sql）

### 2.1 整体结构

- 多 CTE 串联：versions → latest_yms / pl_latest_ym / alloc_domain_item_latest_ym → 3 个 Base → all_data_base → joined_data → joined_with_rid → scope_match → 12 个 scope_* → joined_with_scope → computed_data → final_data → final_data_one_alloc → 最终 SELECT。
- 全量 INSERT OVERWRITE，无增量；Base 层已做公司/币种等过滤，数据量在源表级别已收敛。

### 2.2 性能热点与风险（按影响大致排序）

#### 1）scope_match：g 表 LIKE 关联 + 行膨胀（高）

```sql
LEFT JOIN ods.ods_bi_fr_fee_alloc_scope_entry_df g
  ON ...
  AND j.node_path_code LIKE CONCAT('%', g.entity_code, '%')
```

- **问题**：`node_path_code LIKE '%...%'` 无法用索引做等值/前缀匹配，易导致对 g 表做扫描或大范围探测；且一条明细的 path 可能匹配 g 表多条 entity，产生行膨胀。

... (内容过长，已截断)
```

## 📄 59. DWD模型开发规范 - 强制性前置检查
**File**: `ai_learning/DWD模型开发规范_强制性前置检查.md` | **Type**: 文档
**Preview**: **更新时间**: 2025-12-25 **版本**: v2.0 **所有DWD层表开发前，必须先执行前置检查，加载知识库，避免重复犯错。** ```bash python tools/pre_dev_check.py <model_name> python tools/pre_dev_check...

```
# DWD模型开发规范 - 强制性前置检查

**更新时间**: 2025-12-25  
**版本**: v2.0

## 核心原则

**所有DWD层表开发前，必须先执行前置检查，加载知识库，避免重复犯错。**

```bash
# 开发任何DWD表之前，先运行此命令
python tools/pre_dev_check.py <model_name>

# 示例
python tools/pre_dev_check.py dwd_co_mat_miss_price_df
```

## 为什么需要前置检查

### 问题背景

1. **重复犯错**: 同类错误在不同模型中反复出现（字段名混用、关联条件不全等）
2. **Token浪费**: 每次犯错都需要多轮对话修复，消耗大量Token
3. **效率低下**: 本可避免的错误导致反复修改、重新加载数据
4. **知识库未利用**: 已有的经验教训文档未在开发前查阅

### 解决方案

**强制性前置检查机制**：
- 开发前自动加载知识库
- 显示最近的错误案例和教训
- 提供完整的开发检查清单
- 推荐相关的经验教训文档

## 前置检查工具

### 1. pre_dev_check.py - 开发前检查

```bash
python tools/pre_dev_check.py dwd_co_mat_miss_price_df
```

**输出内容**:
- 🚨 强制性检查清单（critical_reminders）
- ⚠️ 最近7天的错误案例
- 📚 相关经验教训文档（自动匹配）
- ✅ DWD层表开发检查清单
- 🔧 可用工具列表
- 📝 快速命令模板

### 2. parse_design_document.py - Excel文档解析

```bash
python tools/parse_design_document.py \
    "模型设计清单-技术开发.xlsx" \
    "dwd_价格缺失物料信息" \
    "parsed_design.json"
```

**用途**: 完整提取Excel设计文档中的计算逻辑、关联条件、过滤条件

## 开发流程（强制执行）

### 阶段1: 前置准备（必须）

```bash
# 步骤1: 运行前置检查
python tools/pre_dev_check.py <model_name>

# 步骤2: 阅读所有推荐的经验教训文档
# 重点关注：
# - ai_learning/lessons_learned/字段映射规范.md
# - ai_learning/lessons_learned/数据填充规范.md
# - ai_learning/lessons_learned/2025-12-25_Excel设计文档解析规范.md

# 步骤3: 解析Excel设计文档
python tools/parse_design_document.py \
    "model_project/docs/模型设计清单-技术开发.xlsx" \
    "<sheet_name>" \
    "aianswer/$(date +%Y-%m-%d)/parsed_design.json"
```

### 阶段2: 字段验证（必须）

```bash
# 步骤4: 查询数据字典，确认所有字段名
python -c "from hdap_sql import query_data; \
    df = query_data('SELECT * FROM dim.dim_data_dictionary_df WHERE table_name=\"<table_name>\"'); \

... (内容过长，已截断)
```

## 📄 60. ✅ 成本计算逻辑验证 - 最终报告
**File**: `aianswer/2025-12-22/cost_calculation_final_verification.md` | **Type**: 文档
**Preview**: 通过直接查询数据库（使用 hdap_sql 工具类），我已**彻底验证**了您提出的问题。 **结论：当前的 SQL 实现 ✅ 正确** ``` 字段数：13 个 主键：(offering, factory_code) 是否有 calc_month？❌ NO 是否有 pci_bom_code？❌ N...

```
# ✅ 成本计算逻辑验证 - 最终报告

## 📋 执行摘要

通过直接查询数据库（使用 hdap_sql 工具类），我已**彻底验证**了您提出的问题。

**结论：当前的 SQL 实现 ✅ 正确**

---

## 🔍 核心验证结果

### 【验证 1】参数表结构（dwd_co_product_cost_param_df）

```
字段数：13 个
主键：(offering, factory_code)
是否有 calc_month？❌ NO
是否有 pci_bom_code？❌ NO
是否有 supply_ratio？✅ YES（第12列）
```

### 【验证 2】参数表实际数据

```sql
SELECT * FROM dwd.dwd_co_product_cost_param_df
-- 结果：仅 2 条记录
-- offering=FCQ1.5, factory_code=B010, supply_ratio=1.0
-- offering=FCQ1.2, factory_code=2020, supply_ratio=1.0
```

### 【验证 3】成本表结构（dwd_co_product_unit_cost_df）

```
字段总数：34 个
包含字段：
✅ offering（第16列）
✅ supply_ratio（第18列）
✅ max_product_est_cost（第24列）
✅ min_product_est_cost（第25列）
✅ latest_product_est_cost（第26列）
✅ s_product_est_cost（第27列）
✅ v_product_est_cost（第28列）
❌ 无 calc_month
```

### 【验证 4】关键对比

| 项目 | 您的说法 | 实际 | 符合? |
|------|---------|------|-------|
| 供货比例来源 | dwd_产品成本计算参数 | dwd_产品单位成本 中有 | ⚠️ **两个表都有** |
| 关联键 | PCI-BOM编码 | param 表关联键是 offering | ❌ **参数表无 pci_bom_code** |
| 月份维度 | 对应月份的供货比例 | param 表无 calc_month | ❌ **参数表无月份维度** |
| 成本来源 | - | cost 表已有 5 种成本 | ✅ **直接可用** |

---

## 📊 数据现状

### 各表的数据量

| 表名 | 行数 | 用途 | 状态 |
|------|-----|------|------|
| dwd_co_product_unit_cost_df | **0** | 产品成本（主表） | ❌ 空 |
| dwd_co_product_cost_param_df | 2 | 产品参数（备用） | ✅ 有数据 |
| dwd_co_external_purchase_product_df | 804 | 外协成本 | ✅ 有数据 |
| dwd_co_product_predict_cost_df | **0** | 输出表 | ❌ 空（新创建） |

### 重要发现

成本表（dwd_co_product_unit_cost_df）当前为**空表**，原因可能是：
1. 上游数据尚未加载
2. 数据加载流程未执行
3. 等待其他 DWD 层表的准备

---

## 🎯 对您提出的业务逻辑的评估

... (内容过长，已截断)
```

## 📄 61. 快速修复指南
**File**: `aianswer/2025-12-11/quick_fix_guide.md` | **Type**: 文档
**Preview**: 本指南提供关键问题的修复步骤。预计总时间：30 分钟（+ 1-2 天业务确认） 采集同步任务已在数据源侧完成 `mandt='800'` 的过滤，进入到 DWD 层的 SAP 数据已经是客户端 800 的数据。 **数据流**： ``` SAP 源系统（所有客户端数据） ↓ 采集同步任务（过滤：ma...

```
# 快速修复指南

## 概述
本指南提供关键问题的修复步骤。预计总时间：30 分钟（+ 1-2 天业务确认）

---

## ✅ 问题 1：SAP MANDT='800' 过滤 - 无需处理

### 原因
采集同步任务已在数据源侧完成 `mandt='800'` 的过滤，进入到 DWD 层的 SAP 数据已经是客户端 800 的数据。

**数据流**：
```
SAP 源系统（所有客户端数据）
  ↓
采集同步任务（过滤：mandt='800'）✅ 已处理
  ↓
ods_sap_erp_zhone_mat_unit_conversion_get_df（纯 800 数据）
ods_sap_erp_zhone_mat_purchase_price_get_df（纯 800 数据）
  ↓
dwd_co_quotation_bom_df（使用 ODS 数据）
```

因此，在 DWD 层的 SQL 中不需要重复添加 `mandt='800'` 过滤。

---

## 🔴 问题 1：工厂代码映射失效 ⏱️ 1-2天（业务确认）

### 位置
文件：`src/dwd/dwd_co_quotation_bom_df.sql`
具体：`subcon_price_calculation` CTE 中的 JOIN 条件

### 问题描述
PLM 的工厂代码与 SAP 的工厂代码不匹配，导致 JOIN 失败，外包单价全为 0。

**数据映射**：
```
PLM 工厂代码           SAP 工厂代码 (werks)      备注
'B010'        →        '2020'                  （需确认）
'1010'        →        '2020'                  （需确认）
'L001'        →        ?                       （需确认）
```

### 修复选项

#### 选项 A：创建映射表（推荐）

**Step 1: 创建映射表**

```sql
-- 在 DIM 或 DWD 层创建工厂代码映射表
CREATE TABLE IF NOT EXISTS hotzero_dim.dim_factory_mapping_df (
    plm_factory_code VARCHAR(20),      -- PLM 工厂代码
    sap_werks VARCHAR(20),             -- SAP 工厂代码
    factory_name VARCHAR(100),         -- 工厂名称
    status VARCHAR(1) DEFAULT 'Y',     -- 是否有效 Y/N
    insert_dt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY(plm_factory_code) DISTRIBUTED BY HASH(plm_factory_code)
)
DUPLICATE KEY(plm_factory_code);

-- 初始化数据（需业务确认）
INSERT INTO hotzero_dim.dim_factory_mapping_df VALUES
    ('B010', '2020', 'B工厂', 'Y', NOW()),
    ('1010', '2020', '中文工厂名', 'Y', NOW()),

... (内容过长，已截断)
```

## 📄 62. dwd_fin_expense_detail_df 生产数据与文档对齐审计
**File**: `audits/dwd/2026-03-11/dwd_fin_expense_detail_df_audit.md` | **Type**: 文档
**Preview**: **审计日期**: 2026-03-11 **对照文档**: `model_project/docs/model_csv/dwd_费用明细模型.csv` **脚本**: `model_project/src/dwd/dwd_fin_expense_detail_df.sql` **目标表**: `d...

```
# dwd_fin_expense_detail_df 生产数据与文档对齐审计

**审计日期**: 2026-03-11  
**对照文档**: `model_project/docs/model_csv/dwd_费用明细模型.csv`  
**脚本**: `model_project/src/dwd/dwd_fin_expense_detail_df.sql`  
**目标表**: `dwd.dwd_fin_expense_detail_df`

---

## 一、脚本与 DDL/文档 一致性

### 1. 字段对齐

| 项目 | 结论 |
|------|------|
| **最终 SELECT 列数** | 82 列，与 DDL 一致 |
| **列名与顺序** | 与 `dwd_fin_expense_detail_df_ddl.sql` 一致（含 ym, version, … insert_dt） |
| **文档标准字段** | 文档序号 1～82 的字段编码（ym, version, company_code, … source_mark, insert_dt）均已在脚本中输出 |

### 2. 值域与逻辑（文档约定）

| 字段 | 文档值域/规则 | 脚本实现 |
|------|----------------|----------|
| **version** | {V1, V2} | CROSS JOIN versions → 仅 V1、V2 ✅ |
| **source_mark** | BPC费用、手工调整、BPC调整 | 三路 union 分别赋值 ✅ |
| **fee_attribute** | 研发费用、销售费用、管理费用、制造费用 | 按 belong_dept + 成本中心首字 V/E/L/P/F + 产研费属映射 ✅ |
| **fee_type** | 经营、战投、经营不含 | 研发：SI 战投、奖金 经营不含、否则 经营；手工调整取填报 ✅ |
| **process_tag** | D-销服-* / D-研发-* 等 | 按 belong_dept + order_num/account_code/bu 等规则 ✅ |
| **fee_belongs** | 未关联 g 时=一级部门 | COALESCE(scope_fee_belongs, belong_dept) ✅ |
| **分摊比例** | 关联上取 alloc_factor，否则 1 | COALESCE(alloc.alloc_factor, 1) ✅ |
| **alloc_* 金额** | 原金额 × 分摊比例 | 脚本中已按比例计算 ✅ |

### 3. 来源表与关联

- a/h/b 三源 union、成本中心映射/费用映射/实体层级/科目、产研费属映射、**费用分摊范围配置表 g**（见下「最底层」逻辑）、**人员变动表 l**（BPC 调整不替换）、分摊比例 i 表：均已按文档接入 ✅  
- 设计中的「区域」用于分摊比例关联：**i.【分摊域】=【区域】**；文档「0. 优先取费用分摊比例配置表-【分摊参考项】，取不到则取 g 的【区域】」—— 当前脚本**分摊比例关联**已改为 **COALESCE(scope_sales_area_name, dept_province_zone) = alloc.alloc_domain**，与文档一致 ✅。

### 4. 费用分摊范围配置表 g：按文档「实体编码存在于路径」+ 取最大层级（2026-03-11 修正）

... (内容过长，已截断)
```

## 📄 63. SQL语法错误：缺少逗号分隔符
**File**: `ai_learning/lessons_learned/2025-12-22_sql_syntax_errors_missing_commas.md` | **Type**: 文档
**Preview**: **日期**: 2025-12-22 **问题分类**: SQL语法错误 / 格式问题 **严重程度**: 🔴 高（导致SQL无法编译） **影响范围**: dwd_sd_order_detail_df.sql 在重构 `dwd_sd_order_detail_df.sql` 时，因格式调整不当，导...

```
# SQL语法错误：缺少逗号分隔符

**日期**: 2025-12-22  
**问题分类**: SQL语法错误 / 格式问题  
**严重程度**: 🔴 高（导致SQL无法编译）  
**影响范围**: dwd_sd_order_detail_df.sql  

---

## 📋 问题概述

在重构 `dwd_sd_order_detail_df.sql` 时，因格式调整不当，导致两处关键位置**缺少逗号分隔符**，引发SQL编译错误：
1. **错误1**: 字段无法解析 - `Column 'vbap.vgbel' cannot be resolved`
2. **错误2**: 列数不匹配 - `Inserted target column count: 80 doesn't match select/value column count: 81`

---

## 🔴 错误详情

### 错误1：VBAP CTE字段缺少逗号

**错误信息**:
```
Getting analyzing error. Detail message: Column '`vbap`.`vgbel`' cannot be resolved.
```

**错误代码**（第169行）:
```sql
vbap AS (
    SELECT
        ...
        kwmeng,                      -- 订单数量
        kzwi1,                       -- 订单行金额_含税（含运费）
        netwr,                       -- 订单行金额_不含税（含运费）        vgbel,                       -- 参考原单号  ❌ 前一行缺少换行
        vgpos,                       -- 参考原单行号
        ...
```

**问题原因**:
- `netwr` 字段注释后**直接跟着 `vgbel`**，中间没有换行
- SQL解析器认为 `netwr,` 后面的内容是注释，导致 `vgbel` 字段未被包含在CTE中
- 后续主查询引用 `vbap.vgbel` 时找不到该字段

**正确代码**:
```sql
        netwr,                       -- 订单行金额_不含税（含运费）
        vgbel,                       -- 参考原单号  ✅ 独立成行
```

---

### 错误2：INSERT列表字段缺少逗号

**错误信息**:
```
Data truncation: Getting analyzing error. Detail message: 
Inserted target column count: 80 doesn't match select/value column count: 81.
```

**错误代码**（第97行）:
```sql
INSERT INTO dwd.dwd_sd_order_detail_df (
    ...
    order_item_amt_tax,              -- 52. 订单行项目金额_含税 ★字段重命名
    order_item_amt_notax,            -- 53. 订单行项目金额_不含税 ★字段重命名    order_item_tax_value,            -- 54. 订单行货值_含税  ❌ 前一行缺少换行

... (内容过长，已截断)
```

---

## 💡 Learning Tips
- 今天聚焦：理解 AI Agent 的核心逻辑（感知→推理→执行）
- 动手实验：运行 `kb_qa_mvp` 中的示例代码
- 思考：如何将知识库问答应用于你的业务场景？

---
*Generated: 2026-04-20 11:56 | HunterClaw Daily Learning*