#!/usr/bin/env python3
"""
GLM助手 - 统一调用封装
用于不重要的费token任务：报告生成、文档整理、策略解读
"""
import json
import subprocess
import time
from pathlib import Path

# Byebug API配置（GLM-5.1，5亿token额度）
BYEBUG_API = "https://api.minimax.chat/v1"
BYEBUG_KEY = "sk-api-iZiz-X30hWc-Kl_z0fFw-ZZ_W052thjQNnfE0robIqRiq5ezCG62G9p_p9Mha5WQaH5L8DC5kc1LHT9NH8GJITalx3T9s_d6SCIqN9QzAwgUCgF1yekwueI"
MODEL = "MiniMax-M2.7"

# 输出目录
OUTPUT_DIR = Path(__file__).parent / "glm_outputs"
OUTPUT_DIR.mkdir(exist_ok=True)


def _extract_answer(raw: str) -> str:
    """
    从GLM输出中提取实际答案。
    GLM先推理再回答，所以优先找【结论】标记后的内容。
    """
    if not raw:
        return ""
    
    if '【结论】' in raw:
        conclusion_part = raw.split('【结论】')[1]
        if '推理过程' in conclusion_part:
            conclusion_part = conclusion_part.split('推理过程')[0]
        if '分析请求' in conclusion_part:
            conclusion_part = conclusion_part.split('分析请求')[0]
        return conclusion_part.strip()
    
    sections = raw.split('\n\n')
    for sec in reversed(sections):
        sec = sec.strip()
        if len(sec) > 30 and not sec.startswith('1. **') and not sec.startswith('2. **'):
            return sec[:500]
    
    return raw[:300]


def call_glm(prompt: str, max_tokens: int = 3000, temperature: float = 0.7,
             system: str = "你是一位专业的量化交易策略师，回答简洁专业。先给结论，再简要分析。") -> str:
    """
    调用GLM-5.1，返回实际答案内容
    强制GLM先输出【结论】再推理，确保答案不被截断
    """
    wrapped_prompt = f"""在回答时，先写【结论】开头的结论行（这一行就是答案，必须完整且独立），换行后再写简短推理。

问：{prompt}
答：
【结论】"""

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": wrapped_prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BYEBUG_API}/chat/completions",
        "-H", f"Authorization: Bearer {BYEBUG_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]

    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            resp = json.loads(result.stdout)
            
            if "error" in resp:
                return f"[GLM错误] {resp['error'].get('message', '未知错误')}"
            
            msg = resp["choices"][0]["message"]
            raw = msg.get("content") or msg.get("reasoning_content") or ""
            
            if not raw:
                return "[GLM错误] 返回内容为空"
            
            extracted = _extract_answer(raw)
            return extracted if extracted else raw[:300]
                
        except subprocess.TimeoutExpired:
            if attempt < 2:
                time.sleep(5)
                continue
            return "[GLM错误] 调用超时"
        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(3)
                continue
            return f"[GLM错误] 响应解析失败"
        except Exception as e:
            return f"[GLM错误] {e}"

    return "[GLM错误] 多次重试失败"


def call_glm_json(prompt: str, max_tokens: int = 1500) -> str:
    """
    调用GLM-5.1用于需要纯JSON输出的场景
    不使用【结论】包装，直接返回原始输出
    """
    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": "你是一个量化策略描述生成器，只输出JSON，不要任何其他文字。"},
            {"role": "user", "content": prompt}
        ],
        "max_tokens": max_tokens,
        "temperature": 0.3
    }

    cmd = [
        "curl", "-s", "-X", "POST",
        f"{BYEBUG_API}/chat/completions",
        "-H", f"Authorization: Bearer {BYEBUG_KEY}",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload)
    ]

    for attempt in range(3):
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
            resp = json.loads(result.stdout)
            
            if "error" in resp:
                return f"[GLM错误] {resp['error'].get('message', '未知错误')}"
            
            msg = resp["choices"][0]["message"]
            raw = msg.get("content") or msg.get("reasoning_content") or ""
            
            if not raw:
                return "[GLM错误] 返回内容为空"
            
            cleaned = raw.strip()
            if cleaned.startswith('```'):
                lines = cleaned.split('\n')
                cleaned = '\n'.join(lines[1:-1] if lines[-1].strip() == '```' else lines[1:])
            
            return cleaned
                
        except subprocess.TimeoutExpired:
            if attempt < 2:
                time.sleep(5)
                continue
            return "[GLM错误] 调用超时"
        except json.JSONDecodeError:
            if attempt < 2:
                time.sleep(3)
                continue
            return f"[GLM错误] 响应解析失败"
        except Exception as e:
            return f"[GLM错误] {e}"

    return "[GLM错误] 多次重试失败"


