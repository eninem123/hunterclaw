"""
缓存管理模块
支持内存缓存和可选Redis缓存
"""

import time
import hashlib
import threading
from typing import Any, Optional, Dict
from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass
class CacheItem:
    """缓存项"""
    value: Any
    expire_at: float
    
    def is_expired(self) -> bool:
        return time.time() > self.expire_at


class MemoryCache:
    """内存缓存实现"""
    
    def __init__(self):
        self._cache: Dict[str, CacheItem] = {}
        self._lock = threading.RLock()
        self._hits = 0
        self._misses = 0
        self._expired_count = 0
        # 启动自动清理线程
        self._start_cleanup_thread()
    
    def _start_cleanup_thread(self):
        """启动自动清理过期缓存的守护线程"""
        def cleanup_loop():
            while True:
                time.sleep(60)  # 每分钟清理一次
                self.clear_expired()
        thread = threading.Thread(target=cleanup_loop, daemon=True)
        thread.start()
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值"""
        with self._lock:
            item = self._cache.get(key)
            if item is None:
                self._misses += 1
                return None
            
            if item.is_expired():
                del self._cache[key]
                self._misses += 1
                self._expired_count += 1
                return None
            
            self._hits += 1
            return item.value
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值
        
        Args:
            key: 缓存键
            value: 缓存值
            ttl: 过期时间(秒)
        """
        with self._lock:
            expire_at = time.time() + ttl
            self._cache[key] = CacheItem(value=value, expire_at=expire_at)
    
    def delete(self, key: str) -> bool:
        """删除缓存"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            self._cache.clear()
    
    def clear_expired(self) -> int:
        """清空过期缓存，返回清理数量"""
        count = 0
        with self._lock:
            now = time.time()
            expired_keys = [k for k, v in self._cache.items() if v.expire_at < now]
            for key in expired_keys:
                del self._cache[key]
                count += 1
            self._expired_count += count
        return count
    
    def _estimate_memory(self) -> int:
        """估算当前缓存占用的内存字节数"""
        import sys as _sys
        total = 0
        with self._lock:
            for key, item in self._cache.items():
                total += _sys.getsizeof(key)
                total += _sys.getsizeof(item.value)
                total += _sys.getsizeof(item.expire_at)
        return total
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            memory_bytes = self._estimate_memory()
            # 格式化内存大小
            if memory_bytes > 1024 * 1024:
                memory_str = f"{memory_bytes / 1024 / 1024:.2f} MB"
            elif memory_bytes > 1024:
                memory_str = f"{memory_bytes / 1024:.2f} KB"
            else:
                memory_str = f"{memory_bytes} B"
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total": total,
                "hit_rate": round(hit_rate, 4),
                "items": len(self._cache),
                "expired_count": self._expired_count,
                "memory_estimate_bytes": memory_bytes,
                "memory_estimate": memory_str
            }


class CacheManager:
    """缓存管理器"""
    
    # TTL配置(秒)
    TTL_REAL_TIME = 300      # 5分钟 - 实时行情
    TTL_KLINE = 86400        # 1天 - K线数据
    TTL_KLINE_MINUTE = 300   # 5分钟 - 分钟K线
    TTL_FINANCIAL = 86400    # 1天 - 财务数据
    TTL_SECTOR = 300         # 5分钟 - 板块数据
    TTL_LONG = 604800        # 7天 - 长期缓存
    
    def __init__(self):
        self.cache = MemoryCache()
        self.redis_cache = None
        self.redis_available = False
    
    @staticmethod
    def make_key(*parts) -> str:
        """生成缓存键"""
        return ":".join(str(p) for p in parts)
    
    @staticmethod
    def hash_symbol(symbol: str) -> str:
        """标准化股票代码并哈希"""
        # 统一格式: 6位数字
        symbol = symbol.strip().upper()
        if len(symbol) == 6 and symbol.isdigit():
            return symbol
        return symbol
    
    def get_realtime_key(self, symbol: str) -> str:
        return self.make_key("market", "quote", self.hash_symbol(symbol))
    
    def get_kline_key(self, symbol: str, period: str, adjust: str = "qfq") -> str:
        return self.make_key("market", "kline", self.hash_symbol(symbol), period, adjust)
    
    def get_fund_key(self, symbol: str) -> str:
        return self.make_key("fund", "flow", self.hash_symbol(symbol))
    
    def get_financial_key(self, symbol: str, report_type: str) -> str:
        return self.make_key("financial", self.hash_symbol(symbol), report_type)
    
    def get_sector_key(self, sector_type: str) -> str:
        return self.make_key("sector", "list", sector_type)


    # ── 兼容 API Server v2 接口 ──────────────────────
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（直接委托给 MemoryCache）"""
        return self.cache.get(key)

    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值（直接委托给 MemoryCache）"""
        self.cache.set(key, value, ttl)

    def clear(self) -> None:
        """清空所有缓存（直接委托给 MemoryCache）"""
        self.cache.clear()

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计（统一格式，兼容 api_server_v2）"""
        stats = self.cache.stats()
        return {
            "hits": stats["hits"],
            "misses": stats["misses"],
            "hit_rate": round(stats["hit_rate"] * 100, 2),
            "size": stats["items"]
        }

    def delete(self, key: str) -> bool:
        """删除指定缓存键"""
        return self.cache.delete(key)
    
    def init_redis(self, redis_url: str = None) -> bool:
        """尝试初始化Redis缓存层（可选）v2.1
        Args:
            redis_url: Redis连接URL, 默认从环境变量REDIS_URL读取
        Returns:
            bool: True if Redis connected, False otherwise
        """
        try:
            import os
            import redis as _redis
            url = redis_url or os.environ.get("REDIS_URL", "redis://localhost:6379/0")
            self.redis_cache = _redis.from_url(url, socket_timeout=2, 
                                                socket_connect_timeout=2,
                                                decode_responses=True)
            self.redis_cache.ping()
            self.redis_available = True
            logger = __import__('logging').getLogger(__name__)
            logger.info(f"Redis缓存连接成功: {url}")
            return True
        except Exception:
            self.redis_cache = None
            self.redis_available = False
            return False
    
    def set(self, key: str, value: Any, ttl: int = 300) -> None:
        """设置缓存值（双写：内存 + Redis）"""
        self.cache.set(key, value, ttl)
        if self.redis_available and self.redis_cache:
            try:
                import json as _json
                self.redis_cache.setex(key, ttl, _json.dumps(value, ensure_ascii=False))
            except Exception:
                pass
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存值（优先内存，fallback Redis）"""
        val = self.cache.get(key)
        if val is not None:
            return val
        if self.redis_available and self.redis_cache:
            try:
                raw = self.redis_cache.get(key)
                if raw:
                    import json as _json
                    val = _json.loads(raw)
                    # 回写到内存缓存
                    self.cache.set(key, val, 300)
                    return val
            except Exception:
                pass
        return None


# 全局缓存实例
cache_manager = CacheManager()
