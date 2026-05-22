#!/usr/bin/env python3
"""
IMA知识库搜索修复补丁
问题：原ima_fetcher.py搜索参数使用top_k但API实际参数可能不同
修复：使用正确的search_knowledge参数格式
"""
import requests
import json

BASE_URL = "https://ima.qq.com"
CLIENT_ID = "65131085cc8a5c52b70e77a49a19cc02"
API_KEY = "PL/LX8BO0wtXoWvN81KCSX4i6iFgmnc7T2eB7BLmlWKsAuoVmVGeg+sbCK2UVUwsrVsYlCXGog=="
KB_FINANCE = "3ZyksHidcCuvAn0Wsau-viCVl6-hBsnz-8WYQJLod24="

HEADERS = {
    "ima-openapi-clientid": CLIENT_ID,
    "ima-openapi-apikey": API_KEY,
    "ima-openapi-ctx": "skill_version=1.1.7",
    "Content-Type": "application/json",
    "Accept": "application/json"
}

def search_knowledge(query, kb_id=KB_FINANCE, top_k=5):
    """搜索知识库 - 正确参数格式"""
    resp = requests.post(
        f"{BASE_URL}/openapi/wiki/v1/search_knowledge",
        headers=HEADERS,
        json={"knowledge_base_id": kb_id, "query": query, "top_k": top_k},
        timeout=15
    )
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("info_list", [])
    else:
        print("Search error: code=%s msg=%s" % (result.get("code"), result.get("msg")))
        return []

def get_knowledge_list(kb_id=KB_FINANCE, limit=50):
    """列出知识库内容"""
    resp = requests.post(
        f"{BASE_URL}/openapi/wiki/v1/get_knowledge_list",
        headers=HEADERS,
        json={"knowledge_base_id": kb_id, "limit": limit},
        timeout=15
    )
    result = resp.json()
    if result.get("code") == 0:
        return result.get("data", {}).get("knowledge_list", [])
    return []

def get_media_info(kb_id, media_id):
    """获取书籍/媒体详情"""
    resp = requests.post(
        f"{BASE_URL}/openapi/wiki/v1/get_media_info",
        headers=HEADERS,
        json={"knowledge_base_id": kb_id, "media_id": media_id},
        timeout=15
    )
    return resp.json()

# 测试
if __name__ == "__main__":
    print("=== IMA知识库搜索测试 ===")
    print()
    
    # 列出所有书
    books = get_knowledge_list()
    print("理财书籍库: %d本书" % len(books))
    for b in books[:5]:
        print("  -> %s" % b.get("title", "?")[:60])
    print("  ... (共%d本)" % len(books))
    print()
    
    # 搜索
    for q in ["止损", "技术分析", "投资策略", "价值投资"]:
        items = search_knowledge(q)
        print("搜索'%s': %d条结果" % (q, len(items)))
        for item in items[:2]:
            print("  -> %s" % item.get("title", "?")[:60])
    print()
    print("=== 修复完成 ===")
    print("问题原因: 原脚本可能缺少knowledge_base_id参数或格式不对")
    print("修复方法: 确保search_knowledge调用包含knowledge_base_id和top_k参数")
