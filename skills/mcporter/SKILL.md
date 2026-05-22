---
name: mcporter
description: List, configure, authenticate, call, and inspect MCP servers/tools with mcporter over HTTP or stdio.
homepage: http://mcporter.dev
metadata:
  {
    "openclaw":
      {
        "emoji": "📦",
        "requires": { "bins": ["mcporter"] },
        "install":
          [
            {
              "id": "node",
              "kind": "node",
              "package": "mcporter",
              "bins": ["mcporter"],
              "label": "Install mcporter (node)",
            },
          ],
      },
  }
---

# mcporter 完整指南

> 📦 管理 MCP (Model Context Protocol) 服务器的工具，支持 HTTP/stdio 两种通信模式。

---

## 1. MCP 概念入门

### 什么是 MCP？

**MCP (Model Context Protocol)** 是 Anthropic 推出的开放协议，用于让 AI 模型与外部工具，数据源进行标准化通信。

```
┌─────────────┐      MCP       ┌─────────────┐
│   AI Model  │◄──────────────►│ MCP Server │
│             │  JSON-RPC 2.0  │ (stdio/HTTP)│
└─────────────┘                └─────────────┘
                                       │
                              ┌────────┴────────┐
                              │  Filesystem     │
                              │  Web fetch      │
                              │  Database       │
                              │  Slack/GitHub   │
                              │  Custom APIs    │
                              └─────────────────┘
```

### MCP 核心概念

| 概念 | 说明 |
|------|------|
| **MCP Server** | 提供一组工具（tools）的服务端，可通过 stdio 或 HTTP 访问 |
| **Tool** | MCP Server 暴露的操作单元，类似函数 `tool_name(arg1=value1)` |
| **Selector** | 调用工具的简写形式，如 `server.list_items` |
| **Transport** | 通信方式：`stdio`（子进程）或 `http`（HTTP 长连接） |
| **Auth** | MCP Server 可能需要 OAuth/API Key 认证 |

### 两种通信模式对比

| 模式 | 原理 | 优点 | 缺点 |
|------|------|------|------|
| **stdio** | mcporter 启动子进程，通过 stdin/stdout 通信 | 简单，零依赖，无需网络 | 每个调用启动一次进程，慢 |
| **HTTP** | mcporter 与长期运行的 HTTP 服务器通信 | 速度快，支持持久状态 | 需要服务端守护进程 |

---

## 2. mcporter 命令详解

### 2.1 `mcporter list` — 列出服务器

列出所有已配置的 MCP 服务器：

```bash
mcporter list
```

**输出示例：**

```
Configured servers:
  filesystem     stdio    ~/mcp-servers/filesystem/server.js
  slack          http     https://slack-mcp.example.com
  github         http     https://api.github.com/mcp
  filesystem2    stdio    npx -y @modelcontextprotocol/server-filesystem /tmp
```

查看某个服务器的 schema（暴露哪些工具）：

```bash
mcporter list <server> --schema
```

**输出示例（GitHub MCP）：**

```
Server: github
Transport: http
URL: https://api.github.com/mcp

Tools:
  github_list_issues     List issues in a repository
  github_create_issue    Create a new issue
  github_get_file        Get file contents from repository
  ...
```

### 2.2 `mcporter call` — 调用工具

这是最核心的命令，用于实际执行 MCP 工具。

#### 基本语法

```bash
mcporter call <server>.<tool> [arg1=value1] [arg2=value2] [...]
```

#### 调用方式一：Selector 简写（推荐）

```bash
# 调用 linear server 的 list_issues 工具，传入参数
mcporter call linear.list_issues team=ENG limit:5

# 调用 filesystem server 的 read_file
mcporter call filesystem.read_file path=/etc/hosts
```

#### 调用方式二：Function 语法（参数带引号）

```bash
mcporter call "linear.create_issue(title: \"Bug: login fails\", body: \"Steps to reproduce...\")"
```

#### 调用方式三：HTTP 服务器调用

```bash
# 调用公开 HTTP MCP 端点
mcporter call https://api.example.com/mcp.fetch url=https://example.com
```

