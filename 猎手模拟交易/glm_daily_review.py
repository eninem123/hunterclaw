#!/usr/bin/env python3
"""
猎手GLM每日复盘报告
- 生成自然语言分析（替代人工写复盘）
- 集成到cron：每天15:30收盘后自动执行
"""
import sys
import json
import os
from datetime import datetime
from pathlib import Path

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from glm_helper import call_glm, save_output

PORTFOLIO_FILE = '/root/.openclaw/workspace/猎手模拟交易/持仓.json'
REPORT_FILE = '/root/.openclaw/workspace/猎手模拟交易/glm_outputs/每日复盘_GLM_enhanced.md'


def get_market_snapshot():
    """获取市场快照"""
    import urllib.request
    
    indices = [
        ("sh000001", "上证指数"),
        ("sz399001", "深证成指"),
        ("sz399006", "创业板指"),
        ("sh000300", "沪深300"),
    ]
    
    codes = ",".join([f"sh{code[2:]}" if len(code) == 8 else code for code, _ in indices])
    data = {}
    
    try:
        url = f"https://qt.gtimg.cn/q={codes}"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            raw = r.read().decode("gbk")
        
        for line in raw.strip().split("\n"):
            if "~" not in line or len(line) < 50:
                continue
            try:
                parts = line.split('"')[1].split("~")
                if len(parts) < 35:
                    continue
                code_raw = parts[0]
                # 找对应的name
                for c, name in indices:
                    prefix = f"sh{c[2:]}" if len(c) == 8 else c
                    if prefix in code_raw:
                        data[name] = {
                            "price": float(parts[3]) if parts[3] else 0,
                            "chg": float(parts[32]) if parts[32] else 0,
                            "high": float(parts[33]) if parts[33] else 0,
                            "low": float(parts[34]) if parts[34] else 0,
                            "volume_ratio": float(parts[49]) if parts[49] else 0,
                        }
                        break
            except:
                continue
    except Exception as e:
        print(f"[警告] 市场数据获取失败: {e}")
    
    return data


def load_portfolio():
    """加载持仓数据"""
    if not os.path.exists(PORTFOLIO_FILE):
        return None
    with open(PORTFOLIO_FILE) as f:
        return json.load(f)


def build_prompt(portfolio, market_data, market_temp):
    """构造GLM分析prompt"""
    
    # 持仓摘要
    pos_lines = []
    for p in portfolio.get('positions', []):
        if p.get('status') != 'holding':
            continue
        entry = p['entry_price']
        current = p.get('current_price', entry)
        pnl_pct = (current / entry - 1) * 100
        dist_sl = (p['stop_loss'] / current - 1) * 100 if p.get('stop_loss') else 0
        dist_tp = (p['take_profit'] / current - 1) * 100 if p.get('take_profit') else 0
        
        pos_lines.append(
            f"- {p['name']}({p['code']})：买入价¥{entry}，现价¥{current}，"
            f"浮盈亏{pnl_pct:+.2f}%，止损¥{p['stop_loss']}(距{abs(dist_sl):.1f}%)，"
            f"止盈¥{p['take_profit']}(距+{dist_tp:.1f}%)"
        )
    
    if not pos_lines:
        pos_text = "当前空仓。"
    else:
        pos_text = "当前持仓：\n" + "\n".join(pos_lines)
    
    # 市场摘要
    market_lines = []
    for name, d in market_data.items():
        market_lines.append(
            f"- {name}：{d['price']:.2f}点，涨跌{d['chg']:+.2f}%，"
            f"量比{d['volume_ratio']:.2f}，最高{d['high']:.2f}，最低{d['low']:.2f}"
        )
    
    if not market_lines:
        market_text = "市场数据获取失败。"
    else:
        market_text = "\n".join(market_lines)
    
    prompt = f"""你是猎手交易系统的AI复盘分析师，负责生成专业复盘报告。

【今日市场】
{market_text}

【当前持仓】
{pos_text}

【账户信息】
- 现金：¥{portfolio.get('cash', 0):,.0f}
- 市场温度：{market_temp}℃（<50℃偏冷，≥50℃回暖，≥80℃强势）

【猎手核心规则】
- 止损红线：-5%（触发必走）
- 止盈目标：+8%分批走
- 市场<50℃不开新仓
- 单日买入≤3次，单只持仓≤30%

请生成复盘报告，包含：
1. 📊 今日收盘总结（市场走势判断）
2. 🎯 持仓诊断（是否持有/减仓/清仓）
3. 📋 明日操作计划（具体到价格）
4. ⚠️ 风险提示（如有）

先给结论，再简要分析。格式清晰专业。"""
    
    return prompt


