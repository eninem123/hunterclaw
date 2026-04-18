#!/usr/bin/env python3
"""
GBrain 大规模导入脚本
- 提取所有会话历史
- 导入所有项目文档
- 导入猎手系统
- 自动分类
"""
import json
import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

GBRAIN_CLI = "/root/.openclaw/workspace/node_modules/.bin/gbrain"
BRAIN_DIR = Path("/root/.gbrain/brain")
IMPORT_DIR = Path("/tmp/gbrain_import")
SESSIONS_DIR = Path("/root/.openclaw/agents/main/sessions")

def run(cmd, cwd=None):
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=cwd)
    return result.returncode, result.stdout, result.stderr

def clean_text(text):
    """清洗元数据，提取有意义的内容"""
    if not text:
        return ""
    # 移除 Conversation info metadata
    text = re.sub(r'Conversation info[^\n]*```json.*?```', '', text, flags=re.DOTALL)
    # 移除 HEARTBEAT
    text = re.sub(r'HEARTBEAT.*', '', text)
    text = re.sub(r'\[Queued messages[^\n]*\]', '', text)
    # 清理多余空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text.strip()

def slugify(text):
    """转slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:80]

GBRAIN_KEY = "87f5475dbadc41b6b08e293c1f6f300e.C3BZ1dzhJmGPExP7"

def generate_embedding_glm(texts, batch_size=20):
    """直接用GLM生成embeddings，不依赖proxy"""
    import urllib.request, json
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        payload = {"model": "embedding-2", "input": batch}
        req = urllib.request.Request(
            "https://open.bigmodel.cn/api/paas/v4/embeddings",
            data=json.dumps(payload).encode(),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {GBRAIN_KEY}"
            },
            method="POST"
        )
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read())
                for item in data.get("data", []):
                    all_embeddings.append(item["embedding"])
        except Exception as e:
            print(f"  GLM embedding error: {e}")
    return all_embeddings
    """导入所有会话历史"""
    conv_dir = IMPORT_DIR / "conversations"
    conv_dir.mkdir(parents=True, exist_ok=True)

    sessions = sorted(SESSIONS_DIR.glob("*.jsonl"))
    print(f"找到 {len(sessions)} 个会话文件")

    all_conversations = []

    for session_file in sessions:
        messages = []
        session_id = session_file.stem[:12]
        date_prefix = "unknown"

        try:
            with open(session_file) as f:
                for line in f:
                    try:
                        d = json.loads(line.strip())
                        if d.get("type") != "message":
                            continue
                        msg = d.get("message", {})
                        role = msg.get("role", "")
                        if role not in ("user", "assistant"):
                            continue

                        content_parts = msg.get("content", [])
                        text = ""
                        if isinstance(content_parts, list):
                            for p in content_parts:
                                if isinstance(p, dict) and p.get("type") == "text":
                                    text = p.get("text", "")
                                    break
                        elif isinstance(content_parts, str):
                            text = content_parts

                        if not text:
                            continue

                        ts = d.get("timestamp", "")
                        if ts:
                            dt = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                            date_str = dt.strftime("%Y-%m-%d %H:%M")
                            if date_prefix == "unknown":
                                date_prefix = dt.strftime("%Y-%m-%d")
                        else:
                            date_str = "unknown"

                        messages.append({"role": role, "text": clean_text(text), "date": date_str})
                    except Exception:
                        pass
        except Exception as e:
            print(f"  读取会话失败 {session_file.name}: {e}")
            continue

        if not messages:
            continue

        # 按日期组织
        date_groups = {}
        for m in messages:
            d = m["date"].split(" ")[0] if " " in m["date"] else m["date"]
            if d not in date_groups:
                date_groups[d] = []
            date_groups[d].append(m)

        # 每个会话生成一个文件（按日期）
        content_lines = [
            f"# 会话记录",
            f"",
            f"**Session ID**: {session_id}",
            f"**开始日期**: {date_prefix}",
            f"**消息数**: {len(messages)}",
            f"",
            f"---",
            f""
        ]

        for date_key in sorted(date_groups.keys()):
            msgs_on_date = date_groups[date_key]
            content_lines.append(f"## 📅 {date_key}")
            content_lines.append("")
            for m in msgs_on_date:
                role_label = "👤 用户" if m["role"] == "user" else "🤖 助手"
                content_lines.append(f"**{role_label}** [{m['date']}]")
                # 内容截断（GBrain chunk限制）
                content_lines.append(m["text"][:600])
                content_lines.append("")

        # 生成文件名
        safe_name = f"session-{session_id}"
        filepath = conv_dir / f"{safe_name}.md"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(content_lines))

        all_conversations.append(safe_name)

    print(f"  生成 {len(all_conversations)} 个会话文件")

    # 导入到 GBrain
    code, out, err = run([GBRAIN_CLI, "import", str(conv_dir), "--no-embed"])
    if code == 0:
        print(f"  ✅ 会话导入成功")
    else:
        print(f"  ❌ 会话导入失败: {err[:200]}")

def import_memory_files():
    """导入记忆文件"""
    mem_dir = IMPORT_DIR / "memory"
    mem_dir.mkdir(parents=True, exist_ok=True)

    files = [
        ("/root/.openclaw/workspace/MEMORY.md", "memory/memory-long-term.md"),
        ("/root/.openclaw/workspace/memory/2026-04-11.md", "memory/memory-2026-04-11.md"),
        ("/root/.openclaw/workspace/GBRAIN.md", "memory/gbrain-rules.md"),
    ]

    count = 0
    for src, dst in files:
        src_path = Path(src)
        if src_path.exists():
            dst_path = mem_dir / dst.replace("/", "-")
            content = src_path.read_text(encoding="utf-8")
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(f"# {dst}\n\n")
                f.write(content)
            count += 1

    if count > 0:
        run([GBRAIN_CLI, "import", str(mem_dir), "--no-embed"])
        print(f"  ✅ 记忆文件导入成功 ({count} 个)")

def import_hunter_system():
    """导入猎手系统"""
    hunter_dir = IMPORT_DIR / "hunter-system"
    hunter_dir.mkdir(parents=True, exist_ok=True)

    files = [
        ("/root/.openclaw/workspace/hunter/CRON.md", "hunter/cron-config.md"),
        ("/root/.openclaw/workspace/hunter/data/portfolio.json", "hunter/portfolio.json"),
        ("/root/.openclaw/workspace/hunter/data/reviews/2026-04-10.json", "hunter/review-2026-04-10.json"),
    ]

    for src, dst in files:
        src_path = Path(src)
        if src_path.exists():
            dst_path = hunter_dir / dst.replace("/", "-")
            content = src_path.read_text(encoding="utf-8")
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(f"# {src_path.name}\n\n")
                f.write(f"```\n{content}\n```")
            print(f"  写入 {dst_path}")

    code, out, err = run([GBRAIN_CLI, "import", str(hunter_dir), "--no-embed"])
    if code == 0:
        print(f"  ✅ 猎手系统导入成功")
    else:
        print(f"  ❌ 猎手系统导入失败: {err[:200]}")

def import_alpha_terminal():
    """导入 Alpha_Terminal 项目"""
    at_dir = IMPORT_DIR / "alpha-terminal"
    at_dir.mkdir(parents=True, exist_ok=True)

    files = [
        "/root/Alpha_Terminal/agent.md",
        "/root/Alpha_Terminal/README.md",
        "/root/Alpha_Terminal/package.json",
    ]

    count = 0
    for src in files:
        src_path = Path(src)
        if src_path.exists():
            content = src_path.read_text(encoding="utf-8")
            name = src_path.name.replace(".", "-")
            dst_path = at_dir / f"{name}.md"
            with open(dst_path, "w", encoding="utf-8") as f:
                f.write(f"# {src_path.name}\n\n")
                f.write(content[:3000])
            count += 1

    if count > 0:
        code, out, err = run([GBRAIN_CLI, "import", str(at_dir), "--no-embed"])
        print(f"  ✅ Alpha_Terminal 导入成功 ({count} 个)")

def tag_and_link():
    """打标签 + 关联"""
    # 给会话打标签
    code, out, err = run([GBRAIN_CLI, "list", "--type", "conversations", "-n", "20"])
    print(f"\n📋 当前 GBrain 页面统计:")
    run([GBRAIN_CLI, "stats"])

def main():
    print("=" * 50)
    print("GBrain 大规模导入")
    print("=" * 50)

    print("\n📥 导入会话历史...")
    import_conversations()

    print("\n📥 导入记忆文件...")
    import_memory_files()

    print("\n📥 导入猎手系统...")
    import_hunter_system()

    print("\n📥 导入 Alpha_Terminal...")
    import_alpha_terminal()

    print("\n📊 最终状态:")
    code, out, err = run([GBRAIN_CLI, "stats"])
    if code == 0:
        print(out)
    else:
        print(err)

    print("\n✅ 导入完成!")
    print("提示: 运行 `gbrain search <关键词>` 测试召回")

if __name__ == "__main__":
    main()
