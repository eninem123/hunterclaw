#!/usr/bin/env python3
"""
Quiz Generator
Generates 3 quiz questions from daily learning content
"""

import json
import os
import random
import sys
from pathlib import Path

SKILL_DIR = "/root/.openclaw/workspace/skills/daily-learning"
INDEX_FILE = f"{SKILL_DIR}/outputs/learner_index.json"
PROGRESS_FILE = f"{SKILL_DIR}/outputs/progress.json"
OUTPUT_DIR = f"{SKILL_DIR}/outputs/quiz"

MODULE_QUESTIONS = {
    1: {
        "topic": "AI Agent / Knowledge Base",
        "questions": [
            {
                "q": "AI Agent 的核心循环是什么？",
                "options": ["感知→推理→执行→反馈", "输入→处理→输出", "学习→记忆→提取→生成", "感知→记忆→推理→执行"],
                "answer": 0,
                "explanation": "AI Agent 通过感知环境、推理决策、执行动作、反馈结果形成闭环。"
            },
            {
                "q": "知识库问答系统的核心组件包括？",
                "options": ["向量数据库 + Embedding模型 + 检索模块", "关系数据库 + SQL查询 + API", "图数据库 + 知识图谱 + 推理引擎", "搜索引擎 + 爬虫 + 索引"],
                "answer": 0,
                "explanation": "知识库问答基于向量检索，核心是 Embedding 模型将文本转为向量，在向量数据库中检索相似内容。"
            },
            {
                "q": "本地知识库部署的关键步骤？",
                "options": ["数据清洗→Embedding→存入向量库→检索→LLM生成", "爬虫抓取→数据清洗→存储MySQL→API调用", "用户上传→直接存储→返回确认", "模型训练→微调→部署→推理"],
                "answer": 0,
                "explanation": "本地知识库的流程：数据预处理 → Embedding → 向量存储 → 语义检索 → LLM 整合答案。"
            }
        ]
    },
    2: {
        "topic": "Data Pipeline / Script Development",
        "questions": [
            {
                "q": "DWD 层（数据明细宽表）的设计原则？",
                "options": ["原子性+最小冗余+维度退化", "高度聚合+预计算+报表优化", "范式化+多表关联+实时更新", "扁平化+去重+全量同步"],
                "answer": 0,
                "explanation": "DWD 是数据仓库的明细层，强调原子性、最小冗余，通过维度退化提高查询效率。"
            },
            {
                "q": "错误追踪系统的核心功能？",
                "options": ["记录→分类→根因分析→解决→复盘", "报警→通知→忽略→关闭", "抓取→存储→展示→删除", "监控→告警→升级→考核"],
                "answer": 0,
                "explanation": "错误追踪形成闭环：发现问题→分类定位→分析根因→解决处理→沉淀为经验。"
            },
            {
                "q": "Python 脚本中 `gen_cpt*.py` 的作用？",
                "options": ["生成指标数据/维度数据", "编译Python代码", "加密脚本文件", "测试用例生成"],
                "answer": 0,
                "explanation": "`gen_cpt*.py` 系列脚本用于生成数据管道的配置、指标定义或维度数据。"
            }
        ]
    },
    3: {
        "topic": "BI / Fanruan Report Automation",
        "questions": [
            {
                "q": "帆软报表自动化的核心流程？",
                "options": ["数据源配置→报表模板设计→自动化调度→结果验证", "手动制作→导出Excel→发送邮件→完成", "帆软客户端→FineReport→保存→打印", "数据抓取→清洗→保存→手动上传"],
                "answer": 0,
                "explanation": "帆软报表自动化：配置数据源连接 → 制作报表模板 → 配置定时调度任务 → 自动执行并发送结果。"
            },
            {
                "q": "数据审计的主要目的？",
                "options": ["验证数据准确性+完整性+一致性", "删除异常数据+美化报表", "加密敏感数据+防止泄露", "压缩数据体积+节省存储"],
                "answer": 0,
                "explanation": "数据审计核查数据质量：数值准确性、业务逻辑一致性、跨系统数据对齐。"
            },
            {
                "q": "业务需求文档的核心价值？",
                "options": ["桥接业务语言与技术实现", "记录会议纪要", "给领导汇报用", "归档保存"],
                "answer": 0,
                "explanation": "业务需求文档把业务方的诉求转化为技术可执行的需求，是需求分析的交付物。"
            }
        ]
    },
    4: {
        "topic": "Project Practice / Deployment",
        "questions": [
            {
                "q": "项目调研阶段的关键产出？",
                "options": ["需求调研报告+现状分析+可行性评估", "代码仓库地址", "服务器密码", "UI设计稿"],
                "answer": 0,
                "explanation": "项目调研产出：业务现状调研报告、痛点分析、技术可行性评估、项目风险评估。"
            },
            {
                "q": "生产环境部署的标准流程？",
                "options": ["环境检查→代码部署→配置变更→验证测试→监控告警", "直接上传代码→重启服务→完成", "本地测试→打包→邮件发送→告知用户", "开发环境→忽略测试→直接上线"],
                "answer": 0,
                "explanation": "标准生产部署：环境检查 → 灰度/全量发布 → 配置同步 → 功能验证 → 监控告警配置 → 编写部署文档。"
            },
            {
                "q": "项目复盘的核心目的？",
                "options": ["沉淀经验+改进流程+避免重复踩坑", "追究责任+惩罚失误", "展示成绩+汇报领导", "归档保存+完成任务"],
                "answer": 0,
                "explanation": "项目复盘是团队学习的重要环节：回顾目标→评估结果→分析原因→总结经验→改进机制。"
            }
        ]
    }
}


