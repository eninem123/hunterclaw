"""
MCP Server 入口
支持 STDIO 和 HTTP 两种模式
"""

import sys
import json
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def create_mcp_tools():
    """创建MCP工具列表"""
    from src.data_service import data_service
    
    tools = []
    
    # ==================== 实时行情工具 ====================
    
    def get_realtime_quote(symbol: str) -> str:
        """获取单个股票实时行情
        
        Args:
            symbol: 股票代码，如 "000001"
        
        Returns:
            JSON格式的行情数据
        """
        result = data_service.get_realtime_quote(symbol)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_realtime_quote",
        "description": "获取A股股票的实时行情数据，包括当前价格、涨跌幅、成交量等。适用于需要快速查看个股最新报价的场景。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，6位数字，如 '000001' 表示平安银行"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_realtime_quotes_batch(symbols: str) -> str:
        """批量获取股票实时行情
        
        Args:
            symbols: 股票代码列表，逗号分隔，如 "000001,600000,000002"
        
        Returns:
            JSON格式的批量行情数据
        """
        symbol_list = [s.strip() for s in symbols.split(",")]
        result = data_service.get_realtime_quotes_batch(symbol_list)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_realtime_quotes_batch",
        "description": "批量获取多个A股股票的实时行情，适用于需要同时查看多只股票报价的场景。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbols": {
                    "type": "string",
                    "description": "股票代码列表，逗号分隔，如 '000001,600000,000002'"
                }
            },
            "required": ["symbols"]
        }
    })
    
    def get_index_quotes() -> str:
        """获取主要指数实时行情
        
        Returns:
            JSON格式的上证指数、深证成指、创业板指等主要指数行情
        """
        result = data_service.get_index_quotes()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_index_quotes",
        "description": "获取上证指数、深证成指、创业板指、科创50、沪深300等主要指数的实时行情。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_market_overview() -> str:
        """获取市场概览
        
        Returns:
            JSON格式的市场整体情况，包括涨跌停数量、涨跌家数等
        """
        result = data_service.get_market_overview()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_market_overview",
        "description": "获取A股市场整体概览，包括涨跌停数量、上涨下跌平盘家数等，反映市场整体热度。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    # ==================== K线工具 ====================
    
    def get_daily_kline(symbol: str, start_date: str = None, end_date: str = None,
                       adjust: str = "qfq") -> str:
        """获取日K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期，YYYYMMDD格式，默认为一年前
            end_date: 结束日期，YYYYMMDD格式，默认为今天
            adjust: 复权类型 qfq(前复权)/hfq(后复权)/none(不复权)
        
        Returns:
            JSON格式的日K线数据
        """
        result = data_service.get_daily_kline(symbol, start_date, end_date, adjust)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_daily_kline",
        "description": "获取A股股票的日K线数据，包含开盘价、收盘价、最高价、最低价、成交量、成交额等信息。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码，如 '000001'"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，YYYYMMDD格式，如 '20240101'"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期，YYYYMMDD格式，如 '20250101'"
                },
                "adjust": {
                    "type": "string",
                    "description": "复权类型：qfq(前复权，默认)/hfq(后复权)/none(不复权)"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_weekly_kline(symbol: str, start_date: str = None, 
                         end_date: str = None) -> str:
        """获取周K线数据
        
        Args:
            symbol: 股票代码
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            JSON格式的周K线数据
        """
        result = data_service.get_weekly_kline(symbol, start_date, end_date)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_weekly_kline",
        "description": "获取A股股票的周K线数据，用于中线趋势分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "start_date": {
                    "type": "string",
                    "description": "开始日期，YYYYMMDD格式"
                },
                "end_date": {
                    "type": "string",
                    "description": "结束日期，YYYYMMDD格式"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_minute_kline(symbol: str, period: str = "5") -> str:
        """获取分钟K线数据
        
        Args:
            symbol: 股票代码
            period: K线周期 1/5/15/30/60 (分钟)
        
        Returns:
            JSON格式的分钟K线数据
        """
        result = data_service.get_minute_kline(symbol, period)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_minute_kline",
        "description": "获取A股股票的分钟K线数据，适用于短线分析和盘中决策。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "period": {
                    "type": "string",
                    "description": "K线周期：1/5/15/30/60 (分钟)"
                }
            },
            "required": ["symbol"]
        }
    })
    
    # ==================== 资金流向工具 ====================
    
    def get_money_flow(symbol: str) -> str:
        """获取个股资金流向
        
        Args:
            symbol: 股票代码
        
        Returns:
            JSON格式的主力资金流向数据
        """
        result = data_service.get_money_flow(symbol)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_money_flow",
        "description": "获取个股主力资金流向数据，包括主力净流入、超大单净流入、大单净流入等。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_north_money(period: str = "daily") -> str:
        """获取北向资金数据
        
        Args:
            period: 时间周期 daily/weekly/monthly
        
        Returns:
            JSON格式的北向资金数据
        """
        result = data_service.get_north_money(period)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_north_money",
        "description": "获取北向资金（沪深港通）流向数据，反映外资对A股的配置情况。⚠️ 注意：2026-05-13起北向资金不再实时披露，改为T+1盘后数据",
        "inputSchema": {
            "type": "object",
            "properties": {
                "period": {
                    "type": "string",
                    "description": "时间周期：daily(日)/weekly(周)/monthly(月)"
                }
            },
            "required": []
        }
    })
    
    def get_sector_money_flow() -> str:
        """获取板块资金流向
        
        Returns:
            JSON格式的各行业板块资金流向排名
        """
        result = data_service.get_sector_money_flow()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_sector_money_flow",
        "description": "获取各行业板块的资金流向排名，帮助识别资金流入的热点板块。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    # ==================== 财务工具 ====================
    
    def get_financial_report(symbol: str, report_type: str = "annual") -> str:
        """获取财务报表
        
        Args:
            symbol: 股票代码
            report_type: 报告类型 annual/quarter
        
        Returns:
            JSON格式的财务指标数据
        """
        result = data_service.get_financial_report(symbol, report_type)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_financial_report",
        "description": "获取个股的财务报表指标，包括ROE、毛利率、净利率、资产负债率等核心财务数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                },
                "report_type": {
                    "type": "string",
                    "description": "报告类型：annual(年报)/quarter(季报)"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_roe_data(symbol: str) -> str:
        """获取ROE等核心指标
        
        Args:
            symbol: 股票代码
        
        Returns:
            JSON格式的ROE数据
        """
        result = data_service.get_roe_data(symbol)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_roe_data",
        "description": "获取个股的净资产收益率(ROE)、毛利率、净利率等核心盈利指标，用于价值投资分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                }
            },
            "required": ["symbol"]
        }
    })
    
    def get_pe_pb(symbol: str) -> str:
        """获取PE/PB数据
        
        Args:
            symbol: 股票代码
        
        Returns:
            JSON格式的市盈率、市净率数据
        """
        result = data_service.get_pe_pb(symbol)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_pe_pb",
        "description": "获取个股的市盈率(PE)和市净率(PB)数据，用于估值分析。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "symbol": {
                    "type": "string",
                    "description": "股票代码"
                }
            },
            "required": ["symbol"]
        }
    })
    
    # ==================== 板块工具 ====================
    
    def get_sector_list(sector_type: str = "industry") -> str:
        """获取板块列表
        
        Args:
            sector_type: 板块类型 industry(行业)/concept(概念)
        
        Returns:
            JSON格式的板块列表
        """
        result = data_service.get_sector_list(sector_type)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_sector_list",
        "description": "获取A股所有板块列表，包括行业板块和概念板块。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sector_type": {
                    "type": "string",
                    "description": "板块类型：industry(行业板块)/concept(概念板块)"
                }
            },
            "required": []
        }
    })
    
    def get_hot_sectors(limit: int = 10) -> str:
        """获取热门板块
        
        Args:
            limit: 返回数量，默认10
        
        Returns:
            JSON格式的热门板块排名
        """
        result = data_service.get_hot_sectors(limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_hot_sectors",
        "description": "获取当前热门板块排名，按资金流入和涨跌幅排序。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回数量，默认10"
                }
            },
            "required": []
        }
    })
    
    def get_sector_stocks(sector_name: str) -> str:
        """获取板块成分股
        
        Args:
            sector_name: 板块名称，如 "银行"
        
        Returns:
            JSON格式的板块成分股列表
        """
        result = data_service.get_sector_stocks(sector_name)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_sector_stocks",
        "description": "获取指定板块的所有成分股列表。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "sector_name": {
                    "type": "string",
                    "description": "板块名称，如 '银行'、'芯片'"
                }
            },
            "required": ["sector_name"]
        }
    })
    
    # ==================== 市场情绪工具 ====================
    
    def get_market_sentiment() -> str:
        """获取市场情绪指标
        
        Returns:
            JSON格式的市场情绪综合指标
        """
        result = data_service.get_market_sentiment()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_market_sentiment",
        "description": "获取综合市场情绪指标，包括涨跌家数、主力资金、恐慌贪婪指数等。⚠️ 注意：2026-05-13起北向资金不再实时披露，改为T+1盘后数据",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    # ==================== 增强情绪工具 ====================
    
    def get_market_sentiment_enhanced() -> str:
        """获取增强版市场情绪指标（委托模块级函数）"""
        result = _get_market_sentiment_enhanced()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_market_sentiment_enhanced",
        "description": "增强版市场情绪指标，聚合涨跌家数、板块资金流向、指数表现、北向资金等多源数据，返回综合情绪评分(0-100)。⚠️ 注意：2026-05-13起北向资金改为T+1盘后数据，北向数据为T+1盘后延迟",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    return tools


