#!/usr/bin/env python3
"""
主动技术研究 - 每周扫描 GitHub Trending + 沉淀报告
发现相关的开源项目，主动生成研究报告
"""
import os
import json
import requests
from datetime import datetime
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
LOG_DIR = f"{WORKSPACE}/.learnings/tech_research"
os.makedirs(LOG_DIR, exist_ok=True)

# 关注的技术栈
INTERESTS = [
    "trading", "stock", "finance", "quant",  # 量化交易
    "rag", "knowledge-base", "llamaindex", "langchain",  # RAG/知识库
    "fine-report", "bi", "analytics",  # BI/报表
    "agent", "multi-agent", "langgraph",  # Agent
    "stock-market", "a-stock", "china",  # A股相关
]

WATCH_REPOS = [
    "bytedance/deer-flow",
    "TauricResearch/TradingAgents",
    "HKUDS/DeepTutor",
]

def search_github_trending(keywords):
    """搜索 GitHub Trending，找到相关的项目"""
    results = []
    seen = set()
    for kw in keywords:
        try:
            url = f"https://api.github.com/search/repositories"
            params = {
                "q": f"{kw} stars:>50 pushed:>2026-03-01",
                "sort": "updated",
                "per_page": 5
            }
            r = requests.get(url, params=params, timeout=8, headers={"Accept": "application/vnd.github.v3+json"})
            if r.status_code != 200:
                continue
            data = r.json()
            for repo in data.get('items', []):
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
                    "pushed": repo.get('pushed_at', ''),
                    "match_keyword": kw,
                })
        except Exception as e:
            print(f"  搜索 {kw} 失败: {e}")
    return results

def check_watch_repos():
    """检查关注仓库的更新"""
    updates = []
    for repo in WATCH_REPOS:
        try:
            r = requests.get(f"https://api.github.com/repos/{repo}", timeout=5)
            if r.status_code == 200:
                d = r.json()
                updates.append({
                    "name": repo,
                    "description": d.get('description', ''),
                    "stars": d.get('stargazers_count', 0),
                    "latest_tag": None,
                    "url": d.get('html_url', ''),
                    "pushed": d.get('pushed_at', ''),
                })
                # 获取最新 release
                r2 = requests.get(f"https://api.github.com/repos/{repo}/releases/latest", timeout=5)
                if r2.status_code == 200:
                    updates[-1]['latest_tag'] = r2.json().get('tag_name', '')
        except Exception as e:
            print(f"  检查 {repo} 失败: {e}")
    return updates

def generate_report(repos, watch_updates):
    """生成研究报告"""
    today = datetime.now().strftime('%Y-%m-%d')
    report_path = f"{LOG_DIR}/tech_intel_{today}.md"

    lines = [
        f"# 技术情报 | {today}",
        "",
        f"自动生成 | 发现 {len(repos)} 个相关项目",
        "",
    ]

    if watch_updates:
        lines.append("## 🔭 关注仓库动态")
        lines.append("")
        for u in watch_updates:
            tag_info = f" → `{u['latest_tag']}`" if u['latest_tag'] else ""
            lines.append(f"- **{u['name']}** ⭐{u['stars']}{tag_info}")
            lines.append(f"  {u['description']}")
            lines.append(f"  {u['url']}")
        lines.append("")

    if repos:
        lines.append("## 🆕 GitHub Trending 相关项目")
        lines.append("")
        # 按 stars 排序
        repos.sort(key=lambda x: x['stars'], reverse=True)
        for r in repos[:10]:
            topics = ' '.join([f'`{t}`' for t in r['topics'][:3]])
            lines.append(f"- **{r['name']}** ({r['language']}) ⭐{r['stars']} 匹配: `{r['match_keyword']}`")
            lines.append(f"  {r['description']}")
            if topics:
                lines.append(f"  {topics}")
            lines.append(f"  {r['url']}")
            lines.append("")

    lines.append("---")
    lines.append(f"_由 OpenClaw 自动生成_")

    content = '\n'.join(lines)
    with open(report_path, 'w') as f:
        f.write(content)

    return report_path, len(repos)

def main():
    print("=" * 50)
    print(f"主动技术研究扫描 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    print("1/2 扫描 GitHub Trending...")
    repos = search_github_trending(INTERESTS)
    print(f"   发现 {len(repos)} 个相关项目")

    print("2/2 检查关注仓库...")
    watch = check_watch_repos()
    print(f"   关注仓库 {len(watch)} 个")

    report_path, count = generate_report(repos, watch)
    print(f"")
    print(f"✅ 报告已生成: {report_path}")
    print(f"   共 {count} 个相关项目")

if __name__ == "__main__":
    main()
