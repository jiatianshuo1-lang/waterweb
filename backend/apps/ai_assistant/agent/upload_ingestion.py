"""面向 HTTP 上传的安全知识库导入服务。"""

from __future__ import annotations

import shutil
import uuid
import zipfile
from pathlib import Path
from typing import List, Optional

from django.conf import settings
from django.db import transaction
from django.utils.text import get_valid_filename

from apps.ai_assistant.models import AiKnowledgeChunk, AiKnowledgeDocument
from .ingestion import checksum, chunk_markdown, read_document

ALLOWED_SUFFIXES = {".pdf", ".png", ".jpg", ".jpeg", ".md", ".txt", ".docx", ".pptx", ".xlsx"}
MAX_UPLOAD_BYTES = 50 * 1024 * 1024
MAX_ZIP_FILES = 15
MAX_ZIP_UNCOMPRESSED_BYTES = 250 * 1024 * 1024


class UploadIngestionError(ValueError):
    pass


def ingest_uploaded_file(upload, *, user, title: str = "", region=None, is_public: bool = True) -> List[AiKnowledgeDocument]:
    """保存上传原件，并同步解析为可检索分块；ZIP 内每个支持文件成为一个资料。"""
    if upload.size > MAX_UPLOAD_BYTES:
        raise UploadIngestionError("文件不能超过 50 MB")
    suffix = Path(upload.name).suffix.lower()
    if suffix not in ALLOWED_SUFFIXES | {".zip"}:
        raise UploadIngestionError("仅支持 PDF、图片、MD、TXT、DOCX、PPTX、XLSX 或 ZIP")

    upload_dir = Path(settings.MEDIA_ROOT) / "knowledge_uploads" / uuid.uuid4().hex
    upload_dir.mkdir(parents=True, exist_ok=True)
    saved_path = upload_dir / get_valid_filename(Path(upload.name).name)
    with saved_path.open("wb") as destination:
        for block in upload.chunks():
            destination.write(block)

    try:
        sources = _extract_zip(saved_path, upload_dir) if suffix == ".zip" else [saved_path]
        if not sources:
            raise UploadIngestionError("压缩包内没有可导入的文档")
        documents = []
        for index, source in enumerate(sources):
            document_title = title.strip() if len(sources) == 1 and title.strip() else source.stem
            if title.strip() and len(sources) > 1:
                document_title = f"{title.strip()} - {source.stem}"
            documents.append(_ingest_one(source, document_title, user, region, is_public))
        return documents
    except Exception:
        # 失败资料保留在独立目录，便于管理员排障；不留下半成品数据库记录。
        raise


def _extract_zip(zip_path: Path, upload_dir: Path) -> List[Path]:
    try:
        with zipfile.ZipFile(zip_path) as archive:
            members = [item for item in archive.infolist() if not item.is_dir()]
            if len(members) > MAX_ZIP_FILES:
                raise UploadIngestionError(f"压缩包最多包含 {MAX_ZIP_FILES} 个文件")
            if sum(item.file_size for item in members) > MAX_ZIP_UNCOMPRESSED_BYTES:
                raise UploadIngestionError("压缩包解压后不能超过 250 MB")
            target = upload_dir / "extracted"
            target.mkdir()
            sources = []
            for item in members:
                # 禁止 Zip Slip；仅扁平化保存文件名，避免写出上传目录。
                filename = get_valid_filename(Path(item.filename).name)
                suffix = Path(filename).suffix.lower()
                if not filename or suffix not in ALLOWED_SUFFIXES:
                    continue
                destination = target / filename
                if destination.exists():
                    destination = target / f"{uuid.uuid4().hex[:8]}_{filename}"
                with archive.open(item) as source, destination.open("wb") as output:
                    shutil.copyfileobj(source, output)
                sources.append(destination)
            return sources
    except zipfile.BadZipFile as exc:
        raise UploadIngestionError("上传的 ZIP 文件损坏或格式不正确") from exc


def _ingest_one(source: Path, title: str, user, region, is_public: bool) -> AiKnowledgeDocument:
    digest = checksum(source)
    existing = AiKnowledgeDocument.objects.filter(checksum=digest, status="ready").first()
    if existing:
        return existing
    document = AiKnowledgeDocument.objects.create(
        title=title[:200], source_path=str(source), source_type=source.suffix.lstrip(".").lower(),
        checksum=digest, status="pending", region=region, is_public=is_public, created_by=user, updated_by=user,
    )
    try:
        markdown, parser_name, metadata = read_document(source)
        chunks = list(chunk_markdown(markdown))
        if not chunks:
            raise UploadIngestionError("未从文档中提取到可检索文字")
        with transaction.atomic():
            document.parser = parser_name
            document.metadata = {**metadata, "original_name": source.name, "chunk_count": len(chunks)}
            document.status = "ready"
            document.error_message = ""
            document.save(update_fields=["parser", "metadata", "status", "error_message", "updated_at"])
            AiKnowledgeChunk.objects.bulk_create([
                AiKnowledgeChunk(document=document, content=text, ordinal=ordinal, page_start=page, page_end=page,
                                 token_estimate=max(1, len(text) // 4), keywords=keywords, created_by=user, updated_by=user)
                for text, ordinal, page, keywords in chunks
            ])
        return document
    except Exception as exc:
        document.status = "failed"
        document.error_message = str(exc)[:5_000]
        document.save(update_fields=["status", "error_message", "updated_at"])
        raise UploadIngestionError(f"《{title}》导入失败：{exc}") from exc
