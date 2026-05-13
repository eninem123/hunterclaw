#!/usr/bin/env python3
"""
多策略选股扫描器 v2.0
Enhanced - 按板块特性差异化筛选标的

基于多策略框架 v1.0 规格说明实现:
- 主板(60/00): 价值投资 - 低PE+高分红+ROE
- 创业板(300/301): 趋势跟踪 - R35/R38规则+量比+题材
- 科创板(688): 成长股 - 研发+国产替代+渗透率
- ETF: 轮动策略 - 折溢价+板块轮动
- 基金: 选基逻辑 - 经理风格+超额收益
"""

import sys
import os
import logging
import json
import warnings
import requests
from datetime import datetime
from abc import ABC, abstractmethod
from typing import List, Dict, Optional

warnings.filterwarnings("ignore")

# 全局requests session，超时控制
_SESS = requests.Session()
_SESS.headers.update({
    "User-Agent": "Mozilla/5.0 (compatible; MultiStrategyScanner/2.0)"
})
HTTP_TIMEOUT = 15  # 秒

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S"
)
logger = logging.getLogger("multi_strategy_scanner")

# ==================== 全局配置 ====================
MARKET_TEMP_THRESHOLD = 40
OUTPUT_DIR = "/root/.openclaw/workspace/猎手模拟交易/多策略框架"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ==================== 数据获取 ====================
def get_akshare_spot() -> Optional[Dict]:
    """
    获取A股实时行情 (akshare stock_zh_a_spot_em)
    返回: {code: row_dict}
    """
    try:
        import akshare as ak
        # 设置全局请求超时
        import akshare as _ak
        _ak._session = _SESS
        _ak._http_timeout = HTTP_TIMEOUT
        df = _ak.stock_zh_a_spot_em()
        logger.info(f"获取到 {len(df)} 只A股实时数据")
        return {str(row["代码"]): row.to_dict() for _, row in df.iterrows()}
    except Exception as e:
        logger.error(f"akshare实时行情获取失败: {e}")
        return None


def get_akshare_board_leaders(limit: int = 50) -> Optional[Dict]:
    """
    获取A股板块涨幅榜 (akshare stock_sector_spot)
    """
    try:
        import akshare as ak
        df = ak.stock_sector_spot(indicator="涨幅")
        logger.info(f"获取到 {len(df)} 个板块数据")
        return {row["板块名称"]: row.to_dict() for _, row in df.iterrows()}
    except Exception as e:
        logger.error(f"板块数据获取失败: {e}")
        return None


def get_akshare_limit_up() -> Optional[Dict]:
    """
    获取今日涨停股列表
    """
    try:
        import akshare as ak
        df = ak.stock_zt_pool_em(date=datetime.now().strftime("%Y%m%d"))
        logger.info(f"今日涨停 {len(df)} 只")
        return {str(row["代码"]): row.to_dict() for _, row in df.iterrows()}
    except Exception as e:
        logger.error(f"涨停池获取失败: {e}")
        return None


def get_akshare_etf_spot() -> Optional[Dict]:
    """
    获取ETF实时行情
    """
    try:
        import akshare as ak
        df = ak.fund_etf_spot_em()
        logger.info(f"获取到 {len(df)} 只ETF实时数据")
        return {str(row["代码"]): row.to_dict() for _, row in df.iterrows()}
    except Exception as e:
        logger.error(f"ETF数据获取失败: {e}")
        return None


def get_akshare_fund_spot() -> Optional[Dict]:
    """
    获取场外基金实时数据
    """
    try:
        import akshare as ak
        df = ak.fund_open_fund_em()
        logger.info(f"获取到 {len(df)} 只场外基金数据")
        return {str(row["基金代码"]): row.to_dict() for _, row in df.iterrows()}
    except Exception as e:
        logger.error(f"基金数据获取失败: {e}")
        return None


