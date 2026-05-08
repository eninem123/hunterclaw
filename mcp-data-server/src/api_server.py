"""
HTTP API 服务器
为扣子龙虾(Coze)提供远程调用接口
"""

import time
import logging
from typing import Optional, List
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Header, Query, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from src.data_service import data_service
from src.cache_manager import cache_manager
from src.main import create_mcp_tools

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Token
API_TOKEN = "mcp-data-server-token"


# ==================== 请求/响应模型 ====================

class QuoteResponse(BaseModel):
    data: Optional[dict] = None
    source: str = "unknown"
    error: Optional[str] = None


class KlineResponse(BaseModel):
    data: Optional[List[dict]] = None
    source: str = "unknown"
    error: Optional[str] = None


class SectorResponse(BaseModel):
    data: Optional[List[dict]] = None
    source: str = "unknown"
    error: Optional[str] = None


# ==================== FastAPI 应用 ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    logger.info("MCP Data Server HTTP API starting...")
    yield
    logger.info("MCP Data Server HTTP API shutting down...")

app = FastAPI(
    title="MCP Data Server API",
    description="A股数据统一接口 - 支持扣子龙虾远程调用",
    version="1.0.0",
    lifespan=lifespan
)

# CORS配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 认证中间件 ====================

async def verify_token(x_api_token: Optional[str] = Header(None)):
    """验证API Token"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")


# ==================== 系统接口 ====================

@app.get("/api/v1/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "timestamp": time.time()}


@app.get("/api/v1/status")
async def get_status():
    """获取服务状态"""
    cache_stats = cache_manager.cache.stats()
    return {
        "status": "running",
        "version": "1.0.0",
        "cache": cache_stats,
        "timestamp": time.time()
    }


@app.get("/api/v1/tools")
async def list_tools():
    """列出所有可用工具"""
    tools = create_mcp_tools()
    return {
        "tools": [
            {
                "name": t["name"],
                "description": t["description"],
                "parameters": t["inputSchema"]
            }
            for t in tools
        ]
    }


# ==================== 实时行情接口 ====================

@app.get("/api/v1/quote/{symbol}")
async def get_quote(
    symbol: str = Path(..., description="股票代码"),
    x_api_token: Optional[str] = Header(None)
):
    """获取单个股票实时行情"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_realtime_quote(symbol)
    
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    
    return result


@app.get("/api/v1/quotes")
async def get_quotes(
    symbols: str = Query(..., description="股票代码列表，逗号分隔"),
    x_api_token: Optional[str] = Header(None)
):
    """批量获取股票实时行情"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    symbol_list = [s.strip() for s in symbols.split(",")]
    result = data_service.get_realtime_quotes_batch(symbol_list)
    return result


@app.get("/api/v1/index")
async def get_index_quotes(x_api_token: Optional[str] = Header(None)):
    """获取主要指数行情"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_index_quotes()
    return result


@app.get("/api/v1/market/overview")
async def get_market_overview(x_api_token: Optional[str] = Header(None)):
    """获取市场概览"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_market_overview()
    return result


# ==================== K线接口 ====================

@app.get("/api/v1/kline/{symbol}")
async def get_kline(
    symbol: str = Path(..., description="股票代码"),
    period: str = Query("daily", description="周期: daily/weekly/monthly/minute"),
    start_date: Optional[str] = Query(None, description="开始日期 YYYYMMDD"),
    end_date: Optional[str] = Query(None, description="结束日期 YYYYMMDD"),
    adjust: str = Query("qfq", description="复权: qfq/hfq/none"),
    minute_period: str = Query("5", description="分钟周期(仅minute): 1/5/15/30/60"),
    x_api_token: Optional[str] = Header(None)
):
    """获取K线数据"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    if period == "daily":
        result = data_service.get_daily_kline(symbol, start_date, end_date, adjust)
    elif period == "weekly":
        result = data_service.get_weekly_kline(symbol, start_date, end_date)
    elif period == "monthly":
        result = data_service.get_weekly_kline(symbol, start_date, end_date)  # 月线复用周线
    elif period == "minute":
        result = data_service.get_minute_kline(symbol, minute_period)
    else:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    return result


