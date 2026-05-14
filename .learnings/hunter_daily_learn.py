#!/usr/bin/env python3
"""
猎手每日主动学习 - 每日5次
基于社区最新消息 + 开源代码学习 → 优化猎手系统

触发时间（交易日）：
  09:00 - 开盘前学习（昨夜GitHub更新）
  10:30 - 盘中学习（第一波行情后）
  12:00 - 午间学习（社区热议）
  14:00 - 午后期中学习（收官前）
  15:30 - 盘后学习（今日总结）

数据来源：
  1. GitHub Trending（量化交易/Agent/A股相关）
  2. GitHub Watch仓库（TradingAgents/Vibe-Trading等）
  3. 猎手社区讨论（待接入Discord/Telegram）
  4. 猎手今日运行日志

输出：
  - 技术情报报告（tech_intel_YYYY-MM-DD.md）
  - 社区洞察摘要
  - 发现可优化的点
"""

import os
import json
import requests
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

WORKSPACE = "/root/.openclaw/workspace"
LOG_DIR = f"{WORKSPACE}/.learnings/tech_research"
os.makedirs(LOG_DIR, exist_ok=True)

# 关注的技术栈（按优先级）
INTERESTS = [
    # 量化交易（核心）
    ("trading system", "trading", 30),
    ("stock market", "quantitative", 25),
    ("akshare", "tushare", 20),
    # Agent框架
    ("langgraph agent", "multi-agent", 20),
    ("claude agent", "openai agent", 15),
    # A股相关
    ("china stock", "a-stock", 15),
    ("finrl", "tradingagents", 10),
]

# 重点关注的仓库
WATCH_REPOS = [
    "HKUDS/Vibe-Trading",       # 刚集成
    "TauricResearch/TradingAgents",  # 量化Agent
    "akfamily/akshare",         # 行情数据
    "AI4Finance-Foundation/FinRL",  # 强化学习炒股的
    "quant SLA/DeepTrading",    # 深度学习量化
    "Devoxin/QuantChat",        # LLM+量化
    "pastel- industries /phq-135", # 高频量化（备用）
]

# 社区关键词（发现热点）
COMMUNITY_KEYWORDS = [
    "涨停", "龙头股", "量价", "动量", "趋势",
    "rsi", "macd", "止损", "止盈", "仓位管理",
    "选股", "量化策略", "回测",
]


# ══════════════════════════════════════════════════════════
# 1. GitHub Trending 扫描
# ══════════════════════════════════════════════════════════

def search_github_trending() -> List[Dict]:
    results = []
    seen = set()
    for kw, _, min_stars in INTERESTS:
        try:
            url = "https://api.github.com/search/repositories"
            params = {
                "q": f"{kw} stars:>{min_stars} pushed:>{datetime.now()-timedelta(days=7)}",
                "sort": "updated",
                "per_page": 5
            }
            r = requests.get(url, params=params, timeout=8,
                          headers={"Accept": "application/vnd.github.v3+json"})
            if r.status_code != 200:
                continue
            for repo in r.json().get('items', []):
                name = repo['full_name']
                if name in seen:
                    continue
                seen.add(name)
                results.append({
                    "name": name,
                    "description": repo.get('description', ''),
                    "language": repo.get('language', ''),
                    "stars": repo.get('stargazers_count', 0),
                    "topics": repo.get('topics', []),
                    "url": repo.get('html_url', ''),
                    "updated": repo.get('pushed_at', ''),
                    "match": kw,
                })
        except Exception as e:
            print(f"  [{kw}] 失败: {e}")
    # 按stars排序
    results.sort(key=lambda x: x['stars'], reverse=True)
    return results[:15]


def check_watch_repos() -> List[Dict]:
    """检查关注仓库的近期更新"""
    updates = []
    for repo in WATCH_REPOS:
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}", timeout=8)
            if r.status_code != 200:
                continue
            d = r.json()
            pushed = datetime.strptime(d['pushed_at'], '%Y-%m-%dT%H:%M:%SZ')
            days_ago = (datetime.now() - pushed).days
            updates.append({
                "name": repo,
                "description": d.get('description', ''),
                "stars": d.get('stargazers_count', 0),
                "url": d.get('html_url', ''),
                "days_ago": days_ago,
                "lang": d.get('language', ''),
                "topics": d.get('topics', [])[:3],
            })
        except Exception as e:
            print(f"  [{repo}] 检查失败: {e}")
    updates.sort(key=lambda x: x['days_ago'])
    return updates


# ══════════════════════════════════════════════════════════
# 2. 猎手系统自检（发现可优化点）
# ══════════════════════════════════════════════════════════