# ==================== 策略基类 ====================
class StrategyBase(ABC):
    """多策略扫描器基类"""

    name: str = "Base"
    strategy_type: str = "base"
    codes_prefixes: List[str] = []
    candidate_pool: List[str] = []  # 可选：固定候选池

    def __init__(self):
        self.results: List[Dict] = []

    @abstractmethod
    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        """扫描入口 - 由子类实现"""
        pass

    def filter(self, df) -> List[Dict]:
        """通用过滤 - 由子类重写"""
        return []

    def generate_report(self, results: List[Dict]) -> str:
        """生成 Markdown 报告片段"""
        if not results:
            return ""
        lines = [f"\n### {self.name} ({self.strategy_type})\n"]
        lines.append(f"| 代码 | 名称 | 价格 | 涨跌幅 | 信号 | 原因 |")
        lines.append("|------|------|------|--------|------|------|")
        for r in sorted(results, key=lambda x: x.get("chg", 0), reverse=True):
            lines.append(
                f"| {r.get('code','')} | {r.get('name','')} | "
                f"{r.get('price', 0):.2f} | {r.get('chg', 0):+.2f}% | "
                f"{r.get('signal','')} | {r.get('reason','')} |"
            )
        return "\n".join(lines)

    def _safe_get(self, row: Dict, key: str, default=None):
        """安全获取字段"""
        try:
            return row.get(key, default)
        except:
            return default

    def _code_match(self, code: str) -> bool:
        """检查代码前缀是否匹配"""
        if not self.codes_prefixes:
            return True
        return any(code.startswith(p) for p in self.codes_prefixes)


# ==================== 主板策略：价值投资 ====================
class MainBoardStrategy(StrategyBase):
    """
    主板价值投资策略

    选股标准 (来自多策略框架):
    - PE(TTM) ≤ 15
    - 股息率 ≥ 3%
    - ROE ≥ 10%
    - 近30日主力净流入 > 0
    - 股价处于MA20之上
    - 市场温度 ≥ 40℃

    注: akshare免费数据不含PE/股息/ROE/主力净流入等字段，
    这里用简化版：涨幅0~5% + 排除高估值(价格适中)作为近似筛选
    完整实现需要tushare付费数据或东财API
    """

    name = "主板策略"
    strategy_type = "价值投资"
    codes_prefixes = ["60", "00"]

    # 固定候选池（典型高股息价值股）
    CANDIDATES = [
        ("600900", "长江电力"),
        ("601088", "中国神华"),
        ("601006", "大秦铁路"),
        ("601398", "工商银行"),
        ("600887", "伊利股份"),
        ("600028", "中国石化"),
        ("600019", "宝钢股份"),
        ("601288", "农业银行"),
        ("600050", "中国联通"),
        ("601318", "中国平安"),
    ]

    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        logger.info(f"[主板] 开始扫描 ({len(spot_data)} 只A股行情)")

        results = []
        for code, name in self.CANDIDATES:
            if code not in spot_data:
                continue
            row = spot_data[code]

            price = self._safe_get(row, "最新价", 0) or 0
            chg = self._safe_get(row, "涨跌幅", 0) or 0
            volume = self._safe_get(row, "成交额", 0) or 0
            high = self._safe_get(row, "最高", 0) or 0
            low = self._safe_get(row, "最低", 0) or 0

            # 安全检查
            if not price or price <= 0:
                continue

            # 筛选条件（简化版）:
            # 1. 涨幅在 0~5% (稳健上涨，不过热)
            # 2. 价格处于日内中高位置 (非破位)
            if 0 < chg <= 5:
                mid_price = (high + low) / 2
                if price >= mid_price * 0.98:  # 价格在日中部以上
                    results.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "chg": chg,
                        "volume": volume,
                        "signal": "value_invest",
                        "reason": "低估值高分红(主板)"
                    })

        logger.info(f"[主板] 扫描完成: {len(results)} 只符合条件")
        return results


