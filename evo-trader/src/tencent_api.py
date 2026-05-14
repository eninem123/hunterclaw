#!/usr/bin/env python3
"""
腾讯财经API接口（稳定版）
"""
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import Dict, List, Optional

class TencentAPI:
    """腾讯财经API封装"""
    
    def __init__(self, cache_dir="data/quotes"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://gu.qq.com/'
        })
    
    def get_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取实时行情"""
        results = {}
        
        # 分组请求，每10只股票一组
        for i in range(0, len(symbols), 10):
            batch = symbols[i:i+10]
            codes = []
            for symbol in batch:
                if symbol.startswith('6'):
                    codes.append(f'sh{symbol}')
                else:
                    codes.append(f'sz{symbol}')
            
            url = f"https://qt.gtimg.cn/q={','.join(codes)}"
            try:
                response = self.session.get(url, timeout=5)
                response.encoding = 'gbk'
                lines = response.text.strip().split('\n')
                
                for line in lines:
                    if '=' not in line:
                        continue
                    
                    parts = line.split('=')
                    if len(parts) != 2:
                        continue
                    
                    data_str = parts[1].strip('";')
                    data_parts = data_str.split('~')
                    
                    if len(data_parts) < 40:
                        continue
                    
                    # 解析股票数据
                    symbol_raw = data_parts[2]  # 股票代码
                    symbol = symbol_raw
                    results[symbol] = {
                        'code': symbol,
                        'name': data_parts[1],  # 股票名称
                        'price': float(data_parts[3]),  # 最新价
                        'prev_close': float(data_parts[4]),  # 昨收
                        'open': float(data_parts[5]),  # 今开
                        'high': float(data_parts[33]),  # 最高
                        'low': float(data_parts[34]),  # 最低
                        'volume': int(data_parts[6]),  # 成交量
                        'amount': float(data_parts[37]) * 10000,  # 成交额（万元→元）
                        'change': float(data_parts[31]),  # 涨跌额
                        'change_pct': float(data_parts[32]),  # 涨跌幅
                        'timestamp': data_parts[30] if len(data_parts) > 30 else '',
                    }
                    
            except Exception as e:
                print(f"获取实时行情失败: {e}")
                time.sleep(0.5)
        
        return results
    
    def get_kline(self, symbol: str, period: str = 'day', count: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据
        period: day, week, month, 5min, 15min, 30min, 60min
        """
        cache_file = self.cache_dir / f"{symbol}_{period}_{count}.parquet"
        
        # 检查缓存（2小时有效）
        if cache_file.exists():
            cache_time = cache_file.stat().st_mtime
            if time.time() - cache_time < 7200:  # 2小时
                try:
                    df = pd.read_parquet(cache_file)
                    if len(df) >= count * 0.8:  # 缓存数据足够
                        return df.tail(count)
                except:
                    pass
        
        # 确定前缀
        if symbol.startswith('6'):
            prefix = 'sh'
        else:
            prefix = 'sz'
        
        # 映射周期参数
        period_map = {
            'day': 'day',
            'week': 'week',
            'month': 'month',
            '5min': '5m',
            '15min': '15m',
            '30min': '30m',
            '60min': '60m'
        }
        
        period_code = period_map.get(period, 'day')
        
        # 腾讯K线API
        url = f"https://web.ifzq.gtimg.cn/appstock/app/fqkline/get"
        params = {
            'param': f'{prefix}{symbol},{period_code},,{count},qfq',
            '_var': 'kline_day',
            'r': str(int(time.time() * 1000))
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            # 解析K线数据
            if 'data' in data:
                stock_data = data['data'].get(f'{prefix}{symbol}', {})
                if 'qfqday' in stock_data:
                    klines = stock_data['qfqday']
                elif 'day' in stock_data:
                    klines = stock_data['day']
                else:
                    return None
                
                # 解析为DataFrame
                records = []
                for k in klines:
                    if len(k) >= 6:
                        records.append({
                            'date': k[0],
                            'open': float(k[1]),
                            'close': float(k[2]),
                            'high': float(k[3]),
                            'low': float(k[4]),
                            'volume': float(k[5])
                        })
                
                if not records:
                    return None
                
                df = pd.DataFrame(records)
                df['date'] = pd.to_datetime(df['date'])
                df.set_index('date', inplace=True)
                df = df.sort_index()
                
                # 计算成交额（近似）
                if 'amount' not in df.columns:
                    df['amount'] = df['close'] * df['volume']
                
                # 缓存数据
                df.to_parquet(cache_file)
                
                return df.tail(count)
                
        except Exception as e:
            print(f"获取K线数据失败 {symbol}: {e}")
        
        return None
    
    def get_index_list(self) -> List[Dict]:
        """获取主要指数列表"""
        indices = [
            {'code': '000001', 'name': '上证指数', 'market': 'sh'},
            {'code': '399001', 'name': '深证成指', 'market': 'sz'},
            {'code': '399006', 'name': '创业板指', 'market': 'sz'},
            {'code': '000300', 'name': '沪深300', 'market': 'sh'},
            {'code': '000016', 'name': '上证50', 'market': 'sh'},
            {'code': '000905', 'name': '中证500', 'market': 'sh'},
        ]
        
        # 获取实时数据
        codes = [idx['code'] for idx in indices]
        realtime = self.get_realtime(codes)
        
        for idx in indices:
            if idx['code'] in realtime:
                idx.update(realtime[idx['code']])
        
        return indices
    
    def get_stock_list(self, market: str = 'all', limit: int = 100) -> List[Dict]:
        """获取股票列表（沪深300成分股）"""
        # 这里返回一个固定列表，实际应用中可以接入更完整的数据
        stock_list = [
            {'code': '000001', 'name': '平安银行', 'market': 'sz'},
            {'code': '000002', 'name': '万科A', 'market': 'sz'},
            {'code': '000858', 'name': '五粮液', 'market': 'sz'},
            {'code': '000333', 'name': '美的集团', 'market': 'sz'},
            {'code': '000651', 'name': '格力电器', 'market': 'sz'},
            {'code': '002415', 'name': '海康威视', 'market': 'sz'},
            {'code': '002475', 'name': '立讯精密', 'market': 'sz'},
            {'code': '002594', 'name': '比亚迪', 'market': 'sz'},
            {'code': '300750', 'name': '宁德时代', 'market': 'sz'},
            {'code': '300059', 'name': '东方财富', 'market': 'sz'},
            {'code': '600519', 'name': '贵州茅台', 'market': 'sh'},
            {'code': '600036', 'name': '招商银行', 'market': 'sh'},
            {'code': '600276', 'name': '恒瑞医药', 'market': 'sh'},
            {'code': '600887', 'name': '伊利股份', 'market': 'sh'},
            {'code': '601318', 'name': '中国平安', 'market': 'sh'},
            {'code': '601398', 'name': '工商银行', 'market': 'sh'},
            {'code': '601857', 'name': '中国石油', 'market': 'sh'},
            {'code': '601888', 'name': '中国中免', 'market': 'sh'},
            {'code': '603288', 'name': '海天味业', 'market': 'sh'},
            {'code': '688981', 'name': '中芯国际', 'market': 'sh'},
            # 启明星辰（用户关注的股票）
            {'code': '002439', 'name': '启明星辰', 'market': 'sz'},
        ]
        
        # 获取实时数据
        codes = [stock['code'] for stock in stock_list]
        realtime = self.get_realtime(codes[:50])  # 分批获取
        
        for stock in stock_list:
            if stock['code'] in realtime:
                stock.update(realtime[stock['code']])
        
        return stock_list[:limit]

# 测试
if __name__ == "__main__":
    api = TencentAPI()
    
    print("测试腾讯财经API...")
    
    # 测试实时行情
    print("\n1. 测试实时行情:")
    realtime = api.get_realtime(['000001', '600519', '002439'])
    for code, data in realtime.items():
        print(f"  {data['name']}({code}): ¥{data['price']:.2f} ({data['change_pct']:+.2f}%)")
    
    # 测试K线数据
    print("\n2. 测试K线数据:")
    df = api.get_kline('000001', 'day', 10)
    if df is not None:
        print(f"  上证指数最近10天:")
        print(f"  最新收盘: ¥{df['close'].iloc[-1]:.2f}")
        print(f"  区间涨跌: {(df['close'].iloc[-1] - df['close'].iloc[0]) / df['close'].iloc[0]:.2%}")
    
    # 测试指数列表
    print("\n3. 测试指数列表:")
    indices = api.get_index_list()
    for idx in indices[:3]:
        if 'price' in idx:
            print(f"  {idx['name']}({idx['code']}): ¥{idx['price']:.2f}")