def analyze_hunter_issues() -> List[str]:
    """
    分析猎手系统近期运行日志，发现可优化点
    """
    issues = []
    logs_dir = Path(f"{WORKSPACE}/猎手模拟交易/logs")
    if not logs_dir.exists():
        return ["日志目录不存在"]

    # 读最近日志
    recent_logs = sorted(logs_dir.glob("*.log"), reverse=True)[:3]
    error_count = 0
    warning_count = 0

    for log_file in recent_logs:
        try:
            content = log_file.read_text()
            error_count += content.count("ERROR") + content.count("Traceback")
            warning_count += content.count("WARNING") + content.count("失败")
        except Exception:
            pass

    if error_count > 0:
        issues.append(f"⚠️ {error_count}个错误日志需要处理")
    if warning_count > 3:
        issues.append(f"⚠️ {warning_count}个警告日志")

    # 检查持仓异常
    try:
        import json as js
        pf = js.load(open(f"{WORKSPACE}/猎手模拟交易/持仓.json"))
        positions = pf.get("positions", [])
        # 检查是否有买在涨停价的
        for pos in positions:
            note = pos.get("note", "")
            if "买在涨停" in note or "买在" in note:
                issues.append(f"🔴 {pos['name']} 买入记录异常（{note}）")
    except Exception:
        pass

    return issues if issues else ["✅ 今日系统运行正常"]


# ══════════════════════════════════════════════════════════
# 3. 生成学习报告
# ══════════════════════════════════════════════════════════

def generate_learning_report(repos, watch_repos, issues, run_count: int) -> str:
    today = datetime.now()
    date_str = today.strftime('%Y-%m-%d')
    time_str = today.strftime('%H:%M')
    report_path = f"{LOG_DIR}/learning_{date_str}_{run_count:02d}.md"

    # 判断是今天第几次扫描
    run_labels = {1: "开盘前", 2: "盘中", 3: "午间", 4: "午后", 5: "盘后"}

    lines = [
        f"# 🧬 猎手每日主动学习 | {date_str} {time_str}（第{run_count}次/{run_labels.get(run_count, run_count)}）",
        "",
        f"自动生成 | 扫描时间: {today.isoformat()}",
        "",
    ]

    # 系统自检
    lines.append("## 🔍 猎手系统自检")
    for issue in issues:
        lines.append(f"- {issue}")
    lines.append("")

    # 关注仓库动态
    if watch_repos:
        lines.append("## 🔭 重点仓库动态")
        for r in watch_repos[:8]:
            freshness = f"{r['days_ago']}天前" if r['days_ago'] > 0 else "今日更新"
            lines.append(f"- **{r['name']}** ⭐{r['stars']} ({freshness})")
            lines.append(f"  {r['description']}")
            lines.append(f"  {r['url']}")
        lines.append("")

    # GitHub Trending
    if repos:
        lines.append("## 🆕 GitHub 相关项目发现")
        for r in repos[:8]:
            topics = ' '.join([f'`{t}`' for t in r['topics'][:2]])
            lines.append(f"- **{r['name']}** ({r['language']}) ⭐{r['stars']} [匹配:{r['match']}]")
            lines.append(f"  {r['description']}")
            if topics:
                lines.append(f"  {topics}")
        lines.append("")

    # 学习洞察
    lines.append("## 💡 学习洞察")
    if repos:
        top_repo = repos[0]
        lines.append(f"- **{top_repo['name']}** 值得关注：{top_repo['description']}")
    if watch_repos and watch_repos[0]['days_ago'] <= 2:
        lines.append(f"- **{watch_repos[0]['name']}** 有近期更新，可能有新功能")

    lines.append("")
    lines.append(f"---")
    lines.append(f"_由 龙波(OpenClaw) 自动生成 | 第{run_count}/5次学习扫描_")

    content = '\n'.join(lines)
    with open(report_path, 'w') as f:
        f.write(content)
    return report_path


# ══════════════════════════════════════════════════════════
# 4. 主入口
# ══════════════════════════════════════════════════════════

def main(run_count: int = 1):
    print(f"[主动学习] 第{run_count}/5次扫描 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    print("[1/3] 扫描 GitHub Trending...")
    repos = search_github_trending()
    print(f"   发现 {len(repos)} 个相关项目")

    print("[2/3] 检查重点仓库...")
    watch = check_watch_repos()
    print(f"   关注仓库 {len(watch)} 个")

    print("[3/3] 分析猎手系统...")
    issues = analyze_hunter_issues()
    for iss in issues:
        print(f"   {iss}")

    report_path = generate_learning_report(repos, watch, issues, run_num)
    print(f"\n✅ 报告: {report_path}")


if __name__ == "__main__":
    # 支持命令行参数指定第几次
    run_num = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    main(run_num)
