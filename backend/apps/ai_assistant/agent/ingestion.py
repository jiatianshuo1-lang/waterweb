"""知识库导入：文本/PDF 统一转换为带页码的、可引用的 RAG 分块。"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path
from typing import Iterable, List, Tuple

from .rag import _tokenize


def checksum(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_document(path: Path) -> Tuple[str, str, dict]:
    suffix = path.suffix.lower()
    if suffix in {".pdf", ".png", ".jpg", ".jpeg"}:
        from .mineru import parse_file
        parsed = parse_file(str(path))
        return parsed["markdown"], "mineru", {"source_suffix": suffix}
    if suffix in {".md", ".txt"}:
        return path.read_text(encoding="utf-8"), "text", {"source_suffix": suffix}
    raise ValueError(f"不支持的资料类型：{suffix}；支持 PDF/图片/MD/TXT")


def chunk_markdown(markdown: str, target_chars: int = 1_000, overlap_chars: int = 150) -> Iterable[Tuple[str, int, int, List[str]]]:
    """按标题/段落切分，带少量重叠，避免句子和表格行被硬截断。"""
    blocks = [part.strip() for part in re.split(r"\n\s*\n", markdown) if part.strip()]
    current: List[str] = []
    size = 0
    ordinal = 0
    for block in blocks:
        if current and size + len(block) + 2 > target_chars:
            text = "\n\n".join(current)
            yield text, ordinal, None, _tokenize(text)[:20]
            ordinal += 1
            tail = text[-overlap_chars:]
            current, size = ([tail] if tail else []), len(tail)
        current.append(block)
        size += len(block) + 2
    if current:
        text = "\n\n".join(current)
        yield text, ordinal, None, _tokenize(text)[:20]
