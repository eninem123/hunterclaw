#!/usr/bin/env python3
"""
Hermes 策略技能树更新器
每次策略分析后自动调用，将新经验固化到技能树
"""
import json
import yaml
import os
import sys
from datetime import datetime
from pathlib import Path

SKILL_TREE_DIR = Path("/root/.hermes/猎手模拟交易/skill-tree")
L3_SKILLS_DIR = SKILL_TREE_DIR / "L3-Skills"
L4_ARCHIVES_DIR = SKILL_TREE_DIR / "L4-Archives"
INDEX_FILE = SKILL_TREE_DIR / "index.json"

def load_index():
    if INDEX_FILE.exists():
        with open(INDEX_FILE) as f:
            return json.load(f)
    return {"version": "1.0", "L3_Skills": [], "L4_Archives": [], "stats": {}}

def save_index(idx):
    with open(INDEX_FILE, "w") as f:
        json.dump(idx, f, ensure_ascii=False, indent=2)

def skill_exists(idx, skill_id):
    return any(s["id"] == skill_id for s in idx.get("L3_Skills", []))

def archive_exists(idx, date, code):
    return any(
        a.get("date") == date and a.get("code") == code
        for a in idx.get("L4_Archives", [])
    )

def update_skill_score(idx, skill_id, new_score):
    """更新技能评分（取历史最高分）"""
    for s in idx["L3_Skills"]:
        if s["id"] == skill_id:
            if new_score > s.get("score", 0):
                s["score"] = new_score
            s["last_updated"] = datetime.now().strftime("%Y-%m-%d")
            break

def add_lesson(date, code, name, lesson_type, lesson_text, skill_refs, outcome, pnl_pct=0):
    """
    将一次交易经验归档到技能树
    
    date: 交易日期
    code: 股票代码
    name: 股票名称
    lesson_type: 正面/反面/改进
    lesson_text: 经验描述
    skill_refs: 关联技能ID列表
    outcome: 结果
    """
    idx = load_index()
    
    # 检查是否已存在
    if archive_exists(idx, date, code):
        print(f"[技能树] {date} {code} 已归档，跳过")
        return
    
    # 归档到 L4
    archive = {
        "date": date,
        "code": code,
        "name": name,
        "lesson_type": lesson_type,
        "lesson": lesson_text,
        "skill_refs": skill_refs,
        "outcome": outcome,
        "pnl_pct": pnl_pct,
        "archived_at": datetime.now().strftime("%Y-%m-%d %H:%M")
    }
    
    idx.setdefault("L4_Archives", []).append(archive)
    
    # 更新关联技能的评分
    for ref in skill_refs:
        score = 10 if lesson_type == "正面" else (7 if lesson_type == "改进" else 5)
        update_skill_score(idx, ref, score)
    
    # 更新统计
    idx["stats"]["total_trades"] = idx["stats"].get("total_trades", 0) + 1
    
    # 写 L4 归档文件
    archive_file = L4_ARCHIVES_DIR / f"{date}_{code}.yaml"
    with open(archive_file, "w") as f:
        yaml.dump(archive, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    save_index(idx)
    print(f"[技能树] 已归档: {date} {code} {name} | 类型:{lesson_type} | 关联技能:{skill_refs}")
    print(f"[技能树] 当前技能数: {len(idx['L3_Skills'])} | 归档数: {len(idx['L4_Archives'])}")

def show_skill_tree():
    """展示技能树"""
    idx = load_index()
    print("\n" + "=" * 60)
    print("🔮 Hermes 策略技能树")
    print("=" * 60)
    print(f"总技能数: {len(idx['L3_Skills'])}")
    print(f"总归档数: {len(idx['L4_Archives'])}")
    print()
    
    # 按分类分组
    categories = {}
    for s in idx["L3_Skills"]:
        cat = s.get("category", "其他")
        categories.setdefault(cat, []).append(s)
    
    for cat, skills in sorted(categories.items()):
        print(f"【{cat}】")
        for s in sorted(skills, key=lambda x: -x.get("score", 0)):
            status = "✅" if s.get("status") == "active" else "❌"
            print(f"  {status} {s['name']} (评分:{s.get('score', 0)})")
            print(f"      来源: {s.get('source', '?')} | 更新: {s.get('last_updated', s.get('created', '?'))}")
        print()
    
    print("【L4 归档记录】")
    for a in sorted(idx.get("L4_Archives", []), key=lambda x: x["date"], reverse=True)[:5]:
        print(f"  {a.get('date','?')} {a.get('code','?')} {a.get('name','?')} | {a.get('lesson_type', a.get('lesson','?'))} | 盈亏:{a.get('pnl_pct', '?')}%")
    print("=" * 60)

def evolve_new_skill(skill_data):
    """
    从新经验中生长出新技能
    skill_data: {id, name, category, tags, source, rules, cases}
    """
    idx = load_index()
    
    skill_id = skill_data["id"]
    if skill_exists(idx, skill_id):
        print(f"[技能树] 技能 {skill_id} 已存在，跳过")
        return
    
    skill_file = L3_SKILLS_DIR / f"{skill_id}.yaml"
    with open(skill_file, "w") as f:
        yaml.dump(skill_data, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
    
    idx["L3_Skills"].append({
        "id": skill_id,
        "name": skill_data["name"],
        "category": skill_data.get("category", "其他"),
        "tags": skill_data.get("tags", []),
        "status": "active",
        "source": skill_data.get("source", ""),
        "created": datetime.now().strftime("%Y-%m-%d"),
        "score": skill_data.get("initial_score", 5)
    })
    
    save_index(idx)
    print(f"[技能树] 🆕 新技能创建: {skill_id} - {skill_data['name']}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_skill_tree()
    elif sys.argv[1] == "--add" and len(sys.argv) >= 3:
        # python3 skill_tree_manager.py --add 2026-04-15 002439 启明星辰 改进 "追高执行教训" ["execution-discipline","stop-loss-discipline"] 持有
        date = sys.argv[2]
        code = sys.argv[3]
        name = sys.argv[4]
        lesson_type = sys.argv[5]
        lesson_text = sys.argv[6]
        skill_refs = json.loads(sys.argv[7])
        outcome = sys.argv[8] if len(sys.argv) > 8 else ""
        add_lesson(date, code, name, lesson_type, lesson_text, skill_refs, outcome)
    elif sys.argv[1] == "--tree":
        show_skill_tree()
    elif sys.argv[1] == "--evolve":
        # 从标准输入读取技能数据
        data = json.loads(sys.stdin.read())
        evolve_new_skill(data)
