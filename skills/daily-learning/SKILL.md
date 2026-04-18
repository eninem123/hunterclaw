# Daily Learning Push Skill

> 每日学习推送 — 基于 zmproject 知识库，循序渐进掌握 AI + 数据 + 自动化

## Overview

每日推送 zmproject 中的核心内容，分四大模块，难度递增：
- **AI应用** (⭐) → **技术开发** (⭐⭐) → **业务建模** (⭐⭐⭐) → **项目实战** (⭐⭐⭐⭐)

---

## Learning Modules

### 📦 Module 1: AI Applications (Level 1)

**目标**：掌握 AI Agent 开发能力

| Day | Topic | File |
|-----|-------|------|
| 1-3 | AI 知识库问答系统 | `ai_applications/kb_qa_mvp/` |
| 4-5 | Agent Browser 自动化 | `ai_applications/*agent*.md` |
| 6-7 | 本地知识库部署 | `local_knowledge_model/` |

### 🛠️ Module 2: Technical Development (Level 2)

**目标**：掌握数据管道 + 自动化开发

| Day | Topic | File |
|-----|-------|------|
| 8-10 | 数据建模规范 | `ai_learning/DWD模型开发规范*.md` |
| 11-12 | 错误追踪系统 | `ai_learning/error_tracking_system.md` |
| 13-15 | Python 脚本开发 | `gen_cpt*.py`, `load_project_context.py` |

### 📊 Module 3: Business Intelligence (Level 3)

**目标**：掌握业务分析 + 报表自动化

| Day | Topic | File |
|-----|-------|------|
| 16-18 | 帆软报表自动化 | `帆软报表自动化项目/` |
| 19-21 | 数据审计规则 | `audits/*.json` |
| 22-25 | 业务需求文档 | `业务需求/` |

### 🚀 Module 4: Project Practice (Level 4)

**目标**：独立交付 AI 数据项目

| Day | Topic | File |
|-----|-------|------|
| 26-28 | 项目调研模板 | `调研报告/` |
| 29-30 | 部署与运维 | `部署与运维/` |

---

## Scripts

### 1. learner_index.py — 索引项目

```bash
python3 learner_index.py /root/zmproject
```

扫描项目，生成 `learner_index.json`：
```json
{
  "modules": [
    {
      "name": "AI Applications",
      "level": 1,
      "files": [
        {"path": "...", "title": "...", "excerpt": "..."}
      ]
    }
  ],
  "progress": {"current_day": 1, "completed": []}
}
```

### 2. daily_push.py — 每日推送

```bash
python3 daily_push.py --module 1 --day 1
```

生成当日学习内容，写入 `outputs/daily/<module>/` 并推送到微信。

### 3. quiz_check.py — 学习检验

```bash
python3 quiz_check.py --day 1
```

根据当日内容生成 3 道检验题，输出到 `outputs/quiz/`.

---

## Integration with OpenClaw

### Cron Configuration

```bash
# 每天 08:00 推送学习内容
0 8 * * * cd /root/.openclaw/workspace/skills/daily-learning && python3 daily_push.py >> logs/daily_learning.log 2>&1
```

### Heartbeat Integration

检查 `outputs/daily/` 目录，有新内容则推送微信。

---

## Learning Path

```
Week 1: AI应用入门（知识库+Agent）
    ↓
Week 2: 技术开发（数据管道+脚本）
    ↓
Week 3: 业务智能（报表+审计）
    ↓
Week 4: 项目实战（调研+部署）
```

---

## Progress Tracking

- 文件：`outputs/progress.json`
- 格式：`{"day": N, "module": M, "completed_files": [...], "quiz_scores": [...]}`
- 每周一检查进度，未完成自动补推
