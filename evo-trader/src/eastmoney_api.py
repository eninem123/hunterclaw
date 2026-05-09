#!/usr/bin/env python3
"""
东方财富K线API接口（稳定版）
替换失效的腾讯API
"""
import json
import time
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import requests
from typing import Dict, List, Optional

class EastMoneyAPI:
    """东方财富K线API封装"""
    
    def __init__(self, cache_dir="data/quotes"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Referer': 'https://eastmoney.com/'
        })
    
    def _get_secid(self, symbol: str) -> str:
        """转换股票代码为东方财富secid格式"""
        # 上海: 1.600519, 深圳主板: 0.000001, 创业板: 0.300001, 科创板: 1.688001
        if symbol.startswith('6'):
            return f"1.{symbol}"
        elif symbol.startswith('00'):
            return f"0.{symbol}"
        elif symbol.startswith('30'):
            return f"0.{symbol}"
        elif symbol.startswith('688'):
            return f"1.{symbol}"
        else:
            return f"0.{symbol}"
    
    def get_kline(self, symbol: str, period: str = 'day', count: int = 100) -> Optional[pd.DataFrame]:
        """获取K线数据
        period: day, week, month, 5min, 15min, 30min, 60min
        """
        cache_file = self.cache_dir / f"{symbol}_{period}_{count}.parquet"
        
        # 检查缓存（2小时有效）
        if cache_file.exists():
            cache_time = cache_file.stat().st_mtime
            if time.time() - cache_time < 7200:
                try:
                    df = pd.read_parquet(cache_file)
                    if len(df) >= count * 0.8:
                        return df.tail(count)
                except:
                    pass
        
        # 周期映射
        period_map = {
            'day': '101',
            'week': '102',
            'month': '103',
            '5min': '5',
            '15min': '15',
            '30min': '30',
            '60min': '60'
        }
        klt = period_map.get(period, '101')
        
        secid = self._get_secid(symbol)
        
        url = 'https://push2his.eastmoney.com/api/qt/stock/kline/get'
        params = {
            'secid': secid,
            'fields1': 'f1,f2,f3,f4,f5,f6',
            'fields2': 'f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61',
            'klt': klt,
            'fqt': '1',  # 前复权
            'end': '20500101',  # 尽可能新的数据
            'lmt': str(count)
        }
        
        try:
            response = self.session.get(url, params=params, timeout=10)
            data = response.json()
            
            if 'data' not in data or not data['data'] or 'klines' not in data['data']:
                return None
            
            klines = data['data']['klines']
            
            records = []
            for k in klines:
                parts = k.split(',')
                if len(parts) >= 6:
                    records.append({
                        'date': parts[0],
                        'open': float(parts[1]),
                        'close': float(parts[2]),
                        'high': float(parts[3]),
                        'low': float(parts[4]),
                        'volume': float(parts[5]),
                        'amount': float(parts[6]) if len(parts) > 6 else 0
                    })
            
            if not records:
                return None
            
            df = pd.DataFrame(records)
            df['date'] = pd.to_datetime(df['date'])
            df.set_index('date', inplace=True)
            df = df.sort_index()
            
            # 缓存
            df.to_parquet(cache_file)
            return df.tail(count)
        
        except Exception as e:
            print(f"EastMoney API error: {e}")
            return None
    
    def get_realtime(self, symbols: List[str]) -> Dict[str, Dict]:
        """获取实时行情（单条）"""
        results = {}
        for symbol in symbols:
            secid = self._get_secid(symbol)
            url = 'https://push2.eastmoney.com/api/qt/stock/get'
            params = {
                'secid': secid,
                'fields': 'f43,f44,f45,f46,f47,f48,f50,f57,f58,f60,f107,f169,f170'
            }
            try:
                r = self.session.get(url, params=params, timeout=5)
                d = r.json().get('data', {})
                if d:
                    results[symbol] = {
                        'name': d.get('f58', ''),
                        'price': d.get('f43', 0),
                        'open': d.get('f46', 0),
                        'high': d.get('f44', 0),
                        'low': d.get('f45', 0),
                        'volume': d.get('f47', 0),
                        'amount': d.get('f48', 0),
                        'change': d.get('f169', 0),
                        'change_pct': d.get('f170', 0),
                    }
            except:
                pass
        return results


if __name__ == '__main__':
    api = EastMoneyAPI()
    
    # 测试
    print("=== 测试东方财富K线API ===")
    for symbol in ['000001', '600519', '000858', '002439']:
        df = api.get_kline(symbol, 'day', 5)
        if df is not None:
            print(f"{symbol}: {len(df)} rows, last close={df['close'].iloc[-1]:.2f}")
        else:
            print(f"{symbol}: 无数据")
