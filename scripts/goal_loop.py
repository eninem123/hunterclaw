#!/usr/bin/env python3
"""轻量goal循环 - 移植自Hermes /goal 核心逻辑
用法: python3 goal_loop.py "任务目标"
- 每轮执行后自动judge是否完成
- 未完成则自动继续
- 最大20轮
- judge用MiMo API(省token)
"""
import sys, json, time, os
try:
    from openai import OpenAI
except ImportError:
    print("ERROR: pip install openai"); sys.exit(1)

# MiMo API配置
MIMO_API = "https://token-plan-cn.xiaomimimo.com/v1"
MIMO_KEY = "tp-czmhb86n2j7nlx1b717du0e76khpm558ntajjl2158j2u084"
JUDGE_MODEL = "mimo/mimo-v2.5"
MAX_TURNS = 20

# 通信桥
sys.path.insert(0, "/tmp")
try:
    from agent_comm import send_msg, task_update, task_submit, task_review, mistake_log
except:
    pass

JUDGE_SYSTEM = """你是任务完成判断器。根据任务目标和Agent最新回复，判断任务是否完成。
只输出JSON: {"done": true/false, "reason": "完成/未完成的原因"}
不要输出其他内容。"""

JUDGE_PROMPT = """任务目标: {goal}
Agent最新回复: {response}
当前轮次: {turn}/{max_turns}

判断任务是否已完成。完成=Agent已交付产出物且验证通过。未完成=还需要继续工作。
输出JSON: {{"done": true/false, "reason": "..."}}"""

CONTINUATION = """[继续执行目标]
目标: {goal}
你还没完成。上次回复: {last_response}
继续工作，完成下一步。如果已完成，明确说"任务完成"并列出产出物。"""

def judge(goal, response, turn):
    """调用MiMo判断任务是否完成"""
    try:
        client = OpenAI(base_url=MIMO_API, api_key=MIMO_KEY)
        prompt = JUDGE_PROMPT.format(goal=goal[:2000], response=response[:3000], turn=turn, max_turns=MAX_TURNS)
        resp = client.chat.completions.create(
            model=JUDGE_MODEL,
            messages=[{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": prompt}],
            temperature=0, max_tokens=200, timeout=30
        )
        raw = resp.choices[0].message.content.strip()
        # 提取JSON
        if "```" in raw:
            raw = raw.split("```")[1].strip()
            if raw.startswith("json"): raw = raw[4:].strip()
        result = json.loads(raw)
        return result.get("done", False), result.get("reason", "")
    except Exception as e:
        # fail-open: judge失败就继续
        print(f"  judge error: {e}")
        return False, f"judge error: {e}"

def run_goal(agent, goal, task_id=None):
    """执行goal循环"""
    print(f"🎯 Goal开始: {goal[:80]}")
    print(f"  Agent: {agent} | Max turns: {MAX_TURNS}")
    if task_id:
        print(f"  Task: {task_id}")
    
    # 通知Agent开始
    send_msg("goal_loop", agent, f"【目标】{goal}\n请开始执行，完成后通过通信桥汇报结果。", "goal_loop")
    
    last_response = ""
    for turn in range(1, MAX_TURNS + 1):
        print(f"\n--- Turn {turn}/{MAX_TURNS} ---")
        
        # 等待Agent回复(检查inbox)
        time.sleep(10)  # 给Agent时间处理
        
        # 检查通信桥inbox
        import redis
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        msgs = []
        key = f"comm:goal_loop:inbox"
        for _ in range(r.llen(key) if r else 0):
            raw = r.rpop(key)
            if raw:
                msg = json.loads(raw)
                if msg["from"] == agent:
                    msgs.append(msg)
        
        if msgs:
            last_response = msgs[-1]["msg"]
            print(f"  Agent回复: {last_response[:100]}")
        else:
            # 没收到回复，催促
            send_msg("goal_loop", agent, CONTINUATION.format(goal=goal, last_response=last_response[:500]), "goal_loop")
            print(f"  无回复，催促中...")
            continue
        
        # Judge
        done, reason = judge(goal, last_response, turn)
        print(f"  Judge: {'✅ DONE' if done else '🔄 CONTINUE'} - {reason}")
        
        if done:
            print(f"\n🎉 Goal完成! 用了{turn}轮")
            if task_id:
                # 更新任务状态
                task_submit(task_id, last_response[:500], "goal_loop_auto")
            return True
        
        # 未完成，继续
        if turn < MAX_TURNS:
            send_msg("goal_loop", agent, CONTINUATION.format(goal=goal, last_response=last_response[:500]), "goal_loop")
    
    print(f"\n⚠️ Goal达到最大轮次({MAX_TURNS})仍未完成")
    if task_id:
        mistake_log(agent, "timeout", f"goal循环{MAX_TURNS}轮未完成", "任务可能太大需拆分", "拆分为更小的子任务")
    return False

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python3 goal_loop.py <agent> <goal> [task_id]")
        print("  agent: lobster / hermes")
        print("  goal: 任务目标")
        print("  task_id: 可选，关联任务ID")
        sys.exit(1)
    agent = sys.argv[1]
    goal = sys.argv[2]
    task_id = sys.argv[3] if len(sys.argv) >= 4 else None
    run_goal(agent, goal, task_id)
