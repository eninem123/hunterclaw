#!/usr/bin/env python3
"""
猎手闭环系统 v1.0
每日完整闭环：读取→分析→策略→知识→选股→总结

执行时间：
  交易日 15:40 执行
  非交易日 15:00 执行自我迭代

使用方法：
  python3 hunter_closed_loop.py [--date YYYY-MM-DD]
"""

import os
import sys
import json
import urllib.request
import re
import requests
from datetime import datetime, date
from pathlib import Path

# ── 路径 ────────────────────────────────────────────
WORKSPACE = Path("/root/.openclaw/workspace")
HUNTER = WORKSPACE / "猎手模拟交易"
KB = HUNTER / "knowledge_base"
sys.path.insert(0, str(HUNTER / "src"))


# ══════════════════════════════════════════════════════════
# Step 1: 读取今日数据（市场+持仓）
# ══════════════════════════════════════════════════════════

def get_market_data() -> dict:
    """获取今日市场数据"""
    try:
        url = 'https://qt.gtimg.cn/q=sh000001,sz399001,sz399006'
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('gbk')
        indices = {}
        for line in raw.split('\n'):
            m = re.search(r'v_(\w+)="(.+)"', line)
            if not m:
                continue
            p = m.group(2).split('~')
            if len(p) < 32:
                continue
            indices[p[1]] = {'chg': float(p[32]), 'close': float(p[3])}
        return indices
    except Exception as e:
        return {}


def get_position_prices(codes: dict) -> dict:
    """获取持仓今日收盘价"""
    try:
        url = 'https://qt.gtimg.cn/q=' + ','.join(codes.values())
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        resp = urllib.request.urlopen(req, timeout=8)
        raw = resp.read().decode('gbk')
        prices = {}
        for line in raw.split('\n'):
            m = re.search(r'v_(\w+)="(.+)"', line)
            if not m:
                continue
            p = m.group(2).split('~')
            if len(p) < 32:
                continue
            # prices字典以name为key（如"中信证券"）
            prices[p[1]] = {'price': float(p[3]), 'chg': float(p[32])}

        # 备选：如果精确匹配失败，用持仓代码直接查（避免名称差异）
        fallback_prices = {}
        for name, code in codes.items():
            url2 = f'https://qt.gtimg.cn/q={code}'
            try:
                req2 = urllib.request.Request(url2, headers={'User-Agent': 'Mozilla/5.0'})
                resp2 = urllib.request.urlopen(req2, timeout=5)
                raw2 = resp2.read().decode('gbk')
                m2 = re.search(r'v_\w+="(.+)"', raw2)
                if m2:
                    p2 = m2.group(1).split('~')
                    if len(p2) >= 32:
                        fallback_prices[name] = {'price': float(p2[3]), 'chg': float(p2[32])}
            except Exception:
                pass

        # 合并：精确匹配优先，fallback补充缺失
        for name, fd in fallback_prices.items():
            if name not in prices:
                prices[name] = fd

        return prices
    except Exception as e:
        return {}


def step1_read_data() -> dict:
    """Step 1: 读取所有数据"""
    pf_file = HUNTER / "持仓.json"
    with open(pf_file) as f:
        pf = json.load(f)

    indices = get_market_data()
    codes = {p['name']: ('sh' if p['code'].startswith(('6', '5')) else 'sz') + p['code']
             for p in pf['positions']}
    pos_prices = get_position_prices(codes)

    return {'portfolio': pf, 'indices': indices, 'prices': pos_prices}


# ══════════════════════════════════════════════════════════
# Step 2: 今日市场分析（资讯+情绪）
# ══════════════════════════════════════════════════════════

def step2_analyze(data: dict) -> dict:
    """Step 2: 分析今日市场"""
    indices = data['indices']

    # 指数分析
    avg_chg = sum(v['chg'] for v in indices.values()) / len(indices) if indices else 0
    sentiment = "极好" if avg_chg > 1 else "偏好" if avg_chg > 0.3 else "中性" if avg_chg > -0.3 else "偏差" if avg_chg > -1 else "极差"

    analysis = {
        'sentiment': sentiment,
        'index_avg_chg': round(avg_chg, 2),
        'indices': {k: round(v['chg'], 2) for k, v in indices.items()},
        'market_regime': 'trending' if abs(avg_chg) > 0.5 else 'range_bound' if abs(avg_chg) < 0.3 else 'mixed',
    }
    return analysis


