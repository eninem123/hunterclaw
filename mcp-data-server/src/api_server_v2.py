#!/usr/bin/env python3
"""
MCP数据服务器 API v2.0
改进版本：
  - 性能优化：异步请求、连接池
  - 缓存增强：Redis缓存、多级缓存
  - 错误处理：完善的异常处理和重试机制
  - 监控：性能指标、健康检查
  - 文档：OpenAPI规范
  - 限流：API限流保护

使用方法：
  uvicorn api_server_v2:app --host 0.0.0.0 --port 8766
"""

from fastapi import FastAPI, HTTPException, Depends, status, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import asyncio
import aiohttp
import json
import logging
import time
from collections import defaultdict
import hashlib
import random
import uvicorn

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── 配置 ────────────────────────────────────────────
class Config:
    """服务器配置"""
    API_TOKEN = "mcp-data-server-token"
    TIMEOUT = 10
    MAX_RETRIES = 3
    RETRY_DELAY = 1.0
    CACHE_TTL = {
        'quote': 300,  # 5分钟
        'kline': 86400,  # 1天
        'financial': 86400,  # 1天
        'sector': 300,  # 5分钟
    }
    RATE_LIMIT = {
        'default': 100,  # 每分钟请求数
        'burst': 200,  # 突发请求数
    }

config = Config()

# ── FastAPI应用 ───────────────────────────────────────
app = FastAPI(
    title="MCP数据服务器",
    description="A股数据统一接口 v2.0",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 缓存系统（从共享模块导入） ───────────────────────────
from src.cache_manager import CacheManager

cache = CacheManager()

# ── 限流系统 ───────────────────────────────────────────
class RateLimiter:
    """限流器"""
    
    def __init__(self):
        self.requests: Dict[str, List[float]] = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int = 100, window: int = 60) -> bool:
        """检查是否允许请求"""
        now = time.time()
        
        # 清理过期记录
        self.requests[key] = [
            req_time for req_time in self.requests[key]
            if now - req_time < window
        ]
        
        # 检查是否超限
        if len(self.requests[key]) >= limit:
            return False
        
        # 记录请求
        self.requests[key].append(now)
        return True

rate_limiter = RateLimiter()