#### 调用方式四：stdio 服务器调用

```bash
# 启动指定的 stdio 服务器进程，调用其工具
mcporter call --stdio "bun run ./server.ts" scrape url=https://example.com
```

#### 调用方式五：JSON payload

```bash
# 当参数较复杂或包含特殊字符时使用
mcporter call <server>.<tool> --args '{"limit": 5, "filter": {"status": "open"}}'
```

#### 输出格式

```bash
# 人类可读格式（默认）
mcporter call linear.list_issues team=ENG limit:5

# JSON 格式（便于脚本处理）
mcporter call linear.list_issues team=ENG limit:5 --output json
```

---

### 2.3 `mcporter auth` — 认证管理

MCP 服务器需要认证时使用此命令。

#### OAuth 认证流程

```bash
# 对指定服务器进行 OAuth 认证
mcporter auth <server>

# 重新认证（清除旧 token）
mcporter auth <server> --reset

# 对 URL 进行认证
mcporter auth https://api.example.com/mcp
```

#### 常见认证场景

| 服务器 | 认证方式 |
|--------|----------|
| GitHub | Personal Access Token (PAT) |
| Slack | OAuth Bot Token |
| Linear | API Key |
| 文件系统 | 无需认证 |

> 💡 认证信息存储在 `~/.config/mcporter/config.json`（或 `--config` 指定的文件）中。

---

### 2.4 `mcporter config` — 配置管理

#### 列出所有配置

```bash
mcporter config list
```

**输出示例：**

```
Servers:
  filesystem     stdio    node /path/to/filesystem-server.js
  slack          http     https://slack.example.com/mcp
  github         http     https://api.github.com/mcp

Auth:
  github         ✅ token set
  slack          ✅ OAuth complete
  linear         ❌ not configured
```

#### 获取单个配置

```bash
mcporter config get <server>
```

#### 添加服务器配置

```bash
# 添加 stdio 服务器
mcporter config add <server_name> --stdio "node /path/to/server.js"

# 添加 HTTP 服务器
mcporter config add <server_name> --url https://api.example.com/mcp

# 指定认证方式
mcporter config add <server_name> --url https://api.example.com/mcp --auth-type oauth2
```

#### 删除服务器配置

```bash
mcporter config remove <server_name>
```

#### 导入配置

```bash
# 从文件导入（用于分享或备份配置）
mcporter config import ./mcporter-config.json

# 从 URL 导入远程配置
mcporter config import https://example.com/mcporter-config.json
```

#### 登录/登出

```bash
# 登录到服务器（触发交互式 OAuth 流程）
mcporter config login <server>

# 登出（清除认证信息）
mcporter config logout <server>
```

---

### 2.5 `mcporter daemon` — 守护进程管理

对于 HTTP MCP 服务器，可以启动长期运行的守护进程来避免每次调用重新连接。

#### 启动守护进程

```bash
mcporter daemon start
```

#### 查看状态

```bash
mcporter daemon status
```

**输出示例：**

```
Daemon running: PID 12345
Port: 3100
Uptime: 2h 15m
Connected servers: 3
```

#### 停止守护进程

```bash
mcporter daemon stop
```

#### 重启守护进程

```bash
mcporter daemon restart
```

> 💡 守护进程在后台运行，启动后 HTTP 调用会快很多。

---

### 2.6 `mcporter generate-cli` — 生成 CLI 工具

将 MCP 服务器的工具生成为独立的命令行工具，方便直接调用。

#### 基本用法

```bash
# 从已配置的服务器生成 CLI
mcporter generate-cli --server <server_name>

# 从 URL 直接生成
mcporter generate-cli --command "https://api.example.com/mcp"
```

#### 示例

```bash
# 生成了 CLI 后，直接像普通命令一样调用
mcporter generate-cli --server github

# 现在可以直接调用
github-list-issues --repo owner/repo --limit 10
github-create-issue --title "New feature" --body "Description"
```

---

### 2.7 `mcporter inspect-cli` — 检查生成的 CLI

查看已生成的 CLI 工具的详细信息：

