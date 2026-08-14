from django.db import models
from apps.common.models import BaseModel


class AiAssistantConfig(BaseModel):
    PROVIDERS = [
        ("local", "本地模型"),
        ("openai", "OpenAI"),
        ("azure", "Azure OpenAI"),
        ("qwen", "阿里云百炼"),
        ("doubao", "豆包"),
        ("deepseek", "DeepSeek"),
        ("ollama", "Ollama"),
    ]

    name = models.CharField(max_length=100, verbose_name="配置名称")
    provider = models.CharField(max_length=20, choices=PROVIDERS, default="deepseek", verbose_name="服务商")
    model_name = models.CharField(max_length=100, default="deepseek-chat", verbose_name="模型名称")
    api_url = models.CharField(max_length=500, blank=True, verbose_name="API地址")
    api_key = models.CharField(max_length=500, blank=True, verbose_name="API密钥")
    system_prompt = models.TextField(blank=True, verbose_name="系统提示词")
    temperature = models.FloatField(default=0.7, verbose_name="温度(0-1)")
    max_tokens = models.IntegerField(default=2048, verbose_name="最大Token数")
    max_history = models.IntegerField(default=10, verbose_name="最大历史对话数")
    timeout = models.IntegerField(default=30, verbose_name="超时时间(秒)")
    is_active = models.BooleanField(default=True, verbose_name="是否启用")
    description = models.CharField(max_length=255, blank=True, verbose_name="描述")

    class Meta:
        verbose_name = "AI助手配置"
        verbose_name_plural = "AI助手配置管理"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.get_provider_display()})"


class AiChatSession(BaseModel):
    session_id = models.CharField(max_length=100, unique=True, verbose_name="会话ID")
    user = models.ForeignKey("users.User", on_delete=models.CASCADE, related_name="ai_sessions", verbose_name="用户")
    title = models.CharField(max_length=200, blank=True, verbose_name="会话标题")
    config = models.ForeignKey(AiAssistantConfig, on_delete=models.SET_NULL, null=True, blank=True, verbose_name="使用的配置")
    is_active = models.BooleanField(default=True, verbose_name="是否活跃")
    last_message_time = models.DateTimeField(null=True, blank=True, verbose_name="最后消息时间")
    memory_summary = models.TextField(blank=True, verbose_name="会话长期记忆")
    memory_updated_at = models.DateTimeField(null=True, blank=True, verbose_name="记忆更新时间")

    class Meta:
        verbose_name = "AI会话"
        verbose_name_plural = "AI会话管理"
        ordering = ["-last_message_time"]

    def __str__(self):
        return self.title or self.session_id


class AiChatMessage(BaseModel):
    ROLES = [
        ("system", "系统"),
        ("user", "用户"),
        ("assistant", "AI助手"),
    ]

    session = models.ForeignKey(AiChatSession, on_delete=models.CASCADE, related_name="messages", verbose_name="会话")
    role = models.CharField(max_length=20, choices=ROLES, verbose_name="角色")
    content = models.TextField(verbose_name="内容")
    token_count = models.IntegerField(default=0, verbose_name="Token数量")
    response_time = models.FloatField(null=True, blank=True, verbose_name="响应时间(秒)")
    source_documents = models.JSONField(default=list, verbose_name="引用文档")
    is_streamed = models.BooleanField(default=False, verbose_name="是否流式输出")

    class Meta:
        verbose_name = "AI对话消息"
        verbose_name_plural = "AI对话消息"
        ordering = ["created_at"]


