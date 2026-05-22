#!/usr/bin/env python3
"""
猎手闭环系统 v2.0
改进版本：
  - 性能优化：并行数据获取、缓存机制
  - 错误处理：完整的异常捕获和降级策略
  - 日志增强：结构化日志、性能监控
  - 模块化：独立的策略更新、选股、复盘模块
  - 配置化：支持配置文件参数

执行时间：
  交易日 15:40 执行
  非交易日 15:00 执行自我迭代

使用方法：
  python3 hunter_closed_loop_v2.py [--date YYYY-MM-DD] [--config config.json]
"""

import os
import sys
import json
import urllib.request
import re
import requests
import logging
import time
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

# ── 配置 ────────────────────────────────────────────
@dataclass
class HunterConfig:
    """猎手系统配置"""
    workspace: Path = Path("/root/.openclaw/workspace")
    hunter_dir: Optional[Path] = None
    kb_dir: Optional[Path] = None
    
    # API配置
    timeout: int = 8
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # 选股配置
    max_candidates: int = 3
    min_score: float = 60.0
    
    # 止损止盈配置
    stop_loss_pct: float = -5.0
    take_profit_pct: float = 8.0
    
    # 并发配置
    max_workers: int = 5
    
    def __post_init__(self):
        if self.hunter_dir is None:
            self.hunter_dir = self.workspace / "猎手模拟交易"
        if self.kb_dir is None:
            self.kb_dir = self.hunter_dir / "knowledge_base"

# ── 日志配置 ────────────────────────────────────────────
def setup_logging(hunter_dir: Path) -> logging.Logger:
    """配置结构化日志"""
    log_dir = hunter_dir / "logs"
    log_dir.mkdir(exist_ok=True)
    
    log_file = log_dir / f"hunter_loop_{date.today()}.log"
    
    logger = logging.getLogger("hunter")
    logger.setLevel(logging.DEBUG)
    
    # 文件处理器
    fh = logging.FileHandler(log_file, encoding='utf-8')
    fh.setLevel(logging.DEBUG)
    
    # 控制台处理器
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    
    # 格式化
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    fh.setFormatter(formatter)
    ch.setFormatter(formatter)
    
    logger.addHandler(fh)
    logger.addHandler(ch)
    
    return logger

# 全局日志
logger = None

# ── 缓存机制 ────────────────────────────────────────────
class SimpleCache:
    """简单内存缓存"""
    def __init__(self, ttl: int = 300):
        self.cache = {}
        self.ttl = ttl
    
    def get(self, key: str) -> Optional[any]:
        item = self.cache.get(key)
        if item and time.time() - item['time'] < self.ttl:
            return item['value']
        return None
    
    def set(self, key: str, value: any):
        self.cache[key] = {'value': value, 'time': time.time()}
    
    def clear(self):
        self.cache.clear()

# 全局缓存
_cache = SimpleCache(ttl=300)

# ── 路径初始化 ────────────────────────────────────────────
def init_paths(config: Optional[HunterConfig] = None):
    """从配置初始化路径（避免硬编码）"""
    if config is None:
        config = HunterConfig()
    WORKSPACE = config.workspace
    HUNTER = config.hunter_dir
    KB = config.kb_dir
    sys.path.insert(0, str(HUNTER / "src"))
    return WORKSPACE, HUNTER, KB

WORKSPACE, HUNTER, KB = init_paths()

# ── HTTP工具（带重试和缓存）────────────────────────────────
def http_get_with_retry(url: str, encoding: str = 'gbk', 
                        config: HunterConfig = None) -> Optional[str]:
    """带重试机制的HTTP GET请求"""
    if config is None:
        config = HunterConfig()
    
    # 检查缓存
    cache_key = f"http:{hash(url)}"
    cached = _cache.get(cache_key)
    if cached:
        logger.debug(f"缓存命中: {url}")
        return cached
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        "Referer": "https://finance.qq.com"
    }
    
    for attempt in range(config.max_retries):
        try:
            req = urllib.request.Request(url, headers=headers)
            with urllib.request.urlopen(req, timeout=config.timeout) as r:
                data = r.read().decode(encoding, errors="replace")
                _cache.set(cache_key, data)
                return data
        except Exception as e:
            logger.warning(f"HTTP请求失败 (尝试 {attempt+1}/{config.max_retries}): {e}")
            if attempt < config.max_retries - 1:
                time.sleep(config.retry_delay)
    
    logger.error(f"HTTP请求失败: {url}")
    return None

