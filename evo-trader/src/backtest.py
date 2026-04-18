#!/usr/bin/env python3
"""
进化交易系统 - 回测引擎
"""
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from enum import Enum

from strategy_gene import StrategyGene, Action

@dataclass
class Trade:
    """交易记录"""
    date: pd.Timestamp
    symbol: str
    action: Action
    price: float
    shares: int
    value: float
    commission: float = 0.0
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    pnl: Optional[float] = None  # 平仓时的盈亏
    
    def __str__(self):
        action_str = "买入" if self.action == Action.BUY else "卖出"
        return f"{self.date.date()} {self.symbol} {action_str} {self.shares}股 @ ¥{self.price:.2f}"

@dataclass
class Position:
    """持仓记录"""
    symbol: str
    entry_date: pd.Timestamp
    entry_price: float
    shares: int
    current_price: float
    stop_loss: float
    take_profit: float
    max_hold_days: int
    
    @property
    def cost(self):
        return self.entry_price * self.shares
    
    @property
    def market_value(self):
        return self.current_price * self.shares
    
    @property
    def pnl(self):
        return self.market_value - self.cost
    
    @property
    def pnl_pct(self):
        return (self.current_price - self.entry_price) / self.entry_price
    
    def should_sell(self, current_date):
        """检查是否应该卖出"""
        # 检查止损
        if self.current_price <= self.stop_loss:
            return True, "止损"
        
        # 检查止盈
        if self.current_price >= self.take_profit:
            return True, "止盈"
        
        # 检查持有天数
        hold_days = (current_date - self.entry_date).days
        if hold_days >= self.max_hold_days:
            return True, "超时"
        
        return False, "持有"

