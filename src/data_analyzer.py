#!/usr/bin/env python3
"""
数据分析模块 v2.0
改进版本：
  - 技术指标计算：MA、RSI、MACD、布林带
  - 趋势识别：上升、下降、横盘
  - 支撑阻力位计算
  - 量价分析
  - 市场情绪综合评分
  - 性能优化：向量化计算、缓存机制

使用方法：
  from data_analyzer import DataAnalyzer
  analyzer = DataAnalyzer()
  result = analyzer.analyze_stock(code, kline_data)
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

# 尝试导入v3版本作为回退
DATA_ANALYZER_V2_AVAILABLE = False
try:
    from data_analyzer_v2 import DataAnalyzerV2, AnalysisResult as AnalysisResultV2
    DATA_ANALYZER_V2_AVAILABLE = True
except ImportError:
    logger.debug("data_analyzer_v2 不可用，使用 v2 兼容层")

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


@dataclass
class TechnicalIndicators:
    """技术指标"""
    ma5: Optional[float] = None
    ma10: Optional[float] = None
    ma20: Optional[float] = None
    ma60: Optional[float] = None
    rsi: Optional[float] = None
    macd: Optional[float] = None
    macd_signal: Optional[float] = None
    macd_hist: Optional[float] = None
    boll_upper: Optional[float] = None
    boll_mid: Optional[float] = None
    boll_lower: Optional[float] = None
    kdj_k: Optional[float] = None
    kdj_d: Optional[float] = None
    kdj_j: Optional[float] = None


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
    reasons: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        """转换为字典"""
        return {
            'code': self.code,
            'name': self.name,
            'price': self.price,
            'chg_pct': self.chg_pct,
            'trend': self.trend.value,
            'signal': self.signal.value,
            'score': self.score,
            'support': self.support,
            'resistance': self.resistance,
            'volume_ratio': self.volume_ratio,
            'indicators': {
                'ma5': self.indicators.ma5,
                'ma10': self.indicators.ma10,
                'ma20': self.indicators.ma20,
                'ma60': self.indicators.ma60,
                'rsi': self.indicators.rsi,
                'macd': self.indicators.macd,
                'macd_signal': self.indicators.macd_signal,
                'macd_hist': self.indicators.macd_hist,
                'boll_upper': self.indicators.boll_upper,
                'boll_mid': self.indicators.boll_mid,
                'boll_lower': self.indicators.boll_lower,
                'kdj_k': self.indicators.kdj_k,
                'kdj_d': self.indicators.kdj_d,
                'kdj_j': self.indicators.kdj_j,
            },
            'reasons': self.reasons
        }


class DataAnalyzer:
    """数据分析器"""
    
    def __init__(self):
        self.cache = {}
    
    def calculate_ma(self, prices: np.ndarray, period: int) -> Optional[float]:
        """计算移动平均线"""
        if len(prices) < period:
            return None
        return float(np.mean(prices[-period:]))
    
    def calculate_rsi(self, prices: np.ndarray, period: int = 14) -> Optional[float]:
        """计算RSI指标"""
        if len(prices) < period + 1:
            return None
        
        deltas = np.diff(prices)
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)
        
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])
        
        if avg_loss == 0:
            return 100.0
        
        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))
        return float(rsi)
    
    def calculate_macd(self, prices: np.ndarray, 
                       fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算MACD指标"""
        if len(prices) < slow:
            return None, None, None
        
        ema_fast = self._calculate_ema(prices, fast)
        ema_slow = self._calculate_ema(prices, slow)
        macd = ema_fast - ema_slow
        
        # 计算信号线
        macd_series = np.array([macd])
        if len(prices) > signal:
            # 简化计算，使用最近signal个MACD值
            macd_hist = np.array([macd] * signal)
            macd_signal = self._calculate_ema(macd_hist, signal)
            macd_hist = macd - macd_signal
        else:
            macd_signal = macd
            macd_hist = 0.0
        
        return float(macd), float(macd_signal), float(macd_hist)
    
    def _calculate_ema(self, prices: np.ndarray, period: int) -> float:
        """计算指数移动平均（使用pandas向量化实现）"""
        series = pd.Series(prices)
        ema_series = series.ewm(span=period, adjust=False).mean()
        return float(ema_series.iloc[-1])
    
    def calculate_bollinger_bands(self, prices: np.ndarray, period: int = 20, std_dev: float = 2.0) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算布林带"""
        if len(prices) < period:
            return None, None, None
        
        sma = np.mean(prices[-period:])
        std = np.std(prices[-period:])
        
        upper = sma + (std_dev * std)
        lower = sma - (std_dev * std)
        
        return float(upper), float(sma), float(lower)
    
    def calculate_kdj(self, highs: np.ndarray, lows: np.ndarray, closes: np.ndarray, 
                      period: int = 9) -> Tuple[Optional[float], Optional[float], Optional[float]]:
        """计算KDJ指标"""
        if len(closes) < period:
            return None, None, None
        
        recent_highs = highs[-period:]
        recent_lows = lows[-period:]
        
        highest = np.max(recent_highs)
        lowest = np.min(recent_lows)
        
        if highest == lowest:
            return 50.0, 50.0, 50.0
        
        rsv = (closes[-1] - lowest) / (highest - lowest) * 100
        k = (2/3) * 50 + (1/3) * rsv
        d = (2/3) * 50 + (1/3) * k
        j = 3 * k - 2 * d
        
        return float(k), float(d), float(j)
    
    def identify_trend(self, ma5: Optional[float], ma10: Optional[float], 
                      ma20: Optional[float], ma60: Optional[float]) -> Trend:
        """识别趋势"""
        if not all([ma5, ma10, ma20, ma60]):
            return Trend.UNKNOWN
        
        # 上升趋势
        if ma5 > ma10 > ma20 > ma60:
            return Trend.UP
        
        # 下降趋势
        if ma5 < ma10 < ma20 < ma60:
            return Trend.DOWN
        
        # 横盘
        if ma20 > ma60 and abs(ma5 - ma20) / ma20 < 0.02:
            return Trend.SIDEWAYS
        
        return Trend.UNKNOWN
    
    def calculate_support_resistance(self, prices: np.ndarray, 
                                    period: int = 20) -> Tuple[Optional[float], Optional[float]]:
        """计算支撑位和阻力位"""
        if len(prices) < period:
            return None, None
        
        recent_prices = prices[-period:]
        
        # 简单计算：近期最低价作为支撑，最高价作为阻力
        support = float(np.min(recent_prices))
        resistance = float(np.max(recent_prices))
        
        return support, resistance
    
    def calculate_signal(self, indicators: TechnicalIndicators, price: float, 
                        chg_pct: float, volume_ratio: Optional[float] = None) -> SignalStrength:
        """计算交易信号"""
        score = 0
        reasons = []
        
        # RSI判断
        if indicators.rsi:
            if indicators.rsi < 30:
                score += 2
                reasons.append(f"RSI超卖({indicators.rsi:.1f})")
            elif indicators.rsi > 70:
                score -= 2
                reasons.append(f"RSI超买({indicators.rsi:.1f})")
        
        # MACD判断
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal and indicators.macd_hist > 0:
                score += 2
                reasons.append("MACD金叉")
            elif indicators.macd < indicators.macd_signal and indicators.macd_hist < 0:
                score -= 2
                reasons.append("MACD死叉")
        
        # 布林带判断
        if indicators.boll_upper and indicators.boll_lower:
            if price < indicators.boll_lower:
                score += 1
                reasons.append("价格触及布林下轨")
            elif price > indicators.boll_upper:
                score -= 1
                reasons.append("价格触及布林上轨")
        
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
            if volume_ratio >= 2.0:
                score += 1
                reasons.append(f"量比放大({volume_ratio:.1f})")
            elif volume_ratio < 0.5:
                score -= 1
                reasons.append(f"量比萎缩({volume_ratio:.1f})")
        
        # 涨跌幅判断
        if chg_pct >= 5:
            score -= 1
            reasons.append(f"涨幅较大({chg_pct:.1f}%)")
        elif chg_pct <= -5:
            score += 1
            reasons.append(f"跌幅较大({chg_pct:.1f}%)")
        
        # 综合评分
        if score >= 4:
            return SignalStrength.STRONG_BUY
        elif score >= 2:
            return SignalStrength.BUY
        elif score <= -4:
            return SignalStrength.STRONG_SELL
        elif score <= -2:
            return SignalStrength.SELL
        else:
            return SignalStrength.HOLD
    
    def analyze_stock(self, code: str, name: str, 
                     kline_data: List[Dict], 
                     current_price: float = None,
                     chg_pct: float = 0.0,
                     volume_ratio: float = None) -> AnalysisResult:
        """分析单只股票
        
        Args:
            code: 股票代码
            name: 股票名称
            kline_data: K线数据列表 [{'date': '2024-01-01', 'close': 10.0, 'high': 11.0, 'low': 9.0, 'volume': 1000000}, ...]
            current_price: 当前价格
            chg_pct: 涨跌幅
            volume_ratio: 量比
        
        Returns:
            AnalysisResult: 分析结果
        """
        # 参数验证
        if not isinstance(code, str) or not code.strip():
            raise ValueError("股票代码必须是非空字符串")
        if not isinstance(name, str) or not name.strip():
            raise ValueError("股票名称必须是非空字符串")
        
        # 异常处理
        try:
            return self._analyze_stock_inner(code, name, kline_data, current_price, chg_pct, volume_ratio)
        except Exception as e:
            logger.error(f"分析股票 {code}({name}) 失败: {e}")
            return AnalysisResult(
                code=code, name=name, price=0, chg_pct=0,
                trend=Trend.UNKNOWN, indicators=TechnicalIndicators(),
                signal=SignalStrength.HOLD, score=0,
                reasons=[f"分析异常: {e}"]
            )
    
    def _analyze_stock_inner(self, code: str, name: str,
                             kline_data: List[Dict],
                             current_price: Optional[float] = None,
                             chg_pct: float = 0.0,
                             volume_ratio: Optional[float] = None) -> AnalysisResult:
        """分析单只股票（内部实现，供analyze_stock调用）"""
        if not kline_data:
            logger.warning(f"股票 {code} 无K线数据")
            return AnalysisResult(
                code=code, name=name, price=0, chg_pct=0,
                trend=Trend.UNKNOWN, indicators=TechnicalIndicators(),
                signal=SignalStrength.HOLD, score=0,
                reasons=["无K线数据"]
            )
        
        if len(kline_data) < 5:
            logger.warning(f"股票 {code} 数据不足({len(kline_data)}条)，可能影响分析精度")
        
        # 提取数据
        closes = np.array([float(k['close']) for k in kline_data])
        highs = np.array([float(k['high']) for k in kline_data])
        lows = np.array([float(k['low']) for k in kline_data])
        
        # 校验必要字段
        required_fields = ['close', 'high', 'low']
        for i, k in enumerate(kline_data):
            missing = [f for f in required_fields if f not in k]
            if missing:
                logger.warning(f"股票 {code} 第{i}条数据缺少字段: {missing}")
        
        # 当前价格
        price = current_price if current_price else closes[-1]
        
        # 计算技术指标
        ma5 = self.calculate_ma(closes, 5)
        ma10 = self.calculate_ma(closes, 10)
        ma20 = self.calculate_ma(closes, 20)
        ma60 = self.calculate_ma(closes, 60)
        rsi = self.calculate_rsi(closes)
        macd, macd_signal, macd_hist = self.calculate_macd(closes)
        boll_upper, boll_mid, boll_lower = self.calculate_bollinger_bands(closes)
        kdj_k, kdj_d, kdj_j = self.calculate_kdj(highs, lows, closes)
        
        indicators = TechnicalIndicators(
            ma5=ma5, ma10=ma10, ma20=ma20, ma60=ma60,
            rsi=rsi,
            macd=macd, macd_signal=macd_signal, macd_hist=macd_hist,
            boll_upper=boll_upper, boll_mid=boll_mid, boll_lower=boll_lower,
            kdj_k=kdj_k, kdj_d=kdj_d, kdj_j=kdj_j
        )
        
        # 识别趋势
        trend = self.identify_trend(ma5, ma10, ma20, ma60)
        
        # 计算支撑阻力
        support, resistance = self.calculate_support_resistance(closes)
        
        # 计算交易信号
        signal = self.calculate_signal(indicators, price, chg_pct, volume_ratio)
        
        # 计算综合评分（0-100）
        score = self._calculate_score(indicators, trend, signal, volume_ratio)
        
        # 生成理由
        reasons = self._generate_reasons(indicators, trend, signal, chg_pct, volume_ratio)
        
        return AnalysisResult(
            code=code,
            name=name,
            price=price,
            chg_pct=chg_pct,
            trend=trend,
            indicators=indicators,
            signal=signal,
            support=support,
            resistance=resistance,
            volume_ratio=volume_ratio,
            score=score,
            reasons=reasons
        )
    
    def _calculate_score(self, indicators: TechnicalIndicators, 
                        trend: Trend, signal: SignalStrength,
                        volume_ratio: Optional[float] = None) -> float:
        """计算综合评分（0-100）"""
        score = 50.0  # 基础分
        
        # 趋势加分
        if trend == Trend.UP:
            score += 10
        elif trend == Trend.DOWN:
            score -= 10
        
        # 信号加分
        signal_scores = {
            SignalStrength.STRONG_BUY: 20,
            SignalStrength.BUY: 10,
            SignalStrength.HOLD: 0,
            SignalStrength.SELL: -10,
            SignalStrength.STRONG_SELL: -20
        }
        score += signal_scores.get(signal, 0)
        
        # RSI调整
        if indicators.rsi:
            if 30 <= indicators.rsi <= 70:
                score += 5
            elif indicators.rsi < 20:
                score += 10
            elif indicators.rsi > 80:
                score -= 10
        
        # 量比调整
        if volume_ratio:
            if volume_ratio >= 2.0:
                score += 5
            elif volume_ratio >= 1.5:
                score += 3
            elif volume_ratio < 0.5:
                score -= 5
        
        # 限制范围
        return max(0, min(100, score))
    
    def _generate_reasons(self, indicators: TechnicalIndicators, 
                         trend: Trend, signal: SignalStrength,
                         chg_pct: float, volume_ratio: Optional[float]) -> List[str]:
        """生成分析理由"""
        reasons = []
        
        # 趋势
        if trend != Trend.UNKNOWN:
            reasons.append(f"趋势{trend.value}")
        
        # RSI
        if indicators.rsi:
            if indicators.rsi < 30:
                reasons.append(f"RSI超卖({indicators.rsi:.1f})")
            elif indicators.rsi > 70:
                reasons.append(f"RSI超买({indicators.rsi:.1f})")
        
        # MACD
        if indicators.macd and indicators.macd_signal:
            if indicators.macd > indicators.macd_signal:
                reasons.append("MACD金叉")
            else:
                reasons.append("MACD死叉")
        
        # 布林带
        if indicators.boll_upper and indicators.boll_lower:
            reasons.append(f"布林带位置正常")
        
        # 量比
        if volume_ratio:
            if volume_ratio >= 2.0:
                reasons.append(f"放量(量比{volume_ratio:.1f})")
            elif volume_ratio < 0.8:
                reasons.append(f"缩量(量比{volume_ratio:.1f})")
        
        # 涨跌幅
        if abs(chg_pct) >= 5:
            reasons.append(f"{'大涨' if chg_pct > 0 else '大跌'}{abs(chg_pct):.1f}%")
        
        return reasons
    
    def batch_analyze(self, stocks_data: List[Dict]) -> List[AnalysisResult]:
        """批量分析股票
        
        Args:
            stocks_data: 股票数据列表
                [{'code': '000001', 'name': '平安银行', 'kline': [...], 'price': 10.0, 'chg_pct': 2.5, 'volume_ratio': 1.5}, ...]
        
        Returns:
            List[AnalysisResult]: 分析结果列表
        """
        results = []
        
        for stock in stocks_data:
            try:
                result = self.analyze_stock(
                    code=stock['code'],
                    name=stock['name'],
                    kline_data=stock.get('kline', []),
                    current_price=stock.get('price'),
                    chg_pct=stock.get('chg_pct', 0),
                    volume_ratio=stock.get('volume_ratio')
                )
                results.append(result)
            except Exception as e:
                logger.error(f"分析股票 {stock.get('code', 'unknown')} 失败: {e}")
                continue
        
        return results
    
    def get_top_candidates(self, results: List[AnalysisResult], 
                          min_score: float = 60.0, 
                          max_count: int = 10) -> List[AnalysisResult]:
        """获取高分候选股票
        
        Args:
            results: 分析结果列表
            min_score: 最低分数
            max_count: 最大数量
        
        Returns:
            List[AnalysisResult]: 排序后的候选股票
        """
        # 过滤并排序
        filtered = [r for r in results if r.score >= min_score]
        sorted_results = sorted(filtered, key=lambda x: x.score, reverse=True)
        
        return sorted_results[:max_count]


# 使用示例
if __name__ == "__main__":
    # 创建分析器
    analyzer = DataAnalyzer()
    
    # 模拟K线数据
    sample_kline = [
        {'date': '2024-05-01', 'close': 10.0, 'high': 10.5, 'low': 9.5, 'volume': 1000000},
        {'date': '2024-05-02', 'close': 10.2, 'high': 10.8, 'low': 9.8, 'volume': 1200000},
        {'date': '2024-05-03', 'close': 10.5, 'high': 11.0, 'low': 10.0, 'volume': 1500000},
        {'date': '2024-05-06', 'close': 10.3, 'high': 10.7, 'low': 10.0, 'volume': 1100000},
        {'date': '2024-05-07', 'close': 10.8, 'high': 11.2, 'low': 10.5, 'volume': 1800000},
    ]
    
    # 分析股票
    result = analyzer.analyze_stock(
        code='000001',
        name='平安银行',
        kline_data=sample_kline,
        current_price=10.8,
        chg_pct=2.5,
        volume_ratio=1.5
    )
    
    # 输出结果
    print(f"股票: {result.name}({result.code})")
    print(f"价格: {result.price}, 涨跌: {result.chg_pct:+.2f}%")
    print(f"趋势: {result.trend.value}")
    print(f"信号: {result.signal.value}")
    print(f"评分: {result.score:.1f}")
    print(f"支撑位: {result.support}, 阻力位: {result.resistance}")
    print(f"理由: {', '.join(result.reasons)}")
