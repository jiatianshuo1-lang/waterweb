from django.contrib import admin
from .models import AiAssistantConfig, AiChatSession, AiChatMessage, AiKnowledge


@admin.register(AiAssistantConfig)
class AiAssistantConfigAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider', 'model_name', 'is_active', 'created_at']
    list_filter = ['provider', 'is_active']
    search_fields = ['name', 'model_name']


@admin.register(AiChatSession)
class AiChatSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'user', 'title', 'config', 'is_active', 'last_message_time']
    search_fields = ['session_id', 'title', 'user__username']


@admin.register(AiChatMessage)
class AiChatMessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content', 'token_count', 'response_time', 'created_at']
    list_filter = ['role']


@admin.register(AiKnowledge)
class AiKnowledgeAdmin(admin.ModelAdmin):
    list_display = ['title', 'knowledge_type', 'region', 'is_public', 'created_at']
    list_filter = ['knowledge_type', 'is_public']
    search_fields = ['title', 'content']
