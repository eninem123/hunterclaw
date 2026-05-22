# MCP数据服务器工具文档 v1.3

> 猎手MCP工具集成的完整参考指南
> 更新：2026-05-17

---

## 变更日志

### v1.3 (2026-05-17)
- 新增 `get_market_scan` 快速市场扫描工具（一站式市场快照）
- 重构恐慌/时机计算逻辑：消除tools和handlers间的代码重复（DRY原则）
- `get_panic_index`, `get_market_timing` 计算逻辑统一使用共享 `_compute_panic()`/`_compute_timing()` 函数
- `get_market_timing` 新增 `market_state` 状态标签字段
- `get_market_sentiment_enhanced` 新增跌停家数判断指标
- 服务版本号升级至 `1.1.0`
- 工具清单更新至 **25个MCP工具**

### v1.2 (2026-05-15)
- 新增 `get_sector_money_flow_ratio` (V05)
- 新增 `get_futures_basis` (V06)
- 新增 `get_etf_money_flow` (V07)
- 工具清单更新至 **22个MCP工具**

### v1.1 (2026-05-14)
- 新增 `get_market_sentiment_enhanced`
- `get_market_sentiment` 响应结构升级
- 工具调用增加自动重试和降级逻辑

### v1.0 (2026-05-11)
- 初版发布，18个MCP工具

---

## 1. 工具清单

### 实时行情工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_realtime_quote` | 单只股票实时行情 | `symbol`: 股票代码 | v1.0 |
| `get_realtime_quotes_batch` | 批量股票行情 | `symbols`: 逗号分隔代码 | v1.0 |
| `get_index_quotes` | 主要指数行情 | 无 | v1.0 |
| `get_market_overview` | 市场概览 | 无 | v1.0 |

### K线数据工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_daily_kline` | 日K线 | `symbol`, `start_date`, `end_date`, `adjust` | v1.0 |
| `get_weekly_kline` | 周K线 | `symbol`, `start_date`, `end_date` | v1.0 |
| `get_minute_kline` | 分钟K线 | `symbol`, `period`(1/5/15/30/60) | v1.0 |

### 资金流向工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_money_flow` | 个股主力资金流向 | `symbol` | v1.0 |
| `get_north_money` | 北向资金 ⚠️ T+1盘后 | `period` | v1.0 |
| `get_sector_money_flow` | 板块资金流向排名 | 无 | v1.0 |
| `get_sector_money_flow_ratio` | V05: 板块主力净流入率 | `limit` | v1.2 |
| `get_etf_money_flow` | V07: ETF资金流向 | `indicator` | v1.2 |

### 期指衍生品工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_futures_basis` | V06: 期指基差信号 | 无 | v1.2 |

### 财务数据工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_financial_report` | 财务报表 | `symbol`, `report_type` | v1.0 |
| `get_roe_data` | ROE核心指标 | `symbol` | v1.0 |
| `get_pe_pb` | 市盈率/市净率 | `symbol` | v1.0 |

