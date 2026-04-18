#!/usr/bin/env python3
"""
Daily Learning Push
Delivers structured daily learning content from zmproject
"""

import json
import os
import sys
from datetime import datetime, date
from pathlib import Path

SKILL_DIR = "/root/.openclaw/workspace/skills/daily-learning"
INDEX_FILE = f"{SKILL_DIR}/outputs/learner_index.json"
PROGRESS_FILE = f"{SKILL_DIR}/outputs/progress.json"
OUTPUT_DIR = f"{SKILL_DIR}/outputs/daily"
PENDING_DIR = "/root/.openclaw/workspace/pending-summaries"

# Learning schedule: (module_id, days_in_module)
SCHEDULE = [
    # Module 1: AI Applications (7 days)
    (1, 1), (1, 2), (1, 3), (1, 4), (1, 5), (1, 6), (1, 7),
    # Module 2: Technical Development (7 days)
    (2, 1), (2, 2), (2, 3), (2, 4), (2, 5), (2, 6), (2, 7),
    # Module 3: Business Intelligence (7 days)
    (3, 1), (3, 2), (3, 3), (3, 4), (3, 5), (3, 6), (3, 7),
    # Module 4: Project Practice (7 days)
    (4, 1), (4, 2), (4, 3), (4, 4), (4, 5), (4, 6), (4, 7),
]


