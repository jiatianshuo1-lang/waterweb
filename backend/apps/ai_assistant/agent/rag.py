"""
RAG 知识库检索

采用：jieba 中文分词 + 倒排索引（SQL LIKE）+ 可选向量召回（embedding 字段已预留）
目前走 keyword 路径，后续可接入 sentence-transformers 或阿里 DashScope embedding。
"""

import logging
import re
from typing import List, Dict

logger = logging.getLogger("apps.ai_assistant")

# jieba 可选
try:
    import jieba

    JIEBA_AVAILABLE = True
except ImportError:
    JIEBA_AVAILABLE = False


def _ngram_split(text: str, n: int = 2) -> List[str]:
    """中文 n-gram 兜底：把连续中文字符串切成 2-gram"""
    tokens = []
    buf = ""
    for ch in text:
        if "\u4e00" <= ch <= "\u9fff":
            buf += ch
        else:
            if len(buf) >= 2:
                for i in range(len(buf) - n + 1):
                    tokens.append(buf[i : i + n])
            buf = ""
    if len(buf) >= 2:
        for i in range(len(buf) - n + 1):
            tokens.append(buf[i : i + n])
    return tokens


def _tokenize(text: str) -> List[str]:
    """中文分词：优先 jieba，否则 2-gram 兜底"""
    text = re.sub(r"[？?。，,.！!、;；:：""''（）()\[\]【】]", " ", text)
    if JIEBA_AVAILABLE:
        tokens = [w.strip() for w in jieba.cut(text) if len(w.strip()) > 1]
        if tokens:
            return tokens
    # 2-gram 兜底
    tokens = _ngram_split(text, n=2)
    if not tokens:
        tokens = [w for w in text.split() if len(w) > 1]
    return tokens


def retrieve_knowledge(query: str, top_k: int = 4, region=None) -> List[Dict]:
    """
    根据 query 从 AiKnowledge 表中检索 top_k 条最相关文档。

    评分规则：
    - title 命中 +3
    - tags 命中 +2
    - content 命中 +1（每个关键词）
    - is_public=True 的文档优先
    """
    from django.db.models import Q
    from apps.ai_assistant.models import AiKnowledge, AiKnowledgeChunk

    tokens = _tokenize(query)
    if not tokens:
        return []

    # 优先检索已完成解析的分块资料。旧 AiKnowledge 仍保留为兼容回退。
    chunk_q = AiKnowledgeChunk.objects.select_related("document").filter(document__status="ready")
    if region:
        chunk_q = chunk_q.filter(Q(document__is_public=True) | Q(document__region=region))
    else:
        chunk_q = chunk_q.filter(document__is_public=True)
    chunk_expr = Q()
    for token in tokens:
        chunk_expr |= Q(content__icontains=token) | Q(keywords__icontains=token) | Q(document__title__icontains=token)
    chunks = list(chunk_q.filter(chunk_expr)[:top_k * 6])
    chunk_scored = []
    for chunk in chunks:
        text = chunk.content or ""
        score = sum(3 for t in tokens if t in (chunk.document.title or ""))
        score += sum(2 for t in tokens if t in (chunk.keywords or []))
        score += sum(1 for t in tokens if t in text)
        chunk_scored.append((score, chunk))
    chunk_scored.sort(key=lambda item: (-item[0], item[1].document_id, item[1].ordinal))
    if chunk_scored:
        results = []
        for score, chunk in chunk_scored[:top_k]:
            page = f"第{chunk.page_start}页" if chunk.page_start else "页码未知"
            if chunk.page_end and chunk.page_end != chunk.page_start:
                page = f"第{chunk.page_start}-{chunk.page_end}页"
            results.append({
                "id": f"chunk:{chunk.id}", "title": chunk.document.title, "type": "document",
                "summary": "", "content": chunk.content[:1_200], "tags": chunk.keywords,
                "score": score, "citation": page, "document_id": chunk.document_id,
            })
        logger.info("[RAG] query=%r source=chunks hits=%d", query, len(results))
        return results

    q = AiKnowledge.objects.all()
    # 区域过滤（如果有）
    if region:
        q = q.filter(Q(is_public=True) | Q(region=region))
    else:
        q = q.filter(is_public=True)

    # 构建 OR 查询
    q_expr = Q()
    for t in tokens:
        q_expr |= Q(title__icontains=t) | Q(content__icontains=t) | Q(tags__icontains=t)

    candidates = list(q.filter(q_expr)[:top_k * 3])  # 多拉一些用于重排

    # 打分重排
    scored = []
    for doc in candidates:
        score = 0
        for t in tokens:
            if t in (doc.title or ""):
                score += 3
            if t in (doc.tags or ""):
                score += 2
            if t in (doc.content or ""):
                score += 1
        if doc.is_public:
            score += 1
        scored.append((score, doc))

    scored.sort(key=lambda x: -x[0])

    results = []
    for score, doc in scored[:top_k]:
        results.append(
            {
                "id": doc.id,
                "title": doc.title,
                "type": doc.knowledge_type,
                "summary": doc.summary or "",
                "content": doc.content[:500],
                "tags": doc.tags or [],
                "score": score,
                "citation": "旧知识条目",
            }
        )
    logger.info("[RAG] query=%r tokens=%r hits=%d", query, tokens, len(results))
    return results
