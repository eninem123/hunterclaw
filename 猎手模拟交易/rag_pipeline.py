#!/usr/bin/env python3
"""
RAG管线 - 研报/财报检索增强生成
ChromaDB + sentence-transformers + MiMo API
"""

import os
import json
import sqlite3
from datetime import datetime
from typing import List, Dict, Optional

# 向量库
import chromadb
from chromadb.config import Settings

# Embedding
from sentence_transformers import SentenceTransformer

# LLM
import requests

CHROMA_PATH = "/opt/agent_state/chromadb"
EMBED_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"  # 中文友好，384维，快
MIMO_API = "https://token-plan-cn.xiaomimimo.com/v1/chat/completions"
MIMO_KEY = "tp-czmhb86n2j7nlx1b717du0e76khpm558ntajjl2158j2u084"

DB_PATH = "/opt/agent_state/agent.db"


class RAGPipeline:
    def __init__(self):
        # 初始化ChromaDB
        self.client = chromadb.PersistentClient(path=CHROMA_PATH)
        self.embedder = SentenceTransformer(EMBED_MODEL)
        self.collection = None

    def get_or_create_collection(self, name: str = "research_docs"):
        """获取或创建集合"""
        self.collection = self.client.get_or_create_collection(
            name=name,
            metadata={"hnsw:space": "cosine"}
        )
        return self.collection

    def chunk_document(self, text: str, doc_type: str = "research",
                       chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
        """
        文档分块策略
        - 研报: 按段落拆分，保留标题层级
        - 财报: 按科目拆分，保留表格结构
        """
        chunks = []

        if doc_type == "financial_report":
            # 财报按科目拆分（找到"XX科目"或"XX项目"开头的段落）
            sections = text.split('\n\n')
            for i, section in enumerate(sections):
                if len(section.strip()) < 20:
                    continue
                chunks.append({
                    "text": section.strip(),
                    "chunk_index": i,
                    "doc_type": doc_type,
                    "char_count": len(section.strip())
                })
        else:
            # 研报按段落+overlap拆分
            words = text
            start = 0
            idx = 0
            while start < len(words):
                end = start + chunk_size
                chunk_text = words[start:end].strip()
                if len(chunk_text) < 20:
                    start = end - overlap
                    continue
                chunks.append({
                    "text": chunk_text,
                    "chunk_index": idx,
                    "doc_type": doc_type,
                    "char_count": len(chunk_text)
                })
                start = end - overlap
                idx += 1

        return chunks

    def index_document(self, doc_id: str, text: str, metadata: Dict,
                       doc_type: str = "research"):
        """索引文档到ChromaDB"""
        if self.collection is None:
            self.get_or_create_collection()

        chunks = self.chunk_document(text, doc_type)

        if not chunks:
            return 0

        # 生成embedding
        texts = [c["text"] for c in chunks]
        embeddings = self.embedder.encode(texts, show_progress_bar=False).tolist()

        # 生成ID
        ids = [f"{doc_id}_chunk_{c['chunk_index']}" for c in chunks]

        # 元数据
        metas = []
        for c in chunks:
            m = dict(metadata)
            m["chunk_index"] = c["chunk_index"]
            m["doc_type"] = c["doc_type"]
            m["char_count"] = c["char_count"]
            metas.append(m)

        # 写入ChromaDB
        self.collection.upsert(
            ids=ids,
            embeddings=embeddings,
            documents=texts,
            metadatas=metas
        )

        return len(chunks)

    def retrieve(self, query: str, top_k: int = 5,
                 doc_type: Optional[str] = None) -> List[Dict]:
        """检索相关文档"""
        if self.collection is None:
            self.get_or_create_collection()

        query_embedding = self.embedder.encode([query], show_progress_bar=False).tolist()

        where_filter = {}
        if doc_type:
            where_filter["doc_type"] = doc_type

        results = self.collection.query(
            query_embeddings=query_embedding,
            n_results=top_k,
            where=where_filter if where_filter else None,
            include=["documents", "metadatas", "distances"]
        )

        retrieved = []
        for i in range(len(results["ids"][0])):
            retrieved.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i]
            })

        return retrieved

    def generate_answer(self, query: str, context_docs: List[Dict]) -> str:
        """用MiMo生成RAG回答"""
        context_text = "\n\n---\n\n".join([
            f"[来源: {d['metadata'].get('title', '未知')} | {d['metadata'].get('date', '')}]\n{d['text']}"
            for d in context_docs
        ])

        prompt = f"""你是一个专业的A股投研分析师。请基于以下参考资料回答问题。
如果参考资料不足以回答，请明确说明"资料不足"。
回答时必须引用来源，格式：[来源:标题]

参考资料：
{context_text}

问题：{query}

请给出专业、有据可查的分析回答："""

        try:
            resp = requests.post(
                MIMO_API,
                headers={
                    "Authorization": f"Bearer {MIMO_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "mimo-v2.5",
                    "messages": [{"role": "user", "content": prompt}],
                    "temperature": 0.3,
                    "max_tokens": 2000
                },
                timeout=60
            )
            if resp.status_code == 200:
                return resp.json()["choices"][0]["message"]["content"]
            else:
                return f"LLM调用失败: {resp.status_code}"
        except Exception as e:
            return f"LLM调用异常: {e}"

    def query(self, question: str, top_k: int = 5,
              doc_type: Optional[str] = None) -> Dict:
        """完整RAG查询: 检索+生成"""
        # 1. 检索
        docs = self.retrieve(question, top_k, doc_type)

        # 2. 生成
        answer = self.generate_answer(question, docs)

        # 3. 记录查询日志
        self._log_query(question, len(docs), answer[:100])

        return {
            "question": question,
            "answer": answer,
            "sources": [
                {
                    "title": d["metadata"].get("title", "未知"),
                    "date": d["metadata"].get("date", ""),
                    "distance": round(d["distance"], 4),
                    "snippet": d["text"][:200]
                }
                for d in docs
            ],
            "source_count": len(docs),
            "timestamp": datetime.now().isoformat()
        }

    def _log_query(self, question: str, doc_count: int, answer_preview: str):
        """记录查询到SQLite"""
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO decisions (agent, decision, reasoning)
                VALUES (?, ?, ?)
            """, ("rag_pipeline", f"RAG查询: {question[:100]}",
                  f"检索{doc_count}篇 | 回答: {answer_preview}"))
            conn.commit()
            conn.close()
        except Exception:
            pass

    def get_stats(self) -> Dict:
        """获取RAG统计"""
        if self.collection is None:
            self.get_or_create_collection()
        count = self.collection.count()
        return {
            "collection": self.collection.name,
            "document_chunks": count,
            "embed_model": EMBED_MODEL,
            "chroma_path": CHROMA_PATH
        }


def index_research_report(filepath: str, title: str, date: str,
                          source: str, doc_type: str = "research"):
    """便捷函数：索引研报文件"""
    rag = RAGPipeline()

    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    metadata = {
        "title": title,
        "date": date,
        "source": source,
        "indexed_at": datetime.now().isoformat()
    }

    chunk_count = rag.index_document(
        doc_id=f"{source}_{date}_{title[:20]}",
        text=text,
        metadata=metadata,
        doc_type=doc_type
    )

    return chunk_count


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("用法:")
        print("  python3 rag_pipeline.py stats              # 查看统计")
        print("  python3 rag_pipeline.py query '问题'        # RAG查询")
        print("  python3 rag_pipeline.py index 文件路径 标题 日期 来源 [类型]")
        sys.exit(0)

    cmd = sys.argv[1]
    rag = RAGPipeline()

    if cmd == "stats":
        print(json.dumps(rag.get_stats(), ensure_ascii=False, indent=2))

    elif cmd == "query":
        question = sys.argv[2] if len(sys.argv) > 2 else "国电电力Q1净利润下降原因"
        result = rag.query(question)
        print(json.dumps(result, ensure_ascii=False, indent=2))

    elif cmd == "index":
        filepath = sys.argv[2]
        title = sys.argv[3] if len(sys.argv) > 3 else "未命名"
        date = sys.argv[4] if len(sys.argv) > 4 else datetime.now().strftime("%Y-%m-%d")
        source = sys.argv[5] if len(sys.argv) > 5 else "manual"
        doc_type = sys.argv[6] if len(sys.argv) > 6 else "research"
        count = index_research_report(filepath, title, date, source, doc_type)
        print(f"索引完成: {count}个chunk")