# ── 数据服务 ───────────────────────────────────────────
class DataService:
    """数据服务"""
    
    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Referer": "https://finance.qq.com"
        }
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=config.TIMEOUT),
            headers=self.headers
        )
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch(self, url: str, encoding: str = 'gbk') -> Optional[str]:
        """获取数据"""
        cache_key = hashlib.md5(url.encode()).hexdigest()
        
        # 检查缓存
        cached = cache.get(cache_key)
        if cached:
            logger.debug(f"缓存命中: {url}")
            return cached
        
        # 请求数据
        for attempt in range(config.MAX_RETRIES):
            try:
                async with self.session.get(url) as response:
                    if response.status == 200:
                        data = await response.text(encoding=encoding)
                        
                        # 自动确定TTL
                        if 'kline' in url or 'financial' in url:
                            ttl = config.CACHE_TTL['kline']
                        else:
                            ttl = config.CACHE_TTL['quote']
                        
                        cache.set(cache_key, data, ttl)
                        return data
                    else:
                        logger.warning(f"HTTP {response.status}: {url}")
            except Exception as e:
                logger.warning(f"请求失败 (尝试 {attempt+1}/{config.MAX_RETRIES}): {e}")
                if attempt < config.MAX_RETRIES - 1:
                    await asyncio.sleep(config.RETRY_DELAY)
        
        return None
    
    async def get_realtime_quote(self, symbol: str) -> Optional[Dict]:
        """获取实时行情"""
        prefix = 'sh' if symbol.startswith(('6', '5')) else 'sz'
        url = f"https://qt.gtimg.cn/q={prefix}{symbol}"
        data = await self.fetch(url, 'gbk')
        
        if not data:
            return None
        
        import re
        m = re.search(r'v_\w+="(.+)"', data)
        if m:
            parts = m.group(1).split('~')
            if len(parts) >= 32:
                return {
                    'code': symbol,
                    'name': parts[1],
                    'price': float(parts[3]),
                    'prev_close': float(parts[4]),
                    'open': float(parts[5]),
                    'high': float(parts[33]),
                    'low': float(parts[34]),
                    'volume': int(parts[6]),
                    'amount': float(parts[37]),
                    'chg_pct': float(parts[32]),
                    'timestamp': datetime.now().isoformat()
                }
        
        return None
    
    async def get_daily_kline(self, symbol: str, start_date: str, 
                             end_date: str, adjust: str = 'qfq') -> List[Dict]:
        """获取日K线"""
        # 这里使用模拟数据，实际需要调用真实API
        prefix = 'sh' if symbol.startswith(('6', '5')) else 'sz'
        
        # 缓存键
        cache_key = f"kline:{symbol}:{start_date}:{end_date}:{adjust}"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # 模拟K线数据
        import random
        klines = []
        base_price = 10.0
        
        # 解析日期
        start = datetime.strptime(start_date, '%Y%m%d')
        end = datetime.strptime(end_date, '%Y%m%d')
        
        current = start
        while current <= end:
            # 跳过周末
            if current.weekday() < 5:
                change = random.uniform(-0.05, 0.05)
                open_price = base_price * (1 + change)
                close_price = open_price * (1 + random.uniform(-0.03, 0.03))
                high_price = max(open_price, close_price) * (1 + random.uniform(0, 0.02))
                low_price = min(open_price, close_price) * (1 - random.uniform(0, 0.02))
                volume = random.randint(1000000, 10000000)
                
                klines.append({
                    'date': current.strftime('%Y-%m-%d'),
                    'open': round(open_price, 2),
                    'high': round(high_price, 2),
                    'low': round(low_price, 2),
                    'close': round(close_price, 2),
                    'volume': volume,
                    'amount': round(volume * close_price, 2)
                })
                
                base_price = close_price
            
            current += timedelta(days=1)
        
        # 缓存
        cache.set(cache_key, klines, config.CACHE_TTL['kline'])
        
        return klines
    
    async def get_market_overview(self) -> Dict:
        """获取市场概览"""
        # 获取三大指数
        indices = ['sh000001', 'sz399001', 'sz399006']
        results = await asyncio.gather(*[
            self.get_realtime_quote(idx) for idx in indices
        ])
        
        valid_indices = [r for r in results if r]
        
        if not valid_indices:
            return {}
        
        # 计算涨跌家数（模拟）
        total_up = random.randint(1000, 3000)
        total_down = random.randint(500, 2000)
        total_limit_up = random.randint(20, 100)
        total_limit_down = random.randint(5, 30)
        
        return {
            'indices': valid_indices,
            'market_sentiment': {
                'up': total_up,
                'down': total_down,
                'limit_up': total_limit_up,
                'limit_down': total_limit_down
            },
            'timestamp': datetime.now().isoformat()
        }

data_service = DataService()

# ── 依赖注入 ───────────────────────────────────────────
async def get_data_service():
    """获取数据服务实例"""
    async with data_service:
        yield data_service

async def verify_token(request: Request):
    """验证API Token"""
    token = request.headers.get('X-API-Token')
    if token != config.API_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API token"
        )
    return True

async def check_rate_limit(request: Request):
    """检查限流"""
    client_id = request.client.host if request.client else 'unknown'
    if not rate_limiter.is_allowed(client_id, config.RATE_LIMIT['default']):
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded"
        )
    return True

# ── 数据模型 ───────────────────────────────────────────
class QuoteResponse(BaseModel):
    """行情响应"""
    code: str
    name: str
    price: float
    prev_close: float
    open: float
    high: float
    low: float
    volume: int
    amount: float
    chg_pct: float
    timestamp: str

class KlineResponse(BaseModel):
    """K线响应"""
    date: str
    open: float
    high: float
    low: float
    close: float
    volume: int
    amount: float

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    cache_stats: Dict[str, Any]
    uptime: float

# ── API端点 ───────────────────────────────────────────
@app.get("/", response_model=Dict[str, str])
async def root():
    """根路径"""
    return {
        "name": "MCP数据服务器",
        "version": "2.0.0",
        "docs": "/docs",
        "health": "/api/v2/health"
    }

@app.get("/api/v2/health", response_model=HealthResponse)
async def health_check():
    """健康检查 - 缓存状态、服务运行时间"""
    cache_stats = cache.get_stats()
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        cache_stats=cache_stats,
        uptime=time.time()
    )