```bash
mcporter inspect-cli <path_to_cli> [--json]
```

**输出示例：**

```
CLI: github-list-issues
Generated from: github
Path: /usr/local/bin/github-list-issues

Arguments:
  --repo     string   Repository (owner/repo)
  --limit    int      Max number of issues (default: 10)
  --state    string   open/closed/all (default: open)

Flags:
  --json     Output as JSON
  --help     Show help
```

---

### 2.8 `mcporter emit-ts` — 生成 TypeScript 类型

为 MCP 服务器生成 TypeScript 类型定义，方便在 TypeScript 项目中使用。

```bash
# 生成客户端类型
mcporter emit-ts <server> --mode client

# 生成完整类型定义
mcporter emit-ts <server> --mode types
```

**输出示例：**

```typescript
// generated by mcporter emit-ts
export interface McpServer {
  list_issues(params: { team?: string; limit?: number }): Promise<Issue[]>;
  create_issue(params: { title: string; body?: string; team?: string }): Promise<Issue>;
  get_file(params: { repo: string; path: string }): Promise<FileContent>;
}
```

---

## 3. MCP 服务器配置示例

### 3.1 文件系统 MCP（stdio）

用于让 AI 读写本地文件。

```bash
# 通过 npx 直接运行
mcporter config add filesystem --stdio "npx -y @modelcontextprotocol/server-filesystem /tmp"

# 或指定具体路径
mcporter config add filesystem --stdio "node /path/to/filesystem/server.js /home/user"
```

**常用工具：**
- `filesystem.read_file` — 读取文件
- `filesystem.write_file` — 写入文件
- `filesystem.list_directory` — 列出目录
- `filesystem.create_directory` — 创建目录

### 3.2 HTTP MCP 服务器

标准的 HTTP MCP 服务端点。

```json
// config.json 中配置
{
  "servers": {
    "my-api": {
      "transport": "http",
      "url": "https://api.example.com/mcp",
      "auth": {
        "type": "bearer",
        "token": "your-api-token-here"
      }
    }
  }
}
```

或在命令行添加：

```bash
mcporter config add my-api \
  --url https://api.example.com/mcp \
  --header "Authorization: Bearer your-token-here"
```

### 3.3 stdio MCP 服务器

需要通过子进程启动的 MCP 服务器。

```bash
mcporter config add custom-server --stdio "node /path/to/custom-server/index.js"
```

**带参数的 stdio 配置：**

```bash
# 服务器启动时需要参数
mcporter config add slack --stdio "node server.js --channel general"

# 调用
mcporter call slack.post_message text="Hello from mcporter"
```

### 3.4 完整配置示例

```json
// ~/.config/mcporter/config.json
{
  "servers": {
    "filesystem": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/home/user"]
    },
    "github": {
      "transport": "http",
      "url": "https://api.github.com/mcp",
      "headers": {
        "Authorization": "Bearer ghp_xxxxxxxxxxxx",
        "Accept": "application/vnd.github+json"
      }
    },
    "slack": {
      "transport": "http",
      "url": "https://slack-mcp.example.com",
      "auth": {
        "type": "oauth2",
        "clientId": "xxx",
        "clientSecret": "yyy"
      }
    }
  }
}
```

---

## 4. 实战用例

### 4.1 与股票数据 MCP 服务器配合

假设你有一个股票数据 MCP 服务器：

```bash
# 添加服务器
mcporter config add stock-data --url https://stock-mcp.example.com --header "X-API-Key: your-key"

# 查看可用工具
mcporter list stock-data --schema

# 查询股票数据
mcporter call stock-data.get_quote symbol=AAPL --output json

# 批量查询
mcporter call stock-data.get_batch_quotes symbols=["AAPL", "GOOGL", "MSFT"] --output json
```

### 4.2 自动化任务流程

```bash
#!/bin/bash
# 自动备份 + 推送到 GitHub

# 1. 通过文件系统 MCP 读取本地文件
mcporter call filesystem.read_file path=/backup/data.sql

# 2. 通过 GitHub MCP 创建 gist
GIST_CONTENT=$(mcporter call filesystem.read_file path=/backup/data.sql --output json | jq -r '.content')
mcporter call github.create_gist filename=data.sql content="$GIST_CONTENT" --output json
```

