#!/usr/bin/env python3
"""
进化交易系统 - 数据获取模块 v2（腾讯API + 缓存）
"""
import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

try:
    from tencent_api import TencentAPI
    TENCENT_AVAILABLE = True
except ImportError:
    TENCENT_AVAILABLE = False
    print("⚠️ 腾讯API模块未导入，将使用模拟数据")

class DataFetcherV2:
    """数据获取模块 v2 - 腾讯API优先，失败时降级"""
    
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quotes_dir = self.data_dir / "quotes"
        self.quotes_dir.mkdir(exist_ok=True)
        
        # 初始化腾讯API
        self.api = TencentAPI(str(self.quotes_dir)) if TENCENT_AVAILABLE else None
        
        # 股票池
        self.stock_pool = self._load_stock_pool()
        
    def _load_stock_pool(self) -> List[Dict]:
        """加载股票池"""
        pool_file = self.data_dir / "stock_pool.json"
        
        # 如果已有缓存，直接加载
        if pool_file.exists():
            try:
                with open(pool_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        
        # 生成股票池
        stock_list = []
        
        if self.api:
            try:
                # 从腾讯API获取股票列表
                stocks = self.api.get_stock_list(limit=50)
                stock_list = [
                    {
                        'code': s['code'],
                        'name': s.get('name', s['code']),
                        'market': s.get('market', 'sz' if s['code'].startswith('0') else 'sh')
                    }
                    for s in stocks
                ]
            except Exception as e:
                print(f"从API获取股票列表失败: {e}")
                stock_list = self._get_default_stock_pool()
        else:
            stock_list = self._get_default_stock_pool()
        
        # 保存到缓存
        try:
            with open(pool_file, 'w', encoding='utf-8') as f:
                json.dump(stock_list, f, ensure_ascii=False, indent=2)
        except:
            pass
        
        return stock_list
    
    def _get_default_stock_pool(self) -> List[Dict]:
        """获取默认股票池"""
        return [
            {'code': '000001', 'name': '平安银行', 'market': 'sz'},
            {'code': '000002', 'name': '万科A', 'market': 'sz'},
            {'code': '000858', 'name': '五粮液', 'market': 'sz'},
            {'code': '000333', 'name': '美的集团', 'market': 'sz'},
            {'code': '000651', 'name': '格力电器', 'market': 'sz'},
            {'code': '002415', 'name': '海康威视', 'market': 'sz'},
            {'code': '002475', 'name': '立讯精密', 'market': 'sz'},
            {'code': '002594', 'name': '比亚迪', 'market': 'sz'},
            {'code': '002439', 'name': '启明星辰', 'market': 'sz'},
            {'code': '300750', 'name': '宁德时代', 'market': 'sz'},
            {'code': '300059', 'name': '东方财富', 'market': 'sz'},
            {'code': '600519', 'name': '贵州茅台', 'market': 'sh'},
            {'code': '600036', 'name': '招商银行', 'market': 'sh'},
            {'code': '600276', 'name': '恒瑞医药', 'market': 'sh'},
            {'code': '600887', 'name': '伊利股份', 'market': 'sh'},
            {'code': '601318', 'name': '中国平安', 'market': 'sh'},
            {'code': '601398', 'name': '工商银行', 'market': 'sh'},
        ]
    
    def get_daily_data(self, symbol: str, days: int = 60) -> Optional[pd.DataFrame]:
        """获取股票日K线数据"""
        cache_file = self.quotes_dir / f"{symbol}_day_{days}.parquet"
        
        # 检查缓存（4小时有效）
        if cache_file.exists():
            cache_time = cache_file.stat().st_mtime
            if datetime.now().timestamp() - cache_time < 14400:  # 4小时
                try:
                    df = pd.read_parquet(cache_file)
                    if len(df) >= days * 0.7:  # 缓存数据足够
                        return df.tail(days)
                except Exception as e:
                    print(f"读取缓存失败 {symbol}: {e}")
        
        # 从API获取数据
        if self.api:
            try:
                df = self.api.get_kline(symbol, 'day', days * 2)  # 获取多一些数据
                if df is not None and len(df) > 0:
                    # 确保有足够的列
                    required_cols = ['open', 'high', 'low', 'close', 'volume']
                    for col in required_cols:
                        if col not in df.columns:
                            if col == 'volume':
                                df[col] = 1000000  # 默认值
                            else:
                                df[col] = df['close']  # 用收盘价填充
                    
                    # 添加成交额（如果没有）
                    if 'amount' not in df.columns:
                        df['amount'] = df['close'] * df['volume']
                    
                    # 保存到缓存
                    try:
                        df.to_parquet(cache_file)
                    except:
                        pass
                    
                    return df.tail(days)
            except Exception as e:
                print(f"API获取 {symbol} 数据失败: {e}")
        
        # 降级：生成模拟数据
        print(f"⚠️ {symbol} 使用模拟数据")
        return self._generate_mock_data(symbol, days)
    
    def _generate_mock_data(self, symbol: str, days: int) -> pd.DataFrame:
        """生成模拟数据（当API失败时）"""
        np.random.seed(hash(symbol) % 10000)
        
        # 生成日期
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days * 2)
        dates = pd.date_range(start_date, end_date, freq='D')
        
        # 生成价格序列（随机游走）
        n = len(dates)
        returns = np.random.normal(0.0005, 0.02, n)  # 日均0.05%，波动2%
        prices = 100 * np.exp(np.cumsum(returns))
        
        # 添加一些趋势
        trend = np.linspace(0, 0.1 if np.random.random() > 0.5 else -0.1, n)
        prices = prices * (1 + trend)
        
        # 生成OHLCV数据
        df = pd.DataFrame(index=dates)
        df['close'] = prices
        
        # 生成OHL（基于收盘价加减随机波动）
        df['open'] = df['close'].shift(1) * (1 + np.random.normal(0, 0.01, n))
        df['high'] = df[['open', 'close']].max(axis=1) * (1 + np.random.random(n) * 0.02)
        df['low'] = df[['open', 'close']].min(axis=1) * (1 - np.random.random(n) * 0.02)
        
        # 成交量
        df['volume'] = np.random.randint(1000000, 10000000, n)
        df['amount'] = df['close'] * df['volume']
        
        # 清理NaN
        df = df.bfill().ffill()
        
        # 只返回最近days天
        df = df.tail(days)
        
        return df
    
    def get_market_data(self, days: int = 60) -> Optional[pd.DataFrame]:
        """获取市场整体数据（上证指数）"""
        return self.get_daily_data('000001', days)
    
    def get_realtime_quotes(self, symbols: List[str] = None) -> Dict[str, Dict]:
        """获取实时行情"""
        if symbols is None:
            symbols = [s['code'] for s in self.stock_pool[:20]]
        
        if self.api:
            try:
                return self.api.get_realtime(symbols)
            except Exception as e:
                print(f"获取实时行情失败: {e}")
        
        # 降级：返回模拟实时数据
        result = {}
        for symbol in symbols:
            # 从缓存获取最新收盘价作为模拟实时价
            try:
                cache_file = self.quotes_dir / f"{symbol}_day_10.parquet"
                if cache_file.exists():
                    df = pd.read_parquet(cache_file)
                    last_price = df['close'].iloc[-1]
                else:
                    last_price = 100.0
                
                # 添加一些随机波动
                import random
                change_pct = random.uniform(-0.03, 0.03)
                price = last_price * (1 + change_pct)
                
                result[symbol] = {
                    'code': symbol,
                    'name': next((s['name'] for s in self.stock_pool if s['code'] == symbol), symbol),
                    'price': price,
                    'prev_close': last_price,
                    'change': price - last_price,
                    'change_pct': change_pct * 100,
                    'volume': random.randint(1000000, 10000000),
                    'amount': price * random.randint(1000000, 10000000),
                }
            except:
                pass
        
        return result
    
    def update_all_data(self):
        """更新所有股票数据"""
        print(f"开始更新 {len(self.stock_pool)} 只股票数据...")
        
        updated_count = 0
        for i, stock in enumerate(self.stock_pool, 1):
            symbol = stock['code']
            df = self.get_daily_data(symbol, 60)
            if df is not None and len(df) > 10:
                updated_count += 1
                if i % 10 == 0:
                    print(f"[{i}/{len(self.stock_pool)}] 已更新 {updated_count} 只股票")
        
        print(f"数据更新完成，成功更新 {updated_count}/{len(self.stock_pool)} 只股票")

# 测试
if __name__ == "__main__":
    print("测试数据获取模块 v2...")
    
    fetcher = DataFetcherV2()
    
    # 测试获取数据
    print("\n1. 测试获取平安银行数据...")
    df = fetcher.get_daily_data('000001', 20)
    if df is not None:
        print(f"  获取到 {len(df)} 条数据")
        print(f"  最新收盘价: ¥{df['close'].iloc[-1]:.2f}")
        print(f"  近期涨跌: {(df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]:.2%}")
    else:
        print("  获取失败")
    
    # 测试实时行情
    print("\n2. 测试实时行情...")
    realtime = fetcher.get_realtime_quotes(['000001', '600519', '002439'])
    for code, data in realtime.items():
        print(f"  {data['name']}({code}): ¥{data['price']:.2f} ({data['change_pct']:+.2f}%)")
    
    # 显示股票池
    print(f"\n3. 股票池: {len(fetcher.stock_pool)} 只股票")
    for stock in fetcher.stock_pool[:5]:
        print(f"  {stock['name']}({stock['code']})")