# ══════════════════════════════════════════════════════════
# Step 1: 读取今日数据（市场+持仓）
# ══════════════════════════════════════════════════════════

def get_market_data(config: HunterConfig) -> Dict[str, Dict]:
    """获取今日市场数据（三大指数）"""
    cache_key = "market_data"
    cached = _cache.get(cache_key)
    if cached:
        logger.debug("使用缓存的市场数据")
        return cached
    
    try:
        url = 'https://qt.gtimg.cn/q=sh000001,sz399001,sz399006'
        raw = http_get_with_retry(url, 'gbk', config)
        if not raw:
            return {}
        
        indices = {}
        for line in raw.split('\n'):
            m = re.search(r'v_(\w+)="(.+)"', line)
            if not m:
                continue
            p = m.group(2).split('~')
            if len(p) < 32:
                continue
            
            try:
                name = p[1]
                chg = float(p[32])
                close = float(p[3])
                indices[name] = {
                    'chg': chg,
                    'close': close,
                    'code': m.group(1)
                }
            except (ValueError, IndexError) as e:
                logger.warning(f"解析指数数据失败: {e}")
                continue
        
        _cache.set(cache_key, indices)
        logger.info(f"获取市场数据: {len(indices)}个指数")
        return indices
    except Exception as e:
        logger.error(f"获取市场数据异常: {e}")
        return {}


def get_position_prices(codes: Dict[str, str], config: HunterConfig) -> Dict[str, Dict]:
    """并行获取持仓今日收盘价"""
    cache_key = f"pos_prices:{len(codes)}"
    cached = _cache.get(cache_key)
    if cached:
        logger.debug("使用缓存的持仓价格")
        return cached
    
    prices = {}
    
    def fetch_price(name: str, code: str) -> Tuple[str, Optional[Dict]]:
        """获取单个股票价格"""
        try:
            url = f'https://qt.gtimg.cn/q={code}'
            raw = http_get_with_retry(url, 'gbk', config)
            if not raw:
                return name, None
            
            m = re.search(r'v_\w+="(.+)"', raw)
            if m:
                p = m.group(1).split('~')
                if len(p) >= 32:
                    return name, {
                        'price': float(p[3]),
                        'chg': float(p[32])
                    }
        except Exception as e:
            logger.warning(f"获取{name}价格失败: {e}")
            return name, None
        return name, None
    
    # 并发获取
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        futures = {
            executor.submit(fetch_price, name, code): name
            for name, code in codes.items()
        }
        
        for future in as_completed(futures):
            name, price_data = future.result()
            if price_data:
                prices[name] = price_data
    
    _cache.set(cache_key, prices)
    logger.info(f"获取持仓价格: {len(prices)}/{len(codes)}")
    return prices


def step1_read_data(config: HunterConfig) -> Dict:
    """Step 1: 读取所有数据"""
    logger.info("=" * 55)
    logger.info("Step 1: 读取数据")
    
    try:
        pf_file = config.hunter_dir / "持仓.json"
        with open(pf_file, 'r', encoding='utf-8') as f:
            pf = json.load(f)
        logger.info(f"持仓文件加载成功: {len(pf['positions'])}只")
    except Exception as e:
        logger.error(f"加载持仓文件失败: {e}")
        return {}
    
    indices = get_market_data(config)
    codes = {
        p['name']: ('sh' if p['code'].startswith(('6', '5')) else 'sz') + p['code']
        for p in pf['positions']
    }
    pos_prices = get_position_prices(codes, config)
    
    data = {
        'portfolio': pf,
        'indices': indices,
        'prices': pos_prices
    }
    
    logger.info(f"数据读取完成: 持仓{len(pf['positions'])}只, 指数{len(indices)}个")
    return data


# ══════════════════════════════════════════════════════════
# Step 2: 今日市场分析（资讯+情绪）
# ══════════════════════════════════════════════════════════

