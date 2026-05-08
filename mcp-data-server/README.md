# MCP Data Server

A股数据统一接口，支持扣子龙虾(Coze)和腾讯龙虾(OpenClaw)共用。

## 功能特性

- **实时行情**: 个股/指数实时价格
- **K线数据**: 日/周/月/分钟K线
- **资金流向**: 主力/北向/散户资金
- **财务数据**: 财报/ROE/PE/PB
- **板块数据**: 行业/概念板块行情
- **市场情绪**: 涨跌家数/恐慌贪婪指数

## 部署

### 1. 创建虚拟环境

```bash
cd /root/.openclaw/workspace/猎手模拟交易
python3 -m venv venv/mcp-data-server
source venv/mcp-data-server/bin/activate
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 systemd 服务

```bash
# 创建服务文件
cat > /etc/systemd/system/mcp-data-server.service << 'EOF'
[Unit]
Description=MCP Data Server API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/猎手模拟交易/mcp-data-server
ExecStart=/root/.openclaw/venv/mcp-data-server/bin/python -m uvicorn src.api_server:app --host 0.0.0.0 --port 8766
Restart=always
RestartSec=5
StandardOutput=append:/var/log/mcp-data-server.log
StandardError=append:/var/log/mcp-data-server.log

[Install]
WantedBy=multi-user.target
EOF

# 启动服务
systemctl daemon-reload
systemctl enable mcp-data-server
systemctl start mcp-data-server
```

## API 调用示例

### 扣子龙虾 (Coze) - HTTP API

```python
import requests

API_BASE = "http://101.32.218.156:8766"
TOKEN = "mcp-data-server-token"
headers = {"X-API-Token": TOKEN}

# 获取实时行情
resp = requests.get(f"{API_BASE}/api/v1/quote/000001", headers=headers)
print(resp.json())

# 获取K线
resp = requests.get(f"{API_BASE}/api/v1/kline/000001?period=daily&adjust=qfq", headers=headers)
print(resp.json())

# 获取资金流向
resp = requests.get(f"{API_BASE}/api/v1/fund/000001", headers=headers)
print(resp.json())

# 获取市场情绪
resp = requests.get(f"{API_BASE}/api/v1/sentiment", headers=headers)
print(resp.json())
```

### Shell curl 调用

```bash
# 获取实时行情
curl -H "X-API-Token: mcp-data-server-token" \
  http://101.32.218.156:8766/api/v1/quote/000001

# 获取K线
curl -H "X-API-Token: mcp-data-server-token" \
  "http://101.32.218.156:8766/api/v1/kline/000001?period=daily&adjust=qfq"

# 批量获取
curl -H "X-API-Token: mcp-data-server-token" \
  "http://101.32.218.156:8766/api/v1/quotes?symbols=000001,600000,000002"
```

### 腾讯龙虾 (OpenClaw) - MCP 工具

配置 `/root/.openclaw/openclaw.json`:

```json
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

重启 OpenClaw 后可直接使用 MCP 工具:

```
get_realtime_quote(symbol="000001")
get_daily_kline(symbol="000001", start_date="20240101", end_date="20250101")
get_money_flow(symbol="000001")
get_sector_list(sector_type="industry")
get_roe_data(symbol="000001")
```

## API 端点列表

| 方法 | 端点 | 描述 |
|------|------|------|
| GET | /api/v1/health | 健康检查 |
| GET | /api/v1/status | 服务状态 |
| GET | /api/v1/tools | 可用工具列表 |
| GET | /api/v1/quote/{symbol} | 实时行情 |
| GET | /api/v1/quotes | 批量行情 |
| GET | /api/v1/index | 指数行情 |
| GET | /api/v1/kline/{symbol} | K线数据 |
| GET | /api/v1/fund/{symbol} | 资金流向 |
| GET | /api/v1/fund/north | 北向资金 |
| GET | /api/v1/financial/{symbol} | 财务报表 |
| GET | /api/v1/sector/list | 板块列表 |
| GET | /api/v1/sector/hot | 热门板块 |
| GET | /api/v1/sentiment | 市场情绪 |

## 缓存策略

| 数据类型 | TTL | 说明 |
|----------|-----|------|
| 实时行情 | 5分钟 | 价格、涨跌幅等 |
| K线数据 | 1天 | 日/周/月K线 |
| 财务数据 | 1天 | 财报、PE/PB等 |
| 板块数据 | 5分钟 | 板块涨跌 |

## 故障排查

```bash
# 查看服务状态
systemctl status mcp-data-server

# 查看日志
tail -f /var/log/mcp-data-server.log

# 重启服务
systemctl restart mcp-data-server

# 测试API
curl http://localhost:8766/api/v1/health
```

## License

MIT
