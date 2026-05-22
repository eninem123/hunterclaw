#!/usr/bin/env python3
"""
进化交易系统 - 数据获取模块 v2（Tushare优先 + AKShare降级）
"""
import os
import json
import pandas as pd
import tushare as ts
import akshare as ak
import socket
import time
from datetime import datetime, timedelta
from pathlib import Path

class DataFetcher:
    def __init__(self, data_dir="data", use_tushare=True):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.quotes_dir = self.data_dir / "quotes"
        self.quotes_dir.mkdir(exist_ok=True)
        
        # 数据源配置
        self.use_tushare = use_tushare
        self.tushare_token = self._load_tushare_token()
        
        # 初始化Tushare（如果启用且有token）
        self.ts = None
        if self.use_tushare and self.tushare_token:
            ts.set_token(self.tushare_token)
            self.ts = ts.pro_api()
        
        # 股票池（第一期先用沪深300成分股）
        self.stock_pool = self._load_stock_pool()
        
    def _load_tushare_token(self):
        """加载Tushare token"""
        # 优先从环境变量读取
        token = os.environ.get('TUSHARE_TOKEN')
        if token:
            return token
        
        # 其次从配置文件读取
        config_file = self.data_dir / "tushare_config.json"
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('token')
        
        # 最后从全局配置读取
        global_config = Path('/root/.openclaw/workspace/猎手模拟交易/tushare_config.json')
        if global_config.exists():
            with open(global_config, 'r', encoding='utf-8') as f:
                config = json.load(f)
                return config.get('token')
        
        return None
        
    def _load_stock_pool(self):
        """加载股票池（沪深300）"""
        pool_file = self.data_dir / "stock_pool.json"
        if pool_file.exists():
            with open(pool_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            # 文件为空或无效时重新获取
            if data and len(data) > 0:
                return data
        
        # 优先用Tushare获取沪深300成分股
        if self.ts:
            try:
                df = self.ts.index_weight(index_code='000300.SH', start_date='20260101')
                stock_list = []
                for _, row in df.iterrows():
                    code = row['con_code']
                    if len(code) == 6:
                        stock_list.append({
                            'code': code,
                            'name': '',  # Tushare不返回名称，需要单独查询
                            'market': 'sh' if code.startswith(('0', '6')) else 'sz'
                        })
                self._save_stock_pool(stock_list)
                return stock_list
            except Exception as e:
                print(f"Tushare获取股票池失败: {e}, 降级到AKShare")
        
        # 降级到AKShare获取
        try:
            df = ak.index_stock_cons_sina(symbol="000300")
            stock_list = []
            for _, row in df.iterrows():
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
            self._save_stock_pool(stock_list)
            return stock_list
        except Exception as e:
            print(f"AKShare获取股票池失败: {e}")
            return []
            
    def _save_stock_pool(self, stock_list):
        """保存股票池"""
        pool_file = self.data_dir / "stock_pool.json"
        with open(pool_file, 'w', encoding='utf-8') as f:
            json.dump(stock_list, f, ensure_ascii=False, indent=2)
            
    def get_historical_data(self, code, start_date=None, end_date=None):
        """
        获取历史行情数据
        优先使用本地CSV缓存，Tushare/AKShare仅作备用
        
        Args:
            code: 股票代码（6位数字）
            start_date: 开始日期（YYYYMMDD格式）
            end_date: 结束日期（YYYYMMDD格式）
            
        Returns:
            DataFrame: 包含OHLCV数据的DataFrame
        """
        if not start_date:
            start_date = (datetime.now() - timedelta(days=365)).strftime('%Y%m%d')
        if not end_date:
            end_date = datetime.now().strftime('%Y%m%d')
        
        # 优先从本地CSV缓存读取（避免网络超时）
        df = self._load_from_csv_cache(code, start_date, end_date)
        if df is not None and not df.empty:
            return df
        
        # 确定市场
        market = 'SH' if code.startswith(('0', '6')) else 'SZ'
        ts_code = f"{code}.{market}"
        
        # 备用：使用Tushare
        if self.ts:
            try:
                df = self.ts.daily(ts_code=ts_code, start_date=start_date, end_date=end_date)
                if not df.empty:
                    df = df.sort_values('trade_date')
                    return df
            except Exception as e:
                print(f"Tushare获取{code}数据失败: {e}, 降级到AKShare")
        
        # 备用：降级到AKShare（设超时，离线时快速跳过）
        try:
            old_timeout = socket.getdefaulttimeout()
            socket.setdefaulttimeout(5)  # 5秒超时
            df = ak.stock_zh_a_hist(symbol=code, period="daily", start_date=start_date, end_date=end_date, adjust="qfq")
            socket.setdefaulttimeout(old_timeout)
            if not df.empty:
                df = df.sort_values('日期')
                df = df.rename(columns={
                    '日期': 'trade_date',
                    '开盘': 'open',
                    '最高': 'high',
                    '最低': 'low',
                    '收盘': 'close',
                    '成交量': 'vol',
                    '成交额': 'amount'
                })
                return df
        except Exception as e:
            socket.setdefaulttimeout(30)  # 恢复默认
            print(f"AKShare获取{code}数据失败: {e}")
        
        return pd.DataFrame()
    
    def _load_from_csv_cache(self, code, start_date=None, end_date=None):
        """从本地CSV缓存加载数据"""
        try:
            for suffix in ['_day_120.csv', '_day_60.csv', '_day_30.csv', '_day_10.csv']:
                cache_path = self.quotes_dir / f"{code}{suffix}"
                if cache_path.exists():
                    df = pd.read_csv(cache_path)
                    df['trade_date'] = pd.to_datetime(df['date'])
                    df = df.sort_values('trade_date')
                    if 'volume' in df.columns and 'vol' not in df.columns:
                        df['vol'] = df['volume']
                    if 'amount' not in df.columns:
                        df['amount'] = df['close'] * df['vol']
                    if start_date:
                        start_dt = pd.to_datetime(start_date, format='%Y%m%d')
                        df = df[df['trade_date'] >= start_dt]
                    if end_date:
                        end_dt = pd.to_datetime(end_date, format='%Y%m%d')
                        df = df[df['trade_date'] <= end_dt]
                    if not df.empty:
                        print(f"  本地缓存读取{code}数据: {len(df)}条")
                        return df
        except Exception as e:
            print(f"本地缓存读取{code}数据失败: {e}")
        return None
        
    def get_multiple_stocks_data(self, codes, start_date=None, end_date=None, limit=15):
        """
        获取多只股票的历史数据（带限流）
        
        Args:
            codes: 股票代码列表
            start_date: 开始日期
            end_date: 结束日期
            limit: 每次请求的股票数量（避免API限流）
            
        Returns:
            dict: {code: DataFrame}
        """
        result = {}
        
        # 分批获取，避免API限流
        for i in range(0, len(codes), limit):
            batch = codes[i:i+limit]
            for code in batch:
                df = self.get_historical_data(code, start_date, end_date)
                if not df.empty:
                    result[code] = df
            
            # 每批之间暂停1秒，避免限流
            if i + limit < len(codes):
                time.sleep(1)
        
        return result
        
    def update_all_data(self):
        """更新所有股票数据（从本地缓存加载）"""
        print(f"  加载数据缓存，共 {len(self.stock_pool)} 只股票...")
        for i, stock in enumerate(self.stock_pool):
            code = stock['code'] if isinstance(stock, dict) else stock
            cache_path = self.quotes_dir / f"{code}_day_120.csv"
            if cache_path.exists():
                continue
        print(f"  数据缓存就绪，共 {len(self.stock_pool)} 只股票")
        pass
    
    def get_market_data(self, lookback=5):
        """获取市场基准数据（用沪深300指数代表大盘）"""
        try:
            # 获取沪深300指数数据作为市场基准
            if self.ts:
                df = self.ts.index_daily(ts_code='000300.SH', start_date=(datetime.now()-timedelta(days=60)).strftime('%Y%m%d'))
                if df is not None and len(df) > 0:
                    return df.tail(lookback)
            # 降级：用AKShare获取沪深300
            df = ak.index_zh_a_hist(symbol="000300", period="daily", start_date=(datetime.now()-timedelta(days=60)).strftime('%Y%m%d'), end_date=datetime.now().strftime('%Y%m%d'))
            if df is not None and len(df) > 0:
                df = df.rename(columns={'日期':'trade_date','收盘':'close'})
                return df.tail(lookback)
        except Exception as e:
            print(f"获取市场数据失败: {e}")
        return pd.DataFrame()
        
    def get_daily_data(self, code, days=60):
        """获取近期日线数据（兼容旧接口）"""
        end_date = datetime.now().strftime('%Y%m%d')
        start_date = (datetime.now() - timedelta(days=days+30)).strftime('%Y%m%d')  # 多取30天以确保够用
        df = self.get_historical_data(code, start_date, end_date)
        return df if not df.empty else None
    
    def get_realtime_quote(self, code):
        """
        获取实时报价（仅用于signal_processor.py的止损/止盈检查）
        优先使用腾讯财经，因为它更稳定
        """
        try:
            prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
            import urllib.request
            url = f"https://qt.gtimg.cn/q={prefix}{code}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                raw = r.read().decode('gbk')
            import re
            m = re.search(r'v_[\w]+="([^"]+)"', raw)
            if m:
                parts = m.group(1).split("~")
                return float(parts[3]) if len(parts) > 3 else None
        except:
            pass
        return None

if __name__ == "__main__":
    # 测试代码
    print("测试数据获取模块 v2（Tushare优先）")
    
    fetcher = DataFetcher(use_tushare=True)
    
    # 测试获取单只股票数据
    print("\n测试获取000960数据:")
    df = fetcher.get_historical_data("000960", start_date="20240101", end_date="20240430")
    print(f"获取到 {len(df)} 条数据")
    if not df.empty:
        print(df.head())
    
    # 测试获取实时报价
    print("\n测试获取000960实时报价:")
    price = fetcher.get_realtime_quote("000960")
    print(f"当前价格: {price}")