def load_progress():
    """Load learning progress"""
    if os.path.exists(PROGRESS_FILE):
        with open(PROGRESS_FILE, "r") as f:
            return json.load(f)
    return {"current_day": 1, "completed_files": [], "quiz_scores": []}


def get_current_module():
    """Get current module based on progress"""
    progress = load_progress()
    current_day = progress.get("current_day", 1)
    
    SCHEDULE = [
        1, 1, 1, 1, 1, 1, 1,
        2, 2, 2, 2, 2, 2, 2,
        3, 3, 3, 3, 3, 3, 3,
        4, 4, 4, 4, 4, 4, 4,
    ]
    
    idx = (current_day - 2) % len(SCHEDULE)  # -1 because we want current module
    return SCHEDULE[idx]


def generate_quiz(module_id=None):
    """Generate quiz for current or specified module"""
    if module_id is None:
        module_id = get_current_module()
    
    questions = MODULE_QUESTIONS.get(module_id, MODULE_QUESTIONS[1])
    
    quiz_text = []
    quiz_text.append(f"# 📝 Daily Quiz | Module {module_id}")
    quiz_text.append(f"**Topic**: {questions['topic']}")
    quiz_text.append("")
    quiz_text.append("---")
    quiz_text.append("")
    
    for i, q in enumerate(questions["questions"], 1):
        quiz_text.append(f"**Q{i}. {q['q']}**")
        quiz_text.append("")
        for j, opt in enumerate(q["options"]):
            letter = chr(65 + j)  # A, B, C, D
            quiz_text.append(f"  {letter}. {opt}")
        quiz_text.append("")
    
    quiz_text.append("---")
    quiz_text.append("")
    quiz_text.append("## ✅ Answers")
    for i, q in enumerate(questions["questions"], 1):
        letter = chr(65 + q["answer"])
        quiz_text.append(f"**Q{i}**: {letter} - {q['options'][q['answer']]}")
        quiz_text.append(f"   💡 {q['explanation']}")
        quiz_text.append("")
    
    quiz_text.append("")
    quiz_text.append("*回复答案，我会评分并记录到学习进度*")
    
    return "\n".join(quiz_text)


def check_answer(module_id, question_idx, user_answer):
    """Check user's quiz answer"""
    questions = MODULE_QUESTIONS.get(module_id, {}).get("questions", [])
    if question_idx >= len(questions):
        return False, "题目编号错误"
    
    q = questions[question_idx]
    correct = chr(65 + q["answer"]) == user_answer.upper()
    
    return correct, q["explanation"]


def save_quiz_result(question_idx, correct):
    """Save quiz result to progress"""
    progress = load_progress()
    if "quiz_scores" not in progress:
        progress["quiz_scores"] = []
    
    progress["quiz_scores"].append({
        "question": question_idx,
        "correct": correct,
        "date": str(__import__("datetime").date.today())
    })
    
    with open(PROGRESS_FILE, "w") as f:
        json.dump(progress, f, ensure_ascii=False, indent=2)


def run_quiz_check(day=None):
    """Main quiz generation"""
    if day:
        # Get module for specific day
        SCHEDULE = [
            1, 1, 1, 1, 1, 1, 1,
            2, 2, 2, 2, 2, 2, 2,
            3, 3, 3, 3, 3, 3, 3,
            4, 4, 4, 4, 4, 4, 4,
        ]
        idx = (day - 1) % len(SCHEDULE)
        module_id = SCHEDULE[idx]
    else:
        module_id = get_current_module()
    
    quiz = generate_quiz(module_id)
    print(quiz)
    
    # Save to file
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    output_file = f"{OUTPUT_DIR}/quiz_module{module_id}.md"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(quiz)
    
    return quiz


if __name__ == "__main__":
    day = int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[1] == "--day" else None
    run_quiz_check(day)