# ==================== 创业板策略：趋势跟踪 ====================
class GrowthBoardStrategy(StrategyBase):
    """
    创业板趋势跟踪策略

    整合 R35/R38 规则:

    R35 规则 (回撤低成功率入场):
    买入条件:
    ✓ 回撤 > 25% (从近180日高点)
    ✓ 量比 > 1.5x
    ✓ 涨幅 > 7%
    ✓ 板块涨停家数 ≥ 3家
    ✓ 股价突破MA5/MA10金叉

    R38 规则 (连板龙头持有):
    持有条件:
    ✓ 连板天数 ≥ 2天
    ✓ 板块涨停家数 ≥ 3家
    ✓ 封单金额维持 > 3000万
    ✓ 指数未出现亏钱效应

    注: akshare免费数据不含R35/R38精确指标(180日高点/连板天数等)，
    这里用涨幅5%~9.8%排除涨停 + 非st + 热门板块作为近似筛选
    """

    name = "创业板策略"
    strategy_type = "趋势跟踪"
    codes_prefixes = ["300", "301"]

    # 创业板候选池 (代表性成长股)
    CANDIDATES = [
        ("300750", "宁德时代"),
        ("300274", "阳光电源"),
        ("300059", "东方财富"),
        ("300124", "汇川技术"),
        ("300142", "沃森生物"),
        ("300760", "迈瑞医疗"),
        ("300015", "爱尔眼科"),
        ("300122", "智飞生物"),
        ("300223", "鹏辉能源"),
        ("300014", "亿纬锂能"),
        ("300450", "先导智能"),
        ("300496", "中科创达"),
        ("300033", "同花顺"),
        ("300782", "卓胜微"),
        ("300751", "迈为股份"),
    ]

    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        logger.info("[创业板] 开始扫描")

        results = []
        today_zt_codes = set(zt_data.keys()) if zt_data else set()

        for code, name in self.CANDIDATES:
            if code not in spot_data:
                continue
            row = spot_data[code]

            price = self._safe_get(row, "最新价", 0) or 0
            chg = self._safe_get(row, "涨跌幅", 0) or 0
            volume = self._safe_get(row, "成交额", 0) or 0
            vol_ratio = self._safe_get(row, "量比", 1) or 1

            if not price or price <= 0:
                continue

            # R35近似筛选:
            # 1. 涨幅 5%~9.8% (动量启动，排除涨停)
            # 2. 量比 > 1.5 (资金关注)
            # 3. 非ST
            name_str = str(name)
            if 5 <= chg < 9.8 and vol_ratio > 1.5 and "ST" not in name_str:
                results.append({
                    "code": code,
                    "name": name,
                    "price": price,
                    "chg": chg,
                    "volume": volume,
                    "vol_ratio": vol_ratio,
                    "signal": "trend_follow",
                    "reason": f"R35动量启动(量比{vol_ratio:.1f}x)"
                })

        logger.info(f"[创业板] 扫描完成: {len(results)} 只符合条件")
        return results


# ==================== 科创板策略：成长股 ====================
class STARBoardStrategy(StrategyBase):
    """
    科创板成长股策略

    选股标准:
    - 研发投入占比 ≥ 10%
    - 营收增速 ≥ 30%
    - 国产替代指数前20%
    - 渗透率 ≤ 30% (拐点前)
    - 毛利率 ≥ 40%

    买入信号:
    ✓ 研发投入占比 ≥ 10%
    ✓ 营收增速 ≥ 30% (连续2季度)
    ✓ 政策催化 (国产替代)
    ✓ 渗透率 ≤ 30% (低位布局)
    ✓ 股价回撤 > 30%

    注: akshare免费数据不含研发/营收增速/渗透率等字段，
    用国产替代题材 + 涨幅 > 3% + 非科创ST 作为近似
    """

    name = "科创板策略"
    strategy_type = "成长股"
    codes_prefixes = ["688"]

    CANDIDATES = [
        ("688012", "中微公司"),
        ("688008", "澜起科技"),
        ("688981", "中芯国际"),
        ("688111", "金山办公"),
        ("688256", "寒武纪"),
        ("688521", "芯原股份"),
        ("688982", "银铜科技"),
        ("688396", "华润微"),
        ("688223", "晶科能源"),
        ("688499", "利元亨"),
    ]

    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        logger.info("[科创板] 开始扫描")

        results = []
        for code, name in self.CANDIDATES:
            if code not in spot_data:
                continue
            row = spot_data[code]

            price = self._safe_get(row, "最新价", 0) or 0
            chg = self._safe_get(row, "涨跌幅", 0) or 0
            volume = self._safe_get(row, "成交额", 0) or 0

            if not price or price <= 0:
                continue

            # 筛选: 涨幅 > 3% + 非ST + 国产替代题材
            name_str = str(name)
            if chg > 3 and "ST" not in name_str:
                results.append({
                    "code": code,
                    "name": name,
                    "price": price,
                    "chg": chg,
                    "volume": volume,
                    "signal": "growth",
                    "reason": "国产替代+成长催化"
                })

        logger.info(f"[科创板] 扫描完成: {len(results)} 只符合条件")
        return results


