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
    
    @staticmethod
    def _validate_date(date_str: str, field_name: str = "date") -> str:
        """验证并格式化日期字符串
        
        Args:
            date_str: 日期字符串（YYYYMMDD 或 YYYY-MM-DD）
            field_name: 字段名（用于错误消息）
        
        Returns:
            标准化的 YYYYMMDD 格式日期
        """
        if not date_str:
            raise ValueError(f"{field_name} 不能为空")
        
        date_str = date_str.replace("-", "").replace("/", "")
        
        if len(date_str) != 8 or not date_str.isdigit():
            raise ValueError(f"{field_name} 格式无效: {date_str}，需要 YYYYMMDD")
        
        year = int(date_str[:4])
        month = int(date_str[4:6])
        day = int(date_str[6:8])
        
        if year < 1990 or year > 2100:
            raise ValueError(f"{field_name} 年份超出范围: {year}")
        if month < 1 or month > 12:
            raise ValueError(f"{field_name} 月份超出范围: {month}")
        if day < 1 or day > 31:
            raise ValueError(f"{field_name} 日期超出范围: {day}")
        
        return date_str

    def get_daily_kline(self, symbol: str, start_date: str = None, end_date: str = None, 
                        adjust: str = "qfq") -> Dict:
        """获取日K线数据"""
        if start_date is None:
            start_date = (datetime.now() - timedelta(days=365)).strftime("%Y%m%d")
        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        
        # 日期范围验证
        try:
            start_date = self._validate_date(start_date, "start_date")
            end_date = self._validate_date(end_date, "end_date")
        except ValueError as ve:
            return {"error": str(ve), "function": "get_daily_kline"}
        
        # 验证日期范围
        start_dt = datetime.strptime(start_date, "%Y%m%d")
        end_dt = datetime.strptime(end_date, "%Y%m%d")
        if end_dt < start_dt:
            return {"error": "end_date 不能早于 start_date", "function": "get_daily_kline"}
        if (end_dt - start_dt).days > 365 * 5:
            logger.warning(f"日期范围超过5年({(end_dt - start_dt).days}天)，可能影响性能")
        
        cache_key = self.cache.get_kline_key(symbol, "daily", adjust)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        symbol_norm = self.cache.hash_symbol(symbol)
        
        # 降级链：依次尝试多种数据源
        fallback_errors = []
        
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
            fallback_errors.append(str(e))
            logger.error(f"获取日K线失败(主源): {symbol} - {e}")
            
            # 降级1：尝试不复权
            try:
                self._rate_limit()
                logger.info(f"降级获取不复权K线: {symbol}")
                df = ak.stock_zh_a_hist(symbol_norm, period="daily",
                                        start_date=start_date, end_date=end_date)
                data = df.to_dict(orient='records')
                self.cache.cache.set(cache_key, data, CacheManager.TTL_KLINE)
                return {"data": data, "source": "akshare", "note": "降级使用不复权数据"}
            except Exception as e2:
                fallback_errors.append(str(e2))
                
                # 降级2：尝试东方财富接口
                try:
                    self._rate_limit()
                    logger.info(f"降级使用东方财富K线: {symbol}")
                    df = ak.stock_zh_a_hist(symbol_norm, period="daily",
                                            start_date=start_date, end_date=end_date,
                                            adjust="")
                    data = df.to_dict(orient='records')
                    return {"data": data, "source": "akshare_alt", "note": "降级使用备用接口"}
                except Exception as e3:
                    fallback_errors.append(str(e3))
        
        return {"error": "所有数据源均失败", "fallback_errors": fallback_errors}
    
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
    
    # ==================== ETF资金流向 ====================
    
    def get_etf_money_flow(self, indicator: str = "今日") -> Dict:
        """获取ETF资金流向排名
        
        V07规则：ETF资金流向（科技ETF连续净申购→增量信号）
        使用ETF每日净值/市价数据，按增长率和折价率排序。
        
        Args:
            indicator: 时间指标 今日/3日/5日（3日/5日使用缓存数据加推定）
        
        Returns:
            按涨幅排序的ETF数据，可筛选科技/半导体类ETF观测资金流向
        """
        cache_key = self.cache.make_key("fund", "etf", indicator)
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            # 东方财富-ETF每日净值/场地基金数据
            df = ak.fund_etf_fund_daily_em()
            
            if df is None or df.empty:
                return {"error": "ETF数据为空", "indicator": indicator}
            
            # 解析增长率列，排序取前30
            records = df.to_dict(orient='records')
            
            # 解析数值
            for r in records:
                try:
                    gr = str(r.get("增长率", "0%")).replace("%", "").strip()
                    r["_growth_rate_pct"] = float(gr) if gr else 0.0
                except (ValueError, TypeError):
                    r["_growth_rate_pct"] = 0.0
            
            # 按增长率排序
            records.sort(key=lambda x: x.get("_growth_rate_pct", 0), reverse=True)
            
            # 标记科技类ETF（按名称关键词）
            tech_keywords = ["科技", "半导体", "芯片", "AI", "人工智能", "信息", "通信", 
                           "计算机", "电子", "科创", "创新", "数字", "软件", "互联", "新兴"]
            for r in records:
                name = str(r.get("基金简称", ""))
                r["_is_tech"] = any(kw in name for kw in tech_keywords)
            
            data = records[:50]  # 返回前50
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {
                "data": data,
                "source": "akshare",
                "indicator": indicator,
                "note": "V07规则: 使用ETF增长率排序近似资金流向；科技类ETF已标记(_is_tech)",
                "total_etf_count": len(records)
            }
        except Exception as e:
            logger.error(f"获取ETF资金流向失败({indicator}): {e}")
            return {"error": str(e), "indicator": indicator}
    
    # ==================== 期指基差 ====================
    
    def get_futures_basis(self) -> Dict:
        """获取沪深300期指基差数据
        
        V06规则：期指基差信号（沪深300升水>20乐观/贴水>20谨慎）
        获取沪深300现货与期货的价差（基差），用于判断市场情绪。
        
        Returns:
            dict with basis data or fallback structured response
        """
        cache_key = self.cache.make_key("market", "futures", "basis")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        # 降级：通过 trade_state.json 获取
        try:
            fallback = self._get_futures_basis_fallback()
            if any(fb.get("basis") is not None for fb in fallback):
                self.cache.cache.set(cache_key, fallback, CacheManager.TTL_REAL_TIME)
                return {
                    "data": fallback,
                    "source": "trade_state_json",
                    "note": "使用盘后结算数据"
                }
        except Exception as e:
            logger.warning(f"获取期指基差降级数据失败: {e}")
        
        # 再降级：用CSI300指数数据构建结构化响应
        try:
            self._rate_limit()
            csi_df = ak.stock_zh_index_spot_em()
            csi = csi_df[csi_df['代码'] == '000300']
            
            if not csi.empty:
                row = csi.iloc[0]
                spot_price = float(row.get('最新价', 0))
                pct_chg = float(row.get('涨跌幅', 0))
                # 推定基差（没有期货数据时返回基础信息）
                data = [{
                    "index_name": "沪深300",
                    "index_code": "000300",
                    "spot_price": spot_price,
                    "spot_change_pct": pct_chg,
                    "futures_price": None,
                    "basis": None,
                    "basis_pct": None,
                    "signal": "unknown",
                    "csi300_spot": True,
                    "note": "仅获取到现货数据，期货基差需手动查询",
                    "timestamp": datetime.now().isoformat()
                }]
                self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
                return {
                    "data": data,
                    "source": "akshare_spot_only",
                    "note": "仅获取到沪深300现货数据，无实时期货基差"
                }
        except Exception as e:
            logger.warning(f"获取CSI300现货数据失败: {e}")
        
        # 最终降级：纯结构化响应
        now = datetime.now()
        fallback_data = [{
            "symbol": "IF",
            "contract": "IF当月",
            "spot_price": None,
            "futures_price": None,
            "basis": None,
            "basis_pct": None,
            "signal": "unknown",
            "note": "所有数据源均不可用，建议手动查询期指基差",
            "timestamp": now.isoformat(),
            "recommendation": "沪深300期货基差可通过东方财富/同花顺/中金所官网查询"
        }]
        
        return {
            "data": fallback_data,
            "source": "none",
            "error": "无法获取期指基差数据",
            "fallback": True,
            "timestamp": now.isoformat()
        }
    
    def _get_futures_basis_fallback(self) -> List[Dict]:
        """降级获取期指基差数据
        
        尝试读取本地 trade_state.json 缓存文件。
        若均不可用，返回结构化降级信息。
        """
        import os
        state_paths = [
            "/root/.openclaw/workspace/data/trade_state.json",
            "data/trade_state.json",
            "/tmp/trade_state.json"
        ]
        
        for path in state_paths:
            try:
                if os.path.exists(path):
                    with open(path, 'r', encoding='utf-8') as f:
                        state_data = json.load(f)
                    if isinstance(state_data, dict) and "futures_basis" in state_data:
                        return state_data["futures_basis"]
            except Exception:
                continue
        
        # 结构化降级响应
        now = datetime.now()
        return [{
            "symbol": "IF",
            "contract": "IF当月",
            "spot_price": None,
            "futures_price": None,
            "basis": None,
            "basis_pct": None,
            "signal": "unknown",
            "note": "数据源不可用，建议手动查询期指基差",
            "timestamp": now.isoformat(),
            "recommendation": "沪深300期货基差可通过东方财富/同花顺手动查询"
        }]
    
    # ==================== 板块主力净流入率 ====================
    
    def get_sector_money_flow_ratio(self, limit: int = 20) -> Dict:
        """获取板块主力净流入率
        
        V05规则：板块主力净流入率 = 板块主力净流入 / 板块成交额 * 100%
        这是get_sector_money_flow的增强版本，添加了主力净流入率计算。
        
        Args:
            limit: 返回板块数量，默认20
        
        Returns:
            带主力净流入率的板块资金流排名
        """
        cache_key = self.cache.make_key("fund", "sector", "ratio", str(limit))
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            self._rate_limit()
            df = ak.stock_sector_fund_flow_rank(indicator="今日")
            
            if df is None or df.empty:
                return {"error": "板块资金流数据为空"}
            
            # 计算主力净流入率
            records = df.to_dict(orient='records')
            enhanced = []
            for record in records[:limit]:
                try:
                    money_flow = float(record.get("主力净流入", 0) or 0)
                    turnover = float(record.get("成交额", 1) or 0)
                    
                    if turnover > 0:
                        net_flow_ratio = round(money_flow / turnover * 100, 2)
                    else:
                        net_flow_ratio = 0.0
                except (ValueError, TypeError):
                    money_flow = 0
                    turnover = 0
                    net_flow_ratio = 0.0
                
                enhanced.append({
                    **record,
                    "主力净流入率_v05": net_flow_ratio,
                    "interpretation": (
                        "高流入" if net_flow_ratio > 0.5 else
                        "中等流入" if net_flow_ratio > 0.1 else
                        "微流入" if net_flow_ratio > 0 else
                        "净流出"
                    )
                })
            
            self.cache.cache.set(cache_key, enhanced, CacheManager.TTL_REAL_TIME)
            
            return {
                "data": enhanced,
                "source": "akshare",
                "note": "V05规则: 主力净流入率 = 主力净流入 / 成交额 * 100%"
            }
        except Exception as e:
            logger.error(f"获取板块主力净流入率失败: {e}")
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
    
    # ==================== 选股筛选 (v2.1新增) ====================
    
    def screen_stocks(self, filters: Dict = None) -> Dict:
        """多条件选股筛选器 v2.1
        
        Args:
            filters: 筛选条件字典
                - min_pe: 最低PE (默认0)
                - max_pe: 最高PE (默认100)
                - min_pb: 最低PB (默认0)
                - max_pb: 最高PB (默认10)
                - min_roe: 最低ROE (默认0)
                - max_market_cap: 最高市值(亿, 默认10000)
                - sector: 板块名称 (可选)
                - limit: 返回数量 (默认20)
                - sort_by: 排序字段 (默认'pe_ttm')
        
        Returns:
            筛选结果列表
        """
        if filters is None:
            filters = {}
        
        min_pe = filters.get('min_pe', 0)
        max_pe = filters.get('max_pe', 100)
        min_pb = filters.get('min_pb', 0)
        max_pb = filters.get('max_pb', 10)
        min_roe = filters.get('min_roe', 0)
        max_market_cap = filters.get('max_market_cap', 10000)
        sector_name = filters.get('sector', '')
        limit = filters.get('limit', 20)
        sort_by = filters.get('sort_by', 'pe_ttm')
        
        cache_key = self.cache.make_key('screen', 'stocks', 
            f'pe{min_pe}-{max_pe}_pb{min_pb}-{max_pb}_roe{min_roe}_cap{max_market_cap}_{sector_name}_{sort_by}_{limit}')
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {'data': cached, 'source': 'cache'}
        
        try:
            self._rate_limit()
            # 获取全市场数据
            df = ak.stock_zh_a_spot_em()
            
            if df is None or df.empty:
                return {'error': '无法获取全市场数据'}
            
            # 基础过滤
            df = df[
                (df['市盈率-动态'].astype(float) >= min_pe) &
                (df['市盈率-动态'].astype(float) <= max_pe) &
                (df['市净率'].astype(float) >= min_pb) &
                (df['市净率'].astype(float) <= max_pb) &
                (df['总市值'].astype(float) / 1e8 <= max_market_cap)
            ]
            
            # ROE过滤(需要单独获取，此处用近似: 市净率相关)
            if min_roe > 0:
                df = df[df['市净率'].astype(float) > 0.5]  # PB>0.5作为ROE>0的近似
            
            # 排序
            if sort_by == 'pe_ttm':
                df = df.sort_values('市盈率-动态', ascending=True)
            elif sort_by == 'pb':
                df = df.sort_values('市净率', ascending=True)
            elif sort_by == 'volume':
                df = df.sort_values('成交额', ascending=False)
            elif sort_by == 'change_pct':
                df = df.sort_values('涨跌幅', ascending=False)
            
            records = df.head(limit).to_dict(orient='records')
            
            # 简化输出
            result = []
            for r in records:
                result.append({
                    'code': str(r.get('代码', '')),
                    'name': str(r.get('名称', '')),
                    'price': float(r.get('最新价', 0)),
                    'pe_ttm': float(r.get('市盈率-动态', 0)),
                    'pb': float(r.get('市净率', 0)),
                    'market_cap_yi': round(float(r.get('总市值', 0)) / 1e8, 1),
                    'chg_pct': float(r.get('涨跌幅', 0)),
                    'turnover_yi': round(float(r.get('成交额', 0)) / 1e8, 2),
                })
            
            self.cache.cache.set(cache_key, result, CacheManager.TTL_FINANCIAL)
            
            return {
                'data': result,
                'source': 'akshare',
                'filters_applied': filters,
                'total_filtered': len(df)
            }
        except Exception as e:
            logger.error(f'选股筛选失败: {e}')
            return {'error': str(e)}
    
    # ==================== 市场情绪 ====================
    
    def get_market_sentiment(self) -> Dict:
        """获取市场情绪指标（增强版）"""
        cache_key = self.cache.make_key("market", "sentiment")
        
        cached = self.cache.cache.get(cache_key)
        if cached is not None:
            return {"data": cached, "source": "cache"}
        
        try:
            # 1. 涨跌家数概览
            overview = self.get_market_overview()
            overview_data = overview.get("data") if "data" in overview else {}
            
            # 2. 恐慌贪婪指数
            fear_greed = None
            try:
                self._rate_limit()
                fg = ak.quantitative_market_bar(indicator="恐慌指数")
                if fg is not None and not fg.empty:
                    fear_greed = fg.iloc[-1].to_dict() if hasattr(fg.iloc[-1], 'to_dict') else None
            except:
                pass
            
            # 3. 外资动向（北向资金 — T+1盘后）
            north = self.get_north_money("daily")
            north_data = north.get("data") if "data" in north else []
            north_closing_change_day = north.get("closing_date", "")  # 未来可扩展
            
            # 4. 板块资金流向
            sector_flow = None
            try:
                self._rate_limit()
                sdf = ak.stock_sector_fund_flow_rank(indicator="今日")
                if sdf is not None and not sdf.empty:
                    sector_flow = sdf.head(5).to_dict(orient='records')
            except:
                pass
            
            # 5. 计算综合情绪评分
            score = 50  # 中性基准
            reasons = []
            
            if overview_data:
                rising = overview_data.get("rising", 0)
                falling = overview_data.get("falling", 0)
                total = overview_data.get("total", 1)
                limit_up = overview_data.get("limit_up", 0)
                limit_down = overview_data.get("limit_down", 0)
                
                # 涨跌比评分
                if total > 0 and falling > 0:
                    ratio = rising / falling
                    if ratio > 2:
                        score += 15; reasons.append("涨跌比>2")
                    elif ratio > 1.2:
                        score += 8; reasons.append("涨跌比>1.2")
                    elif ratio < 0.5:
                        score -= 15; reasons.append("涨跌比<0.5")
                    elif ratio < 0.8:
                        score -= 8; reasons.append("涨跌比<0.8")
                
                # 涨跌停评分
                if limit_up > 80:
                    score += 10; reasons.append(f"涨停{limit_up}家")
                elif limit_up > 100:
                    score += 15; reasons.append(f"涨停{limit_up}家")
                if limit_down > 10:
                    score -= 10; reasons.append(f"跌停{limit_down}家")
                elif limit_down > 30:
                    score -= 15; reasons.append(f"跌停{limit_down}家")
            
            sentiment_label = (
                "极度恐慌" if score <= 20 else
                "偏恐慌" if score <= 40 else
                "中性" if score <= 60 else
                "偏乐观" if score <= 80 else
                "极度乐观"
            )
            
            data = {
                "market_sentiment_score": max(0, min(100, score)),
                "sentiment_label": sentiment_label,
                "score_reasons": reasons,
                "overview": overview_data,
                "north_money": north_data,
                "north_money_note": "北向资金已于2026-05-13起改为T+1盘后数据，此处为最新盘后值",
                "fear_greed": fear_greed,
                "sector_flow_top5": sector_flow,
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
            
            self.cache.cache.set(cache_key, data, CacheManager.TTL_REAL_TIME)
            
            return {"data": data, "source": "akshare"}
        except Exception as e:
            logger.error(f"获取市场情绪失败: {e}")
            return {"error": str(e)}


# 全局数据服务实例
data_service = DataService()
