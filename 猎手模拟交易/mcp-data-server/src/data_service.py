"""
数据服务核心模块
封装AKShare数据源
"""

import json
import time
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta

import akshare as ak
import pandas as pd

from .cache_manager import cache_manager, CacheManager

logger = logging.getLogger(__name__)


class DataService:
    """数据服务核心类"""
    
    # 指数代码映射
    INDEX_CODES = {
        "上证指数": "000001",
        "深证成指": "399001", 
        "创业板指": "399006",
        "科创50": "000688",
        "沪深300": "000300",
        "上证50": "000016",
        "中证500": "000905",
        "中证1000": "000852"
    }
    
    def __init__(self):
        self.cache = cache_manager
        self._rate_limit_delay = 0.5  # 请求间隔(秒)
        self._last_request_time = 0
    
    def _rate_limit(self):
        """简单的频率限制"""
        now = time.time()
        elapsed = now - self._last_request_time
        if elapsed < self._rate_limit_delay:
            time.sleep(self._rate_limit_delay - elapsed)
        self._last_request_time = time.time()
    
    def _to_json_serializable(self, obj):
        """转换为JSON可序列化格式"""
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        if isinstance(obj, pd.Series):
            return obj.to_dict()
        if isinstance(obj, (datetime, pd.Timestamp)):
            return str(obj)
        if hasattr(obj, 'item'):  # numpy types
            return obj.item()
        return obj
    
    def _safe_call(self, func, *args, **kwargs) -> Optional[Dict]:
        """安全的函数调用，带错误处理"""
        try:
            self._rate_limit()
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.error(f"数据获取失败: {func.__name__} - {str(e)}")
            return {"error": str(e), "function": func.__name__}
    
    # ==================== 实时行情 ====================
    
    def get_realtime_quote(self, symbol: str) -> Dict:
        """获取单个股票实时行情"""
        cache_key = self.cache.get_realtime_key(symbol)
        
        # 检查缓存
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        # 获取数据
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            df = ak.stock_zh_a_spot_em()
            
            # 筛选目标股票
            stock = df[df['代码'] == symbol_norm]
            
            if stock.empty:
                return {"error": f"股票代码 {symbol_norm} 不存在"}
            
            data = stock.iloc[0].to_dict()
            
            # 缓存
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取实时行情失败: {symbol} - {e}")
            return {"error": str(e)}
    
    def get_realtime_quotes_batch(self, symbols: List[str]) -> Dict:
        """批量获取股票实时行情"""
        results = []
        errors = []
        
        for symbol in symbols:
            result = self.get_realtime_quote(symbol)
            if "error" in result:
                errors.append({"symbol": symbol, "error": result["error"]})
            else:
                results.append(result["data"])
        
        return {
            "data": results,
            "errors": errors,
            "total": len(symbols),
            "success": len(results)
        }
    
    def get_index_quotes(self) -> Dict:
        """获取主要指数行情"""
        cache_key = self.cache.make_key("market", "index", "main")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_zh_index_spot_em()
            
            # 筛选主要指数
            index_codes = list(self.INDEX_CODES.values())
            indices = df[df['代码'].isin(index_codes)]
            
            data = indices.to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取指数行情失败: {e}")
            return {"error": str(e)}
    
    def get_market_overview(self) -> Dict:
        """获取市场概览"""
        cache_key = self.cache.make_key("market", "overview")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_zh_a_spot_em()
            
            # 统计涨跌停
            limit_up = len(df[df['涨跌幅'] >= 9.9])
            limit_down = len(df[df['涨跌幅'] <= -9.9])
            rising = len(df[df['涨跌幅'] > 0])
            falling = len(df[df['涨跌幅'] < 0])
            flat = len(df[df['涨跌幅'] == 0])
            
            data = {
                "total": len(df),
                "limit_up": limit_up,
                "limit_down": limit_down,
                "rising": rising,
                "falling": falling,
                "flat": flat,
                "update_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取市场概览失败: {e}")
            return {"error": str(e)}
    
    # ==================== K线数据 ====================
    
    def get_daily_kline(self, symbol: str, start_date: str = None, end_date: str = None, 
                        adjust: str = "qfq") -> Dict:
        """获取日K线数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        cache_key = self.cache.get_kline_key(symbol, "daily", adjust)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            
            if adjust == "qfq":
                df = ak.stock_zh_a_hist(symbol_norm, period="daily", 
                                        start_date=start_date, end_date=end_date,
                                        adjust="qfq")
            else:
                df = ak.stock_zh_a_hist(symbol_norm, period="daily",
                                        start_date=start_date, end_date=end_date,
                                        adjust="hfq")
            
            data = df.to_dict(orient='records')
            
            # 转换为标准格式
            for item in data:
                if '日期' in item:
                    item['date'] = item.pop('日期')
                if '开盘' in item:
                    item['open'] = item.pop('开盘')
                if '收盘' in item:
                    item['close'] = item.pop('收盘')
                if '最高' in item:
                    item['high'] = item.pop('最高')
                if '最低' in item:
                    item['low'] = item.pop('最低')
                if '成交量' in item:
                    item['volume'] = item.pop('成交量')
                if '成交额' in item:
                    item['amount'] = item.pop('成交额')
                if '涨跌幅' in item:
                    item['pct_change'] = item.pop('涨跌幅')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_KLINE)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取日K线失败: {symbol} - {e}")
            return {"error": str(e)}
    
    def get_weekly_kline(self, symbol: str, start_date: str = None, 
                         end_date: str = None) -> Dict:
        """获取周K线数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365*2)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        cache_key = self.cache.get_kline_key(symbol, "weekly")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            df = ak.stock_zh_a_hist(symbol_norm, period="weekly",
                                    start_date=start_date, end_date=end_date)
            
            data = df.to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_KLINE)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取周K线失败: {symbol} - {e}")
            return {"error": str(e)}
    
    def get_minute_kline(self, symbol: str, period: str = "5") -> Dict:
        """获取分钟K线数据
        
        Args:
            symbol: 股票代码
            period: 周期 (1/5/15/30/60)
        """
        cache_key = self.cache.make_key("market", "kline", "minute", 
                                        self.cache.hash_symbol(symbol), period)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            df = ak.stock_zh_a_hist_min(symbol_norm, period=period,
                                       start_date="2024-01-01", adjust="qfq")
            
            data = df.tail(100).to_dict(orient='records')  # 最近100条
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_KLINE_MINUTE)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取分钟K线失败: {symbol} - {e}")
            return {"error": str(e)}
    
    # ==================== 资金流向 ====================
    
    def get_money_flow(self, symbol: str) -> Dict:
        """获取个股资金流向"""
        cache_key = self.cache.get_fund_key(symbol)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            df = ak.stock_individual_fund_flow(stock=symbol_norm, indicator="主力")
            
            data = df.head(10).to_dict(orient='records')  # 最近10个交易日
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取资金流向失败: {symbol} - {e}")
            return {"error": str(e)}
    
    def get_north_money(self, period: str = "daily") -> Dict:
        """获取北向资金数据"""
        cache_key = self.cache.make_key("fund", "north", period)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_hsgt_north_net_flow_in(indicator=period)
            
            data = df.head(20).to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取北向资金失败: {e}")
            return {"error": str(e)}
    
    def get_sector_money_flow(self) -> Dict:
        """获取板块资金流向"""
        cache_key = self.cache.make_key("fund", "sector", "all")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_sector_fund_flow_rank(indicator="今日")
            
            data = df.to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取板块资金流向失败: {e}")
            return {"error": str(e)}
    
    # ==================== 财务数据 ====================
    
    def get_financial_report(self, symbol: str, report_type: str = "annual") -> Dict:
        """获取财务报表"""
        cache_key = self.cache.get_financial_key(symbol, report_type)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            
            if report_type == "annual":
                df = ak.stock_financial_analysis_indicator(symbol_norm, start_year="2020")
            else:
                df = ak.stock_financial_analysis_indicator(symbol_norm, start_year="2020")
            
            data = df.head(8).to_dict(orient='records')  # 最近8期
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_FINANCIAL)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取财务报表失败: {symbol} - {e}")
            return {"error": str(e)}
    
    def get_roe_data(self, symbol: str) -> Dict:
        """获取ROE数据"""
        result = self.get_financial_report(symbol, "annual")
        
        if "error" in result:
            return result
        
        # 提取ROE列
        data = result.get("data", [])
        roe_data = []
        
        for item in data:
            roe_item = {
                "date": item.get("日期", ""),
                "roe": item.get("净资产收益率(%)", ""),
                "roe_avg": item.get("平均净资产收益率(%)", ""),
                "gross_margin": item.get("销售毛利率(%)", ""),
                "net_margin": item.get("销售净利率(%)", "")
            }
            roe_data.append(roe_item)
        
        return {"data": roe_data, "source": result.get("source")}
    
    def get_pe_pb(self, symbol: str) -> Dict:
        """获取PE/PB数据"""
        cache_key = self.cache.make_key("financial", "pepb", self.cache.hash_symbol(symbol))
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        try:
            self._rate_limit()
            df = ak.stock_a_indicator_lg(symbol_norm)
            
            if df.empty:
                return {"error": f"无法获取 {symbol} 的PE/PB数据"}
            
            data = df.tail(1).iloc[0].to_dict()
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_FINANCIAL)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取PE/PB失败: {symbol} - {e}")
            return {"error": str(e)}
    
    # ==================== 板块数据 ====================
    
    def get_sector_list(self, sector_type: str = "industry") -> Dict:
        """获取板块列表"""
        cache_key = self.cache.get_sector_key(sector_type)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            
            if sector_type == "industry":
                df = ak.stock_board_industry_name_em()
            else:
                df = ak.stock_board_concept_name_em()
            
            data = df.to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_SECTOR)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取板块列表失败: {sector_type} - {e}")
            return {"error": str(e)}
    
    def get_hot_sectors(self, limit: int = 10) -> Dict:
        """获取热门板块"""
        cache_key = self.cache.make_key("sector", "hot", limit)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_sector_fund_flow_rank(indicator="今日")
            
            data = df.head(limit).to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取热门板块失败: {e}")
            return {"error": str(e)}
    
    def get_sector_stocks(self, sector_name: str) -> Dict:
        """获取板块成分股"""
        cache_key = self.cache.make_key("sector", "stocks", sector_name)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            
            # 先获取板块列表找到代码
            df_list = ak.stock_board_industry_name_em()
            board = df_list[df_list['板块名称'] == sector_name]
            
            if board.empty:
                return {"error": f"板块 {sector_name} 不存在"}
            
            board_code = board.iloc[0]['板块代码']
            
            # 获取成分股
            self._rate_limit()
            df = ak.stock_board_industry_cons_em(symbol=board_code)
            
            data = df.to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_FINANCIAL)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取板块成分股失败: {sector_name} - {e}")
            return {"error": str(e)}
    
    def get_sector_quotes(self, sector_name: str) -> Dict:
        """获取板块行情"""
        cache_key = self.cache.make_key("sector", "quote", sector_name)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            
            df_list = ak.stock_board_industry_name_em()
            board = df_list[df_list['板块名称'] == sector_name]
            
            if board.empty:
                return {"error": f"板块 {sector_name} 不存在"}
            
            board_code = board.iloc[0]['板块代码']
            
            self._rate_limit()
            df = ak.stock_board_industry_hist_em(symbol=board_code, period="日k", 
                                                  start_date="20240101", end_date="20251231")
            
            data = df.tail(30).to_dict(orient='records')
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取板块行情失败: {sector_name} - {e}")
            return {"error": str(e)}
    
    # ==================== 市场情绪 ====================
    
    def get_market_sentiment(self) -> Dict:
        """获取市场情绪指标"""
        cache_key = self.cache.make_key("market", "sentiment")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            # 涨跌家数
            overview = self.get_market_overview()
            
            # 恐慌贪婪指数 (如果有)
            fear_greed = None
            try:
                self._rate_limit()
                fg = ak.quantitative_market_bar(indicator="恐慌指数")
                if fg is not None and not fg.empty:
                    fear_greed = fg.iloc[-1].to_dict() if hasattr(fg.iloc[-1], 'to_dict') else None
            except:
                pass
            
            # 外资动向
            north = self.get_north_money("daily")
            
            data = {
                "overview": overview.get("data") if "data" in overview else {},
                "north_money": north.get("data") if "data" in north else [],
                "fear_greed": fear_greed,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取市场情绪失败: {e}")
            return {"error": str(e)}


# 全局数据服务实例
data_service = DataService()
