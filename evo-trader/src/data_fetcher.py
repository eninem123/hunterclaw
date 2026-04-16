#!/usr/bin/env python3
"""
进化交易系统 - 数据获取模块
"""
import os
import json
import pandas as pd
from datetime import datetime, timedelta
import akshare as ak
import sqlite3
from pathlib import Path

class DataFetcher:
    def __init__(self, data_dir="data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quotes_dir = self.data_dir / "quotes"
        self.quotes_dir.mkdir(exist_ok=True)
        
        # 股票池（第一期先用沪深300成分股）
        self.stock_pool = self._load_stock_pool()
        
    def _load_stock_pool(self):
        """加载股票池（沪深300）"""
        pool_file = self.data_dir / "stock_pool.json"
        if pool_file.exists():
            with open(pool_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        
        # 如果没有缓存，获取沪深300成分股
        try:
            df = ak.index_stock_cons_sina(symbol="000300")
            stock_list = []
            for _, row in df.iterrows():
                # 解析代码和名称
                code = row['code']
                name = row['name']
                if code.startswith('sz') or code.startswith('sh'):
                    stock_code = code[2:]  # 去掉前缀
                    stock_list.append({
                        'code': stock_code,
                        'name': name,
                        'market': 'sh' if code.startswith('sh') else 'sz'
                    })
            
            # 保存到文件
            with open(pool_file, 'w', encoding='utf-8') as f:
                json.dump(stock_list, f, ensure_ascii=False, indent=2)
            return stock_list[:50]  # 先用前50只测试
        except Exception as e:
            print(f"获取股票池失败: {e}")
            # 返回一些示例股票
            return [
                {'code': '000001', 'name': '平安银行', 'market': 'sz'},
                {'code': '000002', 'name': '万科A', 'market': 'sz'},
                {'code': '600519', 'name': '贵州茅台', 'market': 'sh'},
                {'code': '000858', 'name': '五粮液', 'market': 'sz'},
                {'code': '002439', 'name': '启明星辰', 'market': 'sz'},
            ]
    
    def get_daily_data(self, symbol, days=60):
        """获取股票日K线数据"""
        cache_file = self.quotes_dir / f"{symbol}.parquet"
        
        # 检查缓存
        if cache_file.exists():
            df = pd.read_parquet(cache_file)
            # 检查数据是否足够新
            if len(df) >= days and (datetime.now() - df.index[-1].to_pydatetime()).days < 2:
                return df.tail(days)
        
        # 从akshare获取数据
        try:
            if symbol.startswith('6'):
                stock_code = f"sh{symbol}"
            else:
                stock_code = f"sz{symbol}"
            
            df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
            if df.empty:
                print(f"无法获取 {symbol} 数据")
                return None
            
            # 格式化数据
            df['日期'] = pd.to_datetime(df['日期'])
            df.set_index('日期', inplace=True)
            df = df[['开盘', '最高', '最低', '收盘', '成交量', '成交额']]
            df.columns = ['open', 'high', 'low', 'close', 'volume', 'amount']
            
            # 保存到缓存
            df.to_parquet(cache_file)
            
            return df.tail(days)
        except Exception as e:
            print(f"获取 {symbol} 数据失败: {e}")
            return None
    
    def get_market_data(self, days=60):
        """获取市场整体数据（上证指数）"""
        return self.get_daily_data('000001', days)
    
    def update_all_data(self):
        """更新所有股票数据"""
        print(f"开始更新 {len(self.stock_pool)} 只股票数据...")
        for i, stock in enumerate(self.stock_pool, 1):
            symbol = stock['code']
            df = self.get_daily_data(symbol)
            if df is not None:
                print(f"[{i}/{len(self.stock_pool)}] {stock['name']}({symbol}) 已更新，{len(df)} 天数据")
            else:
                print(f"[{i}/{len(self.stock_pool)}] {stock['name']}({symbol}) 更新失败")
        
        print("数据更新完成")
    
    def get_today_quotes(self):
        """获取今日实时行情（简化版）"""
        # 这里先返回昨日收盘价，后续可以接入实时API
        return {}

if __name__ == "__main__":
    fetcher = DataFetcher()
    # 测试获取数据
    print("获取平安银行数据...")
    df = fetcher.get_daily_data('000001', 20)
    if df is not None:
        print(f"获取到 {len(df)} 条数据")
        print(df.tail())
    else:
        print("获取失败")
    
    # 更新所有数据
    # fetcher.update_all_data()