#!/usr/bin/env python3
"""
IMA Knowledge Bridge - 猎手荐股策略的知识增强模块
连接 Alpha_Terminal 的 IMA 金融知识库，为选股提供上下文推理

数据源：
  - 理财书籍(28篇)        → 投资理念/方法论
  - 有知有行投资第一课(412) → 系统投资框架
  - AI读研报(35,437篇)     → 每日个股研报
  - 财报及业绩会议纪要(285) → 财报基本面
"""

import json
import os
import urllib.request
import urllib.parse
from datetime import datetime
from pathlib import Path
from typing import Optional

# ── IMA 凭证（复用 Alpha_Terminal 配置） ──
CONFIG_DIR = Path(os.path.expanduser("~/.config/ima"))
CLIENT_ID_FILE = CONFIG_DIR / "client_id"
API_KEY_FILE = CONFIG_DIR / "api_key"
ENV_FILE = CONFIG_DIR / ".env"

IMA_API_BASE = "https://ima.qq.com/openapi/wiki/v1"

# ── 金融相关知识库 ID 列表 ──
FINANCIAL_KB = {
    "理财书籍": "3ZyksHidcCuvAn0Wsau-viCVl6-hBsnz-8WYQJLod24=",
    "有知有行投资课": "Zyk5qnxsJF4mONTozfDenORCbWWaMm0UXVqVFnkbWNs=",
    "AI读研报": "vk2hRrUPdBwaLJNrHCcUl46gVGUN9xBW51WzfBbaSf0=",
    "财报及业绩纪要": "3iqyHw2rN25ynrkDX_L_yWw6eGiCdxc2oxO33GEz6S8=",
}


def _load_credentials() -> tuple[str, str]:
    """从 ~/.config/ima 加载 IMA 凭证"""
    client_id = None
    api_key = None

    # 1. 尝试 .env 文件
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().strip().split("\n"):
            if "=" in line:
                k, v = line.strip().split("=", 1)
                if k == "IMA_OPENAPI_CLIENTID":
                    client_id = v
                elif k == "IMA_OPENAPI_APIKEY":
                    api_key = v

    # 2. 回退到独立文件
    if not client_id and CLIENT_ID_FILE.exists():
        client_id = CLIENT_ID_FILE.read_text().strip()
    if not api_key and API_KEY_FILE.exists():
        api_key = API_KEY_FILE.read_text().strip()

    if not client_id or not api_key:
        raise RuntimeError(
            "IMA 凭证未配置。请检查 ~/.config/ima/ 下的 client_id 和 api_key 文件，"
            "或 IMA_OPENAPI_CLIENTID / IMA_OPENAPI_APIKEY 环境变量。"
        )

    return client_id, api_key


def _call_ima_api(endpoint: str, payload: dict, timeout: int = 15) -> dict:
    """调用 IMA OpenAPI 的通用方法"""
    client_id, api_key = _load_credentials()
    url = f"{IMA_API_BASE}/{endpoint}"
    data = json.dumps(payload).encode("utf-8")

    req = urllib.request.Request(url, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("ima-openapi-clientid", client_id)
    req.add_header("ima-openapi-apikey", api_key)

    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read())
            if body.get("code") != 0:
                print(f"[IMA] API 错误 [{endpoint}]: {body.get('msg', '未知错误')}")
                return {"ok": False, "error": body.get("msg", "")}
            return {"ok": True, "data": body.get("data", {})}
    except Exception as e:
        print(f"[IMA] 请求失败 [{endpoint}]: {e}")
        return {"ok": False, "error": str(e)}


# ══════════════════════════════════════════════
#  公开接口
# ══════════════════════════════════════════════

