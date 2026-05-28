#!/usr/bin/env python3
"""三Agent通信桥 v3 - 进化架构版
v2基础 + 状态机 + 交叉验证 + 错误记忆 + 进化档案
"""
import sys, os, json, time, math
try:
    import redis
    REDIS_OK = True
except ImportError:
    REDIS_OK = False
import sqlite3

REDIS_HOST = "localhost"
REDIS_PORT = 6379
DB_PATH = "/opt/agent_state/agent.db"
AGENTS = ["hunter", "lobster", "hermes"]

# 合法状态转换
VALID_TRANSITIONS = {
    "pending": ["in_progress"],
    "in_progress": ["verifying", "failed"],
    "verifying": ["reviewing", "failed"],
    "reviewing": ["completed", "iterated", "failed"],
    "failed": ["in_progress"],  # 允许重试
    "completed": ["iterated"],
    "iterated": ["in_progress"],
}

def get_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True) if REDIS_OK else None

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db

# ── 通信(v2兼容) ──
def send_msg(sender, receiver, message, data_source=""):
    if sender not in AGENTS:
        print(f"ERROR: unknown sender {sender}"); return 1
    targets = AGENTS if receiver == "all" else [receiver]
    for tgt in targets:
        if tgt not in AGENTS:
            print(f"ERROR: unknown receiver {tgt}"); return 1
        if tgt == sender: continue
        msg = {"from": sender, "to": tgt, "time": time.strftime("%Y-%m-%d %H:%M:%S"),
               "ts": int(time.time()*1000), "msg": message, "data_source": data_source}
        r = get_redis()
        if r:
            r.lpush(f"comm:{tgt}:inbox", json.dumps(msg, ensure_ascii=False))
        db = get_db()
        db.execute("INSERT INTO messages(from_agent,to_agent,content,data_source) VALUES (?,?,?,?)",
                   (sender, tgt, message, data_source))
        db.commit(); db.close()
        print(f"OK -> {tgt}")
    return 0

def recv_msg(agent, all_msgs=False):
    if agent not in AGENTS:
        print(f"ERROR: unknown agent {agent}"); return 1
    r = get_redis()
    msgs = []
    if r:
        key = f"comm:{agent}:inbox"
        count = r.llen(key) if all_msgs else 1
        for _ in range(count):
            raw = r.rpop(key)
            if raw: msgs.append(json.loads(raw))
    if not msgs:
        print("EMPTY"); return 0
    for msg in msgs:
        print(f"[{msg['time']}] {msg['from']} -> {msg['to']}:")
        print(f"  {msg['msg']}")
        if msg.get('data_source'):
            print(f"  [source: {msg['data_source']}]")

def ls_msg(agent):
    if agent not in AGENTS:
        print(f"ERROR: unknown agent {agent}"); return 1
    r = get_redis()
    if r:
        key = f"comm:{agent}:inbox"
        count = r.llen(key)
        print(f"{count} messages in {agent} inbox")