# ==================== 资金接口 ====================

@app.get("/api/v1/fund/{symbol}")
async def get_fund_flow(
    symbol: str = Path(..., description="股票代码"),
    x_api_token: Optional[str] = Header(None)
):
    """获取个股资金流向"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_money_flow(symbol)
    return result


@app.get("/api/v1/fund/north")
async def get_north_money(
    period: str = Query("daily", description="周期: daily/weekly/monthly"),
    x_api_token: Optional[str] = Header(None)
):
    """获取北向资金"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_north_money(period)
    return result


@app.get("/api/v1/fund/sector")
async def get_sector_fund_flow(x_api_token: Optional[str] = Header(None)):
    """获取板块资金流向"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_sector_money_flow()
    return result


# ==================== 财务接口 ====================

@app.get("/api/v1/financial/{symbol}")
async def get_financial(
    symbol: str = Path(..., description="股票代码"),
    report_type: str = Query("annual", description="报告类型: annual/quarter"),
    x_api_token: Optional[str] = Header(None)
):
    """获取财务报表"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_financial_report(symbol, report_type)
    return result


@app.get("/api/v1/financial/pe/{symbol}")
async def get_pe_pb(
    symbol: str = Path(..., description="股票代码"),
    x_api_token: Optional[str] = Header(None)
):
    """获取PE/PB数据"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_pe_pb(symbol)
    return result


@app.get("/api/v1/financial/roe/{symbol}")
async def get_roe(
    symbol: str = Path(..., description="股票代码"),
    x_api_token: Optional[str] = Header(None)
):
    """获取ROE数据"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_roe_data(symbol)
    return result


# ==================== 板块接口 ====================

@app.get("/api/v1/sector/list")
async def get_sector_list(
    sector_type: str = Query("industry", description="板块类型: industry/concept"),
    x_api_token: Optional[str] = Header(None)
):
    """获取板块列表"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_sector_list(sector_type)
    return result


@app.get("/api/v1/sector/hot")
async def get_hot_sectors(
    limit: int = Query(10, description="返回数量"),
    x_api_token: Optional[str] = Header(None)
):
    """获取热门板块"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_hot_sectors(limit)
    return result


@app.get("/api/v1/sector/{sector_name}/stocks")
async def get_sector_stocks(
    sector_name: str = Path(..., description="板块名称"),
    x_api_token: Optional[str] = Header(None)
):
    """获取板块成分股"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_sector_stocks(sector_name)
    return result


@app.get("/api/v1/sector/{sector_name}/quote")
async def get_sector_quote(
    sector_name: str = Path(..., description="板块名称"),
    x_api_token: Optional[str] = Header(None)
):
    """获取板块行情"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_sector_quotes(sector_name)
    return result


# ==================== 市场情绪接口 ====================

@app.get("/api/v1/sentiment")
async def get_sentiment(x_api_token: Optional[str] = Header(None)):
    """获取市场情绪"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    result = data_service.get_market_sentiment()
    return result


# ==================== 通用工具调用接口 ====================

@app.post("/api/v1/call/{tool_name}")
async def call_tool(
    tool_name: str,
    arguments: dict = None,
    x_api_token: Optional[str] = Header(None)
):
    """通用工具调用接口"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    from src.main import create_mcp_handlers
    
    handlers = create_mcp_handlers()
    
    if tool_name not in handlers:
        raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")
    
    try:
        result = handlers[tool_name](arguments or {})
        return {"success": True, "result": result}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 缓存管理接口 ====================

@app.post("/api/v1/cache/clear")
async def clear_cache(x_api_token: Optional[str] = Header(None)):
    """清空缓存"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    cache_manager.cache.clear()
    return {"success": True, "message": "Cache cleared"}


@app.post("/api/v1/cache/clear-expired")
async def clear_expired(x_api_token: Optional[str] = Header(None)):
    """清空过期缓存"""
    if x_api_token != API_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid API Token")
    
    count = cache_manager.cache.clear_expired()
    return {"success": True, "cleared": count}


# ==================== 主程序 ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8766, log_level="info")
