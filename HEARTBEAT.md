# HEARTBEAT.md

## 任务列表

### 1. 检查并发送持仓汇报（最高优先）
每次心跳检查 `/root/.openclaw/workspace/pending-summaries/` 目录下是否有持仓报告文件（文件名格式：`portfolio-YYYY-MM-DD-*.md`）。
- 如果有：读取文件，通过 message 工具发送给用户（channel: openclaw-weixin, to: o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat）
- 发送成功后删除该文件
- 有持仓报告就立即发，不受时间限制
- 注意：每个时段（开盘/午盘/收盘/晚间）各有一个文件，都会依次发送

### 2. 检查并发送每日工作总结（22:00 后）
检查 pending-summaries 目录下是否有今日总结文件（文件名格式：`YYYY-MM-DD-summary.md`）。
- 当前小时 < 22：跳过
- 当前小时 >= 22：发送，发送成功后删除文件

### 3. 定期任务检查（非高峰时段）
- 每周一检查一次猎手模拟交易积累情况
- 每周一检查一次 GBrain 健康状态