@app.get("/api/v2/quote/{symbol}", response_model=QuoteResponse)
async def get_quote(
    symbol: str,
    _: bool = Depends(verify_token),
    __: bool = Depends(check_rate_limit),
    service: DataService = Depends(get_data_service)
):
    """获取实时行情"""
    quote = await service.get_realtime_quote(symbol)
    if not quote:
        raise HTTPException(status_code=404, detail="Quote not found")
    return quote

@app.get("/api/v2/kline/{symbol}", response_model=List[KlineResponse])
async def get_kline(
    symbol: str,
    start_date: str,
    end_date: str = None,
    adjust: str = 'qfq',
    _: bool = Depends(verify_token),
    __: bool = Depends(check_rate_limit),
    service: DataService = Depends(get_data_service)
):
    """获取K线数据"""
    if end_date is None:
        end_date = datetime.now().strftime('%Y%m%d')
    
    klines = await service.get_daily_kline(symbol, start_date, end_date, adjust)
    if not klines:
        raise HTTPException(status_code=404, detail="Kline data not found")
    
    return klines

@app.get("/api/v2/market/overview")
async def get_market_overview(
    _: bool = Depends(verify_token),
    __: bool = Depends(check_rate_limit),
    service: DataService = Depends(get_data_service)
):
    """获取市场概览"""
    overview = await service.get_market_overview()
    if not overview:
        raise HTTPException(status_code=404, detail="Market data not found")
    return overview

@app.get("/api/v2/cache/stats")
async def get_cache_stats(_: bool = Depends(verify_token)):
    """获取缓存统计"""
    return cache.get_stats()

@app.post("/api/v2/cache/clear")
async def clear_cache(_: bool = Depends(verify_token)):
    """清空缓存"""
    cache.clear()
    return {"status": "success", "message": "Cache cleared"}