class BacktestEngine:
    """回测引擎"""
    
    def __init__(self, initial_capital=100000):
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trades: List[Trade] = []
        self.equity_curve = []
        self.dates = []
        
    def calculate_technical_indicators(self, df: pd.DataFrame, gene: StrategyGene):
        """计算技术指标"""
        df = df.copy()
        
        # 移动平均线
        df['ma_fast'] = df['close'].rolling(window=gene.ma_fast).mean()
        df['ma_slow'] = df['close'].rolling(window=gene.ma_slow).mean()
        df['ma_signal'] = df['close'].rolling(window=gene.ma_signal).mean()
        
        # RSI计算
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=gene.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=gene.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))
        
        # 成交量均线
        df['volume_ma'] = df['volume'].rolling(window=gene.volume_ma_period).mean()
        df['volume_ratio'] = df['volume'] / df['volume_ma']
        
        # 价格趋势（简单斜率）
        df['trend'] = df['close'].rolling(window=5).apply(
            lambda x: np.polyfit(range(len(x)), x, 1)[0], raw=True
        )
        
        # 信号计算
        df['ma_cross_signal'] = 0
        df.loc[df['ma_fast'] > df['ma_slow'], 'ma_cross_signal'] = 1
        
        df['rsi_signal'] = 0
        df.loc[df['rsi'] < gene.rsi_oversold, 'rsi_signal'] = 1  # 超卖买入信号
        df.loc[df['rsi'] > gene.rsi_overbought, 'rsi_signal'] = -1  # 超买卖出信号
        
        df['volume_signal'] = 0
        df.loc[df['volume_ratio'] > gene.volume_multiplier, 'volume_signal'] = 1
        
        df['trend_signal'] = 0
        df.loc[df['trend'] > 0, 'trend_signal'] = 1
        
        # 综合信号
        df['signal_score'] = (
            gene.weight_ma_cross * df['ma_cross_signal'] +
            gene.weight_rsi_signal * df['rsi_signal'] +
            gene.weight_volume * df['volume_signal'] +
            gene.weight_trend * df['trend_signal']
        )
        
        return df
    
    def run(self, symbol: str, df: pd.DataFrame, gene: StrategyGene):
        """运行回测"""
        self.capital = self.initial_capital
        self.positions = {}
        self.trades = []
        self.equity_curve = []
        self.dates = []
        
        # 计算技术指标
        df = self.calculate_technical_indicators(df, gene)
        
        # 逐日回测
        for i in range(len(df)):
            date = df.index[i]
            row = df.iloc[i]
            
            # 更新持仓市值
            for pos in list(self.positions.values()):
                pos.current_price = row['close']
            
            # 检查持仓是否需要卖出
            for pos_symbol, position in list(self.positions.items()):
                should_sell, reason = position.should_sell(date)
                if should_sell:
                    self._close_position(pos_symbol, date, row['close'], reason)
            
            # 检查买入信号
            if symbol not in self.positions:
                # 计算可用资金
                used_capital = sum(pos.cost for pos in self.positions.values())
                available_capital = self.capital - used_capital
                
                if available_capital > 0 and row['signal_score'] > 0.5:
                    # 计算买入数量
                    position_value = available_capital * gene.position_size
                    price = row['close']
                    shares = int(position_value / price / 100) * 100  # 按手为单位
                    
                    if shares >= 100:  # 至少1手
                        # 计算止损止盈价
                        stop_loss = price * (1 - gene.stop_loss_pct)
                        take_profit = price * (1 + gene.take_profit_pct)
                        
                        # 记录买入
                        trade = Trade(
                            date=date,
                            symbol=symbol,
                            action=Action.BUY,
                            price=price,
                            shares=shares,
                            value=price * shares,
                            commission=price * shares * 0.0003,  # 万三佣金
                            stop_loss=stop_loss,
                            take_profit=take_profit
                        )
                        self.trades.append(trade)
                        
                        # 创建持仓
                        self.positions[symbol] = Position(
                            symbol=symbol,
                            entry_date=date,
                            entry_price=price,
                            shares=shares,
                            current_price=price,
                            stop_loss=stop_loss,
                            take_profit=take_profit,
                            max_hold_days=gene.max_hold_days
                        )
            
            # 计算当日总资产
            total_value = self.capital
            for pos in self.positions.values():
                total_value += pos.market_value
            
            self.equity_curve.append(total_value)
            self.dates.append(date)
        
        # 回测结束，清空所有持仓
        for pos_symbol in list(self.positions.keys()):
            if pos_symbol in self.positions:
                last_price = df.iloc[-1]['close']
                self._close_position(pos_symbol, df.index[-1], last_price, "回测结束")
        
        # 计算绩效指标
        metrics = self.calculate_metrics(df)
        return metrics
    
    def _close_position(self, symbol, date, price, reason):
        """平仓"""
        if symbol not in self.positions:
            return
        
        position = self.positions[symbol]
        
        # 计算盈亏
        pnl = (price - position.entry_price) * position.shares
        pnl_after_commission = pnl - (position.cost * 0.0003) - (price * position.shares * 0.001)  # 买入佣金+卖出印花税
        
        # 记录卖出交易
        trade = Trade(
            date=date,
            symbol=symbol,
            action=Action.SELL,
            price=price,
            shares=position.shares,
            value=price * position.shares,
            commission=price * position.shares * 0.001,  # 千一印花税
            pnl=pnl_after_commission
        )
        self.trades.append(trade)
        
        # 更新资金
        self.capital += price * position.shares - trade.commission
        
        # 移除持仓
        del self.positions[symbol]
        
        # 记录交易原因
        trade.reason = reason
    
    def calculate_metrics(self, df):
        """计算回测绩效指标"""
        if len(self.equity_curve) == 0:
            return {
                'total_return': 0.0,
                'annual_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'trade_count': 0,
                'avg_trade_return': 0.0
            }
        
        # 转换为numpy数组
        equity = np.array(self.equity_curve)
        dates = np.array(self.dates)
        
        # 总收益率
        total_return = (equity[-1] - equity[0]) / equity[0]
        
        # 年化收益率（假设一年252个交易日）
        if len(equity) > 1:
            days = (dates[-1] - dates[0]).days
            if days > 0:
                annual_return = (1 + total_return) ** (365 / days) - 1
            else:
                annual_return = total_return
        else:
            annual_return = total_return
        
        # 日收益率
        daily_returns = np.diff(equity) / equity[:-1]
        
        # 夏普比率（假设无风险利率为0）
        if len(daily_returns) > 0 and np.std(daily_returns) > 0:
            sharpe_ratio = np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)
        else:
            sharpe_ratio = 0.0
        
        # 最大回撤
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0.0
        
        # 交易统计
        sell_trades = [t for t in self.trades if t.action == Action.SELL and t.pnl is not None]
        trade_count = len(sell_trades)
        
        if trade_count > 0:
            win_trades = [t for t in sell_trades if t.pnl > 0]
            win_rate = len(win_trades) / trade_count
            
            total_profit = sum(t.pnl for t in win_trades)
            total_loss = sum(t.pnl for t in sell_trades if t.pnl <= 0)
            
            if abs(total_loss) > 0:
                profit_factor = total_profit / abs(total_loss)
            else:
                profit_factor = float('inf') if total_profit > 0 else 0.0
            
            avg_trade_return = sum(t.pnl for t in sell_trades) / trade_count
        else:
            win_rate = 0.0
            profit_factor = 0.0
            avg_trade_return = 0.0
        
        return {
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'trade_count': trade_count,
            'avg_trade_return': avg_trade_return,
            'final_capital': equity[-1] if len(equity) > 0 else self.initial_capital
        }
    
    def get_trade_summary(self):
        """获取交易摘要"""
        buy_trades = [t for t in self.trades if t.action == Action.BUY]
        sell_trades = [t for t in self.trades if t.action == Action.SELL]
        
        return {
            'total_trades': len(self.trades),
            'buy_trades': len(buy_trades),
            'sell_trades': len(sell_trades),
            'trades': [
                {
                    'date': str(t.date.date()),
                    'symbol': t.symbol,
                    'action': '买入' if t.action == Action.BUY else '卖出',
                    'price': t.price,
                    'shares': t.shares,
                    'value': t.value,
                    'pnl': t.pnl if t.action == Action.SELL else None
                }
                for t in self.trades[-10:]  # 只显示最近10笔
            ]
        }

