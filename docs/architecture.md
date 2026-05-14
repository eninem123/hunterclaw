# HunterClaw 系统架构

## 1. 系统概述

HunterClaw 是基于 OpenClaw Multi-Agent 框架的 A 股智能交易系统，采用三层 AI Agent 协作架构，通过 MCP (Model Context Protocol) 协议统一提供数据服务。

## 2. 架构图

```
                            ┌─────────────────┐
                            │      用户       │
                            │   （微信）      │
                            └────────┬────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────┐
│                     🦞 OpenClaw Gateway                      │
│                                                             │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐   │
│  │  WeChat插件  │    │  Cron调度   │    │  Memory插件  │   │
│  └──────┬──────┘    └──────┬──────┘    └──────┬──────┘   │
│         │                  │                  │           │
│         ▼                  ▼                  ▼           │
│  ┌─────────────────────────────────────────────────────┐   │
│  │              🦞 Claw（主Agent）                      │   │
│  │  - 接收用户消息                                     │   │
│  │  - 协调子Agent                                      │   │
│  │  - 交易执行（auto_trade.py）                        │   │
│  │  - 微信推送 + mcporter调用MCP工具                    │   │
│  └─────────────────────────────────────────────────────┘   │
└─────────────────────────┬─────────────────────────────────┘
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
    ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
    │   🔮 Hermes  │ │  🧠 GBrain  │ │  📊 AI Hedge │
    │   策略Agent  │ │   知识库    │ │   美股风向标 │
    │   (复盘优化)  │ │  (语义搜索)  │ │   (全球情绪) │
    └──────┬──────┘ └─────────────┘ └──────┬──────┘
           │                               │
           └───────────┬───────────────────┘
                       │
                       ▼
          ┌─────────────────────────┐
          │  🗄️ MCP Data Server     │
          │  (mcp-data-server)      │
          │                         │
          │  ┌─────────────────┐    │
          │  │   main.py       │ ◄──│── STDIO (mcporter)
          │  │  (STDIO模式)    │    │
          │  └────────┬────────┘    │
          │           │             │
          │  ┌────────▼────────┐   │
          │  │ api_server_v2.py│ ◄──│── HTTP REST
          │  │  (HTTP模式)     │   │
          │  └────────┬────────┘   │
          │           │            │
          │  ┌────────▼────────┐  │
          │  │ data_service.py │   │
          │  │  (AKShare封装)  │   │
          │  └────────┬────────┘  │
          │           │           │
          │  ┌────────▼────────┐  │
          │  │ cache_manager.py │  │
          │  │  (共享缓存)      │  │
          │  └─────────────────┘  │
          └─────────────────────────┘
```

## 3. MCP 数据服务器模块

### 3.1 模块结构

```
mcp-data-server/
├── src/
│   ├── main.py              # MCP STDIO入口
│   │     ├─ create_mcp_tools()       → 19个工具定义
│   │     ├─ create_mcp_handlers()    → 工具处理器映射
│   │     ├─ _get_market_sentiment_enhanced() → 增强情绪分析
│   │     ├─ _validate_tools_list()   → tools/list格式验证
│   │     ├─ _safe_handler_call()     → 自动重试+降级
│   │     └─ run_stdio_server()       → STDIO JSON-RPC循环
│   │
│   ├── api_server_v2.py     # HTTP API v2（FastAPI异步）
│   │     ├─ /api/v2/health          → 健康检查（含缓存统计）
│   │     ├─ /api/v2/quote/{symbol}  → 实时行情
│   │     ├─ /api/v2/kline/{symbol}  → K线数据
│   │     ├─ /api/v2/market/overview → 市场概览
│   │     ├─ /api/v2/cache/stats     → 缓存统计
│   │     ├─ /api/v2/cache/clear     → 清空缓存
│   │     ├─ /api/v2/rate-limit/stats→ 限流统计
│   │     └─ /api/v2/rate-limit/config→ 限流配置
│   │
│   ├── data_service.py      # 核心数据服务（AKShare封装）
│   │     ├─ 实时行情（单只/批量/指数/概览）
│   │     ├─ K线（日/周/分钟，含日期验证+降级链）
│   │     ├─ 资金流向（个股/北向/板块）
│   │     ├─ 财务数据（报表/ROE/PE-PB）
│   │     ├─ 板块数据（列表/热门/成分股/行情）
│   │     └─ 市场情绪（基础版+增强版）
│   │
│   └── cache_manager.py     # 缓存管理
│         ├─ MemoryCache     → 线程安全内存缓存
│         ├─ CacheManager    → 缓存键管理 + 兼容v2接口
│         └─ TTL: 实时300s / K线86400s / 财务86400s
│
└── requirements.txt
```