### 4.3 复杂参数传递

```bash
# 使用 JSON payload 传递复杂参数
mcporter call github.search_code --args '{
  "repo": "anthropics/mcp",
  "query": "stdio",
  "lang": "typescript",
  "maxResults": 20
}'
```

### 4.4 与 AI 模型对话中调用工具

在 AI 对话系统中集成 mcporter：

```bash
# 模型决定调用工具后，系统执行：
RESULT=$(mcporter call linear.list_issues team=ENG limit:10 --output json)
echo "$RESULT" | jq '.[] | "- [\(.state)] \(.title)"'
```

---

## 5. 故障排除

### 常见问题

#### Q1: `mcporter: command not found`

```bash
# 确认安装
npm list -g mcporter

# 重新安装
npm install -g mcporter

# 确认 PATH 包含 npm global bin
echo $PATH
```

#### Q2: stdio 服务器启动失败

```bash
# 检查命令是否正确
node /path/to/server.js --help

# 检查 Node 版本
node --version  # 需要 v18+

# 查看详细错误
mcporter call --stdio "node /path/to/server.js" tool_name arg=value --verbose
```

#### Q3: HTTP 服务器连接超时

```bash
# 检查服务器是否可达
curl -v https://api.example.com/mcp

# 确认 URL 正确
mcporter config get <server>

# 尝试 ping
mcporter call <server>.ping --timeout 10000
```

#### Q4: 认证失败

```bash
# 重置并重新认证
mcporter auth <server> --reset

# 检查 token 是否过期
mcporter config get <server>

# 手动设置 token
mcporter config add <server> --url https://api.example.com/mcp --token "new-token"
```

#### Q5: 工具参数类型错误

```bash
# 先查看 schema 了解参数类型
mcporter list <server> --schema

# 使用 JSON payload 确保类型正确
mcporter call <server>.<tool> --args '{"limit": 5, "filter": null}'
```

#### Q6: 守护进程无法启动

```bash
# 端口被占用
lsof -i :3100
kill <PID>

# 使用自定义端口
mcporter daemon start --port 3200

# 查看日志
mcporter daemon status
```

### 调试模式

```bash
# 开启详细日志
mcporter call <server>.<tool> --verbose

# 查看完整 HTTP 请求/响应
mcporter call <server>.<tool> --debug

# 检查配置
mcporter config list --verbose
```

### 日志位置

```bash
# 守护进程日志
~/.config/mcporter/logs/daemon.log

# 配置
~/.config/mcporter/config.json
```

---

## 6. 参考速查

### 快速命令速查表

| 操作 | 命令 |
|------|------|
| 列出服务器 | `mcporter list` |
| 查看 schema | `mcporter list <server> --schema` |
| 调用工具 | `mcporter call <server>.<tool> arg=value` |
| 查看配置 | `mcporter config list` |
| 添加服务器 | `mcporter config add <name> --url <url>` |
| 删除服务器 | `mcporter config remove <name>` |
| OAuth 认证 | `mcporter auth <server>` |
| 启动守护 | `mcporter daemon start` |
| 生成 CLI | `mcporter generate-cli --server <name>` |
| 生成 TS 类型 | `mcporter emit-ts <server> --mode types` |

### 配置文件位置

| 环境 | 路径 |
|------|------|
| 默认 | `./config/mcporter.json` |
| 指定 | `--config /path/to/config.json` |
| 用户级 | `~/.config/mcporter/config.json` |

### 输出格式

| 格式 | 用途 |
|------|------|
| (默认) | 人类可读格式 |
| `--output json` | JSON 格式（脚本处理） |
| `--output text` | 纯文本 |

---

## 7. 相关资源

- **官网**: http://mcporter.dev
- **GitHub**: https://github.com/modelcontextprotocol/mcporter
- **MCP Spec**: https://modelcontextprotocol.io
