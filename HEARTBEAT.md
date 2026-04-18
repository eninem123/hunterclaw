# HEARTBEAT.md

## 任务列表

### 1. 持仓汇报推送（最高优先）
检查 `/root/.openclaw/workspace/pending-summaries/` 目录：
- `portfolio-YYYY-MM-DD-*.md` — 有则立即发送（channel: openclaw-weixin），发送后删除
- 多个文件按文件名排序依次发送

### 2. 交易通知推送
检查 `/root/.openclaw/workspace/pending-summaries/` 目录：
- `trade-*.md` — 有则立即发送，发送后删除

### 3. Hermes 策略复盘推送（15:30 后）
检查 `/root/.openclaw/workspace/pending-summaries/` 目录：
- `hermes-strategy-YYYY-MM-DD.md` — 每日15:30后 Hermes 生成策略复盘
- 立即发送微信（channel: openclaw-weixin），发送后删除
- 格式：「🔮 【每日策略复盘】」

### 4. 待确认信号提醒
检查 `/root/.hermes/猎手模拟交易/pending_confirm/` 目录：
- 有文件说明有信号待确认，立即推送提醒
- 提醒格式：「🔔 您有待确认的交易信号，请回复确认」
- 发送后文件保留（等用户真正确认才删除执行）

### 5. 每日工作总结（22:00 后）
检查文件名格式 `YYYY-MM-DD-summary.md`：
- 当前小时 < 22：跳过
- 当前小时 >= 22：发送，发送后删除

### 6. 定期任务检查（非高峰时段）
- 每周一：GBrain 健康检查 + 猎手模拟交易积累回顾
