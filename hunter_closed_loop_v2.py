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
import socket
import ssl
import hashlib
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
        """获取单个股票价格 (v2.1优化: 增强解析鲁棒性)"""
        try:
            url = f'https://qt.gtimg.cn/q={code}'
            raw = http_get_with_retry(url, 'gbk', config, cache_ttl=30)
            if not raw:
                return name, None
            
            m = re.search(r'v_(\w+)="(.+)"', raw)
            if m:
                p = m.group(2).split('~')
                if len(p) >= 38:
                    return name, {
                        'price': float(p[3]),
                        'chg': float(p[32]),
                        'volume': float(p[6]) if p[6] else 0,
                        'turnover': float(p[37]) if p[37] else 0,
                    }
                elif len(p) >= 32:
                    return name, {
                        'price': float(p[3]),
                        'chg': float(p[32]),
                        'volume': float(p[6]) if p[6] else 0
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
    
    # 计算恐慌指数（基于跌幅和广度，模拟market_scanner逻辑）
    panic_index = 60  # 中性
    if avg_chg < -1:
        panic_index -= 15
    elif avg_chg < -0.5:
        panic_index -= 5
    elif avg_chg > 0.5:
        panic_index += 5
    elif avg_chg > 1:
        panic_index += 10
    panic_index = max(0, min(100, panic_index))
    
    # R22回暖预案状态
    r22_active = panic_index < 25 and temperature < 35
    
    # R23假回暖标记 (v4.2.1: 阈值下调)
    r23_warning = panic_index < 25 and 0.3 < avg_chg < 1.5  # 温和上涨中的冰点假回暖可能
    
    # v4.2.1: 三期止损梯队计算
    stop_loss_tier = get_stop_loss_tiers(panic_index)
    
    # v4.2.1: 拐点参数集
    inflection_params = get_inflection_params()
    
    analysis = {
        'sentiment': sentiment,
        'index_avg_chg': round(avg_chg, 2),
        'indices': {k: round(v['chg'], 2) for k, v in indices.items()},
        'market_regime': market_regime,
        'temperature': temperature,
        'panic_index': panic_index,
        'r22_recovery_plan_ready': r22_active,
        'r23_false_recovery_warning': r23_warning,
        # v4.2.1 新增字段
        'stop_loss_tier': stop_loss_tier,
        'inflection_params': inflection_params,
        'k_param_set_version': 'K-0520-1',
        'v421_daily_version': '2026-05-19',
    }
    
    logger.info(f"市场分析: 情绪={sentiment}, 温度={temperature}℃, 状态={market_regime}, 恐慌={panic_index}")
    logger.info(f"  v4.2.1止损梯队: {stop_loss_tier['tier']}-{stop_loss_tier['scenario']}")
    logger.info(f"  v4.2.1拐点参数集: K-0520-1 ({inflection_params['scenario']})")
    if r22_active:
        logger.info(f"  🏥 R22回暖预案已准备 (恐慌{panic_index}<25，温度{temperature}℃)")
    if r23_warning:
        logger.info(f"  ⚠️ R23注意：冰点期温和上涨，防范假回暖一日游")
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


# ══════════════════════════════════════════════════════════
# v4.2.1 新增：纪律评分 + 拐点参数集 (K-0520-1)
# ══════════════════════════════════════════════════════════

def calculate_discipline_score_v421(trade_log: list) -> dict:
    """计算交易纪律评分 v4.2.1
    
    4个维度:
    1. R18冰点禁入(40%权重): 冰点期违规买入比例
    2. 信号执行(30%权重): 非信号交易比例
    3. R09-v2仓位上限(15%权重): 超仓位上限比例
    4. R05单日≤2次(15%权重): 超2次交易日数
    
    Returns:
        {
            "total_score": float(0-100),
            "items": [...],
            "score_label": str,
            "version": "v4.2.1"
        }
    """
    if not trade_log or not isinstance(trade_log, list):
        return {
            "total_score": 100.0,
            "items": [],
            "valid_trades": 0,
            "violations": 0,
            "score_label": "\U0001f3c6 完美(无交易)",
            "version": "v4.2.1"
        }
    
    items = []
    
    # 1. R18: 冰点期违规
    r18_violations = sum(1 for t in trade_log if t.get("panic_index", 50) < 35 and t.get("direction", "") in ("买入", "buy"))
    r18_total = sum(1 for t in trade_log if t.get("panic_index", 50) < 50)
    r18_score = 100.0 if r18_total == 0 else max(0.0, 100.0 - (r18_violations / r18_total * 100))
    items.append({"rule": "R18冰点禁入", "weight": 0.40, "score": r18_score, "detail": f"冰点期违规买入{r18_violations}/{r18_total}次"})
    
    # 2. 信号执行
    not_signal = sum(1 for t in trade_log if not t.get("is_signal_based", True))
    signal_score = 100.0 if not_signal == 0 else max(0.0, 100.0 - (not_signal / len(trade_log) * 100))
    items.append({"rule": "信号执行", "weight": 0.30, "score": signal_score, "detail": f"非信号交易{not_signal}/{len(trade_log)}笔"})
    
    # 3. R09-v2仓位
    over_pos = sum(1 for t in trade_log if t.get("position_pct", 0) > t.get("max_allowed_pct", 100))
    pos_score = 100.0 if over_pos == 0 else max(0.0, 100.0 - (over_pos / len(trade_log) * 100))
    items.append({"rule": "R09-v2仓位上限", "weight": 0.15, "score": pos_score, "detail": f"超仓位{over_pos}/{len(trade_log)}笔"})
    
    # 4. R05单日≤2次
    from collections import Counter
    daily_counts = Counter(t.get("date", "") for t in trade_log)
    exceed_days = sum(1 for c in daily_counts.values() if c > 2)
    r05_score = max(0.0, 100.0 - exceed_days * 25)
    items.append({"rule": "R05单日≤2次", "weight": 0.15, "score": r05_score, "detail": f"超2次天数: {exceed_days}"})
    
    total_score = sum(item["score"] * item["weight"] for item in items)
    
    if total_score >= 90:
        label = "\U0001f3c6 优秀"
    elif total_score >= 80:
        label = "\u2705 良好"
    elif total_score >= 60:
        label = "\u26a0\ufe0f 及格"
    else:
        label = "\u274c 不及格"
    
    return {
        "total_score": round(total_score, 1),
        "items": items,
        "valid_trades": sum(1 for t in trade_log if t.get("pnl_pct", -1) >= 0),
        "violations": sum(1 for i in items if i["score"] < 60),
        "score_label": label,
        "version": "v4.2.1"
    }


def get_inflection_params(phase: str = "initial") -> dict:
    """获取拐点专用参数集 K-0520-1
    
    Args:
        phase: "initial"(回暖首次验证) | "confirm"(验证通过) | "stable"(稳定期)
    
    Returns:
        拐点参数配置dict
    """
    params = {
        "version": "K-0520-1",
        "updated": "2026-05-19",
        "scenario": phase,
        "entry_cadence": [
            {"D+0": "回暖确认日: 仅确认信号不交易"},
            {"D+1": "验证日: 恐慌>25+连续2日, 买入10%(¥7,400)"},
            {"D+2": "验证通过: 恐慌>25+上证收涨, 买入15%(¥11,100)"},
            {"D+3": "稳定: 恐慌>35, 买入20-25%"}
        ]
    }
    
    if phase == "initial":
        params.update({
            "panic_entry": ">25 (连续2日)",
            "max_position_pct": 10,
            "max_single_pct": 5,
            "stop_loss_pct": -2.5,
            "take_profit_triggers": [3, 5, 8],
            "take_profit_ratios": [30, 50, 100],
            "max_hold_days": 3,
            "allowed_types": "\u9632\u5fa1\u578b(\u94f6\u884c/\u516c\u7528/\u6d88\u8d39\u9f99\u5934)",
            "conditions": "\u6050\u614c\u8fde\u7eed2\u65e5>25 + \u4e0a\u8bc1\u6536\u6da8 + \u6da8\u8dcc\u6bd4>1:1"
        })
    elif phase == "confirm":
        params.update({
            "panic_entry": ">25 \u786e\u8ba4",
            "max_position_pct": 15,
            "max_single_pct": 10,
            "stop_loss_pct": -2.5,
            "take_profit_triggers": [3, 5, 8],
            "take_profit_ratios": [30, 50, 100],
            "max_hold_days": 3,
            "allowed_types": "\u9632\u5fa1\u578b+\u5e95\u90e8\u53cd\u5f39\u9996\u5148\u7528"
        })
    elif phase == "stable":
        params.update({
            "panic_entry": ">35",
            "max_position_pct": 25,
            "max_single_pct": 15,
            "stop_loss_pct": -3.0,
            "take_profit_triggers": [5, 8, 12],
            "take_profit_ratios": [33, 33, 34],
            "max_hold_days": 5,
            "allowed_types": "\u5e38\u89c4(\u9664AI/\u534a\u5bfc\u4f53)"
        })
    
    return params


def get_stop_loss_tiers(panic_index: float) -> dict:
    """三期止损梯队 v4.2.1
    
    覆盖3种场景:
    - A: 恐慌<25 (空仓维持, 无需止损)
    - B: 恐慌25-35 (回调初期, 收紧止损)
    - C: 恐慌>35 (恢复正常止损)
    """
    if panic_index < 25:
        return {
            "tier": "A",
            "scenario": "恐慌仍<25",
            "probability": 0.85,
            "action": "\u7a7a\u4ed3\u7ef4\u6301(\u65e0\u9700\u8bbe\u6b62\u635f)",
            "hunter_action": "\u7a7a\u4ed3\u7b49\u5f85\u56de\u6696",
            "kouzi_action": "\u539f\u59cb\u6b62\u635f\u4e0d\u53d8(-8%~-10%)"
        }
    elif panic_index < 35:
        return {
            "tier": "B",
            "scenario": "\u6050\u614c\u56de\u534725-35",
            "probability": 0.12,
            "action": "\u8f7b\u4ed3\u8bd5\u63a215%",
            "hunter_action": "\u5355\u53ea6\u6b62\u635f-2.5%, \u5355\u53ea\u6b62\u76c8+3%/+5%/+8% \u5206\u6279, \u6700\u5927\u6301\u4ed32\u53ea",
            "max_position_pct": 15,
            "stop_loss_pct": -2.5
        }
    else:
        return {
            "tier": "C",
            "scenario": "\u6050\u614c\u56de\u5347>35",
            "probability": 0.03,
            "action": "\u8c28\u614e\u53c2\u4e0e25%",
            "hunter_action": "\u6062\u590d-3.0%\u6807\u51c6\u6b62\u635f, +5%/+8%/+12% \u5206\u6279\u6b62\u76c8, \u6700\u59273\u53ea",
            "max_position_pct": 25,
            "stop_loss_pct": -3.0
        }


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