def _get_market_sentiment_enhanced() -> dict:
    """增强版市场情绪聚合函数（模块级，供tools和handlers共用）"""
    from src.data_service import data_service
    
    try:
        overview = data_service.get_market_overview()
        overview_data = overview.get("data", {})
        indices = data_service.get_index_quotes()
        sector_flow = data_service.get_sector_money_flow()
        sector_data = sector_flow.get("data", [])
        north_money = data_service.get_north_money("daily")

        score = 50
        reasons = []

        rising = overview_data.get("rising", 0)
        falling = overview_data.get("falling", 0)
        total = overview_data.get("total", 1)

        if total > 0 and falling > 0:
            ratio = rising / falling
            if ratio > 2:
                score += 20; reasons.append("涨跌比>2，市场强势")
            elif ratio > 1.2:
                score += 10; reasons.append("涨跌比>1.2，市场偏强")
            elif ratio < 0.5:
                score -= 20; reasons.append("涨跌比<0.5，市场弱势")
            elif ratio < 0.8:
                score -= 10; reasons.append("涨跌比<0.8，市场偏弱")

        limit_up = overview_data.get("limit_up", 0)
        if limit_up > 100:
            score += 15; reasons.append(f"涨停{limit_up}家，情绪亢奋")
        elif limit_up > 50:
            score += 10; reasons.append(f"涨停{limit_up}家，情绪高涨")

        top_sector = sector_data[0] if sector_data else {}
        if top_sector:
            reasons.append(f"资金流入最强板块: {top_sector.get('板块名称', 'N/A')}")

        north_data = north_money.get("data", [])

        sentiment_label = (
            "极度恐慌" if score <= 20 else
            "偏恐慌" if score <= 40 else
            "中性" if score <= 60 else
            "偏乐观" if score <= 80 else
            "极度乐观"
        )

        return {
            "market_sentiment_score": max(0, min(100, score)),
            "sentiment_label": sentiment_label,
            "reasons": reasons,
            "overview": overview_data,
            "indices": indices.get("data", []),
            "sector_flow": sector_data[:5] if sector_data else [],
            "north_money": north_data,
            "north_money_note": "北向资金已改为T+1盘后数据，非实时",
            "timestamp": datetime.now().isoformat(),
            "source": "multi-source aggregated"
        }
    except Exception as e:
        logger.error(f"增强情绪分析失败: {e}")
        return {
            "error": str(e),
            "market_sentiment_score": 50,
            "sentiment_label": "未知",
            "fallback": "基础情绪获取失败，返回默认中性值",
            "timestamp": datetime.now().isoformat()
        }