@app.get("/api/v2/rate-limit/stats")
async def get_rate_limit_stats(_: bool = Depends(verify_token)):
    """获取限流统计（每个客户端IP的请求数）"""
    import time
    now = time.time()
    snapshot = {}
    for client_id, timestamps in list(rate_limiter.requests.items()):
        # 只返回最近窗口内的统计
        recent = [t for t in timestamps if now - t < 60]
        snapshot[client_id] = {
            "requests_last_min": len(recent),
            "limit": config.RATE_LIMIT['default']
        }
    return {
        "clients": snapshot,
        "total_clients": len(snapshot),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/rate-limit/config")
async def get_rate_limit_config():
    """获取限流配置（无需鉴权）"""
    return {
        "default": config.RATE_LIMIT['default'],
        "burst": config.RATE_LIMIT['burst'],
        "window_seconds": 60
    }

# ── v2.1 新增端点 ─────────────────────────────────────

@app.get("/api/v2/market/indices")
async def get_market_indices(
    _: bool = Depends(verify_token),
    service: DataService = Depends(get_data_service)
):
    """获取全市场主要指数实时行情"""
    index_codes = [
        "sh000001", "sz399001", "sz399006", "sh000300",
        "sh000016", "sz399905", "sh000688"
    ]
    tasks = [service.get_realtime_quote(code) for code in index_codes]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    indices = []
    for r in results:
        if isinstance(r, dict) and r:
            indices.append(r)
    
    # 计算涨跌比和均幅
    up_count = sum(1 for i in indices if i.get('chg_pct', 0) > 0)
    down_count = sum(1 for i in indices if i.get('chg_pct', 0) < 0)
    avg_chg = sum(i.get('chg_pct', 0) for i in indices) / max(len(indices), 1)
    
    return {
        "indices": indices,
        "breadth": {
            "up": up_count,
            "down": down_count,
            "avg_chg_pct": round(avg_chg, 2),
            "up_ratio": round(up_count / max(up_count + down_count, 1) * 100, 1)
        },
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/market/breadth")
async def get_market_breadth(
    _: bool = Depends(verify_token),
    service: DataService = Depends(get_data_service)
):
    """获取市场广度数据（涨跌家数、涨停跌停统计）"""
    overview = await service.get_market_overview()
    if not overview:
        raise HTTPException(status_code=404, detail="Market breadth data unavailable")
    
    sentiment = overview.get("market_sentiment", {})
    up = sentiment.get("up", 0)
    down = sentiment.get("down", 0)
    total = up + down
    
    return {
        "up_stocks": up,
        "down_stocks": down,
        "total_active": total,
        "up_ratio": round(up / max(total, 1) * 100, 1),
        "limit_up": sentiment.get("limit_up", 0),
        "limit_down": sentiment.get("limit_down", 0),
        "breadth_level": "强势" if up > down * 2 else ("偏强" if up > down else ("偏弱" if down > up * 2 else "均衡")),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/market/temperature")
async def get_market_temperature(
    _: bool = Depends(verify_token),
    service: DataService = Depends(get_data_service)
):
    """计算市场温度 (0-100) 和恐慌指数"""
    overview = await service.get_market_overview()
    if not overview:
        raise HTTPException(status_code=404, detail="Market data unavailable")
    
    indices = overview.get("indices", [])
    sentiment = overview.get("market_sentiment", {})
    
    # 温度计算（简化版）
    score = 50
    if indices:
        avg_chg = sum(i.get("chg_pct", 0) for i in indices) / max(len(indices), 1)
        score += avg_chg * 5
    
    up = sentiment.get("up", 0)
    down = sentiment.get("down", 0)
    total = max(up + down, 1)
    breadth_ratio = up / total
    score = score * 0.6 + breadth_ratio * 100 * 0.4
    score = max(0, min(100, round(score)))
    
    # 恐慌指数（反向）
    panic_score = max(0, min(100, round(100 - score * 0.8 - breadth_ratio * 20)))
    
    temp_label = "过热" if score >= 70 else ("正常" if score >= 50 else ("偏冷" if score >= 30 else "冰点"))
    panic_label = "安全" if panic_score >= 60 else ("谨慎" if panic_score >= 40 else ("偏冷" if panic_score >= 25 else "冰点"))
    
    return {
        "temperature": score,
        "temperature_label": temp_label,
        "panic_index": panic_score,
        "panic_label": panic_label,
        "breadth_ratio": round(breadth_ratio * 100, 1),
        "avg_change_pct": round(avg_chg if indices else 0, 2),
        "timestamp": datetime.now().isoformat()
    }

@app.post("/api/v2/batch/quotes")
async def batch_quotes(
    symbols: List[str],
    _: bool = Depends(verify_token),
    __: bool = Depends(check_rate_limit),
    service: DataService = Depends(get_data_service)
):
    """批量获取实时行情（最多20只）"""
    if len(symbols) > 20:
        raise HTTPException(status_code=400, detail="Maximum 20 symbols per batch request")
    
    tasks = [service.get_realtime_quote(sym) for sym in symbols]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    quotes = []
    errors = []
    for sym, r in zip(symbols, results):
        if isinstance(r, dict) and r:
            quotes.append(r)
        else:
            errors.append({"symbol": sym, "error": str(r) if r else "No data"})
    
    return {
        "quotes": quotes,
        "errors": errors,
        "total": len(quotes),
        "timestamp": datetime.now().isoformat()
    }

@app.get("/api/v2/health/metrics")
async def health_metrics(_: bool = Depends(verify_token)):
    """扩展健康检查：缓存详情+限流状态+系统信息"""
    cache_stats = cache.get_stats()
    
    # Redis状态检查（如果可用）
    redis_status = "disabled"
    if hasattr(cache, 'redis_cache') and cache.redis_cache:
        try:
            redis_status = "connected" if cache.redis_cache.ping() else "error"
        except Exception:
            redis_status = "error"
    
    return {
        "status": "healthy",
        "version": "2.1.0",
        "timestamp": datetime.now().isoformat(),
        "uptime_seconds": round(time.time() - getattr(app.state, 'start_time', time.time()), 1),
        "cache": {
            **cache_stats,
            "redis": redis_status
        },
        "rate_limiter": {
            "active_clients": len(rate_limiter.requests),
            "default_limit": config.RATE_LIMIT['default']
        }
    }

@app.on_event("startup")
async def startup_event():
    """服务启动初始化"""
    app.state.start_time = time.time()
    logger.info("MCP数据服务器 v2.1 启动完成")

# ── 异常处理 ───────────────────────────────────────────
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """HTTP异常处理"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "timestamp": datetime.now().isoformat(),
            "path": request.url.path
        }
    )

# ── 启动脚本 ───────────────────────────────────────────
if __name__ == "__main__":
    uvicorn.run(
        "api_server_v2:app",
        host="0.0.0.0",
        port=8766,
        reload=True,
        log_level="info"
    )
