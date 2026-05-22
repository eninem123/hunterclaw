# SKILL.md — 技术文档中心 (Tech-Docs Hub)

> 版本：v1.0.0 | 更新：2026-05-10
> 维护者：龙波 (Longbo) | 位置：`/root/.openclaw/workspace/skills/tech-docs/`

---

## 1. 概述

本技能是腾讯龙虾群（Tencent Lobster Swarm）的**技能文档中心**，作为 workspace 内所有自定义技能的元索引、跨技能工作流编排文档和开发规范参考。

**核心职责：**
- 维护 workspace 内所有自定义技能的索引清单（含版本、用途、状态）
- 定义跨技能工作流最佳实践
- 制定技能开发规范，确保一致性
- 提供技能间依赖关系和调用协议的参考文档

**更新策略：**
- 新增技能 → 30天内更新本索引
- 版本升级 → 更新 changelog
- 废弃技能 → 标记 deprecated，不删除（保留追溯性）

---

## 2. 技能索引

> 状态说明：`active` = 正常使用 | `deprecated` = 已废弃 | `wip` = 开发中

### 2.1 交易与分析类

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `hunter-trading` | v1.0 | A股短线交易分析、猎手策略执行 | active | `akshare-finance`, `china-stock-analysis` |
| `china-stock-analysis` | — | A股技术分析（K线、均线、MACD等） | active | `akshare-finance` |
| `akshare-finance` | — | 金融数据获取（行情、财务、宏观） | active | 无（底层数据源） |
| `stock-analyst` | — | 个股诊断与评级 | active | `china-stock-analysis` |
| `invest-decision` | — | 投资决策辅助（基本面+技术面） | active | `akshare-finance`, `china-stock-analysis` |
| `stock-screener-cn` | — | A股筛选器（条件选股） | active | `akshare-finance` |
| `stock-catalyst-hunter` (ticai-lieshou) | — | 事件驱动选股（业绩、公告、研报） | active | `akshare-finance` |
| `trading-agents` | — | 多智能体交易策略编排 | active | `hunter-trading` |
| `vibe-trading` | — | 量化和情绪交易系统 | active | `akshare-finance` |
| `investment-five-questions` | — | 投资决策五问框架 | active | 无 |
| `warren-buffett-investing` | — | 价值投资分析框架 | active | `akshare-finance` |
| `ai-hedge-fund` | — | 对冲基金级组合分析 | active | `akshare-finance` |
| `stock-predictor` | — | 个股价格预测模型 | wip | `akshare-finance` |
| `stock-board` | — | 板块分析与轮动跟踪 | active | `akshare-finance` |
| `a-stock-real-time-monitor` | — | A股实时监控与预警 | active | `akshare-finance` |
| `ac-stock-ultrashort` | — | 超短期择时信号 | active | `akshare-finance` |

### 2.2 数据与文档处理类

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `data-analyst-cn` | v1.0.23 | 数据分析助手（清洗、可视化、报告） | active | 无 |
| `pdf-smart-tool-cn` | — | PDF解析与OCR | active | 无 |
| `excel-xlsx` | — | Excel读写、公式、数据透视表 | active | 无 |
| `pdf-smart-tool-cn` | — | 智能PDF处理 | active | 无 |
| `summarize` | — | 文档/文章摘要生成 | active | 无 |
| `ths-financial-data` | — | 同花顺数据接口封装 | active | `akshare-finance` |
| `eastmoney-tools` | — | 东方财富数据工具 | active | `akshare-finance` |

### 2.3 房产与资产类

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `ai-real-estate-cn` | — | 房产分析（估值、租售比、决策） | active | 无 |
| `mortgage-calculator` | — | 房贷计算器 | active | 无 |
| `budget-vs-actual` | — | 预算vs实际对比分析 | active | `data-analyst-cn` |

