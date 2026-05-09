#!/bin/bash
# IMA自动学习脚本 v3
# 每小时从熊猫交易学社学习，每日同步行业报告

set -e

# 加载IMA凭证（从.env或配置文件）
if [ -f ~/.config/ima/.env ]; then
    export $(grep -E '^IMA_' ~/.config/ima/.env | xargs)
fi
IMA_CLIENT_ID="${IMA_OPENAPI_CLIENTID:-$(cat ~/.config/ima/client_id 2>/dev/null)}"
IMA_API_KEY="${IMA_OPENAPI_APIKEY:-$(cat ~/.config/ima/api_key 2>/dev/null)}"

if [ -z "$IMA_CLIENT_ID" ] || [ -z "$IMA_API_KEY" ]; then
    echo "[$(date)] 缺少IMA凭证，退出"
    exit 1
fi

# 日志函数
log() {
    mkdir -p /root/.openclaw/workspace/learnings/logs
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> /root/.openclaw/workspace/learnings/logs/learn-$(date +%Y%m%d).log
}

# IMA API调用函数
ima_api() {
    local path="$1"
    local body="$2"
    curl -s -X POST "https://ima.qq.com/$path" \
        -H "ima-openapi-clientid: $IMA_CLIENT_ID" \
        -H "ima-openapi-apikey: $IMA_API_KEY" \
        -H "Content-Type: application/json" \
        -d "$body"
}

# 知识库ID（熊猫交易学社）
KNOWLEDGE_BASE_ID="iFPmUeevoDt78KS69UNX6V6UQ0zDvY61vwIvJHoxlPw="

# 学习任务类型
TASK_TYPE="${1:-hourly}"
log "=== 开始IMA学习任务: $TASK_TYPE ==="

if [ "$TASK_TYPE" = "hourly" ]; then
    # 每小时学习：从熊猫交易学社获取最新内容
    log "执行每小时学习任务 - 搜索熊猫交易学社最新内容"
    
    # 搜索知识库最新内容
    search_result=$(ima_api "openapi/wiki/v1/search_knowledge" '{"query":"交易 系统","knowledge_base_id":"'"$KNOWLEDGE_BASE_ID"'","limit":5}')
    log "搜索结果: $search_result"
    
    # 提取高亮内容
    highlights=$(echo "$search_result" | grep -o '"highlight_content":"[^"]*"' | head -3)
    
    # 同步到MEMORY
    mkdir -p /root/.openclaw/memory
    echo '' >> /root/.openclaw/memory/MEMORY.md
    echo '## IMA知识库学习 [$(date '+%Y-%m-%d %H:%M')]' >> /root/.openclaw/memory/MEMORY.md
    echo '- 来源: 熊猫交易学社' >> /root/.openclaw/memory/MEMORY.md
    echo '- 任务类型: 每小时自动学习' >> /root/.openclaw/memory/MEMORY.md
    echo "- 提取内容: $highlights" >> /root/.openclaw/memory/MEMORY.md
    
elif [ "$TASK_TYPE" = "daily" ]; then
    # 每日任务：同步行业报告
    log "执行每日学习任务 - 同步行业报告"
    
    # 获取知识库详情
    kb_info=$(ima_api "openapi/wiki/v1/get_knowledge_base" '{"ids":["'"$KNOWLEDGE_BASE_ID"'"]}')
    log "知识库信息: $kb_info"
    
    # 获取知识库内容列表
    kb_list=$(ima_api "openapi/wiki/v1/get_knowledge_list" '{"knowledge_base_id":"'"$KNOWLEDGE_BASE_ID"'","limit":20}')
    log "知识库列表: $kb_list"
    
    # 同步到MEMORY
    echo '' >> /root/.openclaw/memory/MEMORY.md
    echo '## IMA知识库每日同步 [$(date '+%Y-%m-%d')]' >> /root/.openclaw/memory/MEMORY.md
    echo '- 来源: 熊猫交易学社' >> /root/.openclaw/memory/MEMORY.md
    echo '- 任务类型: 每日行业报告同步' >> /root/.openclaw/memory/MEMORY.md
fi

log "=== 学习任务完成 ==="