def save_output(filename: str, content: str) -> str:
    """保存GLM输出到文件"""
    filepath = OUTPUT_DIR / filename
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    return str(filepath)


# ============================================================
# 任务1：猎手每日复盘报告增强
# ============================================================

def generate_daily_review_report(positions: list, market_data: dict, 
                                  market_temp: int, trade_log: list = None) -> str:
    """
    生成每日复盘报告（自然语言分析）
    """
    pos_summary = []
    for p in positions:
        if p.get('status') != 'holding':
            continue
        pnl_pct = p.get('pnl_pct', 0)
        pos_summary.append(
            f"- {p['name']}({p['code']})：成本¥{p['entry_price']}，"
            f"现价¥{p.get('current_price', p['entry_price'])}，"
            f"浮盈{pnl_pct:+.2f}%，止损¥{p.get('stop_loss', 'N/A')}"
        )
    
    if not pos_summary:
        pos_summary = ["今日无持仓"]
    
    market_summary = []
    for name, data in market_data.items():
        market_summary.append(
            f"- {name}：{data.get('price', 'N/A')}点，涨跌{data.get('chg', 'N/A')}%"
        )
    
    if not market_summary:
        market_summary = ["- 市场数据获取失败"]
    
    trade_summary = []
    if trade_log:
        for t in trade_log[-5:]:
            trade_summary.append(
                f"- {t.get('date', '')} {t.get('action', '')} "
                f"{t.get('name', t.get('code', ''))} @¥{t.get('price', '')}"
            )
    
    prompt = f"""你是专业量化交易策略师，负责生成猎手系统的每日复盘报告。

【持仓情况】
{chr(10).join(pos_summary)}

【市场情况】
{chr(10).join(market_summary)}
- 市场温度：{market_temp}℃（<50℃偏冷，≥50℃回暖，≥80℃强势）

【今日交易记录】
{chr(10).join(trade_summary) if trade_summary else "今日无交易"}

【猎手规则参考】
- 止损红线：-5%（触发必走）
- 止盈目标：+8%达标分批走
- 市场<50℃不开新仓
- 单日买入≤3次，单只持仓≤30%

请生成复盘报告，包含：
1. 持仓诊断（是否持有/减仓/清仓建议）
2. 今日操作回顾
3. 明日操作方向
4. 风险提示

语气：简洁专业，像交易员复盘，不废话。"""

    report = call_glm(prompt, max_tokens=2000)
    return report


# ============================================================
# 任务2：策略描述生成
# ============================================================

def generate_strategy_description(gene_params: dict) -> str:
    """
    根据策略基因参数，生成自然语言描述
    """
    params_str = json.dumps(gene_params, ensure_ascii=False, indent=2)
    
    prompt = f"""你是量化策略专家。请解读以下策略参数的含义和交易逻辑。

【策略参数】
{params_str}

请用简洁的话解释：
1. 这个策略的核心逻辑是什么？
2. 什么时候会买入？什么时候会卖出？
3. 适合什么市场环境？
4. 有什么潜在风险？

控制在200字内。"""

    desc = call_glm(prompt, max_tokens=500, system="你是一位量化策略专家，解读简洁专业。")
    return desc