### 2.4 效率与工具类

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `agent-browser` | — | 浏览器自动化 | active | `playwright-cli-openclaw` |
| `playwright-cli-openclaw` | — | Playwright CLI封装 | active | 无 |
| `browser-automation` | — | 浏览器自动化（官方skill） | active | 无 |
| `find-skills` | — | 技能搜索与发现 | active | 无 |
| `skillhub-preference` | — | ClawHub偏好管理 | active | 无 |
| `github` | — | GitHub操作（PR、issue、repo） | active | 无 |
| `tencent-cos-skill` | — | 腾讯云COS对象存储 | active | 无 |
| `tencentcloud-lighthouse-skill` | — | 腾讯云轻量应用服务器 | active | 无 |
| `cloudbase` | — | CloudBase全栈开发 | active | 无 |
| `pmaster` | — | 项目管理（PMaster） | active | 无 |
| `project-management-2` | — | 项目管理（PM Agent） | active | 无 |
| `douyin-video-downloader` | — | 抖音视频下载 | active | 无 |
| `video-generation-minimax` | — | 视频生成（MiniMax） | active | 无 |
| `image-studio` | — | 图像创作工作室 | active | 无 |
| `travel-planning` | — | 旅行规划 | active | 无 |
| `news-aggregator` | — | 新闻聚合 | active | 无 |
| `news-summary` | — | 新闻摘要 | active | `news-aggregator` |
| `openclaw-tavily-search` | — | Tavily搜索API封装 | active | 无 |

### 2.5 个人成长与知识管理类

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `ai-self-evolution` | — | AI自我进化框架 | active | 无 |
| `self-evolution` | — | 自我进化（第二版本） | active | 无 |
| `daily-learning` | — | 每日学习记录 | active | 无 |
| `memory-hygiene` | — | 记忆系统清洁与维护 | active | 无 |
| `agent-memory` | — | Agent记忆管理 | active | 无 |
| `pua-debugging-pro` | — | 认知偏差调试（心理学） | active | 无 |
| `humanizer-text` | — | 文本人性化改写 | active | 无 |

### 2.6 内置与系统级技能

| 技能名 | 版本 | 用途 | 状态 | 依赖 |
|--------|------|------|------|------|
| `mcporter` | 内置 | MCP服务器管理 | 内置 | 无 |
| `node-connect` | 内置 | Node连接管理 | 内置 | 无 |
| `tmux` | 内置 | Tmux会话管理 | 内置 | 无 |
| `video-frames` | 内置 | 视频帧提取 | 内置 | 无 |
| `healthcheck` | 内置 | 健康检查 | 内置 | 无 |
| `session-logs` | 内置 | 会话日志 | 内置 | 无 |
| `skill-creator` | 内置 | 技能创建工具 | 内置 | 无 |
| `weather` | 内置 | 天气查询 | 内置 | 无 |
| `clawhub` | 内置 | ClawHub市场 | 内置 | 无 |
| `yao-tutorial-skill` | — | Yao框架教程 | active | 无 |

---

## 3. 跨技能工作流

### 工作流 A：A股机会分析 → 建仓决策

```
akshare-finance (获取数据)
    ↓
china-stock-analysis (技术面分析)
    ↓
stock-catalyst-hunter / ticai-lieshou (消息面/催化剂)
    ↓
invest-decision (综合决策)
    ↓
hunter-trading (下单执行 & 风控)
```

**适用场景：** 发现个股机会 → 验证 → 决策 → 执行

### 工作流 B：持仓诊断 → 风控评估

```
hunter-trading (读取持仓)
    ↓
china-stock-analysis (技术面复盘)
    ↓
akshare-finance (财务数据)
    ↓
invest-decision (持有/加仓/止损建议)
```

**适用场景：** 定期持仓复盘，或触发止损预警时

### 工作流 C：数据清洗 → 分析 → 可视化报告

```
akshare-finance (获取原始数据)
    ↓
data-analyst-cn (清洗 & 分析)
    ↓
excel-xlsx (导出Excel)
    ↓
summarize (生成报告摘要)
```

**适用场景：** 批量数据分析、月报生成

### 工作流 D：房产决策全流程

