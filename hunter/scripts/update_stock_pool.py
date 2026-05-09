#!/usr/bin/env python3
"""
每日股票池更新脚本
从东方财富获取全市场A股列表，保存到stock_pool.json
"""
import urllib.request
import json
import time
from pathlib import Path
from datetime import datetime

POOL_FILE = Path("/root/.openclaw/workspace/猎手模拟交易/evo-trader/data/stock_pool.json")

def fetch_stock_list():
    """从东方财富获取全市场A股列表（分页，HTTPS）"""
    all_stocks = []
    total_stocks = 0
    page_size = 50

    # A股全市场（沪深主板+科创板+创业板，不含北交所）
    fs = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23"

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'Referer': 'https://quote.eastmoney.com/'
    }

    base_url = "https://push2.eastmoney.com/api/qt/clist/get"

    # 先获取总数
    url_total = f"{base_url}?pn=1&pz=1&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs={fs}&fields=f12,f14&_=1"
    try:
        req = urllib.request.Request(url_total, headers=headers)
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        total_stocks = data.get('data', {}).get('total', 0)
        print(f"全市场总计: {total_stocks} 只")
    except Exception as e:
        print(f"获取总数失败: {e}")
        return []

    # 分页获取
    page = 1
    while len(all_stocks) < total_stocks:
        url = f"{base_url}?pn={page}&pz={page_size}&po=1&np=1&ut=bd1d9ddb04089700cf9c27f6f7426281&fltt=2&invt=2&fid=f3&fs={fs}&fields=f12,f14&_=1"
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read())
            stocks = data.get('data', {}).get('diff', [])
            if not stocks:
                break
            for s in stocks:
                code = str(s.get('f12', ''))
                name = s.get('f14', code)
                if code.startswith('6') or code.startswith('9'):
                    market = 'sh'
                else:
                    market = 'sz'
                # 过滤ST、停牌、退市
                if code and len(code) >= 6 and not any(x in name for x in ['ST', '*ST', '退']):
                    all_stocks.append({
                        'code': code,
                        'name': name,
                        'market': market
                    })
            print(f"  第{page}页: +{len(stocks)} = {len(all_stocks)}/{total_stocks}")
            page += 1
            time.sleep(0.3)  # 避免请求过快
        except Exception as e:
            print(f"  第{page}页失败: {e}")
            time.sleep(1)
            if page > 3:  # 重试3次后退出
                break

    return all_stocks

if __name__ == '__main__':
    print(f"📦 股票池更新 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 40)

    stocks = fetch_stock_list()
    print(f"\n共获取 {len(stocks)} 只")

    # 去重
    seen = set()
    unique = []
    for s in stocks:
        key = s['code']
        if key not in seen:
            seen.add(key)
            unique.append(s)

    print(f"去重后 {len(unique)} 只")

    # 保存
    POOL_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(POOL_FILE, 'w', encoding='utf-8') as f:
        json.dump(unique, f, ensure_ascii=False, indent=2)

    print(f"✅ 已保存到 {POOL_FILE}")