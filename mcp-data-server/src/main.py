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
    
    # ==================== ETF资金流向工具 ====================
    
    def get_etf_money_flow(indicator: str = "今日") -> str:
        """获取ETF资金流向排名
        
        Args:
            indicator: 时间指标 今日/3日/5日
        
        Returns:
            JSON格式的ETF资金流排名
        """
        result = data_service.get_etf_money_flow(indicator)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_etf_money_flow",
        "description": "获取ETF资金流向排名（按净流入排序），V07规则：科技ETF连续净申购为增量信号。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "indicator": {
                    "type": "string",
                    "description": "时间指标：今日/3日/5日"
                }
            },
            "required": []
        }
    })
    
    def get_futures_basis() -> str:
        """获取沪深300期指基差
        
        Returns:
            JSON格式的期指基差数据
        """
        result = data_service.get_futures_basis()
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_futures_basis",
        "description": "获取沪深300期货基差数据（现货vs期货价差），V06规则：升水>20乐观/贴水>20谨慎。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_sector_money_flow_ratio(limit: int = 20) -> str:
        """获取板块主力净流入率
        
        Args:
            limit: 返回板块数量
        
        Returns:
            JSON格式的板块主力净流入率排名
        """
        result = data_service.get_sector_money_flow_ratio(limit)
        return json.dumps(result, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_sector_money_flow_ratio",
        "description": "获取板块主力净流入率（主力净流入/成交额），V05规则：板块主力净流入率超过0.5%为高流入信号。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回板块数量，默认20"
                }
            },
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
    
    # ==================== 恐慌指数工具 (v4.0新增) ====================
    
    def get_panic_index() -> str:
        """获取恐慌指数"""
        panic_data = _compute_panic()
        return json.dumps(panic_data, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_panic_index",
        "description": "获取市场恐慌指数(0-100)，越低越恐慌。V10规则：恐慌<25强制空仓，<35禁止新开仓。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_market_timing() -> str:
        """获取市场时机评估（v5.0增强版：含市场状态标签+多空力量对比）"""
        timing_data = _compute_timing()
        return json.dumps(timing_data, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_market_timing",
        "description": "市场时机综合评估(温度+恐慌+仓位建议)。基于温度仓位矩阵(6档)和恐慌指数，给出当前市场适合的交易策略。v5.0新增市场状态标签和多空力量对比。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_market_scan() -> str:
        """获取快速市场扫描结果（v5.0新增）"""
        scan_data = _compute_market_scan()
        return json.dumps(scan_data, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_market_scan",
        "description": "快速市场扫描。v5.0新增：整合指数涨跌、涨跌家数、恐慌指数、板块轮动、资金流向的一站式市场快照。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_v4_rules_summary() -> str:
        """获取猎手v4.2.1规则摘要（v4.2升级版：含R23阈值修正/K-0520-1拐点参数）"""
        return json.dumps({
            "version": "v4.2.1",
            "updated": "2026-05-19",
            "change_log": [
                "R23-C阈值下调至65%(原70%)+涨停<25只(原30只)",
                "R23-D数据源从北向切换至Level2板块主力净流入",
                "新增K-0520-1拐点参数集(今日5/19启用)",
                "新增三期止损梯队(场景A/B/C)",
                "新增交易纪律评分系统",
            ],
            "new_rules": ["R22回暖预案", "R23假回暖识别(v4.2.1阈值修正)", "FM-032地量见底(半激活)", "R24双轨草案"],
            "ice_guards": ["R18温度<25禁止", "V10恐慌<25强空", "R19大盘确认", "V11新高不追", "R22回暖预案", "R23假回暖(v4.2.1修正)"],
            "temperature_position_matrix": [
                {"range": ">=80", "pct": 10, "label": "极度活跃"},
                {"range": "70-80", "pct": 20, "label": "活跃"},
                {"range": "50-70", "pct": 50, "label": "正常"},
                {"range": "35-50", "pct": 30, "label": "偏冷"},
                {"range": "25-35", "pct": 10, "label": "寒冷(只出不进)"},
                {"range": "<25", "pct": 0, "label": "冰封(强制空仓)"},
            ],
            "rules": {
                "R01": {"name": "涨停禁止买入", "priority": "P0"},
                "R02-v2": {"name": "5选股三阶清单+回暖子步骤", "priority": "P0"},
                "R03": {"name": "量比门槛(温度自适应)", "priority": "P1"},
                "R04": {"name": "分批止盈", "priority": "P1"},
                "R05": {"name": "单日买入<=2次", "priority": "P1"},
                "R06": {"name": "单只<=20%", "priority": "P1"},
                "R07-v2": {"name": "动态止损+回暖止损矩阵", "priority": "P1"},
                "R08-v2": {"name": "分批止盈+回暖保守止盈", "priority": "P1"},
                "R09-v2": {"name": "温度仓位矩阵", "priority": "P2"},
                "R10": {"name": "隔夜风险扫描", "priority": "P2"},
                "R11": {"name": "熔断(@-3%全清)", "priority": "P0"},
                "R18": {"name": "冰点期禁止新开", "priority": "P0"},
                "R19": {"name": "大盘三重确认", "priority": "P0"},
                "R20": {"name": "浮亏分级响应", "priority": "P1"},
                "R21": {"name": "批量建仓冷却", "priority": "P1"},
                "R22": {"name": "回暖逃生预案", "priority": "P1", "new": True},
                "R23": {"name": "假回暖识别保护", "priority": "P1", "new": True},
                "V09": {"name": "恐慌反弹减半", "priority": "P2"},
                "V10": {"name": "恐慌强制空仓", "priority": "P0"},
                "V11": {"name": "创新高不追涨", "priority": "P2"},
                "FM-032": {"name": "地量见底(半激活)", "priority": "P3", "note": "回暖期参考信号"},
            },
        }, ensure_ascii=False, indent=2)
    
    tools.append({
        "name": "get_v4_rules_summary",
        "description": "获取猎手交易系统v4.2完整规则摘要，包括6档温度仓位矩阵、R01-R23规则、V09-V11补充规则、FM-032半激活。新增R22回暖预案/R23假回暖识别。",
        "inputSchema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    })
    
    def get_recovery_plan(panic_index: float = 0, temperature: float = 50) -> str:
        """获取R22回暖逃生预案"""
        return json.dumps(
            _compute_recovery_plan(panic_index, temperature),
            ensure_ascii=False, indent=2
        )
    
    tools.append({
        "name": "get_recovery_plan",
        "description": "获取R22回暖逃生预案：当恐慌指数从<25回升时，提供分3阶段恢复的操作指南（仓位/止损/标的类型）。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "panic_index": {"type": "number", "description": "当前恐慌指数(0-100)"},
                "temperature": {"type": "number", "description": "当前市场温度(0-100)"}
            },
            "required": []
        }
    })
    
    def get_false_recovery_check(yesterday_pct: float = 0, today_pct: float = 0,
                                  vol_ratio: float = 1.0, panic_index: float = 50,
                                  breadth_up_ratio: float = None, limit_up: int = None) -> str:
        """R23假回暖检查 v4.2.1"""
        return json.dumps(
            _compute_false_recovery_check(yesterday_pct, today_pct, vol_ratio, panic_index,
                                          breadth_up_ratio, limit_up),
            ensure_ascii=False, indent=2
        )
    
    tools.append({
        "name": "get_false_recovery_check",
        "description": "R23假回暖检查(v4.2.1)：冰点期判断市场反弹是否为一日游。支持5种识别条件(含新R23-C/D阈值修正)和3项保护动作。v4.2.1: R23-C阈值下调至65%/25只, D级添加Level2主力数据。",
        "inputSchema": {
            "type": "object",
            "properties": {
                "yesterday_pct": {"type": "number", "description": "昨日涨跌幅(%)"},
                "today_pct": {"type": "number", "description": "今日当前涨跌幅(%)"},
                "vol_ratio": {"type": "number", "description": "今日成交量/前3日均量比"},
                "panic_index": {"type": "number", "description": "恐慌指数(0-100)"},
                "breadth_up_ratio": {"type": "number", "description": "上涨家数占比(%)(v4.2.1新增)"},
                "limit_up": {"type": "integer", "description": "涨停家数(v4.2.1新增)"}
            },
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

        # 涨停/跌停家数指标
        limit_down = overview_data.get("limit_down", 0)
        if limit_down > 30:
            score -= 15; reasons.append(f"跌停{limit_down}家，情绪恐慌")
        elif limit_down > 10:
            score -= 5; reasons.append(f"跌停{limit_down}家")

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


def _compute_panic() -> dict:
    """计算恐慌指数（提取自tool定义，供handlers共用）"""
    enhanced = _get_market_sentiment_enhanced()
    score = enhanced.get("market_sentiment_score", 50)
    panic_idx = max(0, min(100, 100 - score))
    
    if panic_idx >= 60:
        label = "安全"
    elif panic_idx >= 40:
        label = "谨慎"
    elif panic_idx >= 25:
        label = "偏冷"
    elif panic_idx >= 10:
        label = "冰点"
    else:
        label = "恐慌"
    
    return {
        "panic_index": panic_idx,
        "label": label,
        "reasons": enhanced.get("reasons", []),
        "timestamp": enhanced.get("timestamp", ""),
        "version": "v5.0",
    }


def _compute_timing() -> dict:
    """计算市场时机（提取自tool定义，供handlers共用）"""
    enhanced = _get_market_sentiment_enhanced()
    score = enhanced.get("market_sentiment_score", 50)
    panic_idx = max(0, min(100, 100 - score))
    
    if score >= 80:
        max_pos, temp_label = 10, "极度活跃"
    elif score >= 70:
        max_pos, temp_label = 20, "活跃"
    elif score >= 50:
        max_pos, temp_label = 50, "正常"
    elif score >= 35:
        max_pos, temp_label = 30, "偏冷"
    elif score >= 25:
        max_pos, temp_label = 10, "寒冷"
    else:
        max_pos, temp_label = 0, "冰封"
    
    if panic_idx < 25 or score < 25:
        advice = "强制空仓，禁止所有开仓操作"
        market_state = "V10恐慌禁入"
    elif score < 35:
        advice = "冰点期，禁止新开仓，仅可减仓"
        market_state = "R18冰点禁止"
    elif panic_idx < 40:
        advice = "偏冷谨慎，最高10%仓位"
        market_state = "偏冷谨慎"
    elif score >= 70:
        advice = "过热注意风险，建议降仓"
        market_state = "过热预警"
    else:
        advice = "正常交易，控制仓位在建议范围内"
        market_state = "正常交易"
    
    return {
        "market_temperature": score,
        "temperature_label": temp_label,
        "panic_index": panic_idx,
        "max_position_pct": max_pos,
        "trade_advice": advice,
        "market_state": market_state,
        "reasons": enhanced.get("reasons", []),
        "top_sector": (enhanced.get("sector_flow") or [None])[0] if enhanced.get("sector_flow") else None,
        "version": "v5.0",
        "timestamp": enhanced.get("timestamp", ""),
    }


def _compute_market_scan() -> dict:
    """快速市场扫描（一站式市场快照）"""
    from src.data_service import data_service
    
    try:
        timing = _compute_timing()
        indices = data_service.get_index_quotes()
        overview = data_service.get_market_overview()
        sector_flow = data_service.get_sector_money_flow()
        
        index_data = indices.get("data", [])
        overview_data = overview.get("data", {})
        sector_data = sector_flow.get("data", [])[:5]
        
        # 计算多空力量
        rising = overview_data.get("rising", 0)
        falling = overview_data.get("falling", 0)
        total = overview_data.get("total", 1) or 1
        
        if total > 0:
            up_ratio = round(rising / total * 100, 1)
            down_ratio = round(falling / total * 100, 1)
        else:
            up_ratio = down_ratio = 0
        
        return {
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "market_temperature": timing["market_temperature"],
            "temperature_label": timing["temperature_label"],
            "panic_index": timing["panic_index"],
            "panic_label": timing.get("market_state", "未知"),
            "max_position_pct": timing["max_position_pct"],
            "indices": index_data[:6],
            "breadth": {
                "rising": rising,
                "falling": falling,
                "flat": overview_data.get("flat", 0),
                "limit_up": overview_data.get("limit_up", 0),
                "limit_down": overview_data.get("limit_down", 0),
                "up_ratio_pct": up_ratio,
                "down_ratio_pct": down_ratio,
            },
            "top_sectors": sector_data,
            "version": "v5.0",
        }
    except Exception as e:
        logger.error(f"市场扫描失败: {e}")
        return {
            "error": str(e),
            "version": "v5.0",
            "scan_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        }


def _compute_recovery_plan(panic_index: float, temperature: float) -> dict:
    """R22回暖逃生预案 — 恐慌从冰点回升后的入场规划 (v4.2.1 + K-0520-1)
    
    当恐慌指数<25时提供回暖后分阶段恢复预案
    K-0520-1: 今日(5/19)拐点#1启用的专用参数集
    """
    if panic_index >= 25:
        return {
            "panic_index": panic_index,
            "temperature": temperature,
            "recovery_plan": "未激活",
            "reason": "恐慌指数>=25，当前非冰点状态",
            "note": "R22回暖预案仅在恐慌<25期间生效",
            "version": "v4.2.1"
        }
    
    return {
        "panic_index": panic_index,
        "temperature": temperature,
        "recovery_plan": "已准备",
        "market_state": "冰点",
        "k_param_set": "K-0520-1",
        "k_param_date": "2026-05-19 拐点#1",
        "phases": [
            {
                "phase": 1,
                "week": "第1周(回暖确认期)",
                "max_position_pct": 20,
                "max_single_pct": 10,
                "stop_loss_pct": -2.5,
                "take_profit_pct": [3, 5, 8],
                "allowed_types": "防御型(银行/公用事业/消费龙头)",
                "extra_conditions": "信号需3日主力净流入验证; 首次买入设追踪止损; K-0520-1成交量倍数1.3(收紧)"
            },
            {
                "phase": 2,
                "week": "第2周(稳定期)",
                "max_position_pct": 35,
                "stop_loss_pct": -3.0,
                "take_profit_pct": [3, 6, 10],
                "extra_conditions": "可适度参与反弹主线; K-0520-1最大持仓天数3天"
            },
            {
                "phase": 3,
                "week": "第3周(恢复期)",
                "max_position_pct": 50,
                "extra_conditions": "按R09-v2温度仓位矩阵正常操作; 止损恢复-3.0%标准"
            }
        ],
        "entry_conditions": [
            "恐慌连续2日 > 25",
            "上证指数当日收涨",
            "上涨家数 > 下跌家数",
            "当日无重大利空事件",
        ],
        "capital_allocation": {
            "D0_回暖确认日": {"action": "仅确认信号，不交易", "position": 0},
            "D1_验证日": {"action": "恐慌>25连续2日，买入10%", "position": 10, "amount": "≈¥7,400"},
            "D2_验证通过": {"action": "恐慌>25+上证收涨，买入15%", "position": 15, "amount": "≈¥11,100"},
            "D+1week": {"action": "恐慌>35稳定，买入20-25%", "position": "20-25"}
        },
        "version": "v4.2.1"
    }


def _compute_false_recovery_check(yesterday_pct: float, today_pct: float, vol_ratio: float, panic_index: float,
                                    breadth_up_ratio: float = None, limit_up: int = None) -> dict:
    """R23假回暖检查 (v4.2.1 阈值修正) — 防止追入冰点一日游反弹
    
    v4.2.1变更:
    - 条件C阈值: 上涨家数>65%(原70%) + 涨停<25只(原30只)
    - v4.2原有的4条件保持, 新增R23-C/D
    """
    alerts = []
    if panic_index >= 25:
        return {"active": False, "reason": "非冰点状态", "alerts": [], "version": "v4.2.1"}
    
    # 条件A：昨日涨今日跌的快速反转
    if yesterday_pct > 0.5 and today_pct < -0.5:
        alerts.append({
            "type": "A_QUICK_REVERSAL",
            "severity": "\U0001f534 高危",
            "signal": "快速反转 — 昨日涨今日跌",
            "detail": f"冰点期昨日{yesterday_pct:+.1f}%今日{today_pct:+.1f}%，一日游反弹"
        })
    
    # 条件B：放量不涨（虚涨）
    if vol_ratio > 1.5 and abs(today_pct) < 0.3:
        alerts.append({
            "type": "B_VOLUME_STAGNATION",
            "severity": "\U0001f7e1 谨慎",
            "signal": "放量滞涨",
            "detail": f"成交量放大{vol_ratio:.1f}倍但涨幅仅{today_pct:.2f}%，非真实回暖"
        })
    
    # 条件C：单日强力反弹
    if today_pct > 1.5 and vol_ratio < 0.8:
        alerts.append({
            "type": "C_POWER_RALLY",
            "severity": "\U0001f7e1 谨慎",
            "signal": "强力反弹但量能不足",
            "detail": f"涨幅{today_pct:.1f}%但成交量缩至均量的{vol_ratio*100:.0f}%，假回暖特征"
        })
    
    # 条件D (v4.2.1: 阈值下调): 上涨家数>65%但涨停<25只(虚涨)
    if breadth_up_ratio is not None and limit_up is not None:
        if breadth_up_ratio > 65 and limit_up < 25:
            alerts.append({
                "type": "D_VIRTUAL_RISE_v421",
                "severity": "\U0001f7e1 谨慎",
                "signal": f"虚涨(v4.2.1阈值): 上涨占比{breadth_up_ratio:.0f}%涨停{limit_up}只",
                "detail": f"上涨占比{breadth_up_ratio:.0f}% > 65%但涨停仅{limit_up}只 < 25只，虚涨假回暖"
            })
    
    return {
        "active": len(alerts) > 0,
        "panic_index": panic_index,
        "v421": True,
        "alerts": alerts,
        "protection_actions": [
            "维持空仓或仓位上限≤15%",
            "冷却≥3交易日再评估",
            "首次买入盈利后立即设追踪止损"
        ] if alerts else ["无预警，正常观察"],
        "r23_note": "v4.2.1: R23-C阈值下调至65%/25只; R23-D切换至Level2主力净流入",
        "version": "v4.2.1"
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
    handlers["get_etf_money_flow"] = lambda args: data_service.get_etf_money_flow(
        args.get("indicator", "今日")
    )
    handlers["get_futures_basis"] = lambda args: data_service.get_futures_basis()
    handlers["get_sector_money_flow_ratio"] = lambda args: data_service.get_sector_money_flow_ratio(
        args.get("limit", 20)
    )
    
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
    
    # v4.0/v5.0新工具（使用共享计算函数消除重复逻辑）
    handlers["get_panic_index"] = lambda args: _compute_panic()
    handlers["get_market_timing"] = lambda args: _compute_timing()
    handlers["get_market_scan"] = lambda args: _compute_market_scan()
    handlers["get_v4_rules_summary"] = lambda args: {
        "version": "v4.2", "updated": "2026-05-18", 
        "rules_count": 25, 
        "active_rules": "R01-R23 + V01-V11 + FM系列",
        "new_rules": "R22回暖逃生预案, R23假回暖识别, FM-032地量见底(半激活)",
        "note": "v4.2新增回暖期入场/仓位/止损全流程; 6道冰点防护+回暖预案+假回暖识别"
    }
    handlers["get_recovery_plan"] = lambda args: _compute_recovery_plan(
        args.get("panic_index", 0), args.get("temperature", 50)
    )
    handlers["get_false_recovery_check"] = lambda args: _compute_false_recovery_check(
        args.get("yesterday_pct", 0), args.get("today_pct", 0),
        args.get("vol_ratio", 1.0), args.get("panic_index", 0),
        args.get("breadth_up_ratio"), args.get("limit_up")
    )
    
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
    """带降级逻辑的handler调用（增强错误日志）
    
    1. 正常调用
    2. 失败后重试1次
    3. 返回降级结果
    """
    # 获取handler名字信息，方便日志追溯
    handler_name = getattr(handler, '__name__', None)
    if handler_name is None or handler_name == '<lambda>':
        # 尝试从闭包或内部查找
        handler_name = str(handler)[:80]
    
    try:
        return handler(args)
    except Exception as e:
        logger.warning(f"handler调用失败(首次): name={handler_name}, args={json.dumps(args, ensure_ascii=False)[:200]}, error={e}")
        # 重试一次
        try:
            logger.info(f"handler重试: name={handler_name}")
            return handler(args)
        except Exception as e2:
            logger.error(f"handler调用失败(重试后): name={handler_name}, args={json.dumps(args, ensure_ascii=False)[:200]}, error={e2}")
            return {
                "error": str(e2),
                "error_type": type(e2).__name__,
                "handler_name": handler_name,
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
                "version": "1.1.0"
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
                        "serverInfo": {"name": "mcp-data-server", "version": "1.1.0"}
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
