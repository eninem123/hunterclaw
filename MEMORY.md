# MEMORY.md - Long-Term Memory

## Alpha_Terminal 项目

**项目路径：** `/root/Alpha_Terminal/`（GitHub 维护）
**生产环境：** `/var/www/html/`（通过 nginx 提供服务，域名 www.aialter.site）

### 标准开发部署流程（每次改代码后必须执行）

1. 改源码 → `/root/Alpha_Terminal/`
2. 同步生产 → `rsync -av --exclude='.git' --exclude='node_modules' --exclude='.env*' /root/Alpha_Terminal/ /var/www/html/`
3. 重启服务 → `sudo systemctl restart alpha-terminal`
4. 推送 Git → `cd /root/Alpha_Terminal && git add . && git commit -m "描述" && git push`

### 知识库模块

- 知识库下拉框：直接展示 + 分页（每页5个），‹ › 分页按钮
- API 端点：`POST /api/kb/list` 返回 10 个知识库
- 状态提示：顶部显示"已选 X 个"和"第X页/共X页"

### 技术栈

- 后端：Node.js（server.js），端口 8787（nginx 反代 80）
- 前端：原生 HTML + JS（core.js），Tailwind 风格
- IMA API Key：`8b6a36dd-d6c8-4e2a-b25f-9e7d3c1a8f9b`

## 用户偏好

- 用户通过 openclaw-weixin 频道（微信）与我对话
- 用户习惯：改完代码后我会自动同步、部署、重启，用户通过截图确认效果

## 自动行为规则（每次对话都检查）

### 1. 代码改动后自动执行部署流程
改源码 → `/root/Alpha_Terminal/` 后，立即（不需用户提醒）按顺序执行：
1. `rsync -av --exclude='.git' --exclude='node_modules' --exclude='.env*' /root/Alpha_Terminal/ /var/www/html/`
2. `sudo systemctl restart alpha-terminal`
3. `cd /root/Alpha_Terminal && git add . && git commit -m "描述" && git push`
4. 告知用户已完成

### 2. 涉及外部能力时自动找 Skill
当用户询问以下类型问题时，优先检查是否有对应 skill：
- 股票/行情/数据查询 → ths-financial-data、jrj-quote-skill、eastmoney-tools、akshare-finance
- 财务/基本面分析 → stock-analyst、mx-finance-data
- 网页搜索/信息获取 → tavily-search、eastmoney-fin-search、web-tools-guide
- 宏观/全球经济数据 → mx-macro-data
- 腾讯云/服务器管理 → tencentcloud-lighthouse-skill
- 腾讯文档/会议/COS → 对应 skill

先检查 workspace/skills/ 目录是否已有可用 skill，没有则调用 find-skills 搜索并推荐安装。

## 双Agent协作系统

### Agent身份分工
- **🦞 Claw（我）**：主对话接口，项目管理，交易决策
- **🔮 Hermes**：后台协作，记忆整理，策略优化（不直接对接微信）

## 系统版本

| 系统 | 版本 | 用途 |
|------|------|------|
| Hermes | v0.8.0 (最新) | 策略优化、记忆学习 |
| OpenClaw | 2026.4.11 (最新) | 主对话/扩展能力 |

### Hermes配置
- **安装路径**：`/root/.hermes/hermes-agent/`
- **配置**：`~/.hermes/config.yaml`, `~/.hermes/.env`
- **模型**：MiniMax-M2.7（通过breeze API: api.svips.org）
- **身份文件**：`~/.hermes/SOUL.md`

### Hermes职责
1. 记忆沉淀 - 整理重要决策和经验
2. 策略复盘（交易日15:30）
   - 对比推演预测 vs 市场实际
   - 输出到 `~/.hermes/猎手模拟交易/策略优化建议.md`
   - 🔴连续失败时标记提醒
3. 第二视角分析

### 协作规则
- 用户 → Claw（直接响应）
- 需要Hermes时 → Claw委托，Hermes分析，Claw转达
- 所有项目由Claw管理，Hermes不独立操作

## 待执行任务清单

### 已配置定时任务
| 任务 | 执行时间 | 状态 |
|------|----------|------|
| Hermes策略优化分析 | 每个交易日15:30 | ✅ 已配置 |
| 猎手模拟交易推演 | 周一至周五 9:30-14:55（7个任务） | ⚠️ 待周一开盘验证 |
| GBrain Dreamcycle | 夜间（具体时间待确认） | ⚠️ 待配置 |

### 待执行（周一开盘）
- 猎手系统开始推演（9:30起）
- 周一15:30：Hermes首轮策略优化分析
- 周一15:10：复盘记录生成

## 双系统协同架构（猎手 + AI Hedge）

### 系统定位
- **AI Hedge Fund**（`/root/ai-hedge-fund/`）
  - 定位：长线选股顾问
  - 核心：12位投资大师 Agent（巴菲特、芒格、木头姐、Burry 等）
  - 输入：美股/港股基本面、大师策略视角
  - 输出：优质标的池 + 大师评级（bullish/neutral/bearish）

- **猎手系统**（Alpha_Terminal）
  - 定位：短线狙击手
  - 核心：技术面、资金流向、板块轮动
  - 输入：A股择时、快进快出
  - 输出：买入信号 + -5%止损

### 协同规则
| 场景 | AI Hedge | 猎手 |
|------|----------|------|
| 选股 | ✅ 用大师眼光筛池子 | — |
| 买点 | — | ✅ 技术面找时机 |
| 止损 | 建议安全边际 | 严格执行-5% |
| 持仓 | 定期复评 | 短线快出 |
| 指令传递 | **只推荐，不下指令** | 独立决策 |

### 工作流
1. AI Hedge 选出"值得关注"的股票池（大师评级 bullish）
2. 我把这些标的加入猎手观察列表
3. 猎手每日扫描技术面/资金流向
4. 出现买点 → 通知你
5. 入场后严格-5%止损

### API配置
- MiniMax API：`sk-api-iZiz-X30hWc-Kl_z0fFw-ZZ_W052thjQNnfE0robIqRiq5ezCG62G9p_p9Mha5WQaH5L8DC5kc1LHT9NH8GJITalx3T9s_d6SCIqN9QzAwgUCgF1yekwueI`
- Financial Datasets API：`39807e65-5395-4ecd-9f4a-8ab1da06e95c`
- 端点：`https://api.minimaxi.com/v1`

## API 充值记录

| 时间 | 内容 | 备注 |
|------|------|------|
| 2026-04-13 | 充值 glm api | - |

