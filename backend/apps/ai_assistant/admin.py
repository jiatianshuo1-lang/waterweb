from django.contrib import admin, messages
from django.contrib.auth import get_user_model
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
from django.utils.html import format_html

from .models import (AiAssistantConfig, AiChatSession, AiChatMessage,
                     AiKnowledgeDocument, AiToolLog)
from .agent.upload_ingestion import UploadIngestionError, ingest_uploaded_file


# ---------------------------------------------------------------------------
# AI 配置 / 会话 / 消息 / 工具日志（保持原样）
# ---------------------------------------------------------------------------

@admin.register(AiAssistantConfig)
class AiAssistantConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "model_name", "is_active", "created_at"]
    list_filter = ["provider", "is_active"]
    search_fields = ["name", "model_name"]
    fieldsets = [
        (None, {"fields": ["name", "provider", "model_name", "api_url", "api_key"]}),
        ("高级参数", {"fields": ["system_prompt", "temperature", "max_tokens",
                                 "max_history", "timeout"], "classes": ["collapse"]}),
        ("状态", {"fields": ["is_active", "description"]}),
    ]


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    list_display = ["session_id", "user", "title", "config", "is_active", "last_message_time"]
    search_fields = ["session_id", "title", "user__username"]


@admin.register(AiChatMessage)
class AiChatMessageAdmin(admin.ModelAdmin):
    list_display = ["session", "role", "content_short", "token_count", "response_time", "created_at"]
    list_filter = ["role"]
    search_fields = ["content"]

    @admin.display(description="内容")
    def content_short(self, obj):
        return obj.content[:60] + ("..." if len(obj.content) > 60 else "")


@admin.register(AiToolLog)
class AiToolLogAdmin(admin.ModelAdmin):
    list_display = ["tool_name", "user", "success", "summary_short", "is_simulated", "created_at"]
    list_filter = ["tool_name", "success", "is_simulated"]
    search_fields = ["tool_name", "summary"]

    @admin.display(description="摘要")
    def summary_short(self, obj):
        return obj.summary[:50] + ("..." if len(obj.summary) > 50 else "")


# ---------------------------------------------------------------------------
# AiKnowledgeDocument — 文件上传入口 + 批量导入 + 压缩包
# ---------------------------------------------------------------------------

