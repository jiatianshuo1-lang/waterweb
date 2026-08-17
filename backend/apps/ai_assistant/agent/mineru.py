"""MinerU 自托管 API 适配器。服务不可用时明确失败，绝不静默伪造 OCR 文本。"""

from __future__ import annotations

import mimetypes
import os
from pathlib import Path
from typing import Dict

import requests


class MinerUError(RuntimeError):
    pass


def parse_file(path: str, timeout: int = 1_800) -> Dict:
    api_url = os.environ.get("MINERU_API_URL", "").rstrip("/")
    if not api_url:
        raise MinerUError("未配置 MINERU_API_URL；请部署 mineru-api 后再导入扫描件")
    source = Path(path)
    if not source.is_file():
        raise MinerUError(f"文件不存在：{source}")
    with source.open("rb") as handle:
        response = requests.post(
            f"{api_url}/file_parse",
            files={"files": (source.name, handle, mimetypes.guess_type(source.name)[0] or "application/octet-stream")},
            data={"lang_list": "ch", "parse_method": "auto", "return_md": "true", "return_content_list": "true"},
            timeout=timeout,
        )
    try:
        response.raise_for_status()
    except requests.RequestException as exc:
        raise MinerUError(f"MinerU 解析失败：{exc}") from exc
    payload = response.json()
    markdown = _extract_markdown(payload)
    if not markdown.strip():
        raise MinerUError("MinerU 未返回 Markdown 内容；请核对其 /docs 中的 API 版本与响应格式")
    return {"markdown": markdown, "raw": payload}


def _extract_markdown(payload: Dict) -> str:
    """兼容常见 MinerU 同步 API 响应；具体原始响应保存在 metadata 便于排障。"""
    for key in ("markdown", "md_content", "md"):
        if isinstance(payload.get(key), str):
            return payload[key]
    for item in payload.get("results", []) if isinstance(payload.get("results"), list) else []:
        for key in ("markdown", "md_content", "md"):
            if isinstance(item.get(key), str):
                return item[key]
    return ""
