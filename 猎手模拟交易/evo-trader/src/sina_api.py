#!/usr/bin/env python3
"""
新浪财经K线API接口（稳定版）
"""
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import Dict, List, Optional

class SinaFinanceAPI:
    """新浪财经K线API封装"""
    
    def __init__(self, cache_dir="data/quotes"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://finance.sina.com.cn/'
        })
    
    def _get_symbol_prefix(self, symbol: str) -> str:
        """转换A股代码为新浪格式"""
        if symbol.startswith('6'):
            return f'sh{symbol}'
        elif symbol.startswith('00') or symbol.startswith('30') or symbol.startswith('688'):
            return f'sz{symbol}'
        return f'sz{symbol}'
    
    def get_kline(self, symbol: str, period: str = 'day', count: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据
        period: day(240min), week, month, 5min, 15min, 30min, 60min
        """
        cache_file = self.cache_dir / f"{symbol}_{period}_{count}.parquet"
        
        # 2小时缓存
        if cache_file.exists():
            cache_time = cache_file.stat().st_mtime
            if time.time() - cache_time < 7200:
                try:
                    df = pd.read_csv(cache_file.with_suffix('.csv'), index_col=0, parse_dates=True)
                    if len(df) >= count * 0.8:
                        return df.tail(count)
                except:
                    pass
        
        # 周期映射 (sina scale: 5=5min, 15=15min, 30=30min, 60=60min, 240=日K)
        period_map = {
            'day': '240',
            'week': '1440',  # 周K用日K模拟
            'month': '1440',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60'
        }
        scale = period_map.get(period, '240')
        
        symbol_sina = self._get_symbol_prefix(symbol)
        url = 'https://money.finance.sina.com.cn/quotes_service/api/json_v2.php/CN_MarketData.getKLineData'
        params = {
            'symbol': symbol_sina,
            'scale': scale,
            'datalen': str(count),
            'ma': 'no'  # 不带均线
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if not data or not isinstance(data, list):
                return None
            
            records = []
            for k in data:
                records.append({
                    'date': k['day'],
                    'open': float(k['open']),
                    'close': float(k['close']),
                    'high': float(k['high']),
                    'low': float(k['low']),
                    'volume': float(k['volume'])
                })
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            # 计算成交额
            if 'amount' not in df.columns:
                df['amount'] = df['close'] * df['volume']
            
            df.to_csv(cache_file.with_suffix('.csv'), index=True)
            return df.tail(count)
        
        except Exception as e:
            print(f"SinaFinance API error for {symbol}: {e}")
            return None
    
    def get_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取实时行情（批量）"""
        results = {}
        
        # 分批，每批50只
        for i in range(0, len(symbols), 50):
            batch = symbols[i:i+50]
            codes = [self._get_symbol_prefix(s) for s in batch]
            url = f'https://qt.gtimg.cn/q={",".join(codes)}'
            
            try:
                r = self.session.get(url, timeout=5)
                r.encoding = 'gbk'
                lines = r.text.strip().split('\n')
                
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
                    
                    raw_symbol = parts[0].replace('v_', '').replace('sz', '').replace('sh', '')
                    symbol = raw_symbol
                    
                    try:
                        results[symbol] = {
                            'name': data_parts[1],
                            'price': float(data_parts[3]),
                            'open': float(data_parts[4]),
                            'high': float(data_parts[33]),
                            'low': float(data_parts[34]),
                            'volume': float(data_parts[36]) if data_parts[36] else 0,
                            'amount': float(data_parts[37]) if data_parts[37] else 0,
                            'change': float(data_parts[31]) if len(data_parts) > 31 else 0,
                            'change_pct': float(data_parts[32]) if len(data_parts) > 32 else 0,
                        }
                    except (ValueError, IndexError):
                        continue
            
            except Exception as e:
                print(f"Realtime batch error: {e}")
                continue
        
        return results


if __name__ == '__main__':
    api = SinaFinanceAPI()
    print("=== 测试新浪财经K线API ===")
    for symbol in ['000001', '600519', '000858', '002439']:
        df = api.get_kline(symbol, 'day', 5)
        if df is not None:
            print(f"{symbol}: {len(df)} rows, last close={df['close'].iloc[-1]:.2f}")
        else:
            print(f"{symbol}: 无数据")