def create_mcp_handlers():
    """创建MCP工具处理器"""
    from src.data_service import data_service
    
    handlers = {}
    
    # 实时行情
    handlers["get_realtime_quote"] = lambda args: data_service.get_realtime_quote(
        args.get("symbol", "")
    )
    handlers["get_realtime_quotes_batch"] = lambda args: data_service.get_realtime_quotes_batch(
        [s.strip() for s in args.get("symbols", "").split(",") if s.strip()]
    )
    handlers["get_index_quotes"] = lambda args: data_service.get_index_quotes()
    handlers["get_market_overview"] = lambda args: data_service.get_market_overview()
    
    # K线
    handlers["get_daily_kline"] = lambda args: data_service.get_daily_kline(
        args.get("symbol", ""), args.get("start_date"), args.get("end_date"), args.get("adjust", "qfq")
    )
    handlers["get_weekly_kline"] = lambda args: data_service.get_weekly_kline(
        args.get("symbol", ""), args.get("start_date"), args.get("end_date")
    )
    handlers["get_minute_kline"] = lambda args: data_service.get_minute_kline(
        args.get("symbol", ""), args.get("period", "5")
    )
    
    # 资金
    handlers["get_money_flow"] = lambda args: data_service.get_money_flow(args.get("symbol", ""))
    handlers["get_north_money"] = lambda args: data_service.get_north_money(
        args.get("period", "daily")
    )
    handlers["get_sector_money_flow"] = lambda args: data_service.get_sector_money_flow()
    
    # 财务
    handlers["get_financial_report"] = lambda args: data_service.get_financial_report(
        args.get("symbol", ""), args.get("report_type", "annual")
    )
    handlers["get_roe_data"] = lambda args: data_service.get_roe_data(args.get("symbol", ""))
    handlers["get_pe_pb"] = lambda args: data_service.get_pe_pb(args.get("symbol", ""))
    
    # 板块
    handlers["get_sector_list"] = lambda args: data_service.get_sector_list(
        args.get("sector_type", "industry")
    )
    handlers["get_hot_sectors"] = lambda args: data_service.get_hot_sectors(
        args.get("limit", 10)
    )
    handlers["get_sector_stocks"] = lambda args: data_service.get_sector_stocks(
        args.get("sector_name", "")
    )
    
    # 情绪
    handlers["get_market_sentiment"] = lambda args: data_service.get_market_sentiment()
    handlers["get_market_sentiment_enhanced"] = lambda args: _get_market_sentiment_enhanced()
    
    return handlers