class BacktestRunner:
    """回测运行器（多策略批量回测）"""
    
    def __init__(self, data_fetcher, initial_capital=100000):
        self.data_fetcher = data_fetcher
        self.initial_capital = initial_capital
        self.backtest_engine = BacktestEngine(initial_capital)
    
    def test_strategy(self, symbol, gene, days=60):
        """测试单个策略"""
        # 获取数据
        df = self.data_fetcher.get_daily_data(symbol, days)
        if df is None or len(df) < 30:
            return None
        
        # 运行回测
        metrics = self.backtest_engine.run(symbol, df, gene)
        
        return metrics
    
    def batch_test_strategies(self, symbols, genes):
        """批量测试策略"""
        results = []
        
        for gene in genes:
            # 在每个股票上测试策略
            strategy_results = []
            for symbol in symbols[:10]:  # 先用前10只股票测试
                metrics = self.test_strategy(symbol, gene)
                if metrics:
                    strategy_results.append(metrics)
            
            if strategy_results:
                # 计算平均绩效
                avg_return = np.mean([r['total_return'] for r in strategy_results])
                avg_sharpe = np.mean([r['sharpe_ratio'] for r in strategy_results])
                avg_drawdown = np.mean([r['max_drawdown'] for r in strategy_results])
                avg_win_rate = np.mean([r['win_rate'] for r in strategy_results])
                avg_trade_count = np.mean([r['trade_count'] for r in strategy_results])
                
                # 计算适应度（夏普比率为主，考虑收益率和回撤）
                fitness = avg_sharpe * (1 + avg_return) * (1 - abs(avg_drawdown))
                
                results.append({
                    'gene': gene,
                    'fitness': fitness,
                    'returns': avg_return,
                    'sharpe': avg_sharpe,
                    'max_drawdown': avg_drawdown,
                    'win_rate': avg_win_rate,
                    'trade_count': avg_trade_count,
                    'tested_symbols': len(strategy_results)
                })
        
        return results

if __name__ == "__main__":
    print("测试回测引擎...")
    
    # 创建模拟数据
    dates = pd.date_range('2026-01-01', periods=60, freq='D')
    np.random.seed(42)
    
    prices = 100 + np.cumsum(np.random.randn(60) * 2)
    volumes = np.random.randint(100000, 1000000, 60)
    
    df = pd.DataFrame({
        'open': prices * 0.99,
        'high': prices * 1.02,
        'low': prices * 0.98,
        'close': prices,
        'volume': volumes,
        'amount': prices * volumes
    }, index=dates)
    
    # 创建策略基因
    from strategy_gene import StrategyGene
    gene = StrategyGene.random_gene()
    
    # 运行回测
    engine = BacktestEngine(initial_capital=100000)
    metrics = engine.run('TEST', df, gene)
    
    print(f"策略绩效:")
    print(f"  总收益率: {metrics['total_return']:.2%}")
    print(f"  夏普比率: {metrics['sharpe_ratio']:.2f}")
    print(f"  最大回撤: {metrics['max_drawdown']:.2%}")
    print(f"  胜率: {metrics['win_rate']:.2%}")
    print(f"  交易次数: {metrics['trade_count']}")
    
    # 显示交易摘要
    summary = engine.get_trade_summary()
    print(f"\n交易统计: 总共 {summary['total_trades']} 笔交易")
    if summary['trades']:
        print("最近交易:")
        for trade in summary['trades']:
            action = trade['action']
            pnl_str = f" 盈亏: ¥{trade['pnl']:.2f}" if trade['pnl'] is not None else ""
            print(f"  {trade['date']} {trade['symbol']} {action} {trade['shares']}股 @ ¥{trade['price']:.2f}{pnl_str}")