def step2_analyze(data: Dict, config: HunterConfig) -> Dict:
    """Step 2: 分析今日市场"""
    logger.info("Step 2: 市场分析")
    
    indices = data.get('indices', {})
    
    if not indices:
        logger.warning("无市场指数数据，返回中性状态")
        return {
            'sentiment': '中性',
            'index_avg_chg': 0,
            'indices': {},
            'market_regime': 'range_bound',
            'temperature': 50
        }
    
    # 指数分析
    chg_vals = [v['chg'] for v in indices.values()]
    avg_chg = sum(chg_vals) / len(chg_vals)
    
    sentiment = (
        "极好" if avg_chg > 1 else
        "偏好" if avg_chg > 0.3 else
        "中性" if avg_chg > -0.3 else
        "偏差" if avg_chg > -1 else
        "极差"
    )
    
    market_regime = (
        'trending' if abs(avg_chg) > 0.5 else
        'range_bound' if abs(avg_chg) < 0.3 else
        'mixed'
    )
    
    # 计算市场温度（0-100）
    temperature = int(50 + avg_chg * 10)
    temperature = max(0, min(100, temperature))
    
    analysis = {
        'sentiment': sentiment,
        'index_avg_chg': round(avg_chg, 2),
        'indices': {k: round(v['chg'], 2) for k, v in indices.items()},
        'market_regime': market_regime,
        'temperature': temperature
    }
    
    logger.info(f"市场分析: 情绪={sentiment}, 温度={temperature}℃, 状态={market_regime}")
    return analysis


# ══════════════════════════════════════════════════════════
# Step 3: 策略更新（根据今日经验）
# ══════════════════════════════════════════════════════════

def step3_update_strategy(data: Dict, analysis: Dict, config: HunterConfig) -> List[str]:
    """Step 3: 更新策略，写入知识库"""
    logger.info("Step 3: 策略更新（教训/经验）")
    
    pf = data.get('portfolio', {})
    prices = data.get('prices', {})
    learnings = []
    
    today = date.today().isoformat()
    lessons_dir = KB / "lessons"
    lessons_dir.mkdir(parents=True, exist_ok=True)
    
    for pos in pf.get('positions', []):
        code = pos['code']
        name = pos['name']
        entry = pos['entry_price']
        buy_date = pos.get('buy_date', '')
        buy_date_only = buy_date[:10] if buy_date else ''
        note = pos.get('note', '')
        
        # 只分析今日买入的
        if buy_date_only != today:
            continue
        
        # 获取今日收盘价
        price_data = prices.get(name, {})
        today_price = price_data.get('price', entry)
        today_chg = price_data.get('chg', 0)
        
        # 判断是否买在涨停价
        is_limit_up_buy = (today_chg >= 9.8 and abs(today_price - entry) < entry * 0.01)
        
        if is_limit_up_buy:
            lesson = f"⚠️ 【教训-{today}】{name}({code})买在涨停价{entry}元！今日涨幅{today_chg:.2f}%，明日大概率低开/炸板"
            learnings.append(lesson)
            
            lesson_file = lessons_dir / f"lesson_{today}.md"
            try:
                with open(lesson_file, 'a', encoding='utf-8') as f:
                    f.write(f"\n## {lesson}\n")
                    f.write(f"- 买入价格: {entry}元\n")
                    f.write(f"- 今日涨幅: {today_chg:.2f}%\n")
                    f.write(f"- 规则补丁: 涨停股(涨幅>=9.8%)禁止作为买入候选\n")
                logger.info(f"教训已记录: {lesson[:50]}...")
            except Exception as e:
                logger.error(f"写入教训文件失败: {e}")
    
    logger.info(f"策略更新完成: {len(learnings)}个教训/经验")
    return learnings


# ══════════════════════════════════════════════════════════
# Step 4: 选股（明日预备）
# ══════════════════════════════════════════════════════════

def step4_scan_for_tomorrow(max_count: int = 3, config: HunterConfig = None) -> List[Dict]:
    """Step 4: 扫描明日候选"""
    logger.info(f"Step 4: 明日候选扫描 (max={max_count})")
    
    if config is None:
        config = HunterConfig()
    
    try:
        from stock_picker import pick_best_candidates
        candidates = pick_best_candidates(max_count=max_count)
        logger.info(f"选股完成: {len(candidates)}只候选")
        return candidates
    except ImportError:
        logger.error("stock_picker模块导入失败")
        return []
    except Exception as e:
        logger.error(f"选股扫描失败: {e}")
        logger.debug(traceback.format_exc())
        return []