def generate_review():
    """生成每日复盘报告"""
    print(f"[{datetime.now().strftime('%H:%M')}] 开始生成GLM复盘报告...")
    
    # 1. 加载持仓
    portfolio = load_portfolio()
    if not portfolio:
        print("[错误] 无法加载持仓文件")
        return
    
    # 2. 获取市场数据
    print(f"[{datetime.now().strftime('%H:%M')}] 获取市场数据...")
    market_data = get_market_snapshot()
    market_temp = portfolio.get('market_temperature', 35)
    
    # 3. 获取实时持仓价格
    import urllib.request
    for pos in portfolio.get('positions', []):
        if pos.get('status') != 'holding':
            continue
        try:
            code = pos['code']
            prefix = 'sz' if code.startswith(('00', '30')) else 'sh'
            url = f'https://qt.gtimg.cn/q={prefix}{code}'
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=5) as r:
                text = r.read().decode("gbk")
                parts = text.split('~')
                if len(parts) > 3 and parts[3]:
                    pos['current_price'] = float(parts[3])
        except:
            pass
    
    # 4. 生成GLM分析
    print(f"[{datetime.now().strftime('%H:%M')}] 调用GLM分析...")
    prompt = build_prompt(portfolio, market_data, market_temp)
    glm_analysis = call_glm(prompt, max_tokens=2000)
    
    # 5. 组装完整报告
    today = datetime.now().strftime('%Y-%m-%d %H:%M')
    report_lines = [
        f"# 【猎手每日复盘】{today}",
        "",
        "## 🤖 AI分析",
        "",
        glm_analysis if glm_analysis and not glm_analysis.startswith('[GLM错误]') else f"[GLM调用异常](glm_analysis)，使用基础报告。",
        "",
        "---",
        "",
        "## 📈 市场数据",
        "",
    ]
    
    if market_data:
        report_lines.append("| 指数 | 现价 | 涨跌 | 量比 |")
        report_lines.append("|------|------|------|------|")
        for name, d in market_data.items():
            chg_str = f"{d['chg']:+.2f}%"
            report_lines.append(f"| {name} | {d['price']:.2f} | {chg_str} | {d['volume_ratio']:.2f} |")
    else:
        report_lines.append("市场数据获取失败")
    
    report_lines.extend([
        "",
        "## 💼 持仓状态",
        "",
    ])
    
    for p in portfolio.get('positions', []):
        if p.get('status') != 'holding':
            continue
        entry = p['entry_price']
        current = p.get('current_price', entry)
        pnl_pct = (current / entry - 1) * 100
        report_lines.append(f"- **{p['name']}({p['code']})**：¥{current} ({pnl_pct:+.2f}%)")
    
    report_lines.extend([
        f"- 现金：¥{portfolio.get('cash', 0):,.0f}",
        f"- 市场温度：{market_temp}℃",
        "",
        "---",
        "",
        "*本报告由AI自动生成，仅供参考，不构成投资建议。*",
    ])
    
    report = "\n".join(report_lines)
    
    # 6. 保存
    Path(REPORT_FILE).parent.mkdir(parents=True, exist_ok=True)
    with open(REPORT_FILE, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"[{datetime.now().strftime('%H:%M')}] 报告已生成: {REPORT_FILE}")
    print(f"GLM分析片段: {glm_analysis[:200] if glm_analysis else 'N/A'}...")
    return report


if __name__ == "__main__":
    generate_review()
