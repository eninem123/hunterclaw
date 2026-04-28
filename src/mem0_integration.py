#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Mem0分层记忆集成层
提供 save_trading_memory / search_trading_history / search_lessons 等接口
供猎手系统各模块调用，自动注入 /root/mem0_venv 路径
"""

import sys

VENV_PATH = "/root/mem0_venv/lib/python3.11/site-packages"
if VENV_PATH not in sys.path:
    sys.path.insert(0, VENV_PATH)

_connector = None

def _build_connector():
    try:
        from mem0 import Memory
        import json

        with open('/root/.openclaw/openclaw.json', 'r') as f:
            cfg = json.load(f)
        breeze = cfg['models']['providers']['breeze']

        _memory = Memory.from_config({
            "llm": {
                "provider": "openai",
                "config": {
                    "api_key": breeze['apiKey'],
                    "openai_base_url": breeze.get('baseUrl', 'https://api.svips.org/v1'),
                    "model": "MiniMax-M2.7"
                }
            },
            "vector_store": {
                "provider": "faiss",
                "config": {
                    "path": "/root/mem0_db_hf",
                    "embedding_model_dims": 384
                }
            },
            "embedder": {
                "provider": "huggingface",
                "config": {
                    "model": "sentence-transformers/all-MiniLM-L6-v2"
                }
            }
        })

        class _Conn:
            def save_to_level(self, content, level, metadata=None):
                uid = f"layer_{level}"
                try:
                    r = _memory.add(content, user_id=uid, metadata=metadata or {})
                    return r.get('results', [{}])[0].get('id', '') if r else ''
                except Exception:
                    return ''

            def search_from_level(self, query, level, limit=5):
                uid = f"layer_{level}"
                try:
                    res = _memory.search(query, filters={"user_id": uid}, limit=limit)
                    return res.get('results', []) if isinstance(res, dict) else []
                except Exception:
                    return []

            def health_check(self):
                return {"status": "healthy", "connected": True}

        return _Conn()
    except Exception:
        class _Null:
            def save_to_level(self, *a, **kw): return ''
            def search_from_level(self, *a, **kw): return []
            def health_check(self): return {"status": "unhealthy", "connected": False}
        return _Null()

def _get_connector():
    global _connector
    if _connector is None:
        _connector = _build_connector()
    return _connector

def save_trading_memory(symbol, action, price, result=None, note=''):
    """保存交易记忆到情景记忆层"""
    c = _get_connector()
    content = f"{action.upper()} {symbol} @ ¥{price}"
    if note:
        content += f" | {note}"
    if result:
        content += f" | 结果: {result}"
    return c.save_to_level(content, 'episodic', {'symbol': symbol, 'action': action, 'price': price})

def search_trading_history(symbol, limit=5):
    """查询股票的历史交易记忆"""
    c = _get_connector()
    return c.search_from_level(symbol, 'episodic', limit=limit)

def search_lessons(query, limit=5):
    """搜索相关教训（语义记忆层）"""
    c = _get_connector()
    return c.search_from_level(query, 'semantic', limit=limit)

def save_lesson(content, metadata=None):
    """保存教训到语义记忆层"""
    c = _get_connector()
    return c.save_to_level(content, 'semantic', metadata or {})

def save_strategy(content, metadata=None):
    """保存策略到程序记忆层"""
    c = _get_connector()
    return c.save_to_level(content, 'procedural', metadata or {})

def mem0_health():
    """健康检查"""
    return _get_connector().health_check()
