# MCP数据服务器工具文档 v1.1

> 猎手MCP工具集成的完整参考指南
> 更新：2026-05-14

---

## 变更日志

### v1.1 (2026-05-14)
- 新增 `get_market_sentiment_enhanced` 增强情绪分析工具
- `get_market_sentiment` 响应结构升级：添加情绪评分、标签、评分理由
- 所有工具描述统一标注北向资金变更提示（2026-05-13起改为T+1盘后）
- 工具调用增加自动重试和降级逻辑
- `get_daily_kline` 增加日期格式/范围验证 + 多数据源降级链
- api_server_v2 缓存系统统一为共享 `cache_manager.CacheManager`
- api_server_v2 新增 `/api/v2/rate-limit/stats` 端点
- 文档新增「性能优化建议」和「常见错误处理」章节

### v1.0 (2026-05-11)
- 初版发布，18个MCP工具

---

## 1. 工具清单

### 实时行情工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_realtime_quote` | 获取单只股票实时行情 | `symbol`: 股票代码 |
| `get_realtime_quotes_batch` | 批量获取股票行情 | `symbols`: 逗号分隔代码列表 |
| `get_index_quotes` | 获取主要指数（上证/深证/创业板/科创50） | 无 |
| `get_market_overview` | 市场概览（涨跌停/涨跌家数/情绪） | 无 |

### K线数据工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_daily_kline` | 日K线（复权可选，含日期验证+降级链） | `symbol`, `start_date`, `end_date`, `adjust` |
| `get_weekly_kline` | 周K线 | `symbol`, `start_date`, `end_date` |
| `get_minute_kline` | 分钟K线 | `symbol`, `period`(1/5/15/30/60) |

### 资金流向工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_money_flow` | 个股主力资金流向 | `symbol` |
| `get_north_money` | 北向资金（沪深港通）⚠️ T+1盘后数据 | `period`: daily/weekly/monthly |
| `get_sector_money_flow` | 板块资金流向排名 | 无 |

### 财务数据工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_financial_report` | 财务报表（ROE/毛利率/净利率） | `symbol`, `report_type` |
| `get_roe_data` | ROE核心指标 | `symbol` |
| `get_pe_pb` | 市盈率/市净率 | `symbol` |

### 板块数据工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_sector_list` | 板块列表 | `sector_type`: industry/concept |
| `get_hot_sectors` | 热门板块排名 | `limit`: 返回数量 |
| `get_sector_stocks` | 板块成分股 | `sector_name`: 板块名称 |

### 市场情绪工具

| 工具名 | 描述 | 参数 |
|--------|------|------|
| `get_market_sentiment` | 综合市场情绪指标（含评分、标签、评分理由） | 无 |
| `get_market_sentiment_enhanced` | **增强版**情绪分析，聚合涨跌家数+板块资金+指数+北向多源数据，返回0-100评分 | 无 |

---

## 2. get_market_sentiment_enhanced 详解

### 返回结构

```json
{
  "market_sentiment_score": 65,
  "sentiment_label": "偏乐观",
  "reasons": ["涨跌比>1.2，市场偏强", "涨停45家，情绪高涨", "资金流入最强板块: 软件开发"],
  "overview": { "total": 5000, "rising": 2800, "falling": 1800, "limit_up": 45, "limit_down": 8 },
  "indices": [ /* 主要指数行情 */ ],
  "sector_flow": [ /* 前5大资金流入板块 */ ],
  "north_money": [ /* 北向资金（T+1盘后） */ ],
  "north_money_note": "北向资金已于2026-05-13起改为T+1盘后数据，非实时",
  "timestamp": "2026-05-14T10:30:00",
  "source": "multi-source aggregated"
}
```

### 情绪评分规则

| 分数区间 | 标签 | 说明 |
|----------|------|------|
| 0-20 | 极度恐慌 | 跌停>30或涨跌比<0.3 |
| 21-40 | 偏恐慌 | 跌停10+或涨跌比<0.8 |
| 41-60 | 中性 | 涨跌均衡 |
| 61-80 | 偏乐观 | 涨跌比>1.2或涨停50+ |
| 81-100 | 极度乐观 | 涨跌比>2或涨停100+ |

---

## 3. 重要注意事项

### ⚠️ 北向资金变更（2026-05-13）
自2026年5月13日起，北向资金（沪深港通）数据**不再实时披露**，改为**T+1盘后数据**。

