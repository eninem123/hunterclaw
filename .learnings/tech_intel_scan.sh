#!/bin/bash
# 每日技术情报扫描
# 每天 heartbeat 时运行，扫 GitHub Trending，有相关的就沉淀到 learnings

cd /root/.openclaw/workspace

LOG_FILE="/root/.openclaw/workspace/.learnings/tech_intel.log"
mkdir -p /root/.openclaw/workspace/.learnings

echo "=== 技术情报扫描 $(date '+%Y-%m-%d %H:%M') ==="

# 关注的关键字（和当前项目相关）
KEYWORDS="deerflow tradingagents langgraph rag knowledge-base stock-trading fine-report"
# 关注的仓库（主动跟踪）
WATCH_REPOS="bytedance/deer-flow TauricResearch/TradingAgents"

# 扫 GitHub Trending
TRENDING=$(curl -s --max-time 10 "https://api.github.com/search/repositories?q=stars:>100+pushed:>2026-01-01&sort=updated&per_page=20" 2>/dev/null | python3 -c "
import json,sys
data = json.load(sys.stdin)
for r in data.get('items', [])[:10]:
    topics = ' '.join(r.get('topics', []))
    desc = r.get('description', '')
    name = r.get('full_name', '')
    lang = r.get('language', '')
    stars = r.get('stargazers_count', 0)
    print(f'{name}|{lang}|{stars}|{desc[:80]}')
" 2>/dev/null)

# 过滤相关的
RELEVANT=""
for line in $TRENDING; do
    info=$(echo "$line" | grep -iE "$KEYWORDS" || true)
    if [ -n "$info" ]; then
        RELEVANT="$RELEVANT\n$info"
    fi
done

if [ -n "$RELEVANT" ]; then
    echo "=== 发现相关项目 ===" >> "$LOG_FILE"
    date '+%Y-%m-%d %H:%M' >> "$LOG_FILE"
    echo "$RELEVANT" >> "$LOG_FILE"
    echo "---" >> "$LOG_FILE"
    echo "✅ 已记录到 $LOG_FILE"
else
    echo "ℹ️ 本次无新增相关项目"
fi

# 检查 watch repos 的更新
for repo in $WATCH_REPOS; do
    echo "检查 $repo..."
    LAST_TAG=$(curl -s --max-time 5 "https://api.github.com/repos/$repo/releases/latest" 2>/dev/null | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('tag_name',''))" 2>/dev/null)
    echo "  最新版本: $LAST_TAG"
done

echo "=== 扫描完成 ==="
