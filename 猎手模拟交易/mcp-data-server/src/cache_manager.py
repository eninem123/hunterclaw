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
        return count
    
    def stats(self) -> Dict[str, Any]:
        """获取缓存统计"""
        with self._lock:
            total = self._hits + self._misses
            hit_rate = self._hits / total if total > 0 else 0
            return {
                "hits": self._hits,
                "misses": self._misses,
                "total": total,
                "hit_rate": round(hit_rate, 4),
                "items": len(self._cache)
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


# 全局缓存实例
cache_manager = CacheManager()