def search_knowledge(
    query: str,
    kb_ids: Optional[list[str]] = None,
    limit: int = 5,
) -> list[dict]:
    """
    在指定知识库中搜索相关内容

    参数:
        query: 搜索关键词（如 "半导体 2026", "浪潮信息 研报"）
        kb_ids: 知识库 ID 列表，默认搜索所有金融相关知识库
        limit: 每个知识库返回的最大结果数

    返回:
        [{kb_name, title, highlight, source}, ...]
    """
    if kb_ids is None:
        kb_ids = list(FINANCIAL_KB.values())

    name_map = {v: k for k, v in FINANCIAL_KB.items()}
    results = []

    for kb_id in kb_ids:
        resp = _call_ima_api("search_knowledge", {
            "query": query,
            "cursor": "",
            "knowledge_base_id": kb_id,
        })
        if not resp["ok"]:
            continue

        items = resp["data"].get("info_list", [])
        kb_name = name_map.get(kb_id, kb_id[:12])

        for item in items[:limit]:
            results.append({
                "kb_name": kb_name,
                "title": item.get("title", ""),
                "highlight": item.get("highlight_content", ""),
                "media_id": item.get("media_id", ""),
            })

    return results


def enrich_stock_context(
    stock_name: str,
    stock_code: str = "",
    industry: str = "",
) -> str:
    """
    为某只股票搜集 IMA 知识库中的上下文信息

    返回格式化的多知识库搜索结果，可直接注入大模型 prompt
    """
    # 多维度搜索
    queries = [stock_name]
    if stock_code:
        queries.append(stock_code)
    if industry:
        queries.append(f"{industry} 板块 投资逻辑")
    queries.append(f"{stock_name} 研报 2026")

    seen = set()
    context_parts = []

    for q in queries:
        results = search_knowledge(q, limit=3)
        for r in results:
            key = r["title"]
            if key in seen:
                continue
            seen.add(key)
            hl = r["highlight"][:200] if r["highlight"] else ""
            context_parts.append(
                f"[{r['kb_name']}] {r['title']}"
                + (f"\n  → {hl}" if hl else "")
            )

    if not context_parts:
        return ""

    return "📖 IMA知识库参考:\n" + "\n".join(context_parts)


def get_market_context(topic: str = "当前A股市场主线") -> str:
    """获取当前市场主线/热点的知识库参考"""
    results = search_knowledge(topic, kb_ids=[
        FINANCIAL_KB["AI读研报"],
        FINANCIAL_KB["财报及业绩纪要"],
    ], limit=5)
    if not results:
        return ""
    lines = ["📊 IMA市场情报:"]
    for r in results:
        hl = r["highlight"][:200] if r["highlight"] else ""
        lines.append(f"  [{r['kb_name']}] {r['title']}")
        if hl:
            lines.append(f"    {hl}")
    return "\n".join(lines)


def self_test() -> str:
    """自检：验证 IMA 凭证和 API 连通性"""
    try:
        cid, akey = _load_credentials()
    except RuntimeError as e:
        return f"❌ 凭证加载失败: {e}"

    # 搜索测试
    resp = _call_ima_api("search_knowledge_base", {"query": "", "cursor": "", "limit": 5})
    if not resp["ok"]:
        return f"❌ API 连接失败: {resp.get('error')}"

    kbs = resp["data"].get("info_list", [])
    names = [kb.get("kb_name", "?") for kb in kbs[:5]]
    return (
        f"✅ IMA 桥接正常\n"
        f"  凭证: {cid[:8]}... ✓\n"
        f"  知识库({len(kbs)}个): {', '.join(names[:5])}"
    )


# ══════════════════════════════════════════════
#  CLI 入口
# ══════════════════════════════════════════════
if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 2 and sys.argv[1] == "test":
        print(self_test())
    elif len(sys.argv) >= 2 and sys.argv[1] == "search":
        q = " ".join(sys.argv[2:]) or "当前市场主线"
        print(f"\n🔍 搜索: {q}\n")
        results = search_knowledge(q)
        for r in results:
            print(f"[{r['kb_name']}] {r['title']}")
            if r.get("highlight"):
                print(f"  {r['highlight'][:150]}")
            print()
    elif len(sys.argv) >= 2:
        print(enrich_stock_context(*sys.argv[1:3], sys.argv[3] if len(sys.argv) > 3 else ""))
    else:
        # 默认演示：测试连接 + 搜索示例
        print(self_test())
        print()
        demo = enrich_stock_context("浪潮信息", "000977", "计算机")
        print(demo if demo else "（无演示数据）")
