from django.contrib import admin
from .models import (AiAssistantConfig, AiChatSession, AiChatMessage, AiKnowledge,
                     AiKnowledgeDocument, AiKnowledgeChunk, AiToolLog)


@admin.register(AiAssistantConfig)
class AiAssistantConfigAdmin(admin.ModelAdmin):
    list_display = ["name", "provider", "model_name", "is_active", "created_at"]
    list_filter = ["provider", "is_active"]
    search_fields = ["name", "model_name"]


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


@admin.register(AiKnowledge)
class AiKnowledgeAdmin(admin.ModelAdmin):
    list_display = ["title", "knowledge_type", "region", "is_public", "created_at"]
    list_filter = ["knowledge_type", "is_public"]
    search_fields = ["title", "content"]


@admin.register(AiKnowledgeDocument)
class AiKnowledgeDocumentAdmin(admin.ModelAdmin):
    list_display = ["title", "source_type", "parser", "status", "created_at"]
    list_filter = ["status", "parser", "source_type", "is_public"]
    search_fields = ["title", "source_path", "checksum"]


@admin.register(AiKnowledgeChunk)
class AiKnowledgeChunkAdmin(admin.ModelAdmin):
    list_display = ["document", "ordinal", "page_start", "token_estimate", "created_at"]
    search_fields = ["content"]


@admin.register(AiToolLog)
class AiToolLogAdmin(admin.ModelAdmin):
    list_display = ["tool_name", "user", "success", "summary_short", "is_simulated", "created_at"]
    list_filter = ["tool_name", "success", "is_simulated"]
    search_fields = ["tool_name", "summary"]

    @admin.display(description="摘要")
    def summary_short(self, obj):
        return obj.summary[:50] + ("..." if len(obj.summary) > 50 else "")