# ── 任务状态机 ──
def task_create(task_id, agent, title, priority, description=""):
    db = get_db()
    existing = db.execute("SELECT task_id FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if existing:
        print(f"ERROR: task {task_id} already exists"); db.close(); return 1
    db.execute("INSERT INTO tasks(task_id,from_agent,to_agent,title,status,description) VALUES (?,?,?,?,?,?)",
               (task_id, agent, agent, title, "pending", description))
    mistakes = db.execute("SELECT error_type, error_desc, prevention FROM mistakes WHERE agent=? ORDER BY created_at DESC LIMIT 5", (agent,)).fetchall()
    if mistakes:
        print(f"  ⚠ 历史错误提醒({len(mistakes)}条):")
        for m in mistakes:
            print(f"    - [{m['error_type']}] {m['error_desc'][:80]} → {m['prevention'][:60]}")
    db.commit(); db.close()
    print(f"OK: {task_id} created (pending)")

def task_update(task_id, new_status, extra=""):
    db = get_db()
    task = db.execute("SELECT status, from_agent as agent FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if not task:
        print(f"ERROR: task {task_id} not found"); db.close(); return 1
    old_status = task["status"]
    # 状态机校验
    if new_status not in VALID_TRANSITIONS.get(old_status, []):
        print(f"ERROR: cannot transition {old_status} -> {new_status}")
        print(f"  Valid transitions from {old_status}: {VALID_TRANSITIONS.get(old_status, [])}")
        db.close(); return 1
    # 特殊校验: verifying需要output+data_source
    if new_status == "verifying":
        output = db.execute("SELECT output FROM tasks WHERE task_id=?", (task_id,)).fetchone()["output"]
        if not output:
            print("ERROR: cannot move to verifying without output. Use: task_submit <task_id> <output> <data_source>")
            db.close(); return 1
    # 特殊校验: reviewing需要交叉验证通过
    if new_status == "reviewing":
        eval_row = db.execute("SELECT agent FROM evaluations WHERE task_id=? AND eval_type='cross' AND passed=1", (task_id,)).fetchone()
        if not eval_row:
            print("ERROR: cannot move to reviewing without cross-verification passed")
            db.close(); return 1
        db.execute("UPDATE tasks SET verified_by=? WHERE task_id=?", (eval_row["agent"], task_id))
    # 特殊校验: completed需要review
    if new_status == "completed":
        review = db.execute("SELECT review FROM tasks WHERE task_id=?", (task_id,)).fetchone()["review"]
        if not review:
            print("ERROR: cannot complete without review. Use: task_review <task_id> <review_text>")
            db.close(); return 1
    db.execute("UPDATE tasks SET status=?, description=COALESCE(NULLIF(?, ''), description) WHERE task_id=?",
               (new_status, extra, task_id))
    db.commit(); db.close()
    print(f"OK: {task_id} {old_status} -> {new_status}")
    # 自动归档completed
    if new_status == "completed":
        archive_save_auto(task_id)

def task_submit(task_id, output, data_source):
    """提交产出物，自动转到verifying"""
    db = get_db()
    task = db.execute("SELECT status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if not task:
        print(f"ERROR: task {task_id} not found"); db.close(); return 1
    if task["status"] not in ["in_progress", "failed"]:
        print(f"ERROR: can only submit from in_progress/failed, current: {task['status']}")
        db.close(); return 1
    db.execute("UPDATE tasks SET output=?, data_source=?, status='verifying' WHERE task_id=?",
               (output, data_source, task_id))
    db.commit(); db.close()
    print(f"OK: {task_id} submitted -> verifying")

def task_review(task_id, review_text):
    """写复盘记录"""
    db = get_db()
    db.execute("UPDATE tasks SET review=? WHERE task_id=?", (review_text, task_id))
    db.commit(); db.close()
    print(f"OK: review saved for {task_id}")

def task_list(agent=None, status=None):
    db = get_db()
    q = "SELECT task_id as id, from_agent as agent, title, status FROM tasks WHERE 1=1"
    params = []
    if agent:
        q += " AND from_agent=?"; params.append(agent)
    if status:
        q += " AND status=?"; params.append(status)
    q += " ORDER BY id"
    rows = db.execute(q, params).fetchall()
    for r in rows:
        icon = {"completed":"✅", "in_progress":"🔧", "verifying":"🔍", "reviewing":"📝",
                "pending":"⏳", "failed":"❌", "iterated":"🔄"}.get(r["status"], "?")
        print(f"  {icon} {r['id']} | {r['agent']} | {r['title'][:40]} | {r['status']}")
    db.close()

# ── 交叉验证 ──
def verify_submit(task_id, output_json):
    """提交验证请求，自动分配给另一个Agent"""
    db = get_db()
    task = db.execute("SELECT from_agent as agent, status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if not task:
        print(f"ERROR: task {task_id} not found"); db.close(); return 1
    if task["status"] != "verifying":
        print(f"ERROR: task not in verifying state, current: {task['status']}")
        db.close(); return 1
    # 选择验证者(不是自己)
    verifier = [a for a in AGENTS if a != task["agent"]][0]
    db.execute("INSERT INTO evaluations(task_id, agent, eval_type, stage, details) VALUES (?,?,?,?,?)",
               (task_id, verifier, "cross", 1, output_json))
    db.commit(); db.close()
    # 通知验证者
    send_msg("system", verifier, f"请验证任务 {task_id}: {output_json[:200]}", "auto_verify")
    print(f"OK: verification request sent to {verifier}")

def verify_next(agent):
    """获取待验证任务"""
    db = get_db()
    rows = db.execute("SELECT task_id, details, stage FROM evaluations WHERE agent=? AND eval_type='cross' AND passed IS NULL ORDER BY created_at",
                      (agent,)).fetchall()
    if not rows:
        print("NO_PENDING_VERIFICATIONS"); db.close(); return 0
    for r in rows:
        print(f"  Task: {r['task_id']} | Stage: {r['stage']} | Details: {r['details'][:150]}")
    db.close()

def verify_result(task_id, verifier, passed, details=""):
    """提交验证结果"""
    db = get_db()
    passed_bool = 1 if passed.lower() in ("pass", "1", "true", "yes") else 0
    score = 1.0 if passed_bool else 0.0
    db.execute("UPDATE evaluations SET passed=?, score=?, details=COALESCE(NULLIF(?, ''), details) WHERE task_id=? AND agent=? AND eval_type='cross' AND passed IS NULL",
               (passed_bool, score, details, task_id, verifier))
    if not passed_bool:
        # 验证失败，任务回退到failed
        db.execute("UPDATE tasks SET status='failed' WHERE task_id=?", (task_id,))
        print(f"FAIL: {task_id} verification failed -> task back to failed")
    else:
        print(f"PASS: {task_id} verified by {verifier}")
    db.commit(); db.close()

# ── 错误记忆 ──
def mistake_log(agent, error_type, error_desc, root_cause, prevention, task_id=""):
    db = get_db()
    # 检查是否重犯
    similar = db.execute("SELECT id FROM mistakes WHERE agent=? AND error_type=? AND error_desc LIKE ?",
                         (agent, error_type, f"%{error_desc[:30]}%")).fetchall()
    recurred = 1 if similar else 0
    db.execute("INSERT INTO mistakes(agent, task_id, error_type, error_desc, root_cause, prevention, recurred) VALUES (?,?,?,?,?,?,?)",
               (agent, task_id, error_type, error_desc, root_cause, prevention, recurred))
    db.commit(); db.close()
    flag = "🔴 RECURRING" if recurred else "🟡 NEW"
    print(f"OK: mistake logged [{flag}] - {error_type}: {error_desc[:60]}")

def mistake_query(agent="", error_type=""):
    db = get_db()
    q = "SELECT agent, error_type, error_desc, prevention, recurred, created_at FROM mistakes WHERE 1=1"
    params = []
    if agent: q += " AND agent=?"; params.append(agent)
    if error_type: q += " AND error_type=?"; params.append(error_type)
    q += " ORDER BY created_at DESC LIMIT 20"
    rows = db.execute(q, params).fetchall()
    for r in rows:
        icon = "🔴" if r["recurred"] else "🟡"
        print(f"  {icon} [{r['agent']}] {r['error_type']}: {r['error_desc'][:60]} → {r['prevention'][:50]}")
    db.close()

# ── 决策日志 ──
def decision_log(agent, decision, reasoning, outcome="pending"):
    db = get_db()
    db.execute("INSERT INTO decisions(agent, decision, reasoning, outcome) VALUES (?,?,?,?)",
               (agent, decision, reasoning, outcome))
    db.commit(); db.close()
    print(f"OK: decision logged - {decision[:60]}")

# ── 进化档案 ──
def archive_save(task_id, agent, output, score=None):
    db = get_db()
    task = db.execute("SELECT title, status FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if not task:
        print(f"ERROR: task {task_id} not found"); db.close(); return 1
    # 找父代(同agent同类型的上一个)
    parent = db.execute("SELECT id, generation FROM archive WHERE agent=? ORDER BY id DESC LIMIT 1", (agent,)).fetchone()
    generation = (parent["generation"] + 1) if parent else 1
    parent_id = parent["id"] if parent else None
    if score is None:
        # 从evaluations取分
        eval_row = db.execute("SELECT score FROM evaluations WHERE task_id=? ORDER BY created_at DESC LIMIT 1", (task_id,)).fetchone()
        score = eval_row["score"] if eval_row else 0.5
    db.execute("INSERT INTO archive(generation, agent, task_type, input_summary, output, score, parent_id) VALUES (?,?,?,?,?,?,?)",
               (generation, agent, task["title"][:50], task_id, output, score, parent_id))
    db.commit(); db.close()
    print(f"OK: archived gen#{generation} score={score:.2f}")

def archive_save_auto(task_id):
    """completed时自动归档"""
    db = get_db()
    task = db.execute("SELECT from_agent as agent, output FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    if task and task["output"]:
        archive_save(task_id, task["agent"], task["output"])
    db.close()

def archive_query(agent="", task_type=""):
    db = get_db()
    q = "SELECT generation, agent, task_type, score, created_at FROM archive WHERE 1=1"
    params = []
    if agent: q += " AND agent=?"; params.append(agent)
    if task_type: q += " AND task_type LIKE ?"; params.append(f"%{task_type}%")
    q += " ORDER BY generation DESC LIMIT 20"
    rows = db.execute(q, params).fetchall()
    for r in rows:
        bar = "█" * int(r["score"] * 10) + "░" * (10 - int(r["score"] * 10))
        print(f"  gen#{r['generation']:3d} | {r['agent']} | {r['task_type'][:30]:30s} | {bar} {r['score']:.2f} | {r['created_at']}")
    db.close()

# ── 分阶段评估 ──
def staged_eval(task_id, agent, output):
    """分3阶段评估"""
    # Stage 1: 基本检查
    if not output or output.strip() == "":
        print("FAIL Stage 1: output is empty")
        db = get_db()
        db.execute("INSERT INTO evaluations(task_id, agent, eval_type, stage, score, passed, details) VALUES (?,?,?,?,?,?,?)",
                   (task_id, agent, "staged", 1, 0.0, 0, "empty output"))
        db.commit(); db.close()
        return 0.0
    print("PASS Stage 1: output exists")
    
    # Stage 2: 格式检查(是否能JSON解析或包含关键数据)
    try:
        parsed = json.loads(output)
        has_structure = isinstance(parsed, (dict, list)) and len(str(parsed)) > 50
    except:
        has_structure = len(output) > 100  # 非JSON但足够长
    
    if not has_structure:
        print("FAIL Stage 2: output lacks structure or depth")
        db = get_db()
        db.execute("INSERT INTO evaluations(task_id, agent, eval_type, stage, score, passed, details) VALUES (?,?,?,?,?,?,?)",
                   (task_id, agent, "staged", 2, 0.3, 0, "insufficient structure"))
        db.commit(); db.close()
        return 0.3
    print("PASS Stage 2: output has structure")
    
    # Stage 3: 数据来源检查
    db = get_db()
    task = db.execute("SELECT data_source FROM tasks WHERE task_id=?", (task_id,)).fetchone()
    has_source = task and task["data_source"] and task["data_source"].strip() != ""
    score = 1.0 if has_source else 0.7
    passed = 1 if score >= 0.7 else 0
    db.execute("INSERT INTO evaluations(task_id, agent, eval_type, stage, score, passed, details) VALUES (?,?,?,?,?,?,?)",
               (task_id, agent, "staged", 3, score, passed, f"source={'yes' if has_source else 'no'}"))
    db.commit(); db.close()
    print(f"{'PASS' if passed else 'WARN'} Stage 3: score={score:.2f} source={'✓' if has_source else '✗'}")
    return score

# ── 健康检查 ──
def healthcheck():
    r = get_redis()
    redis_ok = r.ping() if r else False
    db = get_db()
    tasks = db.execute("SELECT COUNT(*) as c FROM tasks").fetchone()["c"]
    pending = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='pending'").fetchone()["c"]
    verifying = db.execute("SELECT COUNT(*) as c FROM tasks WHERE status='verifying'").fetchone()["c"]
    mistakes_count = db.execute("SELECT COUNT(*) as c FROM mistakes").fetchone()["c"]
    archive_count = db.execute("SELECT COUNT(*) as c FROM archive").fetchone()["c"]
    db.close()
    print(f"Redis: {'✅' if redis_ok else '❌'}")
    print(f"Tasks: {tasks} total | {pending} pending | {verifying} verifying")
    print(f"Mistakes: {mistakes_count} | Archive: {archive_count} generations")

# ── CLI ──
if __name__ == "__main__":
    if len(sys.argv) < 2: 
        print(__doc__); sys.exit(1)
    cmd = sys.argv[1]
    
    # 通信(v2兼容)
    if cmd == "send" and len(sys.argv) >= 5:
        ds = sys.argv[6] if len(sys.argv) >= 7 else ""
        sys.exit(send_msg(sys.argv[2], sys.argv[3], sys.argv[4], ds))  # Fixed: sender=argv[2], receiver=argv[3], message=argv[4]
    elif cmd == "recv" and len(sys.argv) >= 3:
        sys.exit(recv_msg(sys.argv[2], all_msgs=False))
    elif cmd == "recvall" and len(sys.argv) >= 3:
        sys.exit(recv_msg(sys.argv[2], all_msgs=True))
    elif cmd == "ls" and len(sys.argv) >= 3:
        sys.exit(ls_msg(sys.argv[2]))
    
    # 任务状态机
    elif cmd == "task_create" and len(sys.argv) >= 7:
        task_create(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6] if len(sys.argv)>=7 else "")
    elif cmd == "task_update" and len(sys.argv) >= 4:
        task_update(sys.argv[2], sys.argv[3], sys.argv[4] if len(sys.argv)>=5 else "")
    elif cmd == "task_submit" and len(sys.argv) >= 5:
        task_submit(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "task_review" and len(sys.argv) >= 4:
        task_review(sys.argv[2], sys.argv[3])
    elif cmd == "task_list":
        task_list(sys.argv[2] if len(sys.argv)>=3 else None, sys.argv[3] if len(sys.argv)>=4 else None)
    
    # 交叉验证
    elif cmd == "verify_submit" and len(sys.argv) >= 4:
        verify_submit(sys.argv[2], sys.argv[3])
    elif cmd == "verify_next" and len(sys.argv) >= 3:
        verify_next(sys.argv[2])
    elif cmd == "verify_result" and len(sys.argv) >= 5:
        verify_result(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5] if len(sys.argv)>=6 else "")
    
    # 错误记忆
    elif cmd == "mistake_log" and len(sys.argv) >= 6:
        mistake_log(sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6] if len(sys.argv)>=7 else "")
    elif cmd == "mistake_query":
        mistake_query(sys.argv[2] if len(sys.argv)>=3 else "", sys.argv[3] if len(sys.argv)>=4 else "")
    
    # 决策日志
    elif cmd == "decision_log" and len(sys.argv) >= 5:
        decision_log(sys.argv[2], sys.argv[3], sys.argv[4])
    
    # 进化档案
    elif cmd == "archive_save" and len(sys.argv) >= 5:
        archive_save(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "archive_query":
        archive_query(sys.argv[2] if len(sys.argv)>=3 else "", sys.argv[3] if len(sys.argv)>=4 else "")
    
    # 分阶段评估
    elif cmd == "staged_eval" and len(sys.argv) >= 5:
        staged_eval(sys.argv[2], sys.argv[3], sys.argv[4])
    
    # 健康检查
    elif cmd == "health":
        healthcheck()
    
    else:
        print(__doc__); sys.exit(1)