影响工具：
- `get_north_money` — 数据来源变更为前一天的盘后统计
- `get_market_sentiment` — 情绪指标中的北向部分为延迟数据
- `get_market_sentiment_enhanced` — 同样使用T+1盘后北向数据

### ⚠️ 数据延迟说明
- 实时行情：10-30秒延迟
- 资金流向：15分钟延迟
- 财务数据：T+1更新（季报/年报发布后次日）
- 板块数据：盘中实时

### ⚠️ 频率限制
- MCP STDIO模式：每次调用间隔至少0.5秒
- HTTP API模式：默认每分钟100次限制（可配置）

---

## 4. MCP服务器部署

### STDIO模式（OpenClaw集成）

```json
// openclaw.json 或 openclaw.local.json
{
  "mcp": {
    "servers": {
      "mcp-data-server": {
        "command": "/root/.openclaw/venv/mcp-data-server/bin/python",
        "args": ["-m", "src.main", "--stdio"],
        "cwd": "/root/.openclaw/workspace/猎手模拟交易/mcp-data-server"
      }
    }
  }
}
```

### HTTP API模式（独立服务）

```bash
# 启动 v2 服务（推荐）
cd /root/.openclaw/workspace/猎手模拟交易/mcp-data-server
source venv/mcp-data-server/bin/activate
python -m uvicorn src.api_server_v2:app --host 0.0.0.0 --port 8766

# 或通过systemd
systemctl start mcp-data-server
```

HTTP API调用示例：
```bash
# v1 接口
curl -H "X-API-Token: mcp-data-server-token" \
  http://localhost:8766/api/v1/quote/000001

# v2 接口
curl -H "X-API-Token: mcp-data-server-token" \
  http://localhost:8766/api/v2/quote/000001

# 健康检查（含缓存统计）
curl http://localhost:8766/api/v2/health

# 限流统计
curl -H "X-API-Token: mcp-data-server-token" \
  http://localhost:8766/api/v2/rate-limit/stats
```

---

## 5. API版本对比

| 特性 | v1 (api_server.py) | v2 (api_server_v2.py) |
|------|---------------------|----------------------|
| 框架 | FastAPI | FastAPI |
| 数据源 | akshare | akshare + 腾讯行情 |
| 缓存 | MemoryCache | MemoryCache（共享cache_manager） |
| 异步支持 | ❌ 同步 | ✅ 异步 |
| 限流 | ❌ | ✅ RateLimiter |
| 重试机制 | ❌ | ✅ 自动重试x3 |
| 健康检查 | `/api/v1/health` | `/api/v2/health`（含缓存统计） |
| 限流统计 | ❌ | `/api/v2/rate-limit/stats` |
| 缓存管理 | ❌ | `/api/v2/cache/stats` + `/api/v2/cache/clear` |
| OpenAPI文档 | ❌ | ✅ `/docs` `/redoc` |

---

## 6. 猎手系统集成

### 信号处理器集成（v3.9）

```python
# signal_processor.py 使用 MCP 工具
import json
import subprocess

def call_mcp_tool(tool_name, **kwargs):
    """通过mcporter调用MCP工具"""
    cmd = [
        "mcporter", "call", f"mcp-data-server.{tool_name}"
    ]
    for k, v in kwargs.items():
        cmd.append(f"{k}={v}")
    cmd.append("--outputjson")
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode == 0:
        return json.loads(result.stdout)
    return None

# 示例：获取持仓现价
price_data = call_mcp_tool("get_realtime_quote", symbol="000001")
```

### 选股器集成

```python
# stock_picker.py 使用 MCP 工具验证K线趋势
from datetime import datetime

def verify_with_mcp(code):
    """用MCP工具验证股票趋势"""
    kline_data = call_mcp_tool(
        "get_daily_kline",
        symbol=code,
        start_date="20260401",
        end_date=datetime.now().strftime("%Y%m%d"),
        adjust="qfq"
    )
    if kline_data and len(kline_data) >= 2:
        return True
    return False

# 使用增强情绪分析
def get_market_temperature():
    """获取市场温度"""
    sentiment = call_mcp_tool("get_market_sentiment_enhanced")
    if sentiment and 'market_sentiment_score' in sentiment:
        return sentiment['market_sentiment_score']
    return 50
```

---

## 7. mcporter使用速查