# ══════════════════════════════════════════════════════════
# Step 3: 策略更新（根据今日经验）
# ══════════════════════════════════════════════════════════

def step3_update_strategy(data: dict, analysis: dict) -> list:
    """Step 3: 更新策略，写入知识库"""
    pf = data['portfolio']
    prices = data['prices']
    learnings = []

    for pos in pf['positions']:
        code = pos['code']
        name = pos['name']
        entry = pos['entry_price']
        buy_date = pos.get('buy_date', '')
        today = date.today().isoformat()
        # buy_date包含时间，需要取日期部分比较
        buy_date_only = buy_date[:10] if buy_date else ''
        note = pos.get('note', '')

        if buy_date_only != today:
            continue

        # 获取今日收盘价（prices字典以name为key）
        price_data = prices.get(name, {})
        today_price = price_data.get('price', entry)
        today_chg = price_data.get('chg', 0)

        # 判断是否买在涨停价（今日涨停且收盘价≈买入价）
        is_limit_up_buy = (today_chg >= 9.8 and abs(today_price - entry) < entry * 0.01)

        if is_limit_up_buy:
            lesson = f"⚠️ 【教训-{today}】{name}({code})买在涨停价{entry}元！今日涨幅{today_chg:.2f}%，明日大概率低开/炸板"
            learnings.append(lesson)
            lesson_file = KB / "lessons" / f"lesson_{today}.md"
            with open(lesson_file, 'a') as f:
                f.write(f"\n## {lesson}\n")
                f.write(f"- 买入价格: {entry}元\n")
                f.write(f"- 今日涨幅: {today_chg:.2f}%\n")
                f.write(f"- 规则补丁: 涨停股(涨幅>=9.8%)禁止作为买入候选\n")
            print(f"  📝 教训已记录: {lesson[:50]}...")

    return learnings


# ══════════════════════════════════════════════════════════
# Step 4: 选股（明日预备）
# ══════════════════════════════════════════════════════════

def step4_scan_for_tomorrow(max_count: int = 3) -> list:
    """Step 4: 扫描明日候选"""
    try:
        from stock_picker import pick_best_candidates
        candidates = pick_best_candidates(max_count=max_count)
        return candidates
    except Exception as e:
        print(f"  选股扫描失败: {e}")
        return []


# ══════════════════════════════════════════════════════════
# Step 5: 持仓复盘
# ══════════════════════════════════════════════════════════

def step5_review_positions(data: dict) -> dict:
    """Step 5: 持仓复盘"""
    pf = data['portfolio']
    prices = data['prices']
    today = date.today().isoformat()

    total_cost = 0
    total_value = 0
    total_pnl = 0
    reviews = []

    for pos in pf['positions']:
        code = pos['code']
        entry = pos['entry_price']
        shares = pos['shares']
        stop_loss = pos.get('stop_loss')
        take_profit = pos.get('take_profit')
        cost = entry * shares
        # 159715 is ETF, needs sh prefix
        if code == '159715':
            sh_prefix = 'sh'
        else:
            sh_prefix = 'sh' if code.startswith(('6', '5')) else 'sz'
        name_key = None
        # Try to find by name first (from prices dict keyed by name)
        for pos_data in pf['positions']:
            if pos_data['code'] == code:
                name_key = pos_data['name']
                break
        current_price = prices.get(name_key, {}).get('price', entry) if name_key else entry
        value = current_price * shares
        pnl = value - cost
        pnl_pct = pnl / cost * 100
        total_cost += cost
        total_value += value
        total_pnl += pnl

        # 状态判断
        status = "正常"
        action = "持有"
        if stop_loss and current_price <= stop_loss:
            status = "🔴 触及止损"
            action = "止损"
        elif take_profit and current_price >= take_profit:
            status = "🟢 触及止盈"
            action = "止盈"
        elif current_price < entry * 0.97:
            status = "🟡 浮亏超过3%"
            action = "观察"

        reviews.append({
            'code': code,
            'name': pos['name'],
            'entry': entry,
            'current': current_price,
            'cost': cost,
            'value': value,
            'pnl': pnl,
            'pnl_pct': round(pnl_pct, 2),
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'status': status,
            'action': action,
        })

    total_assets = total_value + pf['cash']
    return {
        'reviews': reviews,
        'total_cost': total_cost,
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_assets': total_assets,
        'cash': pf['cash'],
    }


# ══════════════════════════════════════════════════════════
# Step 6: 今日总结
# ══════════════════════════════════════════════════════════

