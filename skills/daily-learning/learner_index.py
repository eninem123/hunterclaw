#!/usr/bin/env python3
"""
Learner Index Builder
Scans zmproject and builds a structured learning curriculum
"""

import json
import os
import re
from pathlib import Path
from datetime import datetime

PROJECT_PATH = "/root/zmproject"
OUTPUT_FILE = "/root/.openclaw/workspace/skills/daily-learning/outputs/learner_index.json"

# Learning modules definition
MODULES = [
    {
        "id": 1,
        "name": "AI Applications",
        "name_cn": "AI应用入门",
        "level": 1,
        "description": "掌握 AI Agent 开发能力",
        "keywords": ["ai", "agent", "知识库", "kb", "mvp", "browser"],
        "exclude_dirs": ["node_modules", "__pycache__", ".git", ".cursor", ".vscode", ".antigravity", ".trae", ".github", ".idea"],
        "file_priorities": [
            "ai_applications/kb_qa_mvp/README.md",
            "ai_applications/*agent*.md",
            "local_knowledge_model/README.md",
            "local_knowledge_model/QUICKSTART.md",
            "ai_applications/*.md",
        ]
    },
    {
        "id": 2,
        "name": "Technical Development",
        "name_cn": "技术开发",
        "level": 2,
        "description": "掌握数据管道 + 自动化开发",
        "keywords": ["dwd", "数据", "模型", "规范", "error", "追踪", "script", "gen_"],
        "exclude_dirs": ["node_modules", "__pycache__", ".git", ".cursor", ".vscode", ".antigravity", ".trae", ".idea"],
        "file_priorities": [
            "ai_learning/DWD模型开发规范*.md",
            "ai_learning/error_tracking_system.md",
            "gen_cpt.py",
            "gen_cpt2.py",
            "load_project_context.py",
            "ai_learning/*.md",
            "技术开发/**/*.md",
        ]
    },
    {
        "id": 3,
        "name": "Business Intelligence",
        "name_cn": "业务智能",
        "level": 3,
        "description": "掌握业务分析 + 报表自动化",
        "keywords": ["帆软", "fanruan", "报表", "audit", "审计", "业务", "需求"],
        "exclude_dirs": ["node_modules", "__pycache__", ".git", ".cursor", ".vscode", ".antigravity", ".trae", ".idea"],
        "file_priorities": [
            "帆软报表自动化项目/**/*.md",
            "audits/*.json",
            "业务需求/**/*.md",
            "ai_learning/business_insights/*.md",
        ]
    },
    {
        "id": 4,
        "name": "Project Practice",
        "name_cn": "项目实战",
        "level": 4,
        "description": "独立交付 AI 数据项目",
        "keywords": ["调研", "部署", "运维", "项目", "调研报告", "部署"],
        "exclude_dirs": ["node_modules", "__pycache__", ".git", ".cursor", ".vscode", ".antigravity", ".trae", ".idea"],
        "file_priorities": [
            "调研报告/**/*.md",
            "部署与运维/**/*.md",
            "项目管理/**/*.md",
            "帆软报表自动化项目/05_项目文档/*.md",
        ]
    }
]


def scan_files(project_path, module):
    """Scan project for relevant files matching module keywords"""
    files = []
    exclude = set(module.get("exclude_dirs", []))
    
    for root, dirs, filenames in os.walk(project_path):
        # Filter excluded dirs
        dirs[:] = [d for d in dirs if d not in exclude and not d.startswith(".")]
        
        for fname in filenames:
            if fname.startswith(".") or fname.endswith(".pyc"):
                continue
            
            fpath = os.path.join(root, fname)
            relpath = os.path.relpath(fpath, project_path)
            
            # Check if file matches module keywords
            for kw in module["keywords"]:
                if kw.lower() in relpath.lower() or kw.lower() in fname.lower():
                    # Extract title and excerpt
                    title = extract_title(fpath) or fname
                    excerpt = extract_excerpt(fpath) or ""
                    
                    files.append({
                        "path": relpath,
                        "name": fname,
                        "title": title[:100],
                        "excerpt": excerpt[:200],
                        "type": get_file_type(fname),
                        "size": os.path.getsize(fpath),
                        "module_id": module["id"],
                    })
                    break
    
    return files


def extract_title(fpath):
    """Extract title from markdown file"""
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line = line.strip()
                if line.startswith("# "):
                    return line[2:].strip()
                if line.startswith("## "):
                    return line[3:].strip()
    except:
        pass
    return None


def extract_excerpt(fpath, max_lines=10):
    """Extract first non-empty lines as excerpt"""
    try:
        with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("---"):
                    lines.append(line)
                    if len(lines) >= max_lines:
                        break
            return " ".join(lines)
    except:
        return ""


def get_file_type(fname):
    """Get file type category"""
    ext = os.path.splitext(fname)[1].lower()
    types = {
        ".md": "文档",
        ".py": "代码",
        ".json": "数据",
        ".txt": "文本",
        ".sh": "脚本",
        ".yaml": "配置",
        ".yml": "配置",
        ".sql": "SQL",
        ".js": "代码",
    }
    return types.get(ext, "其他")


def build_index():
    """Build complete learning index"""
    print(f"🔍 Scanning {PROJECT_PATH}...")
    
    index = {
        "version": "1.0",
        "generated": datetime.now().isoformat(),
        "project": PROJECT_PATH,
        "modules": [],
        "total_files": 0,
        "progress": {
            "current_day": 1,
            "current_module": 1,
            "completed_files": [],
            "quiz_scores": []
        }
    }
    
    for module in MODULES:
        print(f"  📦 Module {module['id']}: {module['name_cn']}...")
        files = scan_files(PROJECT_PATH, module)
        
        # Sort by file type priority (docs first, then code)
        type_order = {"文档": 0, "代码": 1, "配置": 2, "数据": 3, "文本": 4, "脚本": 5, "SQL": 6, "其他": 7}
        files.sort(key=lambda f: (type_order.get(f["type"], 9), f["size"]))
        
        module_entry = {
            "id": module["id"],
            "name": module["name"],
            "name_cn": module["name_cn"],
            "level": module["level"],
            "description": module["description"],
            "files": files,
            "total_files": len(files)
        }
        index["modules"].append(module_entry)
        index["total_files"] += len(files)
        
        print(f"    Found {len(files)} files")
    
    # Save index
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(index, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Index saved to {OUTPUT_FILE}")
    print(f"   Total: {index['total_files']} files across {len(MODULES)} modules")
    
    return index


if __name__ == "__main__":
    build_index()