class AiKnowledge(BaseModel):
    KNOWLEDGE_TYPES = [
        ("document", "文档"),
        ("qa", "问答对"),
        ("faq", "常见问题"),
        ("procedure", "操作流程"),
        ("policy", "政策制度"),
        ("emergency", "应急预案"),
    ]

    title = models.CharField(max_length=200, verbose_name="标题")
    knowledge_type = models.CharField(max_length=20, choices=KNOWLEDGE_TYPES, default="document", verbose_name="知识类型")
    content = models.TextField(verbose_name="内容")
    summary = models.CharField(max_length=500, blank=True, verbose_name="摘要")
    tags = models.JSONField(default=list, verbose_name="标签")
    region = models.ForeignKey("common.RegionModel", on_delete=models.SET_NULL, null=True, blank=True, verbose_name="关联区域")
    is_public = models.BooleanField(default=True, verbose_name="是否公开")
    embedding = models.JSONField(null=True, blank=True, verbose_name="向量嵌入")

    class Meta:
        verbose_name = "知识库"
        verbose_name_plural = "知识库管理"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class AiKnowledgeDocument(BaseModel):
    """RAG 原始资料及其解析溯源；正文只存放在分块表中。"""

    STATUS_CHOICES = [("pending", "待处理"), ("ready", "可检索"), ("failed", "处理失败")]
    title = models.CharField(max_length=200, verbose_name="文档标题")
    source_path = models.CharField(max_length=500, verbose_name="导入源路径")
    source_type = models.CharField(max_length=30, default="pdf", verbose_name="源文件类型")
    checksum = models.CharField(max_length=64, db_index=True, verbose_name="SHA256")
    parser = models.CharField(max_length=30, default="text", verbose_name="解析器")
    parser_version = models.CharField(max_length=50, blank=True, verbose_name="解析器版本")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    metadata = models.JSONField(default=dict, blank=True, verbose_name="解析元数据")
    error_message = models.TextField(blank=True, verbose_name="失败原因")
    region = models.ForeignKey("common.RegionModel", on_delete=models.SET_NULL, null=True, blank=True)
    is_public = models.BooleanField(default=True)

    class Meta:
        verbose_name = "RAG 原始文档"
        verbose_name_plural = "RAG 原始文档"
        indexes = [models.Index(fields=["status", "is_public"], name="ai_assistan_status_0d08f1_idx")]

    def __str__(self):
        return self.title


class AiKnowledgeChunk(BaseModel):
    """可检索的最小知识单元，保留页码和原文定位以支持引用。"""

    document = models.ForeignKey(AiKnowledgeDocument, on_delete=models.CASCADE, related_name="chunks")
    content = models.TextField(verbose_name="Markdown 文本")
    ordinal = models.PositiveIntegerField(verbose_name="分块序号")
    page_start = models.PositiveIntegerField(null=True, blank=True)
    page_end = models.PositiveIntegerField(null=True, blank=True)
    token_estimate = models.PositiveIntegerField(default=0)
    keywords = models.JSONField(default=list, blank=True)
    embedding = models.JSONField(null=True, blank=True)

    class Meta:
        verbose_name = "RAG 文档分块"
        verbose_name_plural = "RAG 文档分块"
        ordering = ["document_id", "ordinal"]
        constraints = [models.UniqueConstraint(fields=["document", "ordinal"], name="unique_rag_chunk_ordinal")]


class AiToolLog(models.Model):
    """Agent 工具调用日志"""

    user = models.ForeignKey("users.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_tool_logs")
    session = models.ForeignKey(AiChatSession, on_delete=models.SET_NULL, null=True, blank=True, related_name="tool_logs")
    tool_name = models.CharField(max_length=50, verbose_name="工具名称")
    arguments = models.JSONField(default=dict, verbose_name="调用参数")
    summary = models.CharField(max_length=500, blank=True, verbose_name="执行摘要")
    success = models.BooleanField(default=True, verbose_name="是否成功")
    response_data = models.JSONField(null=True, blank=True, verbose_name="工具返回数据")
    is_simulated = models.BooleanField(default=True, verbose_name="是否模拟数据")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="调用时间")

    class Meta:
        verbose_name = "Agent工具日志"
        verbose_name_plural = "Agent工具日志"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tool_name", "-created_at"]),
            models.Index(fields=["user", "-created_at"]),
        ]

    def __str__(self):
        status = "✓" if self.success else "✗"
        return f"{status} {self.tool_name} @ {self.created_at:%m-%d %H:%M}"