# ══════════════════════════════════════════════════════════
# Step 5: 持仓复盘
# ══════════════════════════════════════════════════════════

def step5_review_positions(data: Dict, config: HunterConfig) -> Dict:
    """Step 5: 持仓复盘"""
    logger.info("Step 5: 持仓复盘")
    
    pf = data.get('portfolio', {})
    prices = data.get('prices', {})
    
    total_cost = 0
    total_value = 0
    total_pnl = 0
    reviews = []
    
    for pos in pf.get('positions', []):
        code = pos['code']
        entry = pos['entry_price']
        shares = pos['shares']
        stop_loss = pos.get('stop_loss', entry * (1 + config.stop_loss_pct / 100))
        take_profit = pos.get('take_profit', entry * (1 + config.take_profit_pct / 100))
        
        cost = entry * shares
        
        # 获取当前价格
        name_key = pos['name']
        current_price = prices.get(name_key, {}).get('price', entry)
        value = current_price * shares
        pnl = value - cost
        pnl_pct = pnl / cost * 100
        
        total_cost += cost
        total_value += value
        total_pnl += pnl
        
        # 状态判断
        if stop_loss and current_price <= stop_loss:
            status = "🔴 触及止损"
            action = "止损"
        elif take_profit and current_price >= take_profit:
            status = "🟢 触及止盈"
            action = "止盈"
        elif current_price < entry * 0.97:
            status = "🟡 浮亏超过3%"
            action = "观察"
        else:
            status = "正常"
            action = "持有"
        
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
    
    total_assets = total_value + pf.get('cash', 0)
    
    logger.info(f"持仓复盘: 成本={total_cost:.0f}, 现值={total_value:.0f}, 盈亏={total_pnl:+.0f}")
    
    return {
        'reviews': reviews,
        'total_cost': total_cost,
        'total_value': total_value,
        'total_pnl': total_pnl,
        'total_assets': total_assets,
        'cash': pf.get('cash', 0),
    }


# ══════════════════════════════════════════════════════════
# Step 6: 今日总结
# ══════════════════════════════════════════════════════════

def step6_summary(reviews: List[Dict], learnings: List[str], 
                 analysis: Dict, tomorrow_candidates: List[Dict]) -> Tuple[str, str]:
    """Step 6: 生成今日总结"""
    logger.info("Step 6: 生成日终总结")
    
    today = date.today().isoformat()
    total_pnl = sum(r['pnl'] for r in reviews)
    total_cost = sum(r['cost'] for r in reviews)
    total_pnl_pct = total_pnl / total_cost * 100 if total_cost > 0 else 0
    
    # 判断盈亏
    if total_pnl > 0:
        verdict = f"✅ 今日盈利 {total_pnl:+.0f}元 ({total_pnl_pct:+.2f}%)"
    else:
        verdict = f"❌ 今日亏损 {total_pnl:+.0f}元 ({total_pnl_pct:+.2f}%)"
    
    # 写入总结
    daily_summary_dir = KB / "daily_summary"
    daily_summary_dir.mkdir(exist_ok=True)
    summary_file = daily_summary_dir / f"{today}.md"
    
    candidate_text = ""
    if tomorrow_candidates:
        candidate_text = "### 明日候选（待确认）\n"
        for c in tomorrow_candidates:
            candidate_text += f"- {c['name']}({c['code']}) 涨{c['chg_pct']:+.2f}% 量比{c.get('vol_ratio', 'N/A')} score={c.get('score', 0):.0f}\n"
    
    content = f"""# 📋 猎手日终总结 | {today}

## {verdict}

## 今日市场
- 三大指数: {analysis.get('indices', {})}
- 情绪: {analysis.get('sentiment', 'N/A')}
- 市场温度: {analysis.get('temperature', 50)}℃
- 市场状态: {analysis.get('market_regime', 'N/A')}

## 持仓复盘
| 代码 | 名称 | 成本 | 现价 | 盈亏 | 状态 |
|------|------|------|------|------|------|
"""
    for r in reviews:
        content += f"| {r['code']} | {r['name']} | {r['entry']:.2f} | {r['current']:.2f} | {r['pnl_pct']:+.2f}% | {r['status']} |\n"
    
    content += f"""
## 今日教训/经验
"""
    if learnings:
        for l in learnings:
            content += f"- {l}\n"
    else:
        content += "- 无新增教训/经验\n"
    
    if candidate_text:
        content += f"\n{candidate_text}"
    
    content += f"""
---
_由 猎手闭环系统 v2.0 自动生成 | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}_
"""
    
    try:
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(content)
        logger.info(f"总结文件已保存: {summary_file}")
    except Exception as e:
        logger.error(f"写入总结文件失败: {e}")
    
    return verdict, str(summary_file)