```
ai-real-estate-cn (区域分析 + 估值)
    ↓
mortgage-calculator (月供计算)
    ↓
budget-vs-actual ( affordability 评估)
    ↓
invest-decision (综合决策)
```

**适用场景：** 买房/卖房决策分析

### 工作流 E：新闻 → 摘要 → 交易信号

```
news-aggregator (抓取财经新闻)
    ↓
news-summary (生成摘要)
    ↓
stock-catalyst-hunter (事件标签)
    ↓
invest-decision (信号评级)
    ↓
hunter-trading (执行)
```

**适用场景：** 每日早间新闻速览 + 盘中异动响应

---

## 4. 开发规范

### 4.1 文件命名规范

```
skill-name/
├── SKILL.md              # 技能主文档（必须）
├── CHANGELOG.md          # 变更日志（建议）
├── README.md             # 使用说明（建议）
└── code/                 # 代码目录（如有）
    ├── main.py
    └── utils.py
```

**命名约束：**
- 目录名 = 技能名，全小写，中划线分隔（e.g. `china-stock-analysis`）
- SKILL.md 必须位于技能根目录
- 代码文件使用 snake_case

### 4.2 SKILL.md 结构要求

每个技能的 SKILL.md 必须包含以下章节：

```markdown
# SKILL.md - [技能名称]

## 1. 概述
   - 技能定位
   - 核心功能（bullet list）
   - 适用场景

## 2. 使用前提
   - 依赖的外部服务/API
   - 必需的 env vars
   - 权限要求

## 3. 核心接口
   - Tool名称、参数、返回值
   - 调用示例

## 4. 使用限制
   - 速率限制
   - 数据延迟
   - 合规声明

## 5. 已知问题 / FAQ
```

### 4.3 版本号规范

采用 **语义化版本 (Semantic Versioning)**：
```
主版本.次版本.修订号
  v1.2.3
```

- **主版本 (1)**：不兼容的API变更
- **次版本 (2)**：向后兼容的功能新增
- **修订号 (3)**：向后兼容的bug修复

**版本号记录位置：** SKILL.md 顶部元信息 + CHANGELOG.md

### 4.4 技能状态定义

| 状态 | 含义 | 要求 |
|------|------|------|
| `active` | 正常使用 | 有完整SKILL.md，核心功能可用 |
| `deprecated` | 废弃 | 保留文档，添加废弃声明，指向替代技能 |
| `wip` | 开发中 | 有基本骨架，功能不完整 |
| `broken` | 已损坏 | 功能不可用，待修复 |

---

## 5. 更新日志规范

每个技能应维护 `CHANGELOG.md`，格式如下：

```markdown
# Changelog

## [v1.2.0] - YYYY-MM-DD
### 新增
- Feature A
- Feature B

### 修复
- Bug C

### 变更
- Breaking change D（需注明兼容性方案）

---

## [v1.1.0] - YYYY-MM-DD
...
```

**提交规范：**
- 合并到主分支后更新 changelog
- 更新本索引的技能版本列
- 重大更新（主版本升级）需在 workspace 日记中记录

---

## 6. 附录

### 6.1 技能依赖图（简化）

```
akshare-finance
├── hunter-trading
├── china-stock-analysis
│   ├── stock-analyst
│   └── invest-decision
├── stock-screener-cn
├── ticai-lieshou (stock-catalyst-hunter)
├── trading-agents
└── ths-financial-data / eastmoney-tools

data-analyst-cn
├── budget-vs-actual
└── summarize

cloudbase
├── tencent-cos-skill
└── tencentcloud-lighthouse-skill

browser-automation / agent-browser
└── playwright-cli-openclaw
```

### 6.2 快速命令参考

```bash
# 列出所有技能
ls ~/.openclaw/workspace/skills/

# 查看技能结构
ls ~/.openclaw/workspace/skills/<skill-name>/

# 更新版本号（手动编辑 SKILL.md 顶部）

# 标记废弃技能
# 1. 编辑 SKILL.md 顶部 status: deprecated
# 2. 添加 DEPRECATED.md 章节说明替代方案
# 3. 更新本索引
```