def generate_strategy_desc_json(gene: dict) -> dict:
    """
    为单个策略生成完整描述（JSON格式）
    """
    gene_str = json.dumps(gene, ensure_ascii=False, indent=2)
    
    prompt = f"""你是量化策略专家。请为以下策略参数生成完整的策略描述。

【策略参数】
{gene_str}

请生成以下信息（直接输出JSON，不要其他内容）：
{{
    "name": "策略简称（10字内）",
    "trading_style": "交易风格（趋势/均值回归/突破/量价配合等）",
    "description": "用2-3句话描述这个策略的核心逻辑",
    "buy_condition": "具体描述买入条件（什么情况下买入，1句话）",
    "sell_condition": "具体描述卖出条件（什么情况下卖出，1句话）",
    "suitable_market": "适合的市场环境（1句话）",
    "risk": "最大风险点（1句话）"
}}

输出格式：必须是有效JSON，不要加markdown代码块标记。"""

    raw = call_glm_json(prompt, max_tokens=1500)
    
    try:
        desc = json.loads(raw)
        
        if 'ma_fast' in gene and 'rsi_period' in gene:
            sid = f"MA_RSI_{gene['ma_fast']}_{gene['ma_slow']}_{gene['rsi_period']}"
        elif 'ma_fast' in gene:
            sid = f"MA_{gene['ma_fast']}_{gene['ma_slow']}"
        elif 'rsi_period' in gene:
            sid = f"RSI_{gene['rsi_period']}"
        else:
            sid = f"STRAT_{abs(hash(json.dumps(gene, sort_keys=True))) % 10000}"
        
        desc['strategy_id'] = sid
        desc['params'] = gene
        return desc
        
    except json.JSONDecodeError:
        return {
            "strategy_id": f"ERR_{abs(hash(gene_str)) % 10000}",
            "name": "解析失败",
            "trading_style": "未知",
            "description": raw[:200],
            "buy_condition": "N/A",
            "sell_condition": "N/A",
            "suitable_market": "N/A",
            "risk": "N/A",
            "params": gene,
            "error": "JSON解析失败"
        }


# ============================================================
# 任务3：文档整理（知识库）
# ============================================================

def organize_document(raw_text: str, doc_type: str = "lesson") -> str:
    """
    将原始笔记整理成结构化文档
    """
    type_hints = {
        "lesson": "实战教训记录",
        "rules": "交易规则",
        "analysis": "市场分析",
        "fundamental": "基本面分析"
    }
    
    prompt = f"""你是一位专业金融编辑。请将以下内容整理成结构化的{type_hints.get(doc_type, doc_type)}文档。

【原始内容】
{raw_text}

【要求】
- 添加适当的标题和章节
- 补充关键要点（用列表）
- 添加"核心结论"章节（必须有一条可执行的操作建议）
- 控制篇幅，删除冗余内容
- 语气：专业简洁，不废话"""

    organized = call_glm(prompt, max_tokens=3000, system="你是一位专业金融编辑，擅长整理结构化文档。")
    return organized


# ============================================================
# 任务4：批量标注（实验性）
# ============================================================

def batch_annotate(items: list, annotation_type: str = "sentiment") -> list:
    """
    批量对数据进行标注
    """
    type_hints = {
        "sentiment": "情感（看多/看空/中性）",
        "label": "分类标签",
        "priority": "优先级（高/中/低）"
    }
    
    items_text = "\n".join([f"{i+1}. {item}" for i, item in enumerate(items)])
    
    prompt = f"""请对以下{len(items)}条数据进行{annotation_type}标注（{type_hints.get(annotation_type, annotation_type)}）。

【待标注数据】
{items_text}

【标注要求】
直接输出{len(items)}行，每行格式：序号. 原始内容 → 标注结果
不要解释，不要废话。"""

    result = call_glm(prompt, max_tokens=1500, system="你是一个标注工具，输出简洁直接。")
    
    annotated = []
    for line in result.split("\n"):
        if "→" in line:
            parts = line.split("→")
            if len(parts) == 2:
                annotated.append({
                    "original": parts[0].strip(),
                    "annotation": parts[1].strip()
                })
    
    return annotated if annotated else [{"original": item, "annotation": "标注失败"} for item in items]