# ══════════════════════════════════════════════════════════
# 主闭环入口
# ══════════════════════════════════════════════════════════

def run_closed_loop(config: HunterConfig = None) -> Dict:
    """运行完整闭环"""
    global logger
    
    if config is None:
        config = HunterConfig()
    
    logger = setup_logging(config.hunter_dir)
    
    logger.info("=" * 55)
    logger.info(f"🐉 猎手闭环系统 v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    logger.info("=" * 55)
    
    start_time = time.time()
    
    try:
        # Step 1: 读取数据
        logger.info("")
        data = step1_read_data(config)
        if not data:
            logger.error("数据读取失败，终止闭环")
            return {}
        
        pf = data['portfolio']
        logger.info(f"持仓: {len(pf['positions'])}只 | 现金: {pf['cash']:.0f}元")
        
        # Step 2: 市场分析
        logger.info("")
        analysis = step2_analyze(data, config)
        logger.info(f"指数: {analysis['indices']}")
        logger.info(f"情绪: {analysis['sentiment']} | 温度: {analysis['temperature']}℃ | 状态: {analysis['market_regime']}")
        
        # Step 3: 策略更新
        logger.info("")
        learnings = step3_update_strategy(data, analysis, config)
        if learnings:
            for l in learnings:
                logger.info(f"  📝 {l[:60]}...")
        else:
            logger.info("  ✅ 无新增教训")
        
        # Step 4: 选股（明日预备）
        logger.info("")
        candidates = step4_scan_for_tomorrow(config.max_candidates, config)
        logger.info(f"  候选: {len(candidates)}只")
        for c in candidates[:3]:
            logger.info(f"  - {c['name']}({c['code']}) 涨{c['chg_pct']:+.2f}% score={c.get('score', 0):.0f}")
        
        # Step 5: 持仓复盘
        logger.info("")
        review_result = step5_review_positions(data, config)
        for r in review_result['reviews']:
            logger.info(f"  {r['code']} {r['name']}: {r['pnl_pct']:+.2f}% → {r['status']}")
        
        # Step 6: 总结
        logger.info("")
        verdict, summary_file = step6_summary(
            review_result['reviews'], learnings, analysis, candidates
        )
        logger.info(f"  {verdict}")
        logger.info(f"  📄 总结: {summary_file}")
        
        # 性能统计
        elapsed = time.time() - start_time
        logger.info("")
        logger.info("=" * 55)
        logger.info(f"【猎手闭环完成】耗时: {elapsed:.2f}秒")
        logger.info(f"【今日学到 {len(learnings)} 个关键点】")
        for i, l in enumerate(learnings, 1):
            logger.info(f"  {i}. {l[:60]}...")
        logger.info("=" * 55)
        
        return {
            'learnings': learnings,
            'candidates': candidates,
            'review': review_result,
            'verdict': verdict,
            'elapsed': elapsed,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"闭环执行异常: {e}")
        logger.debug(traceback.format_exc())
        return {
            'error': str(e),
            'success': False
        }
    finally:
        # 清理缓存
        _cache.clear()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='猎手闭环系统 v2.0')
    parser.add_argument('--date', type=str, help='指定日期 (YYYY-MM-DD)')
    parser.add_argument('--config', type=str, help='配置文件路径')
    parser.add_argument('--max-candidates', type=int, default=3, help='最大候选数量')
    
    args = parser.parse_args()
    
    # 加载配置
    config = HunterConfig()
    if args.config:
        try:
            with open(args.config, 'r') as f:
                config_dict = json.load(f)
                for k, v in config_dict.items():
                    if hasattr(config, k):
                        setattr(config, k, v)
        except Exception as e:
            print(f"加载配置文件失败: {e}")
    
    config.max_candidates = args.max_candidates
    
    # 执行闭环
    result = run_closed_loop(config)
    
    # 返回码
    sys.exit(0 if result.get('success', False) else 1)