def load_progress():
    """Load learning progress"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"current_day": 1, "completed_files": [], "quiz_scores": []}


def save_progress(progress):
    """Save learning progress"""
    os.makedirs(os.path.dirname(PROGRESS_FILE), exist_ok=True)
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def load_index():
    """Load learner index"""
    if not os.path.exists(INDEX_FILE):
        print("❌ Index not found. Run learner_index.py first.")
        sys.exit(1)
    with open(INDEX_FILE, "r") as f:
        return json.load(f)


def get_today_content(module_id, day_in_module, index):
    """Get content for today"""
    # Find module
    module = None
    for m in index["modules"]:
        if m["id"] == module_id:
            module = m
            break
    
    if not module:
        return None, f"Module {module_id} not found"
    
    files = module["files"]
    if not files:
        return None, f"No files in module {module_id}"
    
    # Calculate which files to show today
    # Distribute files evenly across days
    files_per_day = max(1, len(files) // 7)
    start_idx = (day_in_module - 1) * files_per_day
    end_idx = start_idx + files_per_day if day_in_module < 7 else len(files)
    
    today_files = files[start_idx:end_idx]
    
    return {
        "module": module,
        "day_in_module": day_in_module,
        "files": today_files,
        "total_files_in_module": len(files),
        "start_idx": start_idx + 1,
        "end_idx": end_idx,
    }, None


def format_file_content(filepath, max_chars=1500):
    """Read and format file content"""
    full_path = f"/root/zmproject/{filepath}"
    if not os.path.exists(full_path):
        return f"⚠️ File not found: {filepath}"
    
    try:
        with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        
        # For markdown files, show first part
        if filepath.endswith(".md"):
            lines = content.split("\n")
            shown = []
            in_code = False
            code_count = 0
            
            for line in lines:
                if len("\n".join(shown)) > max_chars:
                    shown.append("\n... (内容过长，已截断)")
                    break
                shown.append(line)
            
            return "\n".join(shown)
        
        # For code files, show with syntax hints
        elif filepath.endswith(".py"):
            lines = content.split("\n")
            shown = []
            for line in lines[:80]:  # First 80 lines
                if len("\n".join(shown)) > max_chars:
                    shown.append("# ... (代码过长，已截断)")
                    break
                shown.append(line)
            return "\n".join(shown)
        
        # For JSON, pretty print
        elif filepath.endswith(".json"):
            try:
                data = json.loads(content)
                return json.dumps(data, ensure_ascii=False, indent=2)[:max_chars]
            except:
                return content[:max_chars]
        
        else:
            return content[:max_chars]
    
    except Exception as e:
        return f"❌ Error reading file: {e}"


def generate_daily_report(content_info, progress):
    """Generate formatted daily learning report"""
    module = content_info["module"]
    day = content_info["day_in_module"]
    files = content_info["files"]
    total = content_info["total_files_in_module"]
    
    today = date.today()
    day_num = (today - date(2026, 4, 14)).days + 1  # Days since project start
    
    report_lines = []
    report_lines.append(f"# 📚 Daily Learning | Day {day_num}")
    report_lines.append(f"**Module {module['id']}: {module['name']} ({module['name_cn']})**")
    report_lines.append(f"Day {day}/7 in module | Files {content_info['start_idx']}-{content_info['end_idx']} of {total}")
    report_lines.append("")
    report_lines.append("---")
    report_lines.append("")
    
    for i, f in enumerate(files, content_info["start_idx"]):
        report_lines.append(f"## 📄 {i}. {f.get('title', f['name'])}")
        report_lines.append(f"**File**: `{f['path']}` | **Type**: {f['type']}")
        if f.get("excerpt"):
            report_lines.append(f"**Preview**: {f['excerpt'][:150]}...")
        report_lines.append("")
        
        # Read actual content
        file_content = format_file_content(f["path"])
        report_lines.append("```")
        
        # Trim content for display
        if len(file_content) > 2000:
            # For markdown, keep most of it
            if f["path"].endswith(".md"):
                report_lines.append(file_content[:2000])
            else:
                report_lines.append(file_content[:1500])
        else:
            report_lines.append(file_content)
        
        report_lines.append("```")
        report_lines.append("")
        
        # Mark as completed
        if f["path"] not in progress["completed_files"]:
            progress["completed_files"].append(f["path"])
    
    # Learning tips
    report_lines.append("---")
    report_lines.append("")
    report_lines.append("## 💡 Learning Tips")
    if module["id"] == 1:
        report_lines.append("- 今天聚焦：理解 AI Agent 的核心逻辑（感知→推理→执行）")
        report_lines.append("- 动手实验：运行 `kb_qa_mvp` 中的示例代码")
        report_lines.append("- 思考：如何将知识库问答应用于你的业务场景？")
    elif module["id"] == 2:
        report_lines.append("- 今天聚焦：掌握 DWD 层数据建模规范")
        report_lines.append("- 重点理解：数据清洗 → 维度关联 → 事实表设计")
        report_lines.append("- 动手实验：参考 `gen_cpt*.py` 写一个数据生成脚本")
    elif module["id"] == 3:
        report_lines.append("- 今天聚焦：帆软报表自动化流程")
        report_lines.append("- 重点理解：数据源配置 → 报表模板 → 自动化调度")
        report_lines.append("- 思考：哪些重复性报表可以自动化？")
    elif module["id"] == 4:
        report_lines.append("- 今天聚焦：项目交付流程")
        report_lines.append("- 重点理解：调研 → 设计 → 开发 → 部署 → 运维")
        report_lines.append("- 思考：如何将 AI 能力融入现有业务流程？")
    
    report_lines.append("")
    report_lines.append("---")
    report_lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')} | HunterClaw Daily Learning*")
    
    return "\n".join(report_lines)


def get_next_day_content():
    """Determine what content comes next"""
    progress = load_progress()
    index = load_index()
    
    current_day = progress.get("current_day", 1)
    
    # Get schedule index
    schedule_idx = (current_day - 1) % len(SCHEDULE)
    module_id, day_in_module = SCHEDULE[schedule_idx]
    
    content_info, err = get_today_content(module_id, day_in_module, index)
    if err:
        return None, err
    
    return content_info, progress


def run_daily_push():
    """Main daily push execution"""
    print(f"📚 Daily Learning Push - {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    # Get today's content
    content_info, progress = get_next_day_content()
    if not content_info:
        print(f"❌ Error: {progress}")
        return
    
    # Generate report
    report = generate_daily_report(content_info, progress)
    
    # Save to output
    today = date.today().strftime("%Y-%m-%d")
    module_id = content_info["module"]["id"]
    output_file = f"{OUTPUT_DIR}/module{module_id}/day{content_info['day_in_module']}.md"
    
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Report saved: {output_file}")
    
    # Copy to pending for WeChat push
    pending_file = f"{PENDING_DIR}/daily-learning-{today}.md"
    with open(pending_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"✅ Pending push: {pending_file}")
    
    # Update progress
    current_day = progress.get("current_day", 1)
    progress["current_day"] = current_day + 1
    save_progress(progress)
    
    print(f"📊 Progress: Day {current_day} completed, next is Day {progress['current_day']}")
    print(f"   Total files studied: {len(progress['completed_files'])}")
    
    return report


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--build-index":
        # Build index first
        os.system(f"cd {SKILL_DIR} && python3 learner_index.py")
    elif len(sys.argv) > 1 and sys.argv[1] == "--module":
        # Push specific module/day
        module_id = int(sys.argv[2])
        day = int(sys.argv[3])
        index = load_index()
        content_info, err = get_today_content(module_id, day, index)
        if err:
            print(f"❌ Error: {err}")
            sys.exit(1)
        progress = load_progress()
        report = generate_daily_report(content_info, progress)
        print(report)
    else:
        # Normal daily push
        run_daily_push()
