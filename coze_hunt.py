import os
import time
from pathlib import Path

import requests

try:
    from dotenv import load_dotenv

    _here = Path(__file__).resolve().parent
    for _env in (_here / ".env", _here.parent / ".env"):
        if _env.exists():
            load_dotenv(_env)
            break
except ImportError:
    pass

API_KEY = (os.getenv("COZE_API_KEY") or os.getenv("COZE_PAT") or "").strip()
BOT_ID = (os.getenv("COZE_BOT_ID") or "").strip()
BASE_URL = (os.getenv("COZE_BASE_URL") or "https://api.coze.cn").strip()


def chat_with_skill(query, user_id="user_001"):
    """非流式调用 Coze Skill"""

    if not API_KEY or not BOT_ID:
        raise RuntimeError(
            "请设置环境变量 COZE_API_KEY（或 COZE_PAT）与 COZE_BOT_ID；"
            "可在本目录或上级 tools/.env 中配置（勿提交含真实密钥的 .env）。"
        )

    url = f"{BASE_URL}/v3/chat"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
    }
    payload = {
        "bot_id": BOT_ID,
        "user_id": user_id,
        "stream": False,
        "auto_save_history": True,
        "additional_messages": [
            {
                "role": "user",
                "content": query,
                "content_type": "text",
            }
        ],
    }

    resp = requests.post(url, headers=headers, json=payload)
    resp.raise_for_status()
    data = resp.json()

    if data.get("code") != 0:
        print(f"发起对话失败: {data}")
        return None

    chat_id = data["data"]["id"]
    conv_id = data["data"]["conversation_id"]
    print(f"对话已创建: chat_id={chat_id}")

    while True:
        time.sleep(2)
        check_url = f"{BASE_URL}/v3/chat/retrieve?chat_id={chat_id}&conversation_id={conv_id}"
        check = requests.get(check_url, headers=headers).json()
        status = check["data"]["status"]
        print(f"状态: {status}")
        if status == "completed":
            break
        if status in ("failed", "canceled"):
            print(f"对话失败: {check}")
            return None

    msg_url = f"{BASE_URL}/v3/chat/message/list?chat_id={chat_id}&conversation_id={conv_id}"
    msgs = requests.get(msg_url, headers=headers).json()

    for msg in msgs["data"]:
        if msg["role"] == "assistant" and msg["type"] == "answer":
            print(msg["content"])

    return conv_id


if __name__ == "__main__":
    chat_with_skill("帮我分析一下当前A股市场")