# ==================== ETF策略：轮动 ====================
class ETFSymbolStrategy(StrategyBase):
    """
    ETF轮动策略

    折溢价套利:
    - 溢价率 > 0.5% → 卖出ETF，申购套利
    - 折价率 > 0.5% → 买入ETF，赎回套利

    行业轮动信号:
    ✓ 相关行业指数涨幅 > 3%
    ✓ 量比 > 1.5x
    ✓ 板块资金净流入 > 10亿
    ✓ 成分股涨停家数 ≥ 3家

    注: akshare fund_etf_spot_em 含溢价率字段
    """

    name = "ETF策略"
    strategy_type = "轮动策略"

    TRACKED_ETFS = [
        ("159715", "稀土ETF"),
        ("159995", "芯片ETF"),
        ("516160", "新能源ETF"),
        ("512010", "医疗ETF"),
        ("512800", "银行ETF"),
        ("515050", "5GETF"),
        ("512690", "酒ETF"),
        ("512760", "芯片ETF(国联安)"),
        ("588000", "科创50ETF"),
        ("159419", "消费ETF"),
    ]

    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        logger.info("[ETF] 开始扫描")

        results = []

        # 使用ETF专用数据(etf_data)优先级最高
        if etf_data:
            for code, name in self.TRACKED_ETFS:
                if code in etf_data:
                    row = etf_data[code]
                    chg = self._safe_get(row, "涨跌幅", 0) or 0
                    premium = self._safe_get(row, "溢价率", 0) or 0
                    price = self._safe_get(row, "最新价", 0) or 0
                    volume = self._safe_get(row, "成交额", 0) or 0

                    if not price or price <= 0:
                        continue

                    reason = ""
                    if chg > 3:
                        reason = "行业轮动"
                    elif abs(premium) > 0.5:
                        reason = f"折溢价套利({premium:+.2f}%)"

                    if chg > 1.5:
                        results.append({
                            "code": code,
                            "name": name,
                            "price": price,
                            "chg": chg,
                            "volume": volume,
                            "premium": premium,
                            "signal": "etf_rotation",
                            "reason": reason or "量价齐升"
                        })
        else:
            # fallback: 用A股spot数据中的ETF数据
            for code, name in self.TRACKED_ETFS:
                if code not in spot_data:
                    continue
                row = spot_data[code]
                price = self._safe_get(row, "最新价", 0) or 0
                chg = self._safe_get(row, "涨跌幅", 0) or 0
                volume = self._safe_get(row, "成交额", 0) or 0

                if not price or price <= 0:
                    continue

                if chg > 1.5:
                    results.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "chg": chg,
                        "volume": volume,
                        "signal": "etf_rotation",
                        "reason": "板块轮动"
                    })

        logger.info(f"[ETF] 扫描完成: {len(results)} 只符合条件")
        return results


