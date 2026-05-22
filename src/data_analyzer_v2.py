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
    """趋势类型（增强版）"""
    UP = "上升"
    WEAK_UP = "弱上升"
    DOWN = "下降"
    WEAK_DOWN = "弱下降"
    SIDEWAYS = "横盘"
    UNKNOWN = "未知"


class MarketRegime(Enum):
    """市场机制/状态"""
    BULL = "牛市"
    BEAR = "熊市"
    RANGE_BOUND = "震荡"
    VOLATILE = "高波动"
    QUIET = "低活跃"
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
    
    # v3.1新增指标
    stoch_rsi_k: Optional[float] = None  # StochRSI快线
    stoch_rsi_d: Optional[float] = None  # StochRSI慢线
    adx: Optional[float] = None  # 平均趋向指数
    plus_di: Optional[float] = None  # +DI上升方向
    minus_di: Optional[float] = None  # -DI下降方向
    
    # v3.2新增指标
    vwap: Optional[float] = None  # 成交量加权均价
    volume_profile_poc: Optional[float] = None  # 成交量分布POC(最大成交量价位)
    volume_profile_vah: Optional[float] = None  # 价值区域上沿(70%)
    volume_profile_val: Optional[float] = None  # 价值区域下沿(30%)
    mfi: Optional[float] = None  # 资金流量指标
    daily_atr_pct: Optional[float] = None  # ATR百分比
    
    # v3.3新增指标
    volume_divergence: Optional[float] = None  # 量价背离度(正=量价同步, 负=背离)
    market_breadth_zscore: Optional[float] = None  # 市场广度Z分数
    hurst_exponent: Optional[float] = None  # 赫斯特指数(趋势持续性)
    keltner_upper: Optional[float] = None  # 肯特纳通道上轨
    keltner_mid: Optional[float] = None  # 肯特纳通道中轨
    keltner_lower: Optional[float] = None  # 肯特纳通道下轨


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
                'adx': round(self.indicators.adx, 2) if self.indicators.adx else None,
                'stoch_rsi_k': round(self.indicators.stoch_rsi_k, 3) if self.indicators.stoch_rsi_k else None,
                'mfi': round(self.indicators.mfi, 2) if self.indicators.mfi else None,
                'hurst': round(self.indicators.hurst_exponent, 3) if self.indicators.hurst_exponent else None,
                'vol_div': round(self.indicators.volume_divergence, 3) if self.indicators.volume_divergence else None,
                'vwap': round(self.indicators.vwap, 2) if self.indicators.vwap else None,
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
    
    def calculate_stoch_rsi(self, prices: np.ndarray, period: int = 14, 
                              smooth_k: int = 3, smooth_d: int = 3) -> Tuple[Optional[float], Optional[float]]:
        """
        计算Stochastic RSI指标（v3.1新增）
        
        StochRSI = (RSI - min(RSI, n)) / (max(RSI, n) - min(RSI, n))
        将RSI值标准化到0-1范围，比普通RSI更敏感，
        用于精准识别超买超卖区域。
        
        Returns:
            (stoch_k, stoch_d): 快线K和慢线D值 (0-1范围)
        """
        if len(prices) < period * 2 + smooth_k:
            return None, None
        
        # 先计算RSI序列
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0.0)
        losses = np.where(deltas < 0, -deltas, 0.0)
        
        rsi_series = pd.Series(index=range(len(prices)))
        avg_gain = np.mean(gains[:period])
        avg_loss = np.mean(losses[:period])
        
        rsi_values = []
        alfa = 1.0 / period
        for i in range(period, len(prices)):
            if avg_loss == 0:
                rsi = 100.0
            else:
                rs = avg_gain / avg_loss
                rsi = 100 - (100 / (1 + rs))
            rsi_values.append(rsi)
            
            # 更新EMA
            if i < len(prices) - 1:
                gain = max(0, prices[i+1] - prices[i])
                loss = max(0, prices[i] - prices[i+1])
                avg_gain = alfa * gain + (1 - alfa) * avg_gain
                avg_loss = alfa * loss + (1 - alfa) * avg_loss
        
        if len(rsi_values) < period:
            return None, None
        
        rsi_arr = np.array(rsi_values)
        stoch_k_values = []
        for i in range(period, len(rsi_arr)):
            rsi_window = rsi_arr[i-period:i]
            min_rsi = np.min(rsi_window)
            max_rsi = np.max(rsi_window)
            if max_rsi - min_rsi == 0:
                stoch_k = 0.5
            else:
                stoch_k = (rsi_arr[i] - min_rsi) / (max_rsi - min_rsi)
            stoch_k_values.append(stoch_k)
        
        if len(stoch_k_values) < smooth_k:
            return None, None
        
        k_series = pd.Series(stoch_k_values).ewm(alpha=1/smooth_k, adjust=False).mean()
        d_series = k_series.ewm(alpha=1/smooth_d, adjust=False).mean()
        
        return float(k_series.iloc[-1]), float(d_series.iloc[-1])
    
    def calculate_dmi_adx(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray,
                           period: int = 14) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """
        计算DMI/ADX指标（v3.1新增）
        
        ADX ∈ [0,100]，用于衡量趋势强度：
        - ADX > 25: 趋势行情（配合+DI/-DI判断方向）
        - ADX < 20: 震荡行情
        - +DI > -DI: 上升趋势
        - -DI > +DI: 下降趋势
        
        Returns:
            (adx, plus_di, minus_di)
        """
        if len(closes) < period * 2:
            return None, None, None
        
        # 计算True Range和Directional Movement
        high_arr = pd.Series(highs)
        low_arr = pd.Series(lows)
        close_arr = pd.Series(closes)
        
        tr = pd.concat([
            high_arr - low_arr,
            (high_arr - close_arr.shift(1)).abs(),
            (low_arr - close_arr.shift(1)).abs()
        ], axis=1).max(axis=1)
        
        # +DM 和 -DM
        up_move = high_arr - high_arr.shift(1)
        down_move = low_arr.shift(1) - low_arr
        
        plus_dm = pd.Series(0.0, index=high_arr.index)
        minus_dm = pd.Series(0.0, index=low_arr.index)
        
        plus_dm[(up_move > down_move) & (up_move > 0)] = up_move
        minus_dm[(down_move > up_move) & (down_move > 0)] = down_move
        
        # 平滑
        atr = tr.ewm(span=period, adjust=False).mean()
        plus_di = 100 * plus_dm.ewm(span=period, adjust=False).mean() / atr
        minus_di = 100 * minus_dm.ewm(span=period, adjust=False).mean() / atr
        
        # DX 和 ADX
        dx = 100 * (plus_di - minus_di).abs() / (plus_di + minus_di).replace(0, np.nan)
        adx = dx.ewm(span=period, adjust=False).mean()
        
        return (
            float(adx.iloc[-1]) if not np.isnan(adx.iloc[-1]) else None,
            float(plus_di.iloc[-1]) if not np.isnan(plus_di.iloc[-1]) else None,
            float(minus_di.iloc[-1]) if not np.isnan(minus_di.iloc[-1]) else None,
        )
    
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
    
    def calculate_vwap(self, highs: np.ndarray, lows: np.ndarray, 
                       closes: np.ndarray, volumes: np.ndarray) -> Optional[float]:
        """计算VWAP (成交量加权均价) v3.2
        VWAP = sum(典型价格 * 成交量) / sum(成交量)
        当价格 > VWAP时偏多, 价格 < VWAP时偏空
        """
        if len(closes) < 1 or len(volumes) < 1:
            return None
        typical_price = (highs + lows + closes) / 3
        vwap = np.sum(typical_price * volumes) / np.sum(volumes)
        return float(vwap) if np.isfinite(vwap) else None
    
    def calculate_mfi(self, highs: np.ndarray, lows: np.ndarray,
                      closes: np.ndarray, volumes: np.ndarray,
                      period: int = 14) -> Optional[float]:
        """计算资金流量指标(MFI) v3.2
        MFI = 100 - 100/(1 + 正向资金流/负向资金流)
        类似RSI但加入了成交量权重, 80以上超买, 20以下超卖
        """
        if len(closes) < period + 1:
            return None
        typical_price = (highs + lows + closes) / 3
        raw_money_flow = typical_price * volumes
        
        pos_flow = 0.0
        neg_flow = 0.0
        for i in range(1, len(typical_price)):
            if typical_price[i] > typical_price[i-1]:
                pos_flow += raw_money_flow[i]
            elif typical_price[i] < typical_price[i-1]:
                neg_flow += raw_money_flow[i]
        
        if neg_flow == 0:
            return 100.0
        mfr = pos_flow / neg_flow
        mfi = 100 - (100 / (1 + mfr))
        return float(mfi)
    
    def calculate_volume_profile(self, closes: np.ndarray, volumes: np.ndarray,
                                 bins: int = 20) -> tuple:
        """计算成交量分布(Volume Profile) v3.2
        返回 (POC, VAH, VAL):
          - POC: Point of Control (最大成交量价位)
          - VAH: Value Area High (价值区域上沿, 累计70%成交量)
          - VAL: Value Area Low (价值区域下沿, 累计30%成交量)
        """
        if len(closes) < bins or len(volumes) < bins:
            return None, None, None
        
        # 构建价格-成交量分布
        price_min, price_max = np.min(closes), np.max(closes)
        if price_min == price_max:
            return float(price_min), float(price_max), float(price_min)
        
        bin_edges = np.linspace(price_min, price_max, bins + 1)
        bin_centers = (bin_edges[:-1] + bin_edges[1:]) / 2
        vol_profile = np.zeros(bins)
        
        for i in range(len(closes)):
            idx = np.digitize(closes[i], bin_edges) - 1
            if 0 <= idx < bins:
                vol_profile[idx] += volumes[i]
        
        # POC: 最大成交量价位
        poc_idx = np.argmax(vol_profile)
        poc = float(bin_centers[poc_idx])
        
        # VAH/VAL: 累计成交量70%/30%分位
        total_vol = np.sum(vol_profile)
        if total_vol == 0:
            return poc, None, None
        
        cumsum = np.cumsum(vol_profile) / total_vol
        vah_idx = np.searchsorted(cumsum, 0.70)
        val_idx = np.searchsorted(cumsum, 0.30)
        vah = float(bin_centers[min(vah_idx, bins - 1)])
        val = float(bin_centers[min(val_idx, bins - 1)])
        
        return poc, vah, val
    
    def calculate_daily_atr_pct(self, atr_val: Optional[float], price: float) -> Optional[float]:
        """计算ATR百分比 (便于跨股票比较) v3.2"""
        if atr_val is None or price == 0:
            return None
        return float((atr_val / price) * 100)
    
    # ─── v3.3 新增指标 ───
    
    def calculate_volume_divergence(self, closes: np.ndarray, volumes: np.ndarray,
                                     lookback: int = 20) -> Optional[float]:
        """计算量价背离度 v3.3
        
        原理: 比较价格变化率与成交量变化率的相关系数
        - 正值: 量价同步(放量上涨/缩量下跌)
        - 负值: 量价背离(放量下跌/缩量上涨, 危险信号)
        - 值域: [-1, 1]
        """
        if len(closes) < lookback or len(volumes) < lookback:
            return None
        
        price_chg = np.diff(closes[-lookback-1:]) / closes[-lookback-1:-1]
        vol_chg = np.diff(volumes[-lookback-1:]) / (volumes[-lookback-1:-1] + 1e-10)
        
        if len(price_chg) < 5 or len(vol_chg) < 5:
            return None
        
        # 计算皮尔逊相关系数
        correlation = np.corrcoef(price_chg, vol_chg)[0, 1]
        return float(correlation) if not np.isnan(correlation) else None
    
    def calculate_hurst_exponent(self, prices: np.ndarray, max_lag: int = 20) -> Optional[float]:
        """计算赫斯特指数 v3.3
        
        衡量时间序列的趋势持续性:
        - H > 0.5: 趋势持续(动量效应, 顺势操作)
        - H ≈ 0.5: 随机游走(布朗运动)
        - H < 0.5: 均值回归(反转效应, 逆势操作)
        
        使用R/S分析方法(重标极差)
        """
        if len(prices) < max_lag * 2:
            return None
        
        lags = range(2, max_lag + 1)
        tau = []
        
        for lag in lags:
            # 分割为n个不重叠子序列
            n = len(prices) // lag
            if n < 2:
                continue
            
            rs_values = []
            for i in range(n):
                segment = prices[i*lag:(i+1)*lag]
                if len(segment) < 3:
                    continue
                mean_seg = np.mean(segment)
                dev = segment - mean_seg
                cum_dev = np.cumsum(dev)
                R = np.max(cum_dev) - np.min(cum_dev)
                S = np.std(segment)
                if S > 0:
                    rs_values.append(R / S)
            
            if rs_values:
                tau.append([np.log(lag), np.log(np.mean(rs_values))])
        
        if len(tau) < 3:
            return None
        
        tau_arr = np.array(tau)
        # 线性回归斜率 = Hurst指数
        A = np.vstack([tau_arr[:, 0], np.ones(len(tau_arr))]).T
        H, _ = np.linalg.lstsq(A, tau_arr[:, 1], rcond=None)[0]
        
        return float(max(0.1, min(1.0, H)))
    
    def calculate_keltner_channel(self, closes: np.ndarray, highs: np.ndarray, 
                                   lows: np.ndarray, period: int = 20, 
                                   atr_multiplier: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算肯特纳通道(Keltner Channel) v3.3
        
        中轨=EMA(period), 上下轨=中轨±ATR*multiplier
        比布林带更适合趋势跟踪(使用ATR而不是标准差)
        """
        if len(closes) < period:
            return None, None, None
        
        closes_series = pd.Series(closes)
        ema_mid = closes_series.ewm(span=period, adjust=False).mean().iloc[-1]
        
        # 计算ATR
        high_series = pd.Series(highs)
        low_series = pd.Series(lows)
        close_shift = closes_series.shift(1)
        
        tr = pd.concat([
            high_series - low_series,
            (high_series - close_shift).abs(),
            (low_series - close_shift).abs()
        ], axis=1).max(axis=1)
        atr_val = tr.ewm(span=period, adjust=False).mean().iloc[-1]
        
        upper = ema_mid + atr_multiplier * atr_val
        lower = ema_mid - atr_multiplier * atr_val
        
        return float(upper), float(ema_mid), float(lower)
    
    def calculate_market_breadth_zscore(self, closes: np.ndarray, 
                                         benchmark: Optional[np.ndarray] = None) -> Optional[float]:
        """计算个股相对市场广度的Z分数 v3.3
        
        衡量个股价格偏离其近期均值的程度(归一化)
        Z > 1.5: 显著偏强, Z < -1.5: 显著偏弱
        """
        if len(closes) < 30:
            return None
        
        returns = np.diff(closes) / closes[:-1]
        mean_ret = np.mean(returns[-20:])
        std_ret = np.std(returns[-20:])
        
        if std_ret == 0:
            return 0.0
        
        latest_ret = returns[-1]
        zscore = (latest_ret - mean_ret) / std_ret
        return float(zscore)

    def _multi_timeframe_analysis(self, closes: np.ndarray,
                                   highs: np.ndarray,
                                   lows: np.ndarray) -> Dict[str, Any]:
        """多时间框架分析 v3.2
        在不同时间窗口上计算RSI和趋势，检测多周期共振
        返回: {daily_rsi, weekly_rsi, monthly_trend, resonance}
        """
        result = {"daily_rsi": None, "weekly_rsi": None, "monthly_trend": "unknown",
                  "resonance": "none", "resonance_score": 0}
        
        if len(closes) >= 14:
            result["daily_rsi"] = self.calculate_rsi(closes, 14)
        if len(closes) >= 70:
            weekly_closes = closes[-70::5] if len(closes) >= 70 else closes[::5]
            if len(weekly_closes) >= 14:
                result["weekly_rsi"] = self.calculate_rsi(np.array(weekly_closes), 14)
        if len(closes) >= 200:
            monthly_closes = closes[-200::20] if len(closes) >= 200 else closes[::20]
            if len(monthly_closes) >= 2:
                result["monthly_trend"] = "up" if monthly_closes[-1] > monthly_closes[-2] else "down"
        
        # 共振检测
        resonance_score = 0
        signals = []
        if result["daily_rsi"] is not None:
            if result["daily_rsi"] > 60:
                resonance_score += 1
                signals.append("日线偏多")
            elif result["daily_rsi"] < 40:
                resonance_score -= 1
                signals.append("日线偏空")
        if result["weekly_rsi"] is not None:
            if result["weekly_rsi"] > 60:
                resonance_score += 2
                signals.append("周线偏多")
            elif result["weekly_rsi"] < 40:
                resonance_score -= 2
                signals.append("周线偏空")
        if result["monthly_trend"] == "up":
            resonance_score += 2
            signals.append("月线上行")
        elif result["monthly_trend"] == "down":
            resonance_score -= 2
            signals.append("月线下行")
        
        if resonance_score >= 4:
            result["resonance"] = "强烈多头共振"
        elif resonance_score >= 2:
            result["resonance"] = "多头共振"
        elif resonance_score <= -4:
            result["resonance"] = "强烈空头共振"
        elif resonance_score <= -2:
            result["resonance"] = "空头共振"
        else:
            result["resonance"] = "无共振"
        
        result["resonance_score"] = resonance_score
        result["signals"] = signals
        return result

    def identify_trend(self, ma5: Optional[float], ma10: Optional[float], 
                      ma20: Optional[float], ma60: Optional[float],
                      ma120: Optional[float] = None,
                      volume_ratio: Optional[float] = None,
                      macd_hist: Optional[float] = None) -> Trend:
        """
        识别趋势（增强版v2）
        
        新增：
          - 量价确认：volume_ratio > 1.2 强化上升判断
          - MACD确认：macd_hist > 0 强化上升，< 0 强化下降
          - 五个趋势级别：UP / WEAK_UP / DOWN / WEAK_DOWN / SIDEWAYS
        """
        if not all([ma5, ma10, ma20, ma60]):
            return Trend.UNKNOWN
        
        # 均线排列方向
        is_bullish = ma5 > ma10 > ma20
        is_bearish = ma5 < ma10 < ma20
        long_term_bullish = ma20 > ma60 if ma60 else False
        long_term_bearish = ma20 < ma60 if ma60 else False
        
        # 量价与MACD辅助确认
        vol_confirm = volume_ratio is not None and volume_ratio > 1.2
        vol_deny = volume_ratio is not None and volume_ratio < 0.6
        macd_bull = macd_hist is not None and macd_hist > 0
        macd_bear = macd_hist is not None and macd_hist < 0
        
        # 上升趋势（多头排列）
        if is_bullish and long_term_bullish:
            # MA5 > MA120 是强确认
            if ma120 and ma5 > ma120:
                # 量价+MACD双重确认 → 强UP
                if vol_confirm and macd_bull:
                    return Trend.UP
                # 至少一个确认 → UP
                if vol_confirm or macd_bull:
                    return Trend.UP
                # 纯均线多头但无辅助确认 → 还是UP
                return Trend.UP
            # 短期多头但长期还不稳
            if vol_confirm or macd_bull:
                return Trend.WEAK_UP
            return Trend.WEAK_UP
        
        # 下降趋势（空头排列）
        if is_bearish and long_term_bearish:
            if vol_deny or macd_bear:
                return Trend.DOWN
            return Trend.DOWN
        
        # 短期多头但长期空头（或反之）— 分歧
        if is_bullish and not long_term_bullish:
            if macd_bull:
                return Trend.WEAK_UP
            return Trend.SIDEWAYS
        if is_bearish and not long_term_bearish:
            if macd_bear:
                return Trend.WEAK_DOWN
            return Trend.SIDEWAYS
        
        # 横盘（均线纠缠）
        if ma20:
            ma_diff = [ma5/ma20 - 1 if ma20 else 0,
                       ma10/ma20 - 1 if ma20 else 0]
            if all(abs(d) < 0.03 for d in ma_diff):
                # 均线纠缠时看MACD方向
                if macd_bull:
                    return Trend.WEAK_UP
                if macd_bear:
                    return Trend.WEAK_DOWN
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
        
        # v3.1: StochRSI判断（比RSI更灵敏）
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k < 0.15:
                score += 3
                reasons.append(f"StochRSI深度超卖({indicators.stoch_rsi_k:.2f})")
            elif indicators.stoch_rsi_k < 0.25:
                score += 1
            elif indicators.stoch_rsi_k > 0.85:
                score -= 3
                reasons.append(f"StochRSI深度超买({indicators.stoch_rsi_k:.2f})")
            elif indicators.stoch_rsi_k > 0.75:
                score -= 1
        
        # v3.1: ADX趋势强度
        if indicators.adx is not None:
            if indicators.adx > 30:
                # 强趋势市场，方向由+DI/-DI决定
                if indicators.plus_di and indicators.minus_di:
                    if indicators.plus_di > indicators.minus_di:
                        score += 2
                        reasons.append(f"ADX强趋势+DI上行({indicators.adx:.1f})")
                    else:
                        score -= 2
                        reasons.append(f"ADX强趋势-DI下行({indicators.adx:.1f})")
        
        # v3.3: 量价背离检测
        if indicators.volume_divergence is not None:
            if indicators.volume_divergence < -0.3:
                score -= 3
                reasons.append(f"⚠️ 量价背离({indicators.volume_divergence:.2f})，放量下跌风险")
            elif indicators.volume_divergence > 0.5:
                score += 2
                reasons.append(f"量价同步({indicators.volume_divergence:.2f})，放量上涨健康")
        
        # v3.3: 赫斯特指数趋势判断
        if indicators.hurst_exponent is not None:
            if indicators.hurst_exponent > 0.6:
                if price and (chg_pct > 0 or indicators.macd_hist and indicators.macd_hist > 0):
                    score += 2
                    reasons.append(f"赫斯特={indicators.hurst_exponent:.2f}，趋势持续")
            elif indicators.hurst_exponent < 0.4:
                reasons.append(f"赫斯特={indicators.hurst_exponent:.2f}，均值回归倾向")
        
        # v3.3: 肯特纳通道位置
        if indicators.keltner_upper and indicators.keltner_lower and price:
            if price > indicators.keltner_upper:
                score -= 1
                reasons.append("价格突破肯特纳上轨")
            elif price < indicators.keltner_lower:
                score += 1
                reasons.append("价格跌破肯特纳下轨")
        
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
        stoch_rsi_k, stoch_rsi_d = self.calculate_stoch_rsi(closes)
        adx, plus_di, minus_di = self.calculate_dmi_adx(highs, lows, closes)
        # v3.2新增指标
        vwap = self.calculate_vwap(highs, lows, closes, volumes)
        mfi = self.calculate_mfi(highs, lows, closes, volumes)
        poc, vah, val = self.calculate_volume_profile(closes, volumes)
        daily_atr_pct = self.calculate_daily_atr_pct(atr, price)
        multi_tf = self._multi_timeframe_analysis(closes, highs, lows)
        # v3.3新增计算
        vol_divergence = self.calculate_volume_divergence(closes, volumes)
        breadth_zscore = self.calculate_market_breadth_zscore(closes)
        hurst = self.calculate_hurst_exponent(closes)
        keltner_upper, keltner_mid, keltner_lower = self.calculate_keltner_channel(closes, highs, lows)
        
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
            stoch_rsi_k=stoch_rsi_k,
            stoch_rsi_d=stoch_rsi_d,
            adx=adx,
            plus_di=plus_di,
            minus_di=minus_di,
            # v3.2新增
            vwap=vwap,
            volume_profile_poc=poc,
            volume_profile_vah=vah,
            volume_profile_val=val,
            mfi=mfi,
            daily_atr_pct=daily_atr_pct,
            # v3.3新增
            volume_divergence=vol_divergence,
            market_breadth_zscore=breadth_zscore,
            hurst_exponent=hurst,
            keltner_upper=keltner_upper,
            keltner_mid=keltner_mid,
            keltner_lower=keltner_lower,
        )
        
        # 识别趋势（增强版：量价+MACD确认）
        trend = self.identify_trend(
            indicators.ma5, indicators.ma10, 
            indicators.ma20, indicators.ma60, indicators.ma120,
            volume_ratio=volume_ratio,
            macd_hist=indicators.macd_hist
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
        
        # KNN预测
        knn_pred, knn_conf = self._knn_predict(indicators, price, chg_pct, volume_ratio)
        
        # 市场机制检测
        regime = self.detect_market_regime(indicators, price, chg_pct, volume_ratio)
        regime_reasons = []
        if regime == MarketRegime.BULL:
            regime_reasons.append("📈 市场机制：牛市（多指标共振上升）")
        elif regime == MarketRegime.BEAR:
            regime_reasons.append("📉 市场机制：熊市（多指标共振下跌）")
        elif regime == MarketRegime.RANGE_BOUND:
            regime_reasons.append("📊 市场机制：震荡（牛熊信号均衡）")
        elif regime == MarketRegime.VOLATILE:
            regime_reasons.append("⚡ 市场机制：高波动（ATR放大+剧烈震荡）")
        elif regime == MarketRegime.QUIET:
            regime_reasons.append("💤 市场机制：低活跃（缩量+低波）")
        reasons.extend(regime_reasons)
        
        # KNN预测理由
        if knn_pred == "buy" and knn_conf > 0.7:
            reasons.append(f"🤖 ML(KNN)建议买入(置信度{knn_conf:.1%})")
        elif knn_pred == "sell" and knn_conf > 0.7:
            reasons.append(f"🤖 ML(KNN)建议卖出(置信度{knn_conf:.1%})")
        elif knn_pred in ("buy", "sell"):
            reasons.append(f"🤖 ML(KNN)建议{knn_pred}(置信度{knn_conf:.1%})")
        
        # 市场温度分析
        temp_reasons = self._calculate_market_temperature(indicators, chg_pct, volume_ratio)
        reasons.extend(temp_reasons)
        
        # v3.2: 多时间框架共振分析
        if multi_tf["resonance"] != "none":
            reasons.append(f"📊 多周期: {multi_tf['resonance']} (得分{multi_tf['resonance_score']})")
        
        # v3.2: VWAP位置分析
        if indicators.vwap and price:
            vwap_pct = (price - indicators.vwap) / indicators.vwap * 100
            if vwap_pct > 2:
                reasons.append(f"📈 价格高于VWAP {vwap_pct:+.1f}%")
            elif vwap_pct < -2:
                reasons.append(f"📉 价格低于VWAP {vwap_pct:+.1f}%")
        
        # v3.2: 成交量分布POC
        if indicators.volume_profile_poc:
            poc_pct = (price - indicators.volume_profile_poc) / indicators.volume_profile_poc * 100
            if abs(poc_pct) < 1:
                reasons.append(f"🎯 价格接近POC({indicators.volume_profile_poc:.2f})，关键价位")
        
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
        
        # v3.1: StochRSI评分调整
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k < 0.15:
                score += 8  # 深度超卖加分
            elif indicators.stoch_rsi_k > 0.85:
                score -= 8  # 深度超买减分
        
        # v3.1: ADX趋势评分
        if indicators.adx is not None:
            if indicators.adx > 30 and indicators.plus_di and indicators.minus_di:
                if indicators.plus_di > indicators.minus_di:
                    score += 10  # 强上升趋势
                else:
                    score -= 10  # 强下降趋势
        
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
        
        # 指标完整性 (v3.1: 增加新指标)
        complete_count = sum([
            indicators.rsi is not None,
            indicators.macd is not None,
            indicators.kdj_k is not None,
            indicators.cci is not None,
            indicators.adx is not None,
            indicators.stoch_rsi_k is not None,
        ])
        confidence += complete_count * 3
        
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
    
    def _knn_predict(self, indicators: TechnicalIndicators,
                     price: float,
                     chg_pct: float,
                     volume_ratio: Optional[float] = None) -> Tuple[str, float]:
        """
        简化版KNN预测（距离最近模式匹配）
        
        基于当前技术指标与内置参考模式的距离计算，
        返回 buy / hold / sell 以及置信度(0.0-1.0)。
        """
        # 预置参考模式（特征向量 + 标签）(v3.1: 新增StochRSI和ADX维度)
        # 特征顺序：[rsi_norm, macd_hist_norm, cci_norm, stoch_rsi_norm, adx_norm, chg_pct_norm, vol_ratio_norm]
        # 标签：1=买, 0=持有, -1=卖
        reference_patterns = [
            # [rsi, macd_hist, cci, stoch_rsi, adx, chg%, vol_ratio, label]
            # 强买入模式
            [0.15, -0.5, -0.8, 0.10, 0.2, -0.06, 1.5, 1],   # 深度超卖放量
            [0.20, -0.3, -0.7, 0.15, 0.1, -0.04, 1.8, 1],   # 超卖放量反弹
            [0.35, -0.1, -0.5, 0.25, 0.1, -0.03, 0.8, 1],   # 温和超卖缩量
            [0.40,  0.2,  0.1, 0.60, 0.3,  0.02, 1.2, 1],   # MACD刚金叉+StochRSI回升
            # 持有/观望模式
            [0.50,  0.0,  0.0, 0.50, 0.2,  0.00, 1.0, 0],   # 中性
            [0.55,  0.1,  0.2, 0.60, 0.2,  0.01, 0.9, 0],   # 微偏多
            [0.45, -0.1, -0.2, 0.40, 0.2, -0.01, 1.1, 0],   # 微偏空
            [0.60,  0.3,  0.5, 0.70, 0.3,  0.03, 1.4, 0],   # 偏多但未超买
            # 强卖出模式
            [0.80,  0.5,  0.7, 0.85, 0.4,  0.05, 2.0, -1],   # 超买放量
            [0.85,  0.6,  0.8, 0.90, 0.5,  0.07, 2.5, -1],   # 极度超买放量
            [0.75,  0.4,  0.6, 0.80, 0.3,  0.04, 1.8, -1],   # 高位放量
            [0.30, -0.4, -0.6, 0.30, 0.4, -0.05, 0.4, -1],   # 缩量阴跌
        ]
        
        # 构建当前特征向量 (8维)
        rsi_norm = (indicators.rsi / 100.0) if indicators.rsi is not None else 0.5
        macd_hist_norm = np.clip(indicators.macd_hist / 2.0, -1, 1) if indicators.macd_hist is not None else 0.0
        cci_norm = np.clip(indicators.cci / 300.0, -1, 1) if indicators.cci is not None else 0.0
        stoch_rsi_norm = indicators.stoch_rsi_k if indicators.stoch_rsi_k is not None else 0.5
        adx_norm = np.clip(indicators.adx / 50.0, 0, 1) if indicators.adx is not None else 0.3
        chg_pct_norm = np.clip(chg_pct / 10.0, -1, 1)
        vol_ratio_norm = np.clip((volume_ratio or 1.0) / 4.0, 0, 3)
        
        current_vec = np.array([rsi_norm, macd_hist_norm, cci_norm, 
                                stoch_rsi_norm, adx_norm, chg_pct_norm, vol_ratio_norm])
        
        # 计算加权欧氏距离 (v3.1: 引入新指标权重)
        weights = np.array([0.15, 0.20, 0.10, 0.20, 0.10, 0.10, 0.15])  # MACD+StochRSI权重最高
        
        best_dist = float('inf')
        best_label = 0
        second_label = 0
        second_dist = float('inf')
        
        for pattern in reference_patterns:
            vec = np.array(pattern[:7])
            label = pattern[7]
            dist = np.sqrt(np.sum(weights * (current_vec - vec) ** 2))
            if dist < best_dist:
                second_dist = best_dist
                second_label = best_label
                best_dist = dist
                best_label = label
            elif dist < second_dist:
                second_dist = dist
                second_label = label
        
        # 根据最近邻居标签决定最终预测
        if best_dist < 0.3 and best_label == second_label:
            # 两个最近邻居一致且距离很小 → 高置信度
            confidence = 0.8 + (0.3 - best_dist) / 0.3 * 0.2
        elif best_dist < 0.5:
            confidence = 0.6 + (0.5 - best_dist) / 0.5 * 0.3
        elif best_dist < 0.8:
            confidence = 0.5
        else:
            confidence = 0.3 + max(0, (1.0 - best_dist)) * 0.3
        
        # 标签转文字
        label_map = {1: "buy", 0: "hold", -1: "sell"}
        
        return label_map.get(best_label, "hold"), round(min(confidence, 0.99), 3)
    
    def detect_market_regime(self, indicators: TechnicalIndicators,
                             price: Optional[float] = None,
                             chg_pct: float = 0.0,
                             volume_ratio: Optional[float] = None) -> MarketRegime:
        """
        检测市场机制/状态
        
        综合所有指标判断当前市场处于哪种状态：
          - BULL: 强上升 + 量能确认
          - BEAR: 强下降 + 量能确认
          - RANGE_BOUND: 横盘震荡
          - VOLATILE: 高ATR + 大幅波动
          - QUIET: 低量 + 低波动
        """
        # ---- 构建评分信号 ----
        bull_score = 0
        bear_score = 0
        
        # 均线排列
        if indicators.ma5 and indicators.ma10 and indicators.ma20:
            if indicators.ma5 > indicators.ma10 > indicators.ma20:
                bull_score += 2
            elif indicators.ma5 < indicators.ma10 < indicators.ma20:
                bear_score += 2
        
        # RSI
        if indicators.rsi:
            if indicators.rsi > 60:
                bull_score += 1
            elif indicators.rsi < 40:
                bear_score += 1
        
        # MACD
        if indicators.macd_hist is not None:
            if indicators.macd_hist > 0:
                bull_score += 2
            else:
                bear_score += 2
        
        # CCI
        if indicators.cci is not None:
            if indicators.cci > 50:
                bull_score += 1
            elif indicators.cci < -50:
                bear_score += 1
        
        # 量能
        if volume_ratio is not None:
            if volume_ratio > 1.5 and chg_pct > 0:
                bull_score += 1
            elif volume_ratio < 0.6 and chg_pct < 0:
                bear_score += 1
        
        # v3.1: StochRSI贡献
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k > 0.7:
                bull_score += 1
            elif indicators.stoch_rsi_k < 0.3:
                bear_score += 1
        
        # v3.1: ADX/DMI贡献
        if indicators.adx is not None and indicators.adx > 25:
            if indicators.plus_di and indicators.minus_di:
                if indicators.plus_di > indicators.minus_di:
                    bull_score += 2
                else:
                    bear_score += 2
        
        # ---- 波动率和活跃度检测 ----
        vol_high = False
        vol_low = False
        if indicators.atr and indicators.boll_mid:
            vol_ratio_val = indicators.atr / indicators.boll_mid
            if vol_ratio_val > 0.04:
                vol_high = True
            elif vol_ratio_val < 0.01:
                vol_low = True
        
        quiet_volume = volume_ratio is not None and volume_ratio < 0.5
        
        # ---- 综合判定 ----
        # 高波动优先
        if vol_high and abs(chg_pct) > 4:
            return MarketRegime.VOLATILE
        
        # 牛/熊判定
        if bull_score >= 5 and (volume_ratio is None or volume_ratio > 1.0):
            return MarketRegime.BULL
        if bear_score >= 5 and (volume_ratio is None or volume_ratio > 1.0):
            return MarketRegime.BEAR
        
        # 低活跃
        if quiet_volume and vol_low:
            return MarketRegime.QUIET
        
        # 震荡
        bull_bear_diff = abs(bull_score - bear_score)
        if bull_bear_diff <= 2:
            return MarketRegime.RANGE_BOUND
        if bull_bear_diff <= 3:
            if bull_score > bear_score:
                return MarketRegime.BULL
            return MarketRegime.BEAR
        
        return MarketRegime.UNKNOWN
    
    def _calculate_market_temperature(self, indicators: TechnicalIndicators, 
                                       chg_pct: float,
                                       volume_ratio: Optional[float] = None) -> List[str]:
        """
        计算市场温度（v2 - 改进版标签与阈值）
        
        冻结信号：
        - 量比 < 0.5 且跌幅 > 2%（缩量下跌，score+=3）
        - RSI < 25 且 MACD为负（score+=2）
        - 价格连续走弱（score+=1）
        
        解冻信号：
        - 量比 > 1.8 且涨幅 > 1.5%（放量上涨，score+=3）
        - RSI从<35区间回升到>35（score+=2）
        - MACD柱状图由负转正（score+=2）
        
        过热信号：
        - RSI > 78 且量比 > 1.8（score+=3）
        - 价格突破布林上轨且CCI > 120（score+=2）
        - MACD柱大幅为正且急剧增大（score+=2）
        
        返回格式：包含🌡️状态标签的分析理由列表
        """
        reasons = []
        
        freeze_score = 0
        thaw_score = 0
        overheat_score = 0
        
        # ---- 量价分析（权重最高） ----
        if volume_ratio is not None:
            if volume_ratio < 0.5 and chg_pct < -2:
                freeze_score += 3
                reasons.append("❄️ 缩量下跌（量<0.5, 跌>2%），市场冻结信号")
            elif volume_ratio > 1.8:
                if chg_pct > 4:
                    overheat_score += 3
                    reasons.append(f"🔥 放量大涨（量>{volume_ratio:.1f}x, 涨{chg_pct:.1f}%），警惕过热")
                elif chg_pct > 1.5:
                    thaw_score += 3
                    reasons.append(f"🔥 放量上涨（量>{volume_ratio:.1f}x, 涨{chg_pct:.1f}%），市场升温")
            elif volume_ratio < 0.3:
                freeze_score += 1
                reasons.append("❄️ 极度缩量(<0.3x)，流动性不足")
            elif volume_ratio < 0.6:
                freeze_score += 1
                reasons.append(f"🌡️ 量能偏弱({volume_ratio:.1f}x)，市场偏冷")
        
        # ---- RSI分析 ----
        if indicators.rsi:
            if indicators.rsi < 18:
                freeze_score += 2
                reasons.append(f"❄️ RSI深度超卖({indicators.rsi:.1f})")
            elif indicators.rsi < 30:
                freeze_score += 1
                reasons.append(f"❄️ RSI偏低({indicators.rsi:.1f})，市场偏冷")
            elif indicators.rsi > 80:
                overheat_score += 3
                reasons.append(f"🔥 RSI高位({indicators.rsi:.1f})，严重超买")
            elif indicators.rsi > 70:
                overheat_score += 1
                reasons.append(f"🔥 RSI偏高({indicators.rsi:.1f})，超买区")
            elif 40 <= indicators.rsi <= 60:
                thaw_score += 1
                reasons.append(f"🌡️ RSI中性({indicators.rsi:.1f})，市场温和")
        
        # ---- MACD分析 ----
        if indicators.macd_hist is not None:
            if indicators.macd_hist < -1.0:
                freeze_score += 2
                reasons.append(f"❄️ MACD柱深负({indicators.macd_hist:.3f})，空头动能强")
            elif indicators.macd_hist < -0.3:
                freeze_score += 1
                reasons.append(f"❄️ MACD柱为负({indicators.macd_hist:.3f})，偏空")
            elif indicators.macd_hist > 1.0:
                overheat_score += 2
                reasons.append(f"🔥 MACD柱大幅为正({indicators.macd_hist:.3f})，动能过强")
            elif indicators.macd_hist > 0.3:
                thaw_score += 2
                reasons.append(f"🔥 MACD柱为正({indicators.macd_hist:.3f})，偏多")
        
        # ---- 布林带分析 ----
        if indicators.boll_upper and indicators.boll_lower and indicators.boll_mid:
            boll_width_pct = (indicators.boll_upper - indicators.boll_lower) / indicators.boll_mid * 100
            if boll_width_pct < 3:
                freeze_score += 1
                reasons.append(f"🌡️ 布林带极度收窄({boll_width_pct:.1f}%)，即将方向选择")
            elif boll_width_pct < 6:
                reasons.append(f"🌡️ 布林带收窄({boll_width_pct:.1f}%)，蓄势待发")
            elif boll_width_pct > 25:
                overheat_score += 1
                reasons.append(f"🌡️ 布林带扩张({boll_width_pct:.1f}%)，波动加大")
        
        # ---- CCI分析 ----
        if indicators.cci is not None:
            if indicators.cci < -200:
                freeze_score += 2
                reasons.append(f"❄️ CCI深度超卖({indicators.cci:.1f})")
            elif indicators.cci < -100:
                freeze_score += 1
            elif indicators.cci > 200:
                overheat_score += 2
                reasons.append(f"🔥 CCI深度超买({indicators.cci:.1f})")
            elif indicators.cci > 100:
                overheat_score += 1
        
        # ---- v3.1: 新增指标温度分析 ----
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k < 0.15:
                freeze_score += 2
                reasons.append(f"❄️ StochRSI深度超卖({indicators.stoch_rsi_k:.2f})")
            elif indicators.stoch_rsi_k < 0.30:
                freeze_score += 1
            elif indicators.stoch_rsi_k > 0.85:
                overheat_score += 2
                reasons.append(f"🔥 StochRSI深度超买({indicators.stoch_rsi_k:.2f})")
            elif indicators.stoch_rsi_k > 0.70:
                overheat_score += 1
            elif 0.40 <= indicators.stoch_rsi_k <= 0.60:
                thaw_score += 1
        
        if indicators.adx is not None:
            if indicators.adx > 40:
                overheat_score += 2
                reasons.append(f"🌡️ ADX趋势极强({indicators.adx:.1f})，方向选择完成")
            elif indicators.adx > 25:
                direction = "上升" if (indicators.plus_di or 0) > (indicators.minus_di or 0) else "下降"
                reasons.append(f"🌡️ ADX趋势确立({indicators.adx:.1f})，{direction}方向")
            elif indicators.adx < 15:
                freeze_score += 1
                reasons.append(f"🌡️ ADX极低({indicators.adx:.1f})，无方向")
        
        # ---- 综合判定（改进的逻辑链） ----
        max_score = max(freeze_score, thaw_score, overheat_score)
        
        if max_score <= 1:
            reasons.append("🌡️ 市场状态：正常")
        elif overheat_score == max_score and overheat_score >= 3:
            reasons.append("🌡️ 市场状态：过热🔥🔥 注意风险控制")
        elif overheat_score == max_score and overheat_score >= 2:
            reasons.append("🌡️ 市场状态：偏热🔥 短线谨慎")
        elif freeze_score == max_score and freeze_score >= 3:
            reasons.append("🌡️ 市场状态：冻结❄️❄️ 建议观望")
        elif freeze_score == max_score and freeze_score >= 2:
            reasons.append("🌡️ 市场状态：偏冷❄️ 等待企稳")
        elif thaw_score == max_score and thaw_score >= 3:
            reasons.append("🌡️ 市场状态：升温🔥 关注机会")
        elif thaw_score == max_score and thaw_score >= 2:
            reasons.append("🌡️ 市场状态：回暖🌤️ 逐步乐观")
        else:
            reasons.append("🌡️ 市场状态：正常")
        
        return reasons
    
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
        
        # v3.1: 新增指标理由
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k < 0.2:
                reasons.append(f"StochRSI超卖({indicators.stoch_rsi_k:.2f})")
            elif indicators.stoch_rsi_k > 0.8:
                reasons.append(f"StochRSI超买({indicators.stoch_rsi_k:.2f})")
        
        if indicators.adx is not None:
            if indicators.adx > 25:
                direction = "上升" if (indicators.plus_di or 0) > (indicators.minus_di or 0) else "下降"
                reasons.append(f"ADX趋势强({indicators.adx:.1f})，{direction}方向")
            elif indicators.adx < 20:
                reasons.append(f"ADX偏低({indicators.adx:.1f})，震荡行情")
        
        if indicators.plus_di is not None and indicators.minus_di is not None:
            if indicators.plus_di > indicators.minus_di + 5:
                reasons.append(f"+DI领先({indicators.plus_di:.1f} vs {indicators.minus_di:.1f})，上升动能强")
            elif indicators.minus_di > indicators.plus_di + 5:
                reasons.append(f"-DI领先({indicators.minus_di:.1f} vs {indicators.plus_di:.1f})，下降动能强")
        
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
        
        # v3.1: 新增指标预警
        if indicators.stoch_rsi_k is not None:
            if indicators.stoch_rsi_k < 0.1:
                warnings.append(f"⚠️ StochRSI极度超卖({indicators.stoch_rsi_k:.3f})")
            elif indicators.stoch_rsi_k > 0.9:
                warnings.append(f"⚠️ StochRSI极度超买({indicators.stoch_rsi_k:.3f})")
        
        if indicators.adx is not None and indicators.adx > 40:
            warnings.append(f"⚠️ ADX趋势极强({indicators.adx:.1f})，注意趋势末端反转")
        elif indicators.adx is not None and indicators.adx < 15:
            warnings.append(f"⚠️ ADX极低({indicators.adx:.1f})，无明显趋势")
        
        # v3.3: 量价背离警告
        if indicators.volume_divergence is not None:
            if indicators.volume_divergence < -0.5:
                warnings.append(f"🚨 严重量价背离({indicators.volume_divergence:.2f})，放量下跌/缩量上涨")
            elif indicators.volume_divergence < -0.2:
                warnings.append(f"⚠️ 轻微量价背离({indicators.volume_divergence:.2f})")
        
        # v3.3: 赫斯特指数警告
        if indicators.hurst_exponent is not None:
            if indicators.hurst_exponent < 0.35:
                warnings.append(f"⚠️ 赫斯特={indicators.hurst_exponent:.2f}，强均值回归，逆势风险高")
            elif indicators.hurst_exponent > 0.75:
                warnings.append(f"⚠️ 赫斯特={indicators.hurst_exponent:.2f}，极端趋势，反转概率增大")
        
        return warnings


# 批量分析器
    # ==================== v4.0增强: 恐慌/温度感知 ====================
    
    def augment_with_market_context(self, result: AnalysisResult,
                                     market_temperature: int = 50,
                                     panic_index: int = 60) -> AnalysisResult:
        """
        用市场环境(温度+恐慌指数)增强分析结果
        
        Args:
            result: 原始分析结果
            market_temperature: 市场温度(0-100)
            panic_index: 恐慌指数(0-100, 越低越恐慌)
        
        Returns:
            增强后的分析结果(引用修改)
        """
        # 温度修正
        if market_temperature < 25:
            result.reasons.append("🌡️ 市场冰封(<25℃) - 强制空仓环境")
            result.warnings.append("🚨 V10冰封: 温度<25℃, 所有买入信号降级")
            # 降级信号
            if result.signal in (SignalStrength.STRONG_BUY, SignalStrength.BUY):
                result.signal = SignalStrength.HOLD
                result.score = min(result.score, 40)
        elif market_temperature < 35:
            result.reasons.append("🌡️ 市场冰点(<35℃) - 禁止新开仓(R18)")
            if result.signal == SignalStrength.STRONG_BUY:
                result.signal = SignalStrength.BUY
                result.score = min(result.score, 55)
        elif market_temperature < 50:
            result.reasons.append(f"🌡️ 市场偏冷({market_temperature}℃) - 谨慎参与")
        
        # 恐慌修正
        if panic_index < 25:
            result.reasons.append(f"😱 恐慌指数{panic_index} - 全面禁止交易(V10)")
            result.warnings.append(f"🚨 V10: 恐慌{panic_index}<25, 所有买入信号无效")
            result.signal = SignalStrength.HOLD
            result.score = min(result.score, 30)
            result.sentiment = MarketSentiment.BEARISH
        elif panic_index < 40:
            result.reasons.append(f"😰 恐慌指数{panic_index}<40 - 偏冷谨慎")
            if result.signal == SignalStrength.STRONG_BUY:
                result.signal = SignalStrength.BUY
            result.confidence *= 0.8
        
        # 温度仓位建议
        if market_temperature >= 80:
            result.reasons.append("🎯 仓位建议: ≤10%(极度活跃)")
        elif market_temperature >= 70:
            result.reasons.append("🎯 仓位建议: ≤20%(活跃)")
        elif market_temperature >= 50:
            result.reasons.append("🎯 仓位建议: ≤50%(正常)")
        elif market_temperature >= 35:
            result.reasons.append("🎯 仓位建议: ≤30%(偏冷)")
        elif market_temperature >= 25:
            result.reasons.append("🎯 仓位建议: ≤10%(寒冷,只出不进)")
        else:
            result.reasons.append("🎯 仓位建议: 0%(冰封,强制空仓)")
        
        return result


    def analyze_with_context(self, code: str, name: str,
                            kline_data: List[Dict],
                            market_temperature: int = 50,
                            panic_index: int = 60,
                            current_price: float = None,
                            chg_pct: float = 0.0,
                            volume_ratio: float = None) -> AnalysisResult:
        """带市场环境的综合分析"""
        result = self.analyze_stock(code, name, kline_data, current_price, chg_pct, volume_ratio)
        return self.augment_with_market_context(result, market_temperature, panic_index)


class BatchAnalyzer:
    """批量股票分析器"""
    
    def __init__(self, max_workers: int = 4):
        self.analyzer = DataAnalyzerV2()
        self.max_workers = max_workers
        self._batch_cache: Dict[str, Dict[str, AnalysisResult]] = {}  # {batch_id: {code: result}}
        self._batch_cache_max = 10  # 最多缓存10个批次
    
    def _get_batch_cache_key(self, stocks: List[Dict]) -> str:
        """生成批次缓存键"""
        if not stocks:
            return ""
        # 使用股票代码列表 + 最后一条数据的时间戳作为缓存键
        codes = [s.get('code', '') for s in stocks]
        last_updates = []
        for s in stocks:
            kline = s.get('kline', [])
            if kline:
                last_updates.append(kline[-1].get('date', ''))
        return hashlib.md5(f"batch_{codes}_{last_updates}".encode()).hexdigest()[:16]
    
    def analyze_batch(self, stocks: List[Dict]) -> List[AnalysisResult]:
        """
        批量分析多只股票
        
        支持缓存：同一批次键命中时直接返回缓存结果
        """
        cache_key = self._get_batch_cache_key(stocks)
        if not cache_key:
            return []
        
        # 检查缓存
        if cache_key in self._batch_cache:
            logger.debug(f"BatchAnalyzer 缓存命中: {cache_key}")
            cached = self._batch_cache[cache_key]
            # 返回缓存结果的副本，保持原有顺序
            return [cached[s.get('code', '')] for s in stocks if s.get('code', '') in cached]
        
        results = []
        result_map = {}
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
                result_map[stock.get('code', '')] = result
            except Exception as e:
                logger.error(f"分析股票 {stock.get('code')} 失败: {e}")
        
        # 写入缓存
        if len(self._batch_cache) >= self._batch_cache_max:
            # LRU淘汰：移除最早的一个
            oldest_key = next(iter(self._batch_cache))
            del self._batch_cache[oldest_key]
        self._batch_cache[cache_key] = result_map
        
        return results
    
    def clear_cache(self):
        """清空批次缓存"""
        self._batch_cache.clear()
    
    def get_top_signals(self, results: List[AnalysisResult], 
                       signal: SignalStrength = SignalStrength.STRONG_BUY,
                       top_n: int = 10) -> List[AnalysisResult]:
        """获取最强信号股票"""
        filtered = [r for r in results if r.signal == signal]
        filtered.sort(key=lambda x: x.score, reverse=True)
        return filtered[:top_n]
    
    def correlation_matrix(self, results: List[AnalysisResult]) -> Dict[str, Any]:
        """计算多股票相关性矩阵 v3.2
        识别高度相关(>0.7)的股票对，用于分散化决策
        返回: {matrix: [[...]], high_corr_pairs: [...], diversification_score: float}
        """
        if len(results) < 2:
            return {"matrix": [], "high_corr_pairs": [], 
                    "diversification_score": 1.0, "error": "至少需要2只股票"}
        
        # 构建评分向量：用 score, rsi, trend数值作为特征
        features = {}
        for r in results:
            features[r.code] = {
                "score": r.score,
                "rsi": r.indicators.rsi if r.indicators.rsi else 50,
                "trend_val": 1 if r.trend == Trend.UP else (-1 if r.trend == Trend.DOWN else 0),
                "confidence": r.confidence,
            }
        
        codes = sorted(features.keys())
        n = len(codes)
        
        # 计算皮尔逊相关系数矩阵
        corr_matrix = np.zeros((n, n))
        for i in range(n):
            for j in range(n):
                if i == j:
                    corr_matrix[i][j] = 1.0
                    continue
                # 使用特征向量的简单相关性
                vi = np.array(list(features[codes[i]].values()))
                vj = np.array(list(features[codes[j]].values()))
                std_i, std_j = np.std(vi), np.std(vj)
                if std_i == 0 or std_j == 0:
                    corr_matrix[i][j] = 0.0
                else:
                    corr_matrix[i][j] = np.corrcoef(vi, vj)[0, 1]
        
        # 高相关对
        high_corr_pairs = []
        for i in range(n):
            for j in range(i + 1, n):
                if abs(corr_matrix[i][j]) > 0.7:
                    high_corr_pairs.append({
                        "pair": f"{codes[i]}-{codes[j]}",
                        "correlation": round(float(corr_matrix[i][j]), 3)
                    })
        
        # 分散化评分：1 - 平均相关性
        upper_tri = [corr_matrix[i][j] for i in range(n) for j in range(i+1, n)]
        avg_corr = np.mean(upper_tri) if upper_tri else 0
        div_score = round(1.0 - max(0, avg_corr), 3)
        
        return {
            "matrix": [[round(float(corr_matrix[i][j]), 3) for j in range(n)] for i in range(n)],
            "codes": codes,
            "high_corr_pairs": high_corr_pairs,
            "avg_correlation": round(float(avg_corr), 3),
            "diversification_score": div_score,
            "risk_warning": "集中度高, 建议分散" if div_score < 0.3 else ("适中" if div_score < 0.6 else "分散良好")
        }


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