### 3.2 双模式通信

| 模式 | 协议 | 端口/通道 | 适用场景 |
|------|------|-----------|----------|
| STDIO | JSON-RPC 2.0 | stdin/stdout | OpenClaw MCP插件/mcporter |
| HTTP | FastAPI REST | 8766 | 独立API服务/浏览器调试 |

### 3.3 数据源

- **AKShare**：实时行情、K线、财务、板块（主要数据源）
- 所有方法受 `_rate_limit` 保护（0.5秒间隔）
- 支持降级链：主源 → 不复权 → 备用接口

### 3.4 缓存策略

| 数据类型 | TTL | 说明 |
|----------|-----|------|
| 实时行情 | 5min (300s) | 盘中变化较快 |
| 分钟K线 | 5min (300s) | 盘中更新 |
| 板块数据 | 5min (300s) | 盘中变化 |
| 日K线 | 1天 (86400s) | 收盘后不变 |
| 周K线 | 1天 (86400s) | 收盘后不变 |
| 财务数据 | 1天 (86400s) | 变化频率低 |

## 4. Agent 职责

### 4.1 Claw（主控Agent）

| 属性 | 说明 |
|------|------|
| 运行时 | OpenClaw main session |
| 角色 | 执行者、协调者、数据消费端 |
| 核心能力 | 代码执行、文件操作、消息推送、mcporter调用MCP工具 |
| 数据获取 | 通过 `mcporter call mcp-data-server.*` 调用18个MCP工具 |

### 4.2 Hermes（策略Agent）

| 属性 | 说明 |
|------|------|
| 运行时 | Hermès CLI subagent |
| 角色 | 策略顾问、记忆整理、复盘分析 |
| 触发方式 | Cron 15:30 / 22:00 |
| 输出 | 策略优化建议.md |
| 数据依赖 | 通过MCP工具获取历史数据和情绪指标 |

### 4.3 GBrain（知识库）

| 属性 | 说明 |
|------|------|
| 运行时 | PGLite 本地数据库 |
| 角色 | 长期记忆、语义搜索 |
| 规则 | 先查GBrain再调外部API |

### 4.4 MCP Data Server（数据引擎）

| 属性 | 说明 |
|------|------|
| 入口 | `main.py --stdio` / `api_server_v2.py` |
| 角色 | 统一数据接口、缓存加速、限流保护 |
| 数据源 | AKShare + 多源降级 |
| 工具数 | 19个（含增强情绪分析） |
| 缓存 | 共享CacheManager（内存，线程安全） |

## 5. 数据流

### 5.1 MCP工具调用路径

```
Agent（Claw/Hermes）
       │
       ├──→ mcporter call mcp-data-server.get_realtime_quote symbol=000001
       │
       ▼
┌───────────────────────────────┐
│  main.py (STDIO)              │
│                               │
│  1. validate_tools_list()     │ ← tools/list格式验证
│  2. safe_handler_call()       │ ← 自动重试1次+降级
│  3. data_service.xxx()        │ ← AKShare + 缓存
│  4. 返回 JSON-RPC response    │
└───────────────────────────────┘
```

### 5.2 HTTP API 调用路径

```
Client (curl/browser)
       │
       ├──→ GET /api/v2/quote/000001
       │     Header: X-API-Token
       │
       ▼
┌───────────────────────────────┐
│  api_server_v2.py (HTTP)      │
│                               │
│  1. verify_token()            │ ← Token验证
│  2. check_rate_limit()        │ ← 限流检查（100次/分钟）
│  3. cache.get()               │ ← 查缓存
│  4. DataService.fetch()       │ ← 异步请求+重试x3
│  5. cache.set()               │ ← 写缓存
│  6. 返回 JSON response        │
└───────────────────────────────┘
```