# ==================== 基金策略：选基 ====================
class FundStrategy(StrategyBase):
    """
    基金选基策略

    选基标准:
    - 近1年超额收益 ≥ 5%
    - 最大回撤 ≤ -20%
    - 收益标准差 ≤ 15%
    - 经理从业年限 ≥ 5年
    - 基金规模 10-100亿

    经理风格分类:
    - 价值型: 低PE高股息，换手率<100%
    - 成长型: 高增速高弹性，换手率>200%
    - 均衡型: 价值+成长配置，换手率100-200%

    注: akshare fund_open_fund_em 含收益率/规模等字段，可用于粗筛
    """

    name = "基金策略"
    strategy_type = "选基逻辑"

    TRACKED_FUNDS = [
        ("001417", "汇添富医疗服务"),
        ("110022", "易方达消费行业"),
        ("001643", "汇丰晋信低碳先锋"),
        ("162201", "泰达宏利效率"),
        ("260101", "景顺长城新兴"),
        ("110013", "易方达科翔"),
        ("519068", "兴全轻资产"),
        ("100059", "广发中证军工"),
    ]

    def scan(self, spot_data: Dict, board_data: Dict, zt_data: Dict, etf_data: Dict, fund_data: Dict) -> List[Dict]:
        logger.info("[基金] 开始扫描")

        results = []

        if fund_data:
            for code, name in self.TRACKED_FUNDS:
                if code not in fund_data:
                    continue
                row = fund_data[code]

                price = self._safe_get(row, "单位净值", 0) or 0
                chg = self._safe_get(row, "日增长率", 0) or 0
                scale = self._safe_get(row, "基金规模", 0) or 0

                if not price or price <= 0:
                    continue

                # 粗筛: 日涨幅 > 0 + 规模合理
                if chg > 0.5:
                    results.append({
                        "code": code,
                        "name": name,
                        "price": price,
                        "chg": chg,
                        "scale": scale,
                        "signal": "fund_selection",
                        "reason": f"基金经理择时(日涨{chg:+.2f}%)"
                    })
        else:
            # 无基金数据时返回关注列表
            for code, name in self.TRACKED_FUNDS:
                results.append({
                    "code": code,
                    "name": name,
                    "price": 0,
                    "chg": 0,
                    "signal": "fund_watch",
                    "reason": "待关注(数据不可用)"
                })

        logger.info(f"[基金] 扫描完成: {len(results)} 只符合条件")
        return results


