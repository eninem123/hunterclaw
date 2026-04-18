#!/usr/bin/env python3
"""
进化交易系统 - 策略基因编码
"""
import random
import json
import numpy as np
from dataclasses import dataclass, asdict
from typing import List, Dict, Any
from enum import Enum

class Action(Enum):
    HOLD = 0
    BUY = 1
    SELL = -1

@dataclass
class StrategyGene:
    """策略基因 - 定义技术指标参数"""
    # 移动平均线参数
    ma_fast: int = 5      # 快线周期 5-20
    ma_slow: int = 20     # 慢线周期 20-60
    ma_signal: int = 9    # 信号线 5-15
    
    # RSI参数
    rsi_period: int = 14  # RSI周期 7-21
    rsi_overbought: int = 70  # 超买阈值 65-80
    rsi_oversold: int = 30    # 超卖阈值 20-35
    
    # 成交量参数
    volume_ma_period: int = 20  # 成交量均线周期 10-30
    volume_multiplier: float = 1.5  # 量比阈值 1.2-2.0
    
    # 风险参数
    position_size: float = 0.3  # 单次仓位比例 0.1-0.5
    stop_loss_pct: float = 0.05  # 止损比例 0.03-0.08
    take_profit_pct: float = 0.10  # 止盈比例 0.08-0.15
    max_hold_days: int = 10  # 最大持有天数 5-20
    
    # 入场条件权重
    weight_ma_cross: float = 0.3  # 均线金叉权重 0-1
    weight_rsi_signal: float = 0.3  # RSI信号权重 0-1
    weight_volume: float = 0.2  # 成交量权重 0-1
    weight_trend: float = 0.2  # 趋势权重 0-1
    
    @classmethod
    def random_gene(cls):
        """生成随机基因"""
        return cls(
            ma_fast=random.randint(5, 20),
            ma_slow=random.randint(20, 60),
            ma_signal=random.randint(5, 15),
            rsi_period=random.randint(7, 21),
            rsi_overbought=random.randint(65, 80),
            rsi_oversold=random.randint(20, 35),
            volume_ma_period=random.randint(10, 30),
            volume_multiplier=random.uniform(1.2, 2.0),
            position_size=random.uniform(0.1, 0.5),
            stop_loss_pct=random.uniform(0.03, 0.08),
            take_profit_pct=random.uniform(0.08, 0.15),
            max_hold_days=random.randint(5, 20),
            weight_ma_cross=random.random(),
            weight_rsi_signal=random.random(),
            weight_volume=random.random(),
            weight_trend=random.random()
        )
    
    def crossover(self, other: 'StrategyGene', mutation_rate=0.1):
        """交叉操作：生成子代基因"""
        child = StrategyGene()
        
        # 均匀交叉
        for field in self.__dataclass_fields__:
            if random.random() < 0.5:
                setattr(child, field, getattr(self, field))
            else:
                setattr(child, field, getattr(other, field))
        
        # 变异
        child.mutate(mutation_rate)
        
        return child
    
    def mutate(self, mutation_rate=0.1):
        """变异操作"""
        for field in self.__dataclass_fields__:
            if random.random() < mutation_rate:
                current = getattr(self, field)
                if isinstance(current, int):
                    # 整数类型变异
                    if 'period' in field or 'days' in field:
                        # 周期参数：±20% 变异
                        delta = int(current * 0.2)
                        new_value = current + random.randint(-delta, delta)
                        new_value = max(1, new_value)
                    elif 'ma' in field:
                        # 均线参数：±5 变异
                        new_value = current + random.randint(-5, 5)
                        new_value = max(1, new_value)
                    elif 'rsi' in field and ('overbought' in field or 'oversold' in field):
                        # RSI阈值：±5 变异
                        new_value = current + random.randint(-5, 5)
                        if 'overbought' in field:
                            new_value = min(90, max(60, new_value))
                        else:
                            new_value = min(40, max(10, new_value))
                    else:
                        # 其他整数：±10% 变异
                        delta = int(current * 0.1)
                        new_value = current + random.randint(-delta, delta)
                        new_value = max(1, new_value)
                
                elif isinstance(current, float):
                    # 浮点数类型变异
                    if 'pct' in field:
                        # 百分比参数：±20% 变异
                        delta = current * 0.2
                        new_value = current + random.uniform(-delta, delta)
                        new_value = max(0.01, min(0.5, new_value))
                    elif 'weight' in field:
                        # 权重参数：±0.2 变异，归一化到[0,1]
                        new_value = current + random.uniform(-0.2, 0.2)
                        new_value = max(0, min(1, new_value))
                    else:
                        # 其他浮点：±10% 变异
                        delta = current * 0.1
                        new_value = current + random.uniform(-delta, delta)
                        new_value = max(0.01, new_value)
                
                else:
                    # 其他类型不变异
                    continue
                
                setattr(self, field, new_value)
    
    def normalize_weights(self):
        """归一化权重参数"""
        weights = [
            self.weight_ma_cross,
            self.weight_rsi_signal,
            self.weight_volume,
            self.weight_trend
        ]
        total = sum(weights)
        if total > 0:
            self.weight_ma_cross = weights[0] / total
            self.weight_rsi_signal = weights[1] / total
            self.weight_volume = weights[2] / total
            self.weight_trend = weights[3] / total
    
    def to_dict(self):
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]):
        """从字典创建"""
        return cls(**data)
    
    def __str__(self):
        return f"策略基因: MA({self.ma_fast}/{self.ma_slow}) RSI({self.rsi_period}) 仓位{self.position_size:.1%}"

