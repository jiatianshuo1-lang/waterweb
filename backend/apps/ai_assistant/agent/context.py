"""上下文工程：预算控制、长期记忆和可追溯 RAG 上下文。"""

from __future__ import annotations

from typing import Dict, List, Tuple


MAX_HISTORY_CHARS = 12_000


def _clip(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "…"


def build_context(history: List[Dict], memory_summary: str, max_turns: int) -> Tuple[List[Dict], str]:
    """保留最近完整对话；更早信息只从受控长期记忆注入，避免上下文无限增长。"""
    recent = history[-max(2, max_turns * 2):]
    selected: List[Dict] = []
    remaining = MAX_HISTORY_CHARS
    for message in reversed(recent):
        content = _clip(message.get("content", ""), min(4_000, remaining))
        if not content:
            continue
        selected.append({"role": message["role"], "content": content})
        remaining -= len(content)
        if remaining <= 0:
            break
    selected.reverse()
    memory = _clip(memory_summary or "", 2_000)
    return selected, memory


def build_memory_summary(previous: str, history: List[Dict]) -> str:
    """不调用模型的安全压缩：仅保留用户明确陈述的偏好、区域、设备和待办。"""
    candidates = [m.get("content", "").strip() for m in history if m.get("role") == "user"]
    facts = [x for x in candidates if 4 <= len(x) <= 240][-8:]
    merged = [line for line in (previous or "").splitlines() if line.startswith("- ")]
    for fact in facts:
        line = f"- 用户已提及：{fact}"
        if line not in merged:
            merged.append(line)
    return "\n".join(merged[-12:])[:2_000]