@admin.register(AiKnowledgeDocument)
class AiKnowledgeDocumentAdmin(admin.ModelAdmin):
    change_list_template = "admin/ai_assistant/aiknowledgedocument/change_list.html"

    list_display = ["title", "source_type", "parser", "status_col", "chunk_count",
                    "is_public", "created_by", "created_at", "reparse_action"]
    list_filter = ["status", "source_type", "parser", "is_public"]
    search_fields = ["title", "source_path", "checksum"]
    list_per_page = 20
    actions = ["reparse_selected", "mark_public", "mark_private", "delete_selected_chunks"]

    @admin.display(description="状态", boolean=False)
    def status_col(self, obj):
        color_map = {"ready": "green", "pending": "orange", "failed": "red"}
        return format_html(
            '<span style="color:{};font-weight:600">{}</span>',
            color_map.get(obj.status, "#888"),
            obj.get_status_display(),
        )

    @admin.display(description="分块数")
    def chunk_count(self, obj):
        return obj.chunks.count()

    @admin.display(description="操作")
    def reparse_action(self, obj):
        url = reverse("admin:ai_assistant_aiknowledgedocument_reparse", args=[obj.pk])
        return format_html(
            '<a href="{}">重新解析</a>', url
        )

    # ------ 自定义 action ------
    @admin.action(description="重新解析选中文档")
    def reparse_selected(self, request, queryset):
        from .agent.upload_ingestion import _ingest_text_into_chunks, _parse_one, UploadIngestionError
        updated, failed = 0, 0
        for doc in queryset:
            if not doc.file:
                messages.warning(request, f"{doc.title} 没有关联源文件，无法重新解析")
                continue
            try:
                doc.file.seek(0)
                raw = doc.file.read()
                text, meta = _parse_one(doc.file.name, raw)
                _ingest_text_into_chunks(doc, text)
                updated += 1
            except Exception as exc:
                doc.status = "failed"
                doc.error_message = str(exc)
                doc.save()
                failed += 1
        messages.success(request, f"重新解析完成：成功 {updated}，失败 {failed}")

    @admin.action(description="设为公开")
    def mark_public(self, request, queryset):
        queryset.update(is_public=True)

    @admin.action(description="设为私有")
    def mark_private(self, request, queryset):
        queryset.update(is_public=False)

    @admin.action(description="清空分块但保留文档")
    def delete_selected_chunks(self, request, queryset):
        total = 0
        for doc in queryset:
            n = doc.chunks.count()
            doc.chunks.all().delete()
            doc.status = "pending"
            doc.save()
            total += n
        messages.success(request, f"已清空 {total} 个分块（{queryset.count()} 个文档）")

    # ------ 自定义 URL / 视图 ------
    def get_urls(self):
        urls = super().get_urls()
        custom = [
            path("upload/", self.admin_site.admin_view(self.upload_view),
                 name="ai_assistant_aiknowledgedocument_upload"),
            path("upload-batch/", self.admin_site.admin_view(self.upload_batch_view),
                 name="ai_assistant_aiknowledgedocument_upload_batch"),
            path("<int:pk>/reparse/", self.admin_site.admin_view(self.reparse_view),
                 name="ai_assistant_aiknowledgedocument_reparse"),
        ]
        return custom + urls

    def changelist_view(self, request, extra_context=None):
        extra = extra_context or {}
        extra["upload_url"] = reverse("admin:ai_assistant_aiknowledgedocument_upload")
        extra["upload_batch_url"] = reverse("admin:ai_assistant_aiknowledgedocument_upload_batch")
        return super().changelist_view(request, extra_context=extra)

    def upload_view(self, request):
        """单文件上传：最简单，用户只选文件，其他自动填"""
        if request.method == "POST":
            files = request.FILES.getlist("file")
            if not files:
                messages.error(request, "请选择要上传的文件")
                return HttpResponseRedirect(
                    reverse("admin:ai_assistant_aiknowledgedocument_upload"))
            created, skipped, failed = 0, 0, 0
            for f in files:
                try:
                    docs = ingest_uploaded_file(f, user=request.user, is_public=True)
                    created += len(docs)
                except UploadIngestionError as exc:
                    failed += 1
                    messages.error(request, f"{f.name}: {exc}")
            if created:
                messages.success(request, f"成功导入 {created} 个文档")
            if skipped:
                messages.info(request, f"跳过 {skipped} 个重复文档")
            return HttpResponseRedirect(
                reverse("admin:ai_assistant_aiknowledgedocument_changelist"))

        ctx = dict(self.admin_site.each_context(request))
        ctx.update({
            "title": "上传文档（单文件 / 压缩包）",
            "opts": self.model._meta,
            "help_texts": [
                "支持 .txt / .md / .csv / .json / .xml / .yaml / .html / .pdf / .docx",
                "也支持直接上传 .zip / .tar.gz / .tgz / .tar 批量导入",
                "无需填写其他字段，标题自动从文件名生成",
            ],
        })
        return render(request, "admin/ai_assistant/aiknowledgedocument/upload.html", ctx)

    def upload_batch_view(self, request):
        """批量上传（一次选多个文件）"""
        return self.upload_view(request)  # 同一个处理函数，模板上只是说明不同

    def reparse_view(self, request, pk):
        doc = AiKnowledgeDocument.objects.filter(pk=pk).first()
        if not doc:
            messages.error(request, "文档不存在")
        else:
            from .agent.upload_ingestion import _ingest_text_into_chunks, _parse_one
            if not doc.file:
                messages.warning(request, f"{doc.title} 没有关联源文件，无法重新解析")
            else:
                try:
                    doc.file.seek(0)
                    raw = doc.file.read()
                    text, _ = _parse_one(doc.file.name, raw)
                    n = _ingest_text_into_chunks(doc, text)
                    messages.success(request, f"重新解析完成：{n} 个分块")
                except Exception as exc:
                    doc.status = "failed"
                    doc.error_message = str(exc)
                    doc.save()
                    messages.error(request, f"解析失败：{exc}")
        return HttpResponseRedirect(
            reverse("admin:ai_assistant_aiknowledgedocument_changelist"))