def _validate_tools_list(tools: list) -> bool:
    """验证 tools/list 返回格式是否符合 MCP 规范"""
    for t in tools:
        if "name" not in t or "description" not in t or "inputSchema" not in t:
            logger.warning(f"工具 {t.get('name', 'unknown')} 缺少必要字段")
            return False
        if not isinstance(t["inputSchema"], dict):
            logger.warning(f"工具 {t['name']} 的 inputSchema 不是字典")
            return False
    return True


def _safe_handler_call(handler, args: dict) -> dict:
    """带降级逻辑的handler调用
    
    1. 正常调用
    2. 失败后重试1次
    3. 返回降级结果
    """
    try:
        return handler(args)
    except Exception as e:
        logger.warning(f"handler调用失败(首次): {e}")
        # 重试一次
        try:
            return handler(args)
        except Exception as e2:
            logger.error(f"handler调用失败(重试后): {e2}")
            return {
                "error": str(e2),
                "error_type": type(e2).__name__,
                "message": "服务临时不可用，请稍后重试",
                "fallback": True,
                "timestamp": datetime.now().isoformat()
            }


def run_stdio_server():
    """运行STDIO模式的MCP服务器"""
    logger.info("Starting MCP Data Server (STDIO mode)")
    
    tools = create_mcp_tools()
    handlers = create_mcp_handlers()
    
    # 输出服务发现信息
    response = {
        "jsonrpc": "2.0",
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mcp-data-server",
                "version": "1.0.0"
            },
            "tools": [
                {
                    "name": t["name"],
                    "description": t["description"],
                    "inputSchema": t["inputSchema"]
                }
                for t in tools
            ]
        },
        "id": None
    }
    print(json.dumps(response))
    
    # 处理请求
    for line in sys.stdin:
        try:
            request = json.loads(line.strip())
            
            if request.get("method") == "initialize":
                response = {
                    "jsonrpc": "2.0",
                    "result": {
                        "protocolVersion": "2024-11-05",
                        "capabilities": {"tools": {}},
                        "serverInfo": {"name": "mcp-data-server", "version": "1.0.0"}
                    },
                    "id": request.get("id")
                }
                print(json.dumps(response))
                
            elif request.get("method") == "tools/list":
                # 验证 tools/list 返回格式
                if not _validate_tools_list(tools):
                    logger.warning("tools/list 返回格式不完整，已修复")
                
                # 确保每个工具都有正确的 inputSchema
                validated_tools = []
                for t in tools:
                    validated_tools.append({
                        "name": t["name"],
                        "description": t["description"],
                        "inputSchema": t.get("inputSchema", {"type": "object", "properties": {}, "required": []})
                    })
                
                response = {
                    "jsonrpc": "2.0",
                    "result": {"tools": validated_tools},
                    "id": request.get("id")
                }
                print(json.dumps(response))
                
            elif request.get("method") == "tools/call":
                tool_name = request.get("params", {}).get("name")
                tool_args = request.get("params", {}).get("arguments", {})
                
                if tool_name in handlers:
                    result = _safe_handler_call(handlers[tool_name], tool_args)
                    response = {
                        "jsonrpc": "2.0",
                        "result": {
                            "content": [
                                {
                                    "type": "text",
                                    "text": json.dumps(result, ensure_ascii=False)
                                }
                            ]
                        },
                        "id": request.get("id")
                    }
                else:
                    response = {
                        "jsonrpc": "2.0",
                        "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"},
                        "id": request.get("id")
                    }
                print(json.dumps(response))
                
            elif request.get("method") == "notifications/initialized":
                pass  # 忽略
                
        except json.JSONDecodeError:
            continue
        except Exception as e:
            logger.error(f"Error processing request: {e}")
    
    sys.stdout.flush()


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--stdio":
        run_stdio_server()
    else:
        logger.info("Use --stdio flag for MCP STDIO mode")
        logger.info("Or run api_server.py for HTTP API mode")
