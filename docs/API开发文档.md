# MCP数据服务器 API 开发文档 v2.1

> 版本: v2.1 | 更新: 2026-05-20 | 端口: 8766

---

## 1. 概述

MCP数据服务器提供A股市场的统一数据接口，支持实时行情、K线数据、市场概览、温度/恐慌指数计算等功能。

### 基础信息

| 项目 | 值 |
|------|-----|
| 协议 | HTTP/1.1 |
| 格式 | JSON |
| 编码 | UTF-8 |
| 端口 | 8766 |
| 认证 | Header `X-API-Token` |
| 限流 | 默认100次/分钟/IP |
| 文档 | `/docs` (Swagger UI) |
| 健康检查 | `/api/v2/health` |

---

## 2. 认证

所有API端点（除配置查询外）需要在请求头中携带Token：

```http
GET /api/v2/quote/600519 HTTP/1.1
Host: localhost:8766
X-API-Token: mcp-data-server-token
```

---

## 3. API端点

### 3.1 实时行情

**GET** `/api/v2/quote/{symbol}`

获取单只股票实时行情。

| 参数 | 类型 | 说明 |
|------|------|------|
| symbol | string | 股票代码，如 600519 |

**响应示例**:
```json
{
  "code": "600519",
  "name": "贵州茅台",
  "price": 1680.50,
  "prev_close": 1675.00,
  "open": 1678.00,
  "high": 1685.00,
  "low": 1670.00,
  "volume": 2345600,
  "amount": 3945678900.00,
  "chg_pct": 0.33,
  "timestamp": "2026-05-20T09:35:00"
}
```

### 3.2 K线数据

**GET** `/api/v2/kline/{symbol}`

获取历史K线数据。

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| symbol | string | ✅ | 股票代码 |
| start_date | string | ✅ | 开始日期 (YYYYMMDD) |
| end_date | string | ❌ | 结束日期 (默认今天) |
| adjust | string | ❌ | 复权类型: qfq/hfq/None |

### 3.3 市场概览

**GET** `/api/v2/market/overview`

获取全市场概览数据。

**响应示例**:
```json
{
  "indices": [...],
  "market_sentiment": {
    "up": 2156,
    "down": 1234,
    "limit_up": 45,
    "limit_down": 8
  },
  "timestamp": "2026-05-20T09:35:00"
}
```

---

## 4. v2.1 新增端点

### 4.1 全市场指数

**GET** `/api/v2/market/indices`

获取7大主要指数实时行情 + 涨跌比。

**响应**:
```json
{
  "indices": [
    {"code": "sh000001", "name": "上证指数", "price": 4135.20, "chg_pct": 0.12},
    {"code": "sz399001", "name": "深证成指", ...},
    ...
  ],
  "breadth": {
    "up": 4,
    "down": 3,
    "avg_chg_pct": 0.08,
    "up_ratio": 57.1
  },
  "timestamp": "..."
}
```

### 4.2 市场广度

**GET** `/api/v2/market/breadth`

涨跌家数统计、涨停跌停数据、广度评级。

| 广度评级 | 条件 |
|---------|------|
| 强势 | 涨家数 > 跌家数×2 |
| 偏强 | 涨家数 > 跌家数 |
| 均衡 | ~1:1 |
| 偏弱 | 跌家数 > 涨家数×2 |

### 4.3 市场温度/恐慌指数

**GET** `/api/v2/market/temperature`

计算市场温度(0-100)和恐慌指数(0-100, 越低越恐慌)。

**温度标签**:
| 温度 | 标签 | 建议仓位 |
|------|------|---------|
| ≥70 | 过热 | ≤10% |
| 50-69 | 正常 | ≤50% |
| 30-49 | 偏冷 | ≤30% |
| <30 | 冰点 | 0%(强制空仓) |

**恐慌标签**:
| 恐慌 | 标签 | 含义 |
|------|------|------|
| ≥60 | 安全 | 正常交易 |
| 40-59 | 谨慎 | 减仓 |
| 25-39 | 偏冷 | 只出不进 |
| <25 | 冰点 | 全面禁止(V10) |

### 4.4 批量行情

**POST** `/api/v2/batch/quotes`

最多20只股票批量实时行情。

**请求体**:
```json
["600519", "000858", "300750", "601138"]
```

**响应**:
```json
{
  "quotes": [...],
  "errors": [],
  "total": 4,
  "timestamp": "..."
}
```

### 4.5 扩展健康检查

**GET** `/api/v2/health/metrics`

综合监控端点，包含缓存、Redis、限流状态。

---

## 5. 缓存系统

### 5.1 双层缓存架构

```
请求 → 内存缓存(L1) → Redis缓存(L2, 可选) → 数据源
         ↓ 命中                     ↓ 命中
       返回数据                 回写L1+返回
```

### 5.2 Redis配置

```bash
# 环境变量
export REDIS_URL="redis://localhost:6379/0"

# Python代码
from src.cache_manager import cache_manager
cache_manager.init_redis()  # 自动从环境变量读取
```

### 5.3 TTL配置

| 数据类型 | TTL | 说明 |
|---------|-----|------|
| 实时行情 | 300s (5分钟) | 交易时段频繁变化 |
| K线数据 | 86400s (1天) | 日线每日更新 |
| 财务数据 | 86400s (1天) | 季度更新 |
| 板块数据 | 300s (5分钟) | 交易时段更新 |

---

## 6. 限流策略

| 级别 | 限制 | 说明 |
|------|------|------|
| 默认 | 100次/分钟 | 普通API调用 |
| 突发 | 200次/分钟 | 短时突发 |
| 窗口 | 60秒 | 滑动窗口 |

限流统计: `GET /api/v2/rate-limit/stats`

---

## 7. 错误码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 参数错误 |
| 401 | Token无效 |
| 404 | 数据未找到 |
| 429 | 请求过频 |
| 500 | 服务器内部错误 |

---

## 8. 使用示例

### Python
```python
import requests

headers = {"X-API-Token": "mcp-data-server-token"}

# 获取行情
r = requests.get("http://localhost:8766/api/v2/quote/600519", headers=headers)
print(r.json())

# 批量行情
r = requests.post("http://localhost:8766/api/v2/batch/quotes",
    json=["600519", "000858"], headers=headers)
print(r.json())

# 市场温度
r = requests.get("http://localhost:8766/api/v2/market/temperature", headers=headers)
temp = r.json()
print(f"温度: {temp['temperature']}°C ({temp['temperature_label']})")
print(f"恐慌: {temp['panic_index']} ({temp['panic_label']})")
```

---

*文档自动生成 | OpenClaw | 2026-05-20 05:00 AM*