def step6_summary(reviews: list, learnings: list, analysis: dict, tomorrow_candidates: list) -> str:
    """Step 6: 生成今日总结"""
    today = date.today().isoformat()
    total_pnl = sum(r['pnl'] for r in reviews)
    total_pnl_pct = total_pnl / sum(r['cost'] for r in reviews) * 100 if reviews else 0

    # 判断盈亏
    if total_pnl > 0:
        verdict = f"✅ 今日盈利 {total_pnl:+.0f}元 ({total_pnl_pct:+.2f}%)"
    else:
        verdict = f"❌ 今日亏损 {total_pnl:+.0f}元 ({total_pnl_pct:+.2f}%)"

    # 写入总结
    summary_file = KB / "daily_summary" / f"{today}.md"
    summary_file.parent.mkdir(exist_ok=True)

    candidate_text = ""
    if tomorrow_candidates:
        candidate_text = "### 明日候选（待确认）\n"
        for c in tomorrow_candidates:
            candidate_text += f"- {c['name']}({c['code']}) 涨{c['chg_pct']:+.2f}% 量比{c['vol_ratio']} score={c['score']:.0f}\n"

    content = f"""# 📋 猎手日终总结 | {today}

## {verdict}

## 今日市场
- 三大指数: {analysis['indices']}
- 情绪: {analysis['sentiment']}
- 市场状态: {analysis['market_regime']}

## 持仓复盘
| 代码 | 名称 | 成本 | 现价 | 盈亏 | 状态 |
|------|------|------|------|------|------|
"""
    for r in reviews:
        content += f"| {r['code']} | {r['name']} | {r['entry']} | {r['current']} | {r['pnl_pct']:+.2f}% | {r['status']} |\n"

    content += f"""
## 今日教训/经验
"""
    for l in learnings:
        content += f"- {l}\n"

    if candidate_text:
        content += f"\n{candidate_text}"

    content += f"""
---
_由 龙波(OpenClaw) 自动生成_
"""

    with open(summary_file, 'w') as f:
        f.write(content)

    return verdict, str(summary_file)


# ══════════════════════════════════════════════════════════
# 主闭环入口
# ══════════════════════════════════════════════════════════

def run_closed_loop():
    print("=" * 55)
    print(f"🐉 猎手闭环系统 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 55)

    # Step 1: 读取数据
    print("\n【Step1】读取数据")
    data = step1_read_data()
    pf = data['portfolio']
    print(f"  持仓: {len(pf['positions'])}只 | 现金: {pf['cash']:.0f}元")

    # Step 2: 市场分析
    print("\n【Step2】市场分析")
    analysis = step2_analyze(data)
    print(f"  指数: {analysis['indices']}")
    print(f"  情绪: {analysis['sentiment']} | 市场状态: {analysis['market_regime']}")

    # Step 3: 策略更新
    print("\n【Step3】策略更新（写入教训/经验）")
    learnings = step3_update_strategy(data, analysis)
    if learnings:
        for l in learnings:
            print(f"  📝 {l[:50]}...")
    else:
        print("  ✅ 无新增教训")

    # Step 4: 选股（明日预备）
    print("\n【Step4】明日候选扫描")
    candidates = step4_scan_for_tomorrow()
    print(f"  候选: {len(candidates)}只")
    for c in candidates[:3]:
        print(f"  - {c['name']}({c['code']}) 涨{c['chg_pct']:+.2f}% score={c.get('score',0):.0f}")

    # Step 5: 持仓复盘
    print("\n【Step5】持仓复盘")
    review_result = step5_review_positions(data)
    for r in review_result['reviews']:
        print(f"  {r['code']} {r['name']}: {r['pnl_pct']:+.2f}% → {r['status']}")

    # Step 6: 总结
    print("\n【Step6】生成日终总结")
    verdict, summary_file = step6_summary(
        review_result['reviews'], learnings, analysis, candidates
    )
    print(f"  {verdict}")
    print(f"  📄 总结: {summary_file}")

    # 最终输出
    print()
    print("=" * 55)
    print(f"【猎手今日学到 {len(learnings)} 个关键点】")
    for i, l in enumerate(learnings, 1):
        print(f"  {i}. {l[:60]}...")
    print("=" * 55)

    return {
        'learnings': learnings,
        'candidates': candidates,
        'review': review_result,
        'verdict': verdict,
    }


if __name__ == "__main__":
    result = run_closed_loop()