class StrategyPool:
    """策略池管理"""
    def __init__(self, pool_size=20):
        self.pool_size = pool_size
        self.strategies: List[Dict[str, Any]] = []
        self.fitness_scores = []
        
    def initialize_random(self):
        """初始化随机策略池"""
        self.strategies = []
        for _ in range(self.pool_size):
            gene = StrategyGene.random_gene()
            gene.normalize_weights()
            self.strategies.append({
                'id': len(self.strategies),
                'gene': gene,
                'fitness': 0.0,
                'returns': 0.0,
                'sharpe': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'trade_count': 0
            })
    
    def select_parents(self, num_parents=5):
        """选择父代策略（基于适应度）"""
        # 按适应度排序
        sorted_strategies = sorted(self.strategies, key=lambda x: x['fitness'], reverse=True)
        return sorted_strategies[:num_parents]
    
    def evolve(self, elite_count=3, mutation_rate=0.1):
        """进化一代"""
        # 按适应度排序
        self.strategies.sort(key=lambda x: x['fitness'], reverse=True)
        
        # 保留精英
        new_strategies = self.strategies[:elite_count]
        
        # 生成新策略
        while len(new_strategies) < self.pool_size:
            # 选择父代（轮盘赌选择）
            parent1 = self._roulette_select()
            parent2 = self._roulette_select()
            
            # 交叉产生子代
            child_gene = parent1['gene'].crossover(parent2['gene'], mutation_rate)
            child_gene.normalize_weights()
            
            new_strategies.append({
                'id': len(new_strategies),
                'gene': child_gene,
                'fitness': 0.0,
                'returns': 0.0,
                'sharpe': 0.0,
                'max_drawdown': 0.0,
                'win_rate': 0.0,
                'trade_count': 0
            })
        
        self.strategies = new_strategies
    
    def _roulette_select(self):
        """轮盘赌选择"""
        # 计算适应度总和
        total_fitness = sum(max(s['fitness'], 0.01) for s in self.strategies)
        pick = random.uniform(0, total_fitness)
        current = 0
        
        for strategy in self.strategies:
            current += max(strategy['fitness'], 0.01)
            if current >= pick:
                return strategy
        
        return self.strategies[0]  # 备选
    
    def update_fitness(self, strategy_id, fitness, returns, sharpe, max_drawdown, win_rate, trade_count):
        """更新策略适应度"""
        for s in self.strategies:
            if s['id'] == strategy_id:
                s['fitness'] = fitness
                s['returns'] = returns
                s['sharpe'] = sharpe
                s['max_drawdown'] = max_drawdown
                s['win_rate'] = win_rate
                s['trade_count'] = trade_count
                break
    
    def get_best_strategy(self):
        """获取最优策略"""
        if not self.strategies:
            return None
        return max(self.strategies, key=lambda x: x['fitness'])
    
    def save_to_file(self, filepath):
        """保存策略池到文件"""
        data = {
            'pool_size': self.pool_size,
            'strategies': [
                {
                    'id': s['id'],
                    'gene': s['gene'].to_dict(),
                    'fitness': s['fitness'],
                    'returns': s['returns'],
                    'sharpe': s['sharpe'],
                    'max_drawdown': s['max_drawdown'],
                    'win_rate': s['win_rate'],
                    'trade_count': s['trade_count']
                }
                for s in self.strategies
            ]
        }
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_from_file(self, filepath):
        """从文件加载策略池"""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.pool_size = data['pool_size']
        self.strategies = []
        for s_data in data['strategies']:
            self.strategies.append({
                'id': s_data['id'],
                'gene': StrategyGene.from_dict(s_data['gene']),
                'fitness': s_data['fitness'],
                'returns': s_data['returns'],
                'sharpe': s_data['sharpe'],
                'max_drawdown': s_data['max_drawdown'],
                'win_rate': s_data['win_rate'],
                'trade_count': s_data['trade_count']
            })

if __name__ == "__main__":
    # 测试策略基因
    print("测试策略基因...")
    gene1 = StrategyGene.random_gene()
    gene2 = StrategyGene.random_gene()
    
    print(f"基因1: {gene1}")
    print(f"基因2: {gene2}")
    
    # 测试交叉
    child = gene1.crossover(gene2)
    print(f"子代基因: {child}")
    
    # 测试策略池
    pool = StrategyPool(pool_size=10)
    pool.initialize_random()
    print(f"\n策略池初始化完成，共 {len(pool.strategies)} 个策略")
    
    # 设置一些假适应度
    for i, s in enumerate(pool.strategies):
        pool.update_fitness(s['id'], random.random(), 
                           random.uniform(-0.1, 0.3),
                           random.uniform(0, 2),
                           random.uniform(0, 0.15),
                           random.uniform(0.3, 0.7),
                           random.randint(5, 50))
    
    best = pool.get_best_strategy()
    print(f"最优策略适应度: {best['fitness']:.3f}")
    
    # 测试进化
    pool.evolve()
    print(f"进化后策略数: {len(pool.strategies)}")