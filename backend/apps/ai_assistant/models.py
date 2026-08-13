from django.db import models
from apps.common.models import BaseModel


class AiAssistantConfig(BaseModel):
    PROVIDERS = [
        ('local', '本地模型'),
        ('openai', 'OpenAI'),
        ('azure', 'Azure OpenAI'),
        ('qwen', '阿里云百炼'),
        ('doubao', '豆包'),
        ('deepseek', 'DeepSeek'),
        ('ollama', 'Ollama'),
    ]

    name = models.CharField(max_length=100, verbose_name='配置名称')
    provider = models.CharField(max_length=20, choices=PROVIDERS, default='local', verbose_name='服务商')
    model_name = models.CharField(max_length=100, verbose_name='模型名称')
    api_url = models.CharField(max_length=500, blank=True, verbose_name='API地址')
    api_key = models.CharField(max_length=500, blank=True, verbose_name='API密钥')
    system_prompt = models.TextField(blank=True, verbose_name='系统提示词')
    temperature = models.FloatField(default=0.7, verbose_name='温度(0-1)')
    max_tokens = models.IntegerField(default=2048, verbose_name='最大Token数')
    max_history = models.IntegerField(default=10, verbose_name='最大历史对话数')
    timeout = models.IntegerField(default=30, verbose_name='超时时间(秒)')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    description = models.CharField(max_length=255, blank=True, verbose_name='描述')

    class Meta:
        verbose_name = 'AI助手配置'
        verbose_name_plural = 'AI助手配置管理'
        ordering = ['-created_at']


class AiChatSession(BaseModel):
    session_id = models.CharField(max_length=100, unique=True, verbose_name='会话ID')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='ai_sessions', verbose_name='用户')
    title = models.CharField(max_length=200, blank=True, verbose_name='会话标题')
    config = models.ForeignKey(AiAssistantConfig, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='使用的配置')
    is_active = models.BooleanField(default=True, verbose_name='是否活跃')
    last_message_time = models.DateTimeField(null=True, blank=True, verbose_name='最后消息时间')

    class Meta:
        verbose_name = 'AI会话'
        verbose_name_plural = 'AI会话管理'
        ordering = ['-last_message_time']


class AiChatMessage(BaseModel):
    ROLES = [
        ('system', '系统'),
        ('user', '用户'),
        ('assistant', 'AI助手'),
    ]

    session = models.ForeignKey(AiChatSession, on_delete=models.CASCADE, related_name='messages', verbose_name='会话')
    role = models.CharField(max_length=20, choices=ROLES, verbose_name='角色')
    content = models.TextField(verbose_name='内容')
    token_count = models.IntegerField(default=0, verbose_name='Token数量')
    response_time = models.FloatField(null=True, blank=True, verbose_name='响应时间(秒)')
    source_documents = models.JSONField(default=list, verbose_name='引用文档')
    is_streamed = models.BooleanField(default=False, verbose_name='是否流式输出')

    class Meta:
        verbose_name = 'AI对话消息'
        verbose_name_plural = 'AI对话消息'
        ordering = ['created_at']


class AiKnowledge(BaseModel):
    KNOWLEDGE_TYPES = [
        ('document', '文档'),
        ('qa', '问答对'),
        ('faq', '常见问题'),
        ('procedure', '操作流程'),
        ('policy', '政策制度'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES, default='document', verbose_name='知识类型')
    content = models.TextField(verbose_name='内容')
    summary = models.CharField(max_length=500, blank=True, verbose_name='摘要')
    tags = models.JSONField(default=list, verbose_name='标签')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联区域')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    embedding = models.JSONField(null=True, blank=True, verbose_name='向量嵌入')

    class Meta:
        verbose_name = '知识库'
        verbose_name_plural = '知识库管理'
        ordering = ['-created_at']