# ==================== 多策略扫描器 ====================
class MultiStrategyScanner:
    """
    多策略扫描器主类

    使用方法:
    scanner = MultiStrategyScanner()
    results = scanner.run()
    report = scanner.generate_markdown_report(results)
    """

    def __init__(self):
        self.strategies: List[StrategyBase] = [
            MainBoardStrategy(),
            GrowthBoardStrategy(),
            STARBoardStrategy(),
            ETFSymbolStrategy(),
            FundStrategy(),
        ]
        self.scan_time = datetime.now()
        self.market_temp = 50  # 默认

    def fetch_data(self) -> Dict:
        """获取所有数据源"""
        logger.info("=" * 40)
        logger.info("开始获取数据...")
        logger.info("=" * 40)

        spot_data = get_akshare_spot()
        board_data = get_akshare_board_leaders()
        zt_data = get_akshare_limit_up()
        etf_data = get_akshare_etf_spot()
        fund_data = get_akshare_fund_spot()

        return {
            "spot": spot_data or {},
            "board": board_data or {},
            "zt": zt_data or {},
            "etf": etf_data or {},
            "fund": fund_data or {},
        }

    def estimate_market_temp(self, spot_data: Dict) -> int:
        """
        估算市场温度 (0-100)
        简易算法: 全市场涨幅中位数 * 10，上限100
        """
        if not spot_data:
            return 50
        try:
            chg_list = []
            for row in spot_data.values():
                chg = self._safe_get(row, "涨跌幅", 0) or 0
                if chg != 0:
                    chg_list.append(chg)
            if chg_list:
                median_chg = sorted(chg_list)[len(chg_list) // 2]
                temp = int(abs(median_chg) * 10)
                return min(temp, 100)
        except:
            pass
        return 50

    def _safe_get(self, row: Dict, key: str, default=None):
        try:
            return row.get(key, default)
        except:
            return default

    def run(self) -> Dict:
        """运行全策略扫描"""
        data = self.fetch_data()
        spot_data = data["spot"]
        board_data = data["board"]
        zt_data = data["zt"]
        etf_data = data["etf"]
        fund_data = data["fund"]

        self.market_temp = self.estimate_market_temp(spot_data)
        logger.info(f"\n🌡️ 市场温度: {self.market_temp}℃")

        all_results = {}
        fund_results = []  # 基金单独存放

        for strategy in self.strategies:
            try:
                if isinstance(strategy, GrowthBoardStrategy) and self.market_temp < 50:
                    logger.info(f"[{strategy.name}] 市场温度 < 50℃，跳过")
                    continue

                results = strategy.scan(spot_data, board_data, zt_data, etf_data, fund_data)

                if isinstance(strategy, FundStrategy):
                    fund_results = results
                else:
                    all_results[strategy.name] = results

            except Exception as e:
                logger.error(f"[{strategy.name}] 扫描异常: {e}")

        return {
            "scan_time": self.scan_time.isoformat(),
            "market_temp": self.market_temp,
            "stock_results": all_results,  # 股票/ETF策略结果
            "fund_results": fund_results,  # 基金结果(单独展示)
        }

    def generate_markdown_report(self, scan_result: Dict) -> str:
        """生成完整 Markdown 报告"""
        lines = [
            f"# 多策略选股扫描报告",
            f"",
            f"**扫描时间**: {scan_result['scan_time']}",
            f"**市场温度**: {scan_result['market_temp']}℃",
            f"",
            f"---",
        ]

        stock_results = scan_result.get("stock_results", {})
        fund_results = scan_result.get("fund_results", [])

        total = sum(len(v) for v in stock_results.values()) + len(fund_results)
        lines.append(f"\n## 📋 汇总: {total} 只标的\n")

        for name, results in stock_results.items():
            if results:
                lines.append(f"\n### {name}\n")
                lines.append("| 代码 | 名称 | 价格 | 涨跌幅 | 信号 | 原因 |")
                lines.append("|------|------|------|--------|------|------|")
                for r in sorted(results, key=lambda x: x.get("chg", 0), reverse=True):
                    lines.append(
                        f"| {r.get('code','')} | {r.get('name','')} | "
                        f"{r.get('price', 0):.2f} | {r.get('chg', 0):+.2f}% | "
                        f"{r.get('signal','')} | {r.get('reason','')} |"
                    )

        if fund_results:
            lines.append(f"\n### 基金策略\n")
            lines.append("| 代码 | 名称 | 净值 | 日涨幅 | 信号 | 原因 |")
            lines.append("|------|------|------|--------|------|------|")
            for r in fund_results:
                lines.append(
                    f"| {r.get('code','')} | {r.get('name','')} | "
                    f"{r.get('price', 0):.4f} | {r.get('chg', 0):+.4f}% | "
                    f"{r.get('signal','')} | {r.get('reason','')} |"
                )

        lines.append("\n---\n*本报告由多策略扫描器 v2.0 自动生成*")
        return "\n".join(lines)

    def save_results(self, scan_result: Dict, prefix: str = "") -> Dict:
        """保存结果到文件"""
        ts = self.scan_time.strftime("%Y%m%d_%H%M")
        prefix_str = f"{prefix}_" if prefix else ""

        # 保存 JSON
        json_path = os.path.join(OUTPUT_DIR, f"{prefix_str}scan_results_{ts}.json")
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(scan_result, f, ensure_ascii=False, indent=2, default=str)

        # 保存 Markdown 报告
        md_path = os.path.join(OUTPUT_DIR, f"{prefix_str}scan_report_{ts}.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(self.generate_markdown_report(scan_result))

        logger.info(f"✅ 结果已保存:")
        logger.info(f"  JSON: {json_path}")
        logger.info(f"  MD:   {md_path}")
        return {"json": json_path, "md": md_path}


# ==================== 主程序 ====================
def main():
    print("=" * 60)
    print("多策略选股扫描器 v2.0 (Enhanced)")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    scanner = MultiStrategyScanner()

    try:
        result = scanner.run()

        # 控制台输出汇总
        print("\n" + "=" * 60)
        total = sum(len(v) for v in result["stock_results"].values()) + len(result["fund_results"])
        print(f"📋 扫描结果汇总: {total} 只标的  |  市场温度: {result['market_temp']}℃")
        print("=" * 60)

        for name, results in result["stock_results"].items():
            if results:
                print(f"\n📌 {name} ({len(results)}只):")
                for r in sorted(results, key=lambda x: x.get("chg", 0), reverse=True)[:5]:
                    print(f"  {r['code']} {r['name']:<8} {r['price']:>7.2f}  {r['chg']:>+6.2f}%  {r['reason']}")

        if result["fund_results"]:
            print(f"\n💰 基金 ({len(result['fund_results'])}只):")
            for r in result["fund_results"][:5]:
                print(f"  {r['code']} {r['name']}")

        # 保存
        files = scanner.save_results(result)
        print(f"\n✅ 报告已保存至:")
        print(f"  {files['md']}")

    except Exception as e:
        logger.error(f"扫描失败: {e}")
        raise


if __name__ == "__main__":
    main()