### 5.3 盘中交易流程

```
1. Cron触发（9:30-14:30每30分钟）
       │
       ▼
2. auto_trade.py 执行检测
       │
       ├──→ 通过MCP工具获取持仓实时行情
       │     （get_realtime_quote → 止损/止盈检查）
       │
       ├──→ 通过MCP工具计算市场温度
       │     （get_market_sentiment_enhanced → 情绪评分）
       │
       └──→ 判断是否触发熔断
       │
       ▼
3. 生成持仓报告
       │
       ▼
4. 写入 pending-summaries/
       │
       ▼
5. 心跳检测到 → 推送微信
```

### 5.4 收盘复盘流程

```
1. Cron触发（15:30）
       │
       ▼
2. strategy_analysis.sh 执行
       │
       ▼
3. Hermes 生成策略分析
       │
       ├──→ 通过MCP工具读取持仓数据
       │     （get_money_flow → 主力资金分析）
       │
       ├──→ 通过MCP工具读取今日K线
       │     （get_daily_kline → 技术指标计算）
       │
       └──→ 对比预测vs实际
       │
       ▼
4. 输出策略优化建议.md
       │
       ▼
5. 推送微信
```

## 6. 安全机制

### 6.1 熔断机制

```
总回撤 ≥ 3% → 触发熔断
       │
       ├──→ 禁止新买入
       └──→ 必要时清仓
```

### 6.2 止损止盈

```
止损：-5%（绝对红线，触发必走）
止盈：+10%（达标分批走）
```

### 6.3 仓位限制

```
单日买入：≤ 3次
单只仓位：≤ 30%
```

## 7. MCP工具清单

| 工具名 | 分类 | 数据来源 | 说明 |
|--------|------|----------|------|
| `get_realtime_quote` | 行情 | AKShare | 单只实时行情 |
| `get_realtime_quotes_batch` | 行情 | AKShare | 批量行情 |
| `get_index_quotes` | 行情 | AKShare | 主要指数 |
| `get_market_overview` | 行情 | AKShare | 涨跌家数 |
| `get_daily_kline` | K线 | AKShare | 日K线（降级链） |
| `get_weekly_kline` | K线 | AKShare | 周K线 |
| `get_minute_kline` | K线 | AKShare | 分钟K线 |
| `get_money_flow` | 资金 | AKShare | 个股主力资金流向 |
| `get_north_money` | 资金 | AKShare | 北向资金（T+1盘后） |
| `get_sector_money_flow` | 资金 | AKShare | 板块资金排名 |
| `get_financial_report` | 财务 | AKShare | 财务指标 |
| `get_roe_data` | 财务 | AKShare | ROE/毛利率 |
| `get_pe_pb` | 财务 | AKShare | 估值指标 |
| `get_sector_list` | 板块 | AKShare | 板块列表 |
| `get_hot_sectors` | 板块 | AKShare | 热门板块 |
| `get_sector_stocks` | 板块 | AKShare | 板块成分股 |
| `get_market_sentiment` | 情绪 | AKShare | 综合情绪（含评分） |
| `get_market_sentiment_enhanced` | 情绪 | 多源聚合 | **增强版**情绪评分 |

## 8. 技术栈

| 组件 | 技术 |
|------|------|
| 主框架 | OpenClaw 2026.4.x |
| 策略Agent | Hermes CLI |
| 知识库 | GBrain v0.7.0 + PGLite |
| MCP数据服务 | Python + FastAPI + AKShare |
| 缓存 | MemoryCache（线程安全，可扩展Redis） |
| 限流 | 内存RateLimiter（默认100次/分钟） |
| 数据获取 | AKShare / aiohttp 异步请求 |
| 定时调度 | Linux Cron |
| 推送渠道 | WeChat (OpenClaw Plugin) |

## 9. 扩展计划

- [ ] 接入实盘API（需要模拟盘许可）
- [ ] 增加更多技术指标到MCP工具集
- [ ] 机器学习优化买点判断
- [ ] 多市场支持（港股、美股）
- [ ] Redis缓存支持（共享CacheManager已预留接口）
- [ ] WebSocket实时推送

---

_文档版本：v2.0 | 更新：2026-05-14_
