# 猎手系统 - 定时任务配置

## 任务总览

| # | 时间 | 任务名 | 脚本参数 | 定位 |
|---|------|--------|----------|------|
| 1 | 09:30 | 开盘提醒 | `--morning` | 市场温度 + 仓位检查 |
| 2 | 10:00 | 上午推演① | 无 | 盘中机会扫描 |
| 3 | 11:00 | 上午推演② | 无 | 临近午盘检查 |
| 4 | 13:00 | 下午开盘 | `--afternoon` | 午后行情判断 |
| 5 | 14:00 | 下午推演① | 无 | 盘中机会扫描 |
| 6 | 14:30 | 下午推演② | 无 | 尾盘准备 |
| 7 | 14:55 | 撤退检查 | `--closing` | 核心决策点 |

## 定向推送规则

- **推送渠道**：openclaw-weixin
- **推送对象**：当前对话用户（`o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat`）
- **当前账户**：`665a0448707a-im-bot`

## 任务详情

### 任务1 - 09:30 开盘提醒
```bash
python3 /root/.openclaw/workspace/hunter/scripts/market_scanner.py --morning
```
重点：
- 开盘跳空高开/低开幅度
- 竞价量能
- 北向资金开盘方向
- 昨日预警回顾

### 任务7 - 14:55 撤退检查（重点）
```bash
python3 /root/.openclaw/workspace/hunter/scripts/market_scanner.py --closing
```
**加重检查：**
- 主力资金是否尾盘偷袭撤退
- 北向资金最后30分钟异动
- 持仓板块是否出现跳水信号
- 给出明确操作建议：清仓 / 减仓 / 持有

## 安装方式

```bash
openclaw cron add "30 09 * * 1-5" --name "猎手-开盘提醒" \
  --command "python3 /root/.openclaw/workspace/hunter/scripts/run_scan.py --morning" \
  --channel openclaw-weixin \
  --to "o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat"

openclaw cron add "55 14 * * 1-5" --name "猎手-撤退检查" \
  --command "python3 /root/.openclaw/workspace/hunter/scripts/run_scan.py --closing" \
  --channel openclaw-weixin \
  --to "o9cq801u9_6B8BEUnp-foIPm8pP0@im.wechat"
```
