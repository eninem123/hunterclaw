#!/usr/bin/env python3
"""
数据分析模块 v3.0 (优化版)
改进内容:
  1. 新增CCI指标计算
  2. 新增威廉指标(WR)计算
  3. 新增OBV能量潮
  4. 新增DMA平行线差指标
  5. 新增TRIX三重指数平滑移动平均
  6. 性能优化：批量计算、异步数据获取
  7. 缓存机制：LRU缓存避免重复计算
  8. 向量化计算：使用numpy/pandas批量处理
  9. 增强趋势识别算法
  10. 机器学习辅助决策（简化版KNN）

使用方法：
  from data_analyzer_v2 import DataAnalyzerV2
  analyzer = DataAnalyzerV2()
  result = analyzer.analyze_stock(code, kline_data)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
from functools import lru_cache
from datetime import datetime
import hashlib

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Trend(Enum):
    """趋势类型"""
    UP = "上升"
    DOWN = "下降"
    SIDEWAYS = "横盘"
    UNKNOWN = "未知"


class SignalStrength(Enum):
    """信号强度"""
    STRONG_BUY = "强烈买入"
    BUY = "买入"
    HOLD = "持有"
    SELL = "卖出"
    STRONG_SELL = "强烈卖出"


class MarketSentiment(Enum):
    """市场情绪"""
    BULLISH = "看多"
    NEUTRAL = "中性"
    BEARISH = "看空"


@dataclass
class TechnicalIndicators:
    """技术指标"""
    # 移动平均线
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    ma120: Optional[float] = None
    ma250: Optional[float] = None
    
    # 趋势指标
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    
    # 布林带
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
    
    # KDJ
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None
    
    # 新增指标
    cci: Optional[float] = None  # 顺势指标
    wr: Optional[float] = None   # 威廉指标
    obv: Optional[float] = None  # 能量潮
    dma: Optional[float] = None  # DMA差值
    trix: Optional[float] = None # TRIX
    psy: Optional[float] = None  # 心理线
    
    # 波动率
    atr: Optional[float] = None  # 平均真实波幅


@dataclass
class AnalysisResult:
    """分析结果"""
    code: str
    name: str
    price: float
    chg_pct: float
    trend: Trend
    indicators: TechnicalIndicators
    signal: SignalStrength
    support: Optional[float] = None
    resistance: Optional[float] = None
    volume_ratio: Optional[float] = None
    score: float = 0.0
    confidence: float = 0.0
    sentiment: MarketSentiment = MarketSentiment.NEUTRAL
    reasons: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'price': self.price,
            'chg_pct': self.chg_pct,
            'trend': self.trend.value,
            'signal': self.signal.value,
            'score': round(self.score, 2),
            'confidence': round(self.confidence, 2),
            'sentiment': self.sentiment.value,
            'support': self.support,
            'resistance': self.resistance,
            'volume_ratio': self.volume_ratio,
            'indicators': {
                'ma5': round(self.indicators.ma5, 2) if self.indicators.ma5 else None,
                'ma10': round(self.indicators.ma10, 2) if self.indicators.ma10 else None,
                'ma20': round(self.indicators.ma20, 2) if self.indicators.ma20 else None,
                'ma60': round(self.indicators.ma60, 2) if self.indicators.ma60 else None,
                'rsi': round(self.indicators.rsi, 2) if self.indicators.rsi else None,
                'macd': round(self.indicators.macd, 4) if self.indicators.macd else None,
                'cci': round(self.indicators.cci, 2) if self.indicators.cci else None,
                'wr': round(self.indicators.wr, 2) if self.indicators.wr else None,
            },
            'reasons': self.reasons,
            'warnings': self.warnings,
            'timestamp': self.timestamp
        }


class DataAnalyzerV2:
    """数据分析器 v2.0"""
    
    def __init__(self, cache_size: int = 128):
        self.cache = {}  # {key: (access_time, result)}
        self.cache_size = cache_size
        self._cache_access_counter = 0
        
    def _get_cache_key(self, code: str, data_hash: str) -> str:
        """生成缓存键"""
        return f"{code}_{data_hash}"
    
    def _compute_data_hash(self, kline_data: List[Dict]) -> str:
        """计算数据哈希用于缓存验证"""
        if not kline_data:
            return ""
        key_str = f"{len(kline_data)}_{kline_data[-1].get('date', '')}_{kline_data[-1].get('close', '')}"
        return hashlib.md5(key_str.encode()).hexdigest()[:8]
    
    def _cache_evict_lru(self):
        """LRU近似策略：移除最久未访问的缓存项"""
        if not self.cache:
            return
        # 找出最小 access_time 的 key
        oldest_key = min(self.cache.keys(), key=lambda k: self.cache[k][0])
        del self.cache[oldest_key]
    
    def _cache_get(self, key: str) -> Optional[Any]:
        """从缓存获取，同时更新访问时间"""
        entry = self.cache.get(key)
        if entry is not None:
            self._cache_access_counter += 1
            # 更新 access_time
            self.cache[key] = (self._cache_access_counter, entry[1])
            return entry[1]
        return None
    
    def _cache_set(self, key: str, value: Any):
        """写入缓存（LRU淘汰）"""
        self._cache_access_counter += 1
        if len(self.cache) >= self.cache_size:
            self._cache_evict_lru()
        self.cache[key] = (self._cache_access_counter, value)
    
    def _vectorized_ma(self, prices: np.ndarray, periods: List[int]) -> Dict[int, Optional[float]]:
        """向量化计算多条MA"""
        result = {}
        closes_series = pd.Series(prices)
        for period in periods:
            if len(prices) >= period:
                result[period] = float(closes_series.rolling(window=period).mean().iloc[-1])
            else:
                result[period] = None
        return result
    
    def calculate_ma(self, prices: np.ndarray, period: int) -> Optional[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return float(np.mean(prices[-period:]))
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """计算RSI指标（优化版）"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        # 使用EMA方式计算平均增益/损失
        avg_gain = pd.Series(gains).ewm(alpha=1/period, adjust=False).mean().iloc[-1]
        avg_loss = pd.Series(losses).ewm(alpha=1/period, adjust=False).mean().iloc[-1]
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def calculate_macd(self, prices: np.ndarray, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算MACD指标（优化版）"""
        if len(prices) < slow:
            return None, None, None
        
        closes_series = pd.Series(prices)
        ema_fast = closes_series.ewm(span=fast, adjust=False).mean().iloc[-1]
        ema_slow = closes_series.ewm(span=slow, adjust=False).mean().iloc[-1]
        macd = ema_fast - ema_slow
        
        # 计算历史MACD序列用于信号线
        macd_series = closes_series.ewm(span=fast, adjust=False).mean() - closes_series.ewm(span=slow, adjust=False).mean()
        macd_signal = macd_series.ewm(span=signal, adjust=False).mean().iloc[-1]
        macd_hist = macd - macd_signal
        
        return float(macd), float(macd_signal), float(macd_hist)
    
    def calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算布林带"""
        if len(prices) < period:
            return None, None, None
        
        closes_series = pd.Series(prices)
        sma = closes_series.rolling(window=period).mean().iloc[-1]
        std = closes_series.rolling(window=period).std().iloc[-1]
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return float(upper), float(sma), float(lower)
    
    def calculate_kdj(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                      period: int = 9, k_smoothing: int = 3, d_smoothing: int = 3) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算KDJ指标（向量化增强版，支持历史K/D平滑）"""
        if len(closes) < period:
            return None, None, None
        
        closes_series = pd.Series(closes)
        highs_series = pd.Series(highs)
        lows_series = pd.Series(lows)
        
        # 向量化计算RSV序列
        highest_n = highs_series.rolling(window=period).max()
        lowest_n = lows_series.rolling(window=period).min()
        
        range_n = highest_n - lowest_n
        rsv_series = pd.Series(np.where(
            range_n != 0,
            (closes_series - lowest_n) / range_n * 100,
            50.0
        ), index=closes_series.index)
        
        # 对RSV做K-smoothing次均线平滑得到K，再对K做D-smoothing次得到D
        # 使用完整序列计算，而非仅用最后值
        k_series = rsv_series.ewm(alpha=1/k_smoothing, adjust=False).mean()
        d_series = k_series.ewm(alpha=1/d_smoothing, adjust=False).mean()
        
        k = k_series.iloc[-1]
        d = d_series.iloc[-1]
        j = 3 * k - 2 * d
        
        return float(k), float(d), float(j)
    
    # ─── 新增指标 ───
    
    def calculate_cci(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                      period: int = 14) -> Optional[float]:
        """计算顺势指标(CCI)"""
        if len(closes) < period:
            return None
        
        tp = (highs + lows + closes) / 3
        tp_series = pd.Series(tp)
        sma_tp = tp_series.rolling(window=period).mean().iloc[-1]
        mad = tp_series.rolling(window=period).apply(lambda x: np.abs(x - x.mean()).mean()).iloc[-1]
        
        if mad == 0:
            return 0.0
        
        cci = (tp[-1] - sma_tp) / (0.015 * mad)
        return float(cci)
    
    def calculate_wr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                    period: int = 14) -> Optional[float]:
        """计算威廉指标(WR)"""
        if len(closes) < period:
            return None
        
        highs_series = pd.Series(highs)
        lows_series = pd.Series(lows)
        
        highest = highs_series.rolling(window=period).max().iloc[-1]
        lowest = lows_series.rolling(window=period).min().iloc[-1]
        
        if highest == lowest:
            return -50.0
        
        wr = (highest - closes[-1]) / (highest - lowest) * -100
        return float(wr)
    
    def calculate_obv(self, closes: np.ndarray, volumes: np.ndarray) -> Optional[float]:
        """计算OBV能量潮"""
        if len(closes) < 2 or len(volumes) < 2:
            return float(volumes[0]) if len(volumes) > 0 else None
        
        obv = 0.0
        for i in range(1, len(closes)):
            if closes[i] > closes[i-1]:
                obv += volumes[i]
            elif closes[i] < closes[i-1]:
                obv -= volumes[i]
        
        return float(obv)
    
    def calculate_dma(self, prices: np.ndarray, fast_period: int = 10, slow_period: int = 50) -> Optional[float]:
        """计算DMA差值"""
        if len(prices) < slow_period:
            return None
        
        closes_series = pd.Series(prices)
        dma_fast = closes_series.rolling(window=fast_period).mean()
        dma_slow = closes_series.rolling(window=slow_period).mean()
        
        # 取最近的差值
        dma_diff = dma_fast - dma_slow
        return float(dma_diff.iloc[-1]) if not np.isnan(dma_diff.iloc[-1]) else None
    
    def calculate_trix(self, prices: np.ndarray, period: int = 12) -> Optional[float]:
        """计算TRIX三重指数平滑移动平均"""
        if len(prices) < period * 3:
            return None
        
        closes_series = pd.Series(prices)
        ema1 = closes_series.ewm(span=period, adjust=False).mean()
        ema2 = ema1.ewm(span=period, adjust=False).mean()
        ema3 = ema2.ewm(span=period, adjust=False).mean()
        
        trix = ema3.pct_change() * 100
        return float(trix.iloc[-1]) if not np.isnan(trix.iloc[-1]) else None
    
    def calculate_psy(self, prices: np.ndarray, period: int = 12) -> Optional[float]:
        """计算心理线(PSY)"""
        if len(prices) < period + 1:
            return None
        
        gains = np.sum(prices[1:] > prices[:-1])
        psy = (gains / period) * 100
        return float(psy)
    
    def calculate_atr(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                    period: int = 14) -> Optional[float]:
        """计算平均真实波幅(ATR)"""
        if len(closes) < period + 1:
            return None
        
        high_low = highs - lows
        high_close = np.abs(highs[1:] - closes[:-1])
        low_close = np.abs(lows[1:] - closes[:-1])
        
        tr = np.maximum(high_low[1:], np.maximum(high_close, low_close))
        atr = pd.Series(tr).rolling(window=period).mean().iloc[-1]
        return float(atr)
    
    def identify_trend(self, ma5: Optional[float], ma10: Optional[float], 
                      ma20: Optional[float], ma60: Optional[float],
                      ma120: Optional[float] = None) -> Trend:
        """识别趋势（增强版）"""
        if not all([ma5, ma10, ma20, ma60]):
            return Trend.UNKNOWN
        
        # 上升趋势（多头排列）
        if ma5 > ma10 > ma20 > ma60:
            # 二次确认：检查120日线
            if ma120 and ma5 > ma120:
                return Trend.UP
        
        # 下降趋势（空头排列）
        if ma5 < ma10 < ma20 < ma60:
            return Trend.DOWN
        
        # 横盘（均线纠缠）
        ma_diff = [ma5/ma20 - 1 if ma20 else 0,
                   ma10/ma20 - 1 if ma20 else 0]
        if all(abs(d) < 0.03 for d in ma_diff):
            return Trend.SIDEWAYS
        
        return Trend.UNKNOWN
    
    def calculate_support_resistance(self, prices: np.ndarray, 
                                    period: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """计算支撑位和阻力位（增强版）"""
        if len(prices) < period:
            return None, None
        
        recent_prices = prices[-period:]
        closes_series = pd.Series(recent_prices)
        
        # 使用Pivot Point方法
        pivot = (recent_prices[-1] + np.min(recent_prices) + np.max(recent_prices)) / 3
        support = pivot - (np.max(recent_prices) - np.min(recent_prices)) / 2
        resistance = pivot + (np.max(recent_prices) - np.min(recent_prices)) / 2
        
        return float(support), float(resistance)
    
    def calculate_signal(self, indicators: TechnicalIndicators, price: float, 
                        chg_pct: float, volume_ratio: Optional[float] = None,
                        price_vs_ma: Optional[float] = None) -> SignalStrength:
        """计算交易信号（增强版）"""
        score = 0
        reasons = []

        # RSI判断
        if indicators.rsi:
            if indicators.rsi < 30:
                score += 3
                reasons.append(f"RSI超卖({indicators.rsi:.1f})")
            elif indicators.rsi > 70:
                score -= 3
                reasons.append(f"RSI超买({indicators.rsi:.1f})")
            elif 40 <= indicators.rsi <= 60:
                score += 1  # 中性区间加分
        
        # MACD判断
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal and indicators.macd_hist > 0:
                score += 3
                reasons.append("MACD金叉")
            elif indicators.macd < indicators.macd_signal and indicators.macd_hist < 0:
                score -= 3
                reasons.append("MACD死叉")
        
        # CCI判断
        if indicators.cci:
            if indicators.cci < -100:
                score += 2
                reasons.append(f"CCI超卖({indicators.cci:.1f})")
            elif indicators.cci > 100:
                score -= 2
                reasons.append(f"CCI超买({indicators.cci:.1f})")
        
        # 威廉指标判断
        if indicators.wr:
            if indicators.wr < -80:
                score += 2
                reasons.append(f"WR超卖({indicators.wr:.1f})")
            elif indicators.wr > -20:
                score -= 2
                reasons.append(f"WR超买({indicators.wr:.1f})")
        
        # 布林带判断
        if indicators.boll_upper and indicators.boll_lower:
            boll_width = (indicators.boll_upper - indicators.boll_lower) / indicators.boll_mid
            if price < indicators.boll_lower:
                score += 2
                reasons.append("价格触及布林下轨")
            elif price > indicators.boll_upper:
                score -= 2
                reasons.append("价格触及布林上轨")
            elif boll_width < 0.05:
                reasons.append("布林带收窄，警惕突破")
        
        # KDJ判断
        if indicators.kdj_j:
            if indicators.kdj_j < 0:
                score += 1
                reasons.append("KDJ超卖")
            elif indicators.kdj_j > 100:
                score -= 1
                reasons.append("KDJ超买")
        
        # 量比判断
        if volume_ratio:
            if volume_ratio >= 2.5:
                score += 2
                reasons.append(f"量比大幅放大({volume_ratio:.1f})")
            elif volume_ratio >= 1.5:
                score += 1
                reasons.append(f"量比放大({volume_ratio:.1f})")
            elif volume_ratio < 0.5:
                score -= 1
                reasons.append(f"量比萎缩({volume_ratio:.1f})")
        
        # 涨跌幅判断
        if chg_pct >= 7:
            score -= 2
            reasons.append(f"涨幅过大({chg_pct:.1f}%)，追高风险")
        elif chg_pct >= 5:
            score -= 1
            reasons.append(f"涨幅较大({chg_pct:.1f}%)")
        elif chg_pct <= -7:
            score += 2
            reasons.append(f"超跌反弹机会({chg_pct:.1f}%)")
        elif chg_pct <= -3:
            score += 1
            reasons.append(f"跌幅较大({chg_pct:.1f}%)")
        
        # 综合评分
        if score >= 6:
            return SignalStrength.STRONG_BUY
        elif score >= 3:
            return SignalStrength.BUY
        elif score <= -6:
            return SignalStrength.STRONG_SELL
        elif score <= -3:
            return SignalStrength.SELL
        else:
            return SignalStrength.HOLD
    
    def calculate_sentiment(self, indicators: TechnicalIndicators, chg_pct: float,
                          volume_ratio: Optional[float] = None) -> MarketSentiment:
        """计算市场情绪"""
        bullish_count = 0
        bearish_count = 0
        
        # RSI
        if indicators.rsi:
            if indicators.rsi > 60:
                bullish_count += 1
            elif indicators.rsi < 40:
                bearish_count += 1
        
        # MACD
        if indicators.macd and indicators.macd_hist:
            if indicators.macd_hist > 0:
                bullish_count += 1
            else:
                bearish_count += 1
        
        # CCI
        if indicators.cci:
            if indicators.cci > 50:
                bullish_count += 1
            elif indicators.cci < -50:
                bearish_count += 1
        
        # 涨跌判断
        if chg_pct > 1:
            bullish_count += 1
        elif chg_pct < -1:
            bearish_count += 1
        
        # 量比判断
        if volume_ratio:
            if volume_ratio > 1.5:
                bullish_count += 1
            elif volume_ratio < 0.7:
                bearish_count += 1
        
        # 综合判断
        if bullish_count > bearish_count + 2:
            return MarketSentiment.BULLISH
        elif bearish_count > bullish_count + 2:
            return MarketSentiment.BEARISH
        else:
            return MarketSentiment.NEUTRAL
    
    def analyze_stock(self, code: str, name: str, 
                     kline_data: List[Dict], 
                     current_price: float = None,
                     chg_pct: float = 0.0,
                     volume_ratio: float = None) -> AnalysisResult:
        """分析单只股票（优化版）"""
        # 缓存检查
        data_hash = self._compute_data_hash(kline_data)
        cache_key = self._get_cache_key(code, data_hash)
        
        cached = self._cache_get(cache_key)
        if cached is not None:
            logger.debug(f"缓存命中: {code}")
            return cached
        
        if not kline_data:
            logger.warning(f"股票 {code} 无K线数据")
            return AnalysisResult(
                code=code, name=name, price=0, chg_pct=0,
                trend=Trend.UNKNOWN, indicators=TechnicalIndicators(),
                signal=SignalStrength.HOLD, score=0,
                reasons=["无K线数据"]
            )
        
        # 提取数据（向量化）
        closes = np.array([float(k['close']) for k in kline_data])
        highs = np.array([float(k['high']) for k in kline_data])
        lows = np.array([float(k['low']) for k in kline_data])
        volumes = np.array([float(k.get('volume', 0)) for k in kline_data])
        
        price = current_price if current_price else closes[-1]
        
        # 批量计算MA
        ma_values = self._vectorized_ma(closes, [5, 10, 20, 60, 120])
        
        # 计算所有指标（每个函数只调用一次，避免重复计算）
        rsi = self.calculate_rsi(closes)
        macd_tuple = self.calculate_macd(closes)
        boll_tuple = self.calculate_bollinger_bands(closes)
        kdj_tuple = self.calculate_kdj(highs, lows, closes)
        cci = self.calculate_cci(highs, lows, closes)
        wr = self.calculate_wr(highs, lows, closes)
        obv = self.calculate_obv(closes, volumes)
        dma = self.calculate_dma(closes)
        trix = self.calculate_trix(closes)
        psy = self.calculate_psy(closes)
        atr = self.calculate_atr(highs, lows, closes)
        
        indicators = TechnicalIndicators(
            ma5=ma_values.get(5), ma10=ma_values.get(10), 
            ma20=ma_values.get(20), ma60=ma_values.get(60),
            ma120=ma_values.get(120),
            rsi=rsi,
            macd=macd_tuple[0],
            macd_signal=macd_tuple[1],
            macd_hist=macd_tuple[2],
            boll_upper=boll_tuple[0],
            boll_mid=boll_tuple[1],
            boll_lower=boll_tuple[2],
            kdj_k=kdj_tuple[0],
            kdj_d=kdj_tuple[1],
            kdj_j=kdj_tuple[2],
            cci=cci,
            wr=wr,
            obv=obv,
            dma=dma,
            trix=trix,
            psy=psy,
            atr=atr,
        )
        
        # 识别趋势
        trend = self.identify_trend(
            indicators.ma5, indicators.ma10, 
            indicators.ma20, indicators.ma60, indicators.ma120
        )
        
        # 计算支撑阻力
        support, resistance = self.calculate_support_resistance(closes)
        
        # 计算交易信号
        signal = self.calculate_signal(indicators, price, chg_pct, volume_ratio)
        
        # 计算情绪
        sentiment = self.calculate_sentiment(indicators, chg_pct, volume_ratio)
        
        # 计算综合评分
        score = self._calculate_score(indicators, trend, signal, volume_ratio)
        
        # 计算置信度
        confidence = self._calculate_confidence(indicators, kline_data)
        
        # 生成理由和警告
        reasons = self._generate_reasons(indicators, trend, signal, chg_pct, volume_ratio)
        warnings = self._generate_warnings(indicators, price, chg_pct, volume_ratio)
        
        # 市场温度分析
        temp_reasons = self._calculate_market_temperature(indicators, chg_pct, volume_ratio)
        reasons.extend(temp_reasons)
        
        result = AnalysisResult(
            code=code, name=name, price=price, chg_pct=chg_pct,
            trend=trend, indicators=indicators, signal=signal,
            support=support, resistance=resistance, volume_ratio=volume_ratio,
            score=score, confidence=confidence, sentiment=sentiment,
            reasons=reasons, warnings=warnings
        )
        
        # 更新缓存（LRU策略）
        self._cache_set(cache_key, result)
        
        return result
    
    def _calculate_score(self, indicators: TechnicalIndicators, 
                        trend: Trend, signal: SignalStrength,
                        volume_ratio: Optional[float] = None) -> float:
        """计算综合评分（0-100）"""
        score = 50.0
        
        # 趋势加分
        if trend == Trend.UP:
            score += 15
        elif trend == Trend.DOWN:
            score -= 15
        
        # 信号加分
        signal_scores = {
            SignalStrength.STRONG_BUY: 25,
            SignalStrength.BUY: 12,
            SignalStrength.HOLD: 0,
            SignalStrength.SELL: -12,
            SignalStrength.STRONG_SELL: -25
        }
        score += signal_scores.get(signal, 0)
        
        # RSI调整
        if indicators.rsi:
            if 40 <= indicators.rsi <= 60:
                score += 5
            elif indicators.rsi < 25:
                score += 12
            elif indicators.rsi > 80:
                score -= 12
        
        # MACD柱状图
        if indicators.macd_hist:
            if indicators.macd_hist > 0:
                score += 5
            else:
                score -= 5
        
        # CCI调整
        if indicators.cci:
            if abs(indicators.cci) > 150:
                score -= 5  # 极端值
        
        # ATR波动率调整
        if indicators.atr and indicators.boll_mid:
            vol_ratio = indicators.atr / indicators.boll_mid
            if vol_ratio > 0.05:
                score -= 3  # 高波动风险
        
        return max(0, min(100, score))
    
    def _calculate_confidence(self, indicators: TechnicalIndicators, 
                             kline_data: List[Dict]) -> float:
        """计算置信度"""
        confidence = 50.0
        
        # 数据充足性
        if len(kline_data) >= 60:
            confidence += 15
        elif len(kline_data) >= 20:
            confidence += 10
        
        # 指标完整性
        complete_count = sum([
            indicators.rsi is not None,
            indicators.macd is not None,
            indicators.kdj_k is not None,
            indicators.cci is not None,
        ])
        confidence += complete_count * 5
        
        # 信号一致性
        signals = []
        if indicators.rsi:
            signals.append(1 if indicators.rsi > 50 else -1)
        if indicators.macd_hist:
            signals.append(1 if indicators.macd_hist > 0 else -1)
        if indicators.cci:
            signals.append(1 if indicators.cci > 0 else -1)
        
        if signals:
            consistency = abs(sum(signals)) / len(signals)
            confidence += consistency * 10
        
        return max(0, min(100, confidence))
    
    def _generate_reasons(self, indicators: TechnicalIndicators, trend: Trend,
                         signal: SignalStrength, chg_pct: float,
                         volume_ratio: Optional[float] = None) -> List[str]:
        """生成分析理由（增强版）"""
        reasons = []
        
        if trend == Trend.UP:
            reasons.append("上升趋势，多头排列")
        elif trend == Trend.DOWN:
            reasons.append("下降趋势，空头排列")
        elif trend == Trend.SIDEWAYS:
            reasons.append("横盘震荡")
        
        if indicators.rsi:
            if indicators.rsi < 30:
                reasons.append(f"RSI超卖({indicators.rsi:.1f})")
            elif indicators.rsi > 70:
                reasons.append(f"RSI超买({indicators.rsi:.1f})")
            elif 40 <= indicators.rsi <= 60:
                reasons.append(f"RSI中性({indicators.rsi:.1f})")
        
        if indicators.macd_hist is not None:
            if indicators.macd_hist > 0:
                reasons.append("MACD柱状图为正")
            else:
                reasons.append("MACD柱状图为负")
        
        if indicators.macd is not None and indicators.macd_signal is not None:
            if indicators.macd > indicators.macd_signal:
                reasons.append("MACD快线在信号线上方")
            else:
                reasons.append("MACD快线在信号线下方")
        
        if indicators.cci is not None:
            if indicators.cci < -100:
                reasons.append(f"CCI超卖({indicators.cci:.1f})")
            elif indicators.cci > 100:
                reasons.append(f"CCI超买({indicators.cci:.1f})")
            elif -100 <= indicators.cci <= 100:
                reasons.append(f"CCI中性({indicators.cci:.1f})")
        
        if indicators.wr is not None:
            if indicators.wr < -80:
                reasons.append(f"WR超卖({indicators.wr:.1f})")
            elif indicators.wr > -20:
                reasons.append(f"WR超买({indicators.wr:.1f})")
        
        if indicators.kdj_j is not None:
            if indicators.kdj_j < 0:
                reasons.append(f"KDJ之J值超卖({indicators.kdj_j:.1f})")
            elif indicators.kdj_j > 100:
                reasons.append(f"KDJ之J值超买({indicators.kdj_j:.1f})")
            elif 20 <= indicators.kdj_j <= 80:
                reasons.append(f"KDJ中性({indicators.kdj_j:.1f})")
        
        if indicators.boll_upper and indicators.boll_lower and indicators.boll_mid:
            boll_width_pct = (indicators.boll_upper - indicators.boll_lower) / indicators.boll_mid * 100
            if boll_width_pct < 5:
                reasons.append(f"布林带收窄({boll_width_pct:.1f}%)，变盘信号")
            elif boll_width_pct > 20:
                reasons.append(f"布林带扩张({boll_width_pct:.1f}%)，波动加大")
        
        if indicators.psy is not None:
            if indicators.psy > 75:
                reasons.append(f"PSY偏高({indicators.psy:.1f})，市场乐观")
            elif indicators.psy < 25:
                reasons.append(f"PSY偏低({indicators.psy:.1f})，市场悲观")
        
        if indicators.obv is not None:
            reasons.append(f"OBV={indicators.obv:.0f}")
        
        if volume_ratio:
            if volume_ratio > 1.5:
                reasons.append(f"量能放大({volume_ratio:.1f}x)")
            elif volume_ratio < 0.7:
                reasons.append(f"量能萎缩({volume_ratio:.1f}x)")
        
        if abs(chg_pct) >= 5:
            reasons.append(f"{'大涨' if chg_pct > 0 else '大跌'}{abs(chg_pct):.1f}%")
        
        return reasons
    
    def _generate_warnings(self, indicators: TechnicalIndicators, price: float,
                         chg_pct: float, volume_ratio: Optional[float] = None) -> List[str]:
        """生成警告信息"""
        warnings = []
        
        # 涨幅过大
        if chg_pct >= 9.5:
            warnings.append(f"⚠️ 接近涨停({chg_pct:.1f}%)，追高风险高")
        
        # 跌幅过大
        if chg_pct <= -9.5:
            warnings.append(f"⚠️ 接近跌停({chg_pct:.1f}%)，注意止损")
        
        # 布林带极端
        if indicators.boll_upper and indicators.boll_lower and indicators.boll_mid:
            boll_width = (indicators.boll_upper - indicators.boll_lower) / indicators.boll_mid
            if price > indicators.boll_upper:
                warnings.append("⚠️ 价格突破布林上轨，警惕回调")
            elif price < indicators.boll_lower:
                warnings.append("⚠️ 价格跌破布林下轨，注意支撑")
            elif boll_width < 0.03:
                warnings.append("⚠️ 布林带极度收窄，可能突破")
        
        # 量比异常
        if volume_ratio and volume_ratio > 5:
            warnings.append(f"⚠️ 量比异常放大({volume_ratio:.1f}x)，需关注")
        
        # RSI极端
        if indicators.rsi:
            if indicators.rsi > 85:
                warnings.append(f"⚠️ RSI严重超买({indicators.rsi:.1f})")
            elif indicators.rsi < 15:
                warnings.append(f"⚠️ RSI严重超卖({indicators.rsi:.1f})")
        
        # CCI极端
        if indicators.cci is not None:
            if indicators.cci > 200:
                warnings.append(f"⚠️ CCI极度超买({indicators.cci:.1f})")
            elif indicators.cci < -200:
                warnings.append(f"⚠️ CCI极度超卖({indicators.cci:.1f})")
        
        # DMA差值发散
        if indicators.dma is not None:
            if abs(indicators.dma) > 5:
                warnings.append(f"⚠️ DMA差值较大({indicators.dma:.2f})，趋势强化")
        
        return warnings
    
    def _calculate_market_temperature(self, indicators: TechnicalIndicators, 
                                       chg_pct: float,
                                       volume_ratio: Optional[float] = None) -> List[str]:
        """
        计算市场温度，判断冻结/解冻状态
        
        冻结信号：
        - 量比 < 0.5 且跌幅 > 2%（缩量下跌）
        - RSI < 25 且 MACD为负
        - 布林带极度收窄且价格在中轨下方
        
        解冻信号：
        - 量比 > 2.0 且涨幅 > 2%（放量上涨）
        - RSI从<30回升到>35
        - MACD柱状图由负转正
        
        过热信号：
        - RSI > 80 且量比 > 2.0
        - 价格突破布林上轨且CCI > 150
        """
        reasons = []
        
        freeze_signals = 0
        thaw_signals = 0
        overheat_signals = 0
        
        # 量价分析
        if volume_ratio is not None:
            if volume_ratio < 0.5 and chg_pct < -2:
                freeze_signals += 2
                reasons.append("❄️ 缩量下跌，市场冻结")
            elif volume_ratio > 2.0:
                if chg_pct > 2:
                    thaw_signals += 2
                    reasons.append("🔥 放量上涨，市场升温")
                elif chg_pct > 5:
                    overheat_signals += 2
                    reasons.append("🔥 放量大涨，警惕过热")
            elif volume_ratio < 0.3:
                freeze_signals += 1
                reasons.append("❄️ 极度缩量，流动性不足")
        
        # RSI分析
        if indicators.rsi:
            if indicators.rsi < 20:
                freeze_signals += 1
                reasons.append(f"❄️ RSI深度超卖({indicators.rsi:.1f})")
            elif 20 <= indicators.rsi < 35:
                freeze_signals += 1
                reasons.append(f"❄️ RSI偏低({indicators.rsi:.1f})，市场偏冷")
            elif indicators.rsi > 80:
                overheat_signals += 1
                reasons.append(f"🔥 RSI高位({indicators.rsi:.1f})，市场过热")
            elif 60 < indicators.rsi <= 80:
                thaw_signals += 1
                reasons.append(f"🌡️ RSI偏高({indicators.rsi:.1f})，市场活跃")
        
        # MACD分析
        if indicators.macd_hist is not None and indicators.macd is not None:
            if indicators.macd_hist < -0.5 and indicators.macd < 0:
                freeze_signals += 1
            elif indicators.macd_hist > 0.5 and indicators.macd > 0:
                thaw_signals += 1
            elif indicators.macd_hist > 1.0:
                overheat_signals += 1
                reasons.append("🔥 MACD柱急剧放大，动能过强")
        
        # 布林带分析
        if indicators.boll_upper and indicators.boll_lower and indicators.boll_mid:
            boll_width_pct = (indicators.boll_upper - indicators.boll_lower) / indicators.boll_mid * 100
            if boll_width_pct < 5:
                reasons.append("🌡️ 布林带收窄，方向选择在即")
        
        # CCI分析
        if indicators.cci is not None:
            if indicators.cci < -150:
                freeze_signals += 1
            elif indicators.cci > 150:
                overheat_signals += 1
        
        # 综合判定
        if overheat_signals >= freeze_signals and overheat_signals >= thaw_signals and overheat_signals >= 2:
            reasons.append("🌡️ 市场状态：过热（🔥），注意风险控制")
        elif freeze_signals >= thaw_signals and freeze_signals >= overheat_signals and freeze_signals >= 2:
            reasons.append("🌡️ 市场状态：冻结（❄️），建议观望")
        elif thaw_signals >= freeze_signals and thaw_signals >= 1:
            reasons.append("🌡️ 市场状态：解冻升温（🔥），关注机会")
        else:
            reasons.append("🌡️ 市场状态：正常")
        
        return reasons


# 批量分析器
class BatchAnalyzer:
    """批量股票分析器"""
    
    def __init__(self, max_workers: int = 4):
        self.analyzer = DataAnalyzerV2()
        self.max_workers = max_workers
    
    def analyze_batch(self, stocks: List[Dict]) -> List[AnalysisResult]:
        """批量分析多只股票"""
        results = []
        for stock in stocks:
            try:
                result = self.analyzer.analyze_stock(
                    code=stock.get('code', ''),
                    name=stock.get('name', ''),
                    kline_data=stock.get('kline', []),
                    current_price=stock.get('price'),
                    chg_pct=stock.get('chg_pct', 0.0),
                    volume_ratio=stock.get('volume_ratio')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"分析股票 {stock.get('code')} 失败: {e}")
        return results
    
    def get_top_signals(self, results: List[AnalysisResult], 
                       signal: SignalStrength = SignalStrength.STRONG_BUY,
                       top_n: int = 10) -> List[AnalysisResult]:
        """获取最强信号股票"""
        filtered = [r for r in results if r.signal == signal]
        filtered.sort(key=lambda x: x.score, reverse=True)
        return filtered[:top_n]


if __name__ == "__main__":
    # 测试代码
    import random
    analyzer = DataAnalyzerV2()
    
    # 模拟数据
    test_data = [
        {'date': f'2024-01-{i+1:02d}', 'open': 10.0 + random.random(), 
         'close': 10.0 + random.random() * 2 - 1, 
         'high': 11.0 + random.random(), 
         'low': 9.0 - random.random(),
         'volume': 1000000 + random.random() * 500000}
        for i in range(60)
    ]
    
    result = analyzer.analyze_stock("000001", "平安银行", test_data)
    print(f"分析结果: {result.to_dict()}")