```bash
# 列出所有已配置MCP服务器
mcporter list

# 查看服务器工具schema
mcporter list mcp-data-server --schema

# 调用工具（Selector语法）
mcporter call mcp-data-server.get_realtime_quote symbol=000001

# 调用工具（JSON payload）
mcporter call mcp-data-server.get_daily_kline --args '{"symbol":"000001","start_date":"20260401","adjust":"qfq"}'

# 输出JSON格式
mcporter call mcp-data-server.get_market_sentiment --output json
mcporter call mcp-data-server.get_market_sentiment_enhanced --output json

# 添加HTTP服务器
mcporter config add mcp-data-server --url http://localhost:8766 --header "X-API-Token: mcp-data-server-token"

# 启动守护进程
mcporter daemon start
```

---

## 8. 常见错误处理

### 8.1 工具调用失败

```
{"error": "服务临时不可用，请稍后重试", "fallback": true}
```

**原因**: 数据源暂时不可用（如AKShare API超时）
**处理**: 内置自动重试1次 + 降级逻辑，等待30秒后重试

### 8.2 K线日期格式错误

```
{"error": "start_date 格式无效: abc123，需要 YYYYMMDD"}
```

**原因**: 日期参数不符合 YYYYMMDD 或 YYYY-MM-DD 格式
**处理**: 检查日期参数格式

### 8.3 股票代码错误

```
{"error": "股票代码 XXXXXX 不存在"}
```

**原因**: 系统中找不到该股票代码
**处理**: 确认代码为6位数字，如 "000001"

### 8.4 北向资金数据为空

```
{"north_money": [], "north_money_note": "北向资金已于2026-05-13起改为T+1..."}
```

**原因**: 非交易时段或无盘后数据
**处理**: 此为正常情况，北向数据仅T+1盘后可用

### 8.5 API限流

```
HTTP 429 Too Many Requests
{"error": "Rate limit exceeded"}
```

**原因**: 超过每分钟100次调用限制
**处理**: 降低调用频率，或在 api_server_v2.py 中调整 `config.RATE_LIMIT`

---

## 9. 性能优化建议

### 9.1 缓存策略

| 数据类型 | TTL | 建议 |
|----------|-----|------|
| 实时行情 | 5分钟 | 无需频繁调用，缓存命中率高 |
| K线数据 | 1天 | 每日收盘后数据不变 |
| 分钟K线 | 5分钟 | 盘中更新 |
| 财务数据 | 1天 | 变化频率低 |
| 板块数据 | 5分钟 | 盘中可适当降低频率 |

### 9.2 调用建议

1. **优先使用批量接口**: `get_realtime_quotes_batch` 代替多次调用 `get_realtime_quote`
2. **缓存感知**: 减少重复查询，特别是财务数据（T+1更新）
3. **避免非交易时段查询**: 9:30-15:00 外的数据无变化
4. **情绪工具选择**: 普通场景用 `get_market_sentiment`，深度分析用 `get_market_sentiment_enhanced`
5. **K线查询范围**: 默认1年，避免超过5年的查询范围

### 9.3 最大请求限制

| 维度 | 限制 |
|------|------|
| MCP STDIO单次调用 | 0.5秒间隔 |
| HTTP API默认 | 100次/分钟 |
| HTTP API突发 | 200次/分钟 |
| K线查询范围 | 最多5年 |

---

## 10. 猎手系统v3.9 MCP集成状态

| 组件 | 状态 | 说明 |
|------|------|------|
| `mcp-data-server` | ✅ 已部署 | `/root/.openclaw/workspace/猎手模拟交易/mcp-data-server/` |
| 信号处理器 | ✅ 已优化 | signal_processor.py v3.9 含涨停过滤/量比门槛 |
| 选股器 | ✅ 已优化 | stock_picker.py 含涨停过滤 |
| backtest_mcp | ✅ 可用 | china-stock-mcp集成 |
| mcporter | ✅ 已配置 | Skill文档完整 |

---

## 11. 故障排查

```bash
# 检查MCP服务器状态
mcporter list

# 检查mcp-data-server进程
ps aux | grep mcp-data-server

# 检查端口占用
lsof -i :8766

# 查看服务日志
journalctl -u mcp-data-server -f

# 测试API健康检查
curl http://localhost:8766/api/v2/health

# 手动调用MCP工具调试
mcporter call --stdio "python3 -m src.main --stdio" get_realtime_quote symbol=000001

# 检查语法
python3 -m py_compile src/main.py
python3 -m py_compile src/data_service.py
python3 -m py_compile src/api_server_v2.py
```

---

_文档版本：v1.1 | 更新：2026-05-14_
