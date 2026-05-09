#!/usr/bin/env python3
"""
进化交易系统 - 数据获取模块
"""
import os
import json
import pandas as pd
import akshare as ak
import socket
import time
from datetime import datetime, timedelta
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
                data = json.load(f)
            # 文件为空或无效时重新获取
            if data and len(data) > 0:
                return data
        
        # 如果没有缓存，获取沪深300成分股
        try:
            df = ak.index_stock_cons_sina(symbol="000300")
            stock_list = []
            for _, row in df.iterrows():
                # 兼容新旧akshare格式：新版返回600000，旧版返回sz600000
                code = str(row['code'])
                name = row['name']
                if code.startswith(('sz', 'sh')):
                    code = code[2:]
                if len(code) == 6 and code.isdigit():
                    stock_list.append({
                        'code': code,
                        'name': name,
                        'market': 'sh' if code.startswith(('0', '6')) else 'sz'
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
        if cache_file.exists() and cache_file.stat().st_size > 0:
            try:
                df = pd.read_parquet(cache_file)
                # 检查数据是否足够新
                if len(df) >= days and (datetime.now() - df.index[-1].to_pydatetime()).days < 2:
                    return df.tail(days)
            except Exception:
                pass  # 缓存损坏，重新获取
        
        # 从akshare获取数据，带重试和超时
        socket.setdefaulttimeout(10)
        last_err = None
        for attempt in range(2):
            try:
                df = ak.stock_zh_a_hist(symbol=symbol, period="daily", adjust="qfq")
                if df is None or df.empty:
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
                last_err = e
                if attempt < 2:
                    time.sleep(1)
        
        # 所有重试都失败，打印错误并返回None
        if last_err:
            print(f"获取 {symbol} 数据失败: {str(last_err)[:60]}")
        return None
    
    def get_market_data(self, days=60):
        """获取市场整体数据（上证指数）"""
        return self.get_daily_data('000001', days)
    
    def update_all_data(self, max_stocks=15):
        """更新股票数据（限制数量避免超时）"""
        # 只更新进化需要的股票（前max_stocks只）
        stocks_to_update = self.stock_pool[:max_stocks]
        print(f"快速更新 {len(stocks_to_update)} 只股票数据（已缓存优先）...")
        success = 0
        for i, stock in enumerate(stocks_to_update, 1):
            symbol = stock['code']
            # 检查是否已有有效缓存
            cache_file = self.quotes_dir / f"{symbol}.parquet"
            if cache_file.exists() and cache_file.stat().st_size > 0:
                try:
                    df = pd.read_parquet(cache_file)
                    if len(df) >= 30 and (datetime.now() - df.index[-1].to_pydatetime()).days < 2:
                        print(f"[{i}/{len(stocks_to_update)}] {stock['name']}({symbol}) 缓存命中")
                        success += 1
                        continue
                except Exception:
                    pass
            # 缓存无效，从网络获取
            df = self.get_daily_data(symbol)
            if df is not None:
                print(f"[{i}/{len(stocks_to_update)}] {stock['name']}({symbol}) 更新成功")
                success += 1
            else:
                print(f"[{i}/{len(stocks_to_update)}] {stock['name']}({symbol}) 失败")
        print(f"数据更新完成: {success}/{len(stocks_to_update)} 成功")
    
    def get_today_quotes(self):
        """获取今日实时行情（简化版）"""
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