# HEARTBEAT.md

## 任务列表

### 1. 持仓汇报推送（最高优先）
检查 `/root/.openclaw/workspace/pending-summaries/` 目录下的持仓报告文件：
- `portfolio-YYYY-MM-DD-*.md` — 有则立即发送（channel: openclaw-weixin, to: o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat），发送后删除
- 多个文件按文件名排序依次发送

### 2. 交易通知推送
检查 `/root/.openclaw/workspace/pending-summaries/` 目录下的交易通知文件：
- `trade-*.md` — 有则立即发送，发送后删除
- 交易通知有最高优先权（买卖成交后立即通知）

### 3. 每日工作总结（22:00 后）
检查文件名格式 `YYYY-MM-DD-summary.md`：
- 当前小时 < 22：跳过
- 当前小时 >= 22：发送，发送后删除

### 4. 定期任务检查（非高峰时段）
- 每周一：GBrain 健康检查 + 猎手模拟交易积累回顾