### 板块数据工具

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_sector_list` | 板块列表 | `sector_type` | v1.0 |
| `get_hot_sectors` | 热门板块排名 | `limit` | v1.0 |
| `get_sector_stocks` | 板块成分股 | `sector_name` | v1.0 |

### 市场情绪/时机工具 🆕

| 工具名 | 描述 | 参数 | 版本 |
|--------|------|------|------|
| `get_market_sentiment` | 综合市场情绪 | 无 | v1.0 |
| `get_market_sentiment_enhanced` | 增强版情绪(多源聚合) | 无 | v1.1 |
| `get_panic_index` | 恐慌指数(0-100) | 无 | v4.0 |
| `get_market_timing` | 市场时机评估(v5.0含state) | 无 | v4.0 |
| **`get_market_scan`** 🆕 | **快速市场扫描** | **无** | **v5.0** |
| `get_v4_rules_summary` | 猎手规则库摘要 | 无 | v4.0 |

---

## 2. 新增工具: get_market_scan (v5.0)

### 概述
一站式快速市场扫描工具。整合指数涨跌、涨跌家数、恐慌指数、板块轮动、资金流向，返回结构化的市场快照。

适用于需要快速了解市场全貌的场景（开盘前/盘中快速检查）。

### 返回结构

```json
{
  "scan_time": "2026-05-17 09:35:00",
  "market_temperature": 45,
  "temperature_label": "偏冷",
  "panic_index": 38,
  "panic_label": "偏冷",
  "max_position_pct": 30,
  "indices": [
    {"name": "上证指数", "price": 3250.5, "change_pct": -0.35, ...}
  ],
  "breadth": {
    "rising": 1200,
    "falling": 2800,
    "flat": 150,
    "limit_up": 35,
    "limit_down": 12,
    "up_ratio_pct": 28.6,
    "down_ratio_pct": 66.7
  },
  "top_sectors": [
    {"板块名称": "银行", "主力净流入": 12.5, ...},
    {"板块名称": "半导体", "主力净流入": 8.3, ...}
  ],
  "version": "v5.0"
}
```

### 字段说明
| 字段 | 类型 | 说明 |
|------|------|------|
| `scan_time` | string | 扫描时间 |
| `market_temperature` | int | 市场温度(0-100) |
| `temperature_label` | string | 温度标签 |
| `panic_index` | int | 恐慌指数(0-100) |
| `panic_label` | string | 恐慌标签 |
| `max_position_pct` | int | 建议仓位上限(%) |
| `indices` | array | 主要指数行情(前6个) |
| `breadth.rising` | int | 上涨家数 |
| `breadth.falling` | int | 下跌家数 |
| `breadth.limit_up` | int | 涨停家数 |
| `breadth.limit_down` | int | 跌停家数 |
| `breadth.up_ratio_pct` | float | 上涨比例(%) |
| `top_sectors` | array | 资金流入前5板块 |

---

## 3. 架构说明 (v1.3重构)

v1.3进行了代码重构，消除恐慌指数和时机评估的重复逻辑：

### 重构前
```
create_mcp_tools():
  get_panic_index()    → 内联恐慌计算逻辑
  get_market_timing()  → 内联时机计算逻辑

create_mcp_handlers():
  _panic_index_handler → 完全相同的恐慌计算逻辑 (代码重复)
  _timing_handler      → 完全相同的时机计算逻辑 (代码重复)
```

### 重构后 (v1.3)
```
共享计算函数:
  _compute_panic()     → 恐慌指数计算 (唯一入口)
  _compute_timing()    → 市场时机计算 (唯一入口)
  _compute_market_scan() → 市场扫描 (依赖_compute_timing)

create_mcp_tools():
  get_panic_index()    → 调用 _compute_panic()
  get_market_timing()  → 调用 _compute_timing()
  get_market_scan()    → 调用 _compute_market_scan()

create_mcp_handlers():
  get_panic_index      → lambda: _compute_panic()
  get_market_timing    → lambda: _compute_timing()
  get_market_scan      → lambda: _compute_market_scan()
```

---

## 4. V11规则说明 (新增)

### V11: 创新高不追涨

**规则**：近1年价格新高禁止追涨建仓

**原因分析**：
- 价格创新高时追涨风险高，容易被高位套牢
- V11规则与R02（五位一体）配合，当一个标的突破历史新高时，即使其他维度都达标，也禁止作为买入候选

**已在以下模块应用**：
- `get_v4_rules_summary` 规则摘要包含V11

---

## 5. 北向数据变更总结

⚠️ **重要提示**：自2026-05-13起，北向资金（沪深港通）不再实时披露，改为T+1盘后数据。

影响工具：
- `get_north_money` → 返回T+1盘后数据
- `get_market_sentiment` → 北向字段标注为盘后
- `get_market_sentiment_enhanced` → 北向标注已过时
- `get_market_timing` → 不依赖北向实时数据

---

## 6. 性能优化建议

### 缓存策略
| 数据类型 | 缓存TTL | 工具 |
|---------|--------|------|
| 实时行情 | 30-60秒 | `get_realtime_quote` |
| K线数据 | 1天 | `get_daily_kline` |
| 财务数据 | 1天 | `get_financial_report` |
| 板块数据 | 5分钟 | `get_sector_money_flow` |

### 批量调用
- 使用 `get_realtime_quotes_batch` 替代多个单次调用
- 每个batch最大支持50个代码

---

## 7. 常见错误处理

| 错误码 | 原因 | 处理方式 |
|--------|------|---------|
| -32601 | Unknown tool | 检查工具名是否在清单中 |
| -32602 | Invalid params | 检查参数字段名和类型 |
| HTTP 503 | 数据源不可用 | 自动重试1次后返回降级数据 |
| 空数据 | 股票代码不存在 | 返回含error字段的JSON |

---

*MCP工具文档 v1.3 | OpenClaw龙虾Agent | 2026-05-17*
