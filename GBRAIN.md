# GBRAIN.md — 第二大脑集成规则

## 引擎信息
- **引擎**: GBrain v0.7.0 (Custom GLM Fork)
- **存储**: PGLite 本地数据库 (`/root/.gbrain/brain.pglite`)
- **Embedding**: GLM embedding-2 (1024维)，直连GLM API
- **索引**: 456 chunks / 423 已生成向量（剩余33 chunks待GLM配额恢复）
- **搜索**: 关键词搜索 ✅ + 语义搜索 ✅（423 chunks已激活）

---

## 硬性行为规则（无例外）

### 规则1：先查大脑，再调外网

```
任何涉及人物、项目、公司、决策、对话内容的问题
→ 必须先查 GBrain
→ 查到 → 直接用大脑内容回答
→ 查不到 → 才允许调用外部API（搜索/API）
```

### 规则2：写入优先

```
用户说了任何新的：
- 项目需求、技术方案
- 会议结论、决策
- 人物信息、个人偏好
- 原创想法、投资判断
→ 立即写入 GBrain，不批量，不延迟
```

### 规则3：纠正最高优先

```
用户纠正了我的说法（关于人/项目/公司/决策）
→ 立即更新 GBrain 对应页面
→ 在 timeline 记录原始错误 + 纠正内容
```

---

## 工具调用

```bash
# 运行命令（必须用 bun run）
export PATH="$HOME/.bun/bin:$PATH"
cd /root/.openclaw/workspace/node_modules/gbrain && \
PATH="$HOME/.bun/bin:$PATH" bun run src/cli.ts <cmd>

# 关键词搜索（毫秒级）
bun run src/cli.ts search "关键词"

# 语义搜索（向量相似度）
bun run src/cli.ts query "描述性问题"

# 读取页面
bun run src/cli.ts get <slug>

# 写入页面
echo "# 内容" | bun run src/cli.ts put <slug>

# 查 backlinks（谁关联到这个实体）
bun run src/cli.ts backlinks <slug>

# 统计
bun run src/cli.ts stats
```

---

## 页面结构规范

每个 GBrain 页面分两段（`---` 分隔）：

**上方 — 编译真相（Compiled Truth）**
- 当前状态摘要（第一段是执行摘要）
- 结构化字段（State）
- 开放线程（Open Threads — 解决后移到下方）
- 交叉引用（See Also）

**下方 — 时间线（Append-only）**
- 逆序排列
- 每条：日期、来源、事件描述
- 永不删除，永不修改

---

## 大脑目录（MECE 分类）

```
/root/.gbrain/brain/
├── people/        ← 人物档案
├── projects/      ← 项目/产品
├── meetings/      ← 会议记录
├── ideas/         ← 原创想法
├── conversations/ ← 对话记录
├── timeline/      ← 时间线事件
├── skills/        ← 技能/SOP
└── inbox/        ← 待分类
```

---

## 实体检测规则

每次交互后，检测并记录：
- 人物名字 → `people/{slug}`
- 项目名称 → `projects/{slug}`
- 会议/决策 → `meetings/{slug}`
- 想法 → `ideas/{slug}`

---

## Dream Cycle（夜间自动优化）

**时间**: 每天 02:00 Asia/Shanghai

**任务**:
1. `bun run src/cli.ts embed --stale` — 刷新所有陈旧embeddings
2. `bun run src/cli.ts doctor --json` — 健康检查
3. `bun run src/cli.ts stats` — 页面统计
4. 如有异常，更新对应brain页面
5. 将本次Dream Cycle结果简要报告给用户

**注意**: 运行命令必须设置:
```bash
export PATH="$HOME/.bun/bin:$PATH"
cd /root/.openclaw/workspace/node_modules/gbrain
PATH="$HOME/.bun/bin:$PATH" bun run src/cli.ts <cmd>
```

---

## 禁止事项

- ❌ 不经大脑直接搜索/调用 API
- ❌ 将敏感信息写入外部服务
- ❌ 修改任何运维配置文件（`/var/www/`, `/etc/`, `.env*`）
- ❌ 修改已有业务代码或 cron 配置
- ❌ 跳过 `gbrain search` 直接调用 `web_search`

---

## 验证命令

```bash
# 检查大脑状态
cd /root/.openclaw/workspace/node_modules/gbrain && \
PATH="$HOME/.bun/bin:$PATH" bun run src/cli.ts stats

# 健康检查
cd /root/.openclaw/workspace/node_modules/gbrain && \
PATH="$HOME/.bun/bin:$PATH" bun run src/cli.ts doctor --json

# 测试语义召回
cd /root/.openclaw/workspace/node_modules/gbrain && \
PATH="$HOME/.bun/bin:$PATH" bun run src/cli.ts query "用户上次讨论的猎手系统策略"
```

---

## GLM API Key

Key: `87f5475dbadc41b6b08e293c1f6f300e.C3BZ1dzhJmGPExP7`
状态: 余额不足（剩余embedding额度可支撑约100页更新）
配额恢复: 下个计费周期或充值后自动恢复

---

*Last updated by agent: 2026-04-11*
*GBrain version: 0.7.0 (Custom Fork)*
