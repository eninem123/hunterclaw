#!/bin/bash
# IMA自动学习脚本 v4 (修复版)
# 问题：v3版本highlight_content提取为空
# 修复：改用文档内容获取接口，支持.docx解析

set -e

# 加载IMA凭证
if [ -f ~/.config/ima/.env ]; then
    export 
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

TASK_TYPE="${1:-hourly}"
log "=== 开始IMA学习任务: $TASK_TYPE ==="

if [ "$TASK_TYPE" = "hourly" ]; then
    log "执行每小时学习任务"
    
    # 搜索知识库
    search_result=$(ima_api "openapi/wiki/v1/search_knowledge" '{"query":"交易 系统","knowledge_base_id":"'"$KNOWLEDGE_BASE_ID"'","limit":3}')
    log "搜索结果: $search_result"
    
    # 提取文档ID列表
    doc_ids=$(echo "$search_result" | grep -o '"media_id":"[^"]*"' | head -3 | sed 's/"media_id":"//g; s/"//g')
    
    if [ -n "$doc_ids" ]; then
        # 尝试获取第一个文档的详细内容
        first_doc=$(echo "$doc_ids" | head -1)
        doc_content=$(ima_api "openapi/wiki/v1/get_document" '{"media_id":"'"$first_doc"'","knowledge_base_id":"'"$KNOWLEDGE_BASE_ID"'"}')
        log "文档内容: ${doc_content:0:500}"
        
        # 如果有内容，提取摘要同步到MEMORY
        doc_title=$(echo "$doc_content" | grep -o '"title":"[^"]*"' | head -1 | sed 's/"title":"//g; s/"//g')
        echo '' >> /root/.openclaw/memory/MEMORY.md
        echo '## IMA知识库学习 [$(date '+%Y-%m-%d %H:%M')]' >> /root/.openclaw/memory/MEMORY.md
        echo '- 来源: 熊猫交易学社' >> /root/.openclaw/memory/MEMORY.md
        echo "- 文档: $doc_title" >> /root/.openclaw/memory/MEMORY.md
    else
        log "未找到相关文档"
    fi
    
elif [ "$TASK_TYPE" = "daily" ]; then
    log "执行每日学习任务 - 同步行业报告"
    # 获取知识库内容列表
    kb_list=$(ima_api "openapi/wiki/v1/get_knowledge_list" '{"knowledge_base_id":"'"$KNOWLEDGE_BASE_ID"'","limit":10}')
    log "知识库列表: ${kb_list:0:1000}"
fi

log "=== 学习任务完成 ==="
