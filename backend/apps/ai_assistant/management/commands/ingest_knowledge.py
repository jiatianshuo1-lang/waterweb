from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.ai_assistant.agent.ingestion import checksum, chunk_markdown, read_document
from apps.ai_assistant.models import AiKnowledgeChunk, AiKnowledgeDocument


class Command(BaseCommand):
    help = "导入知识库资料；扫描型 PDF/图片通过 MINERU_API_URL 指向的 MinerU 服务解析。"

    def add_arguments(self, parser):
        parser.add_argument("path")
        parser.add_argument("--title")
        parser.add_argument("--replace", action="store_true")
        parser.add_argument("--private", action="store_true")

    def handle(self, *args, **options):
        path = Path(options["path"]).resolve()
        if not path.is_file():
            raise CommandError(f"找不到文件：{path}")
        digest = checksum(path)
        existing = AiKnowledgeDocument.objects.filter(checksum=digest).first()
        if existing and not options["replace"]:
            self.stdout.write(self.style.WARNING(f"资料已导入：{existing.title}；使用 --replace 可重建分块"))
            return
        document = existing or AiKnowledgeDocument(title=options["title"] or path.stem, source_path=str(path), source_type=path.suffix.lstrip("."), checksum=digest)
        document.status = "pending"
        document.save()
        try:
            markdown, parser_name, metadata = read_document(path)
            chunks = list(chunk_markdown(markdown))
            if not chunks:
                raise ValueError("解析后未获得可用文本")
            with transaction.atomic():
                document.title = options["title"] or document.title
                document.parser = parser_name
                document.metadata = metadata
                document.is_public = not options["private"]
                document.status = "ready"
                document.error_message = ""
                document.save()
                document.chunks.all().delete()
                AiKnowledgeChunk.objects.bulk_create([
                    AiKnowledgeChunk(document=document, content=text, ordinal=ordinal, page_start=page, page_end=page,
                                     token_estimate=max(1, len(text) // 4), keywords=keywords)
                    for text, ordinal, page, keywords in chunks
                ])
            self.stdout.write(self.style.SUCCESS(f"已导入 {document.title}：{len(chunks)} 个分块，解析器={parser_name}"))
        except Exception as exc:
            document.status = "failed"
            document.error_message = str(exc)
            document.save(update_fields=["status", "error_message", "updated_at"])
            raise CommandError(str(exc)) from exc
