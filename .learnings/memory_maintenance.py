#!/usr/bin/env python3
"""
每周记忆整理 - 知识库自动维护
每周一 09:00 运行：清理过期文件、更新 MEMORY.md、整理 learnings
"""
import os
import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

WORKSPACE = "/root/.openclaw/workspace"
LOG_DIR = f"{WORKSPACE}/.learnings"
MEMORY_FILE = f"{WORKSPACE}/MEMORY.md"
os.makedirs(LOG_DIR, exist_ok=True)

def log(msg):
    print(f"[记忆整理] {msg}")

def get_file_age_days(path):
    return (datetime.now() - datetime.fromtimestamp(os.path.getmtime(path))).days

# ========== 1. 清理临时文件 ==========
def clean_temp_files():
    patterns = ['*.tmp', '*.bak', '*.log.*', 'test_*.py', '__pycache__']
    cleaned = []
    for root, dirs, files in os.walk(WORKSPACE):
        # 跳过特定目录
        if any(x in root for x in ['.git', 'node_modules', 'venv', '.venv', 'TradingAgents']):
            continue
        for p in patterns:
            for f in files:
                if f.endswith(p.replace('*', '')) or f.startswith('test_'):
                    path = os.path.join(root, f)
                    age = get_file_age_days(path)
                    if age >= 7:  # 超过7天的临时文件
                        try:
                            os.remove(path)
                            cleaned.append(path)
                        except:
                            pass
    return cleaned

# ========== 2. 整理 learnings 日志 ==========
def consolidate_learnings():
    """把分散的 learnings 合并整理"""
    learnings_file = f"{LOG_DIR}/consolidated_learnings.md"
    sections = []

    for fname in ['ERRORS.md', 'LEARNINGS.md', 'FEATURE_REQUESTS.md']:
        fpath = os.path.join(LOG_DIR, fname)
        if os.path.exists(fpath):
            with open(fpath) as f:
                content = f.read().strip()
            if content:
                sections.append(f"## {fname.replace('.md','')}\n\n{content}\n")

    if sections:
        with open(learnings_file, 'w') as f:
            f.write(f"# 经验沉淀汇总 (更新于 {datetime.now().strftime('%Y-%m-%d')})\n\n")
            f.write("\n".join(sections))
        return learnings_file
    return None

# ========== 3. 更新 MEMORY.md ==========
def update_memory_from_learnings():
    """从 learnings 提炼高价值经验到 MEMORY.md"""
    errors_file = os.path.join(LOG_DIR, 'ERRORS.md')
    if not os.path.exists(errors_file):
        return

    with open(errors_file) as f:
        content = f.read()

    # 提取最近一周的错误模式
    lines = content.split('\n')
    recent_errors = []
    for i, line in enumerate(lines):
        if '## ' in line and get_file_age_days(errors_file) <= 7:
            recent_errors.append(line.strip('# '))

    if recent_errors:
        # 在 MEMORY.md 末尾追加错误模式提醒
        section = f"\n## 🔴 常见错误模式 (最近一周)\n"
        for err in recent_errors[:5]:  # 最多5条
            section += f"- {err}\n"

        with open(MEMORY_FILE, 'a') as f:
            f.write(section)
        return True
    return False

# ========== 4. 清理旧的 daily learning ==========
def clean_old_daily_learning():
    """清理超过30天的每日学习文件"""
    learning_dir = f"{WORKSPACE}/skills/daily-learning"
    if not os.path.exists(learning_dir):
        return []
    cleaned = []
    for f in os.listdir(learning_dir):
        if f.endswith('.md') and 'daily-learning' in f:
            path = os.path.join(learning_dir, f)
            if get_file_age_days(path) >= 30:
                os.remove(path)
                cleaned.append(f)
    return cleaned

# ========== 5. 健康报告 ==========
def generate_health_report():
    report = {
        "timestamp": datetime.now().isoformat(),
        "workspace_size_mb": 0,
        "learnings_count": 0,
        "temp_files_cleaned": 0,
        "old_learning_cleaned": 0,
        "issues": []
    }

    # 工作区大小
    total = sum(os.path.getsize(os.path.join(r, f)) for r, d, fs in os.walk(WORKSPACE) for f in fs)
    report['workspace_size_mb'] = round(total / 1024 / 1024, 1)

    # learnings 数量
    if os.path.exists(LOG_DIR):
        report['learnings_count'] = len([f for f in os.listdir(LOG_DIR) if f.endswith('.md')])

    return report

# ========== 主程序 ==========
if __name__ == "__main__":
    print("=" * 50)
    print(f"每周记忆整理 {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 50)

    print("1/5 清理临时文件...")
    cleaned = clean_temp_files()
    print(f"   清理了 {len(cleaned)} 个临时文件")

    print("2/5 整理 learnings...")
    consolidated = consolidate_learnings()
    print(f"   合并到 {consolidated}" if consolidated else "   无 learnings 内容")

    print("3/5 更新 MEMORY.md...")
    updated = update_memory_from_learnings()
    print(f"   {'已更新 MEMORY.md' if updated else '无需更新'}")

    print("4/5 清理过期每日学习...")
    old = clean_old_daily_learning()
    print(f"   清理了 {len(old)} 个过期文件")

    print("5/5 生成健康报告...")
    report = generate_health_report()
    print(f"   工作区: {report['workspace_size_mb']} MB")
    print(f"   learnings: {report['learnings_count']} 个文件")

    print()
    print(f"✅ 整理完成")
