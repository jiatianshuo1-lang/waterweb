# Generated manually for WaterWeb RAG architecture.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("ai_assistant", "0004_rename_ai_tool_log_tool_5b7b4d_idx_ai_assistan_tool_na_600bb9_idx_and_more")]

    operations = [
        migrations.AddField(model_name="aichatsession", name="memory_summary", field=models.TextField(blank=True, verbose_name="会话长期记忆")),
        migrations.AddField(model_name="aichatsession", name="memory_updated_at", field=models.DateTimeField(blank=True, null=True, verbose_name="记忆更新时间")),
        migrations.CreateModel(
            name="AiKnowledgeDocument",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="软删除")),
                ("title", models.CharField(max_length=200, verbose_name="文档标题")),
                ("source_path", models.CharField(max_length=500, verbose_name="导入源路径")),
                ("source_type", models.CharField(default="pdf", max_length=30, verbose_name="源文件类型")),
                ("checksum", models.CharField(db_index=True, max_length=64, verbose_name="SHA256")),
                ("parser", models.CharField(default="text", max_length=30, verbose_name="解析器")),
                ("parser_version", models.CharField(blank=True, max_length=50, verbose_name="解析器版本")),
                ("status", models.CharField(choices=[("pending", "待处理"), ("ready", "可检索"), ("failed", "处理失败")], default="pending", max_length=20)),
                ("metadata", models.JSONField(blank=True, default=dict, verbose_name="解析元数据")),
                ("error_message", models.TextField(blank=True, verbose_name="失败原因")),
                ("is_public", models.BooleanField(default=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated", to=settings.AUTH_USER_MODEL, verbose_name="更新人")),
                ("region", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="common.regionmodel")),
            ],
            options={"verbose_name": "RAG 原始文档", "verbose_name_plural": "RAG 原始文档"},
        ),
        migrations.CreateModel(
            name="AiKnowledgeChunk",
            fields=[
                ("id", models.BigAutoField(primary_key=True, serialize=False)),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="创建时间")),
                ("updated_at", models.DateTimeField(auto_now=True, verbose_name="更新时间")),
                ("is_deleted", models.BooleanField(default=False, verbose_name="软删除")),
                ("content", models.TextField(verbose_name="Markdown 文本")),
                ("ordinal", models.PositiveIntegerField(verbose_name="分块序号")),
                ("page_start", models.PositiveIntegerField(blank=True, null=True)),
                ("page_end", models.PositiveIntegerField(blank=True, null=True)),
                ("token_estimate", models.PositiveIntegerField(default=0)),
                ("keywords", models.JSONField(blank=True, default=list)),
                ("embedding", models.JSONField(blank=True, null=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_created", to=settings.AUTH_USER_MODEL, verbose_name="创建人")),
                ("updated_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="%(class)s_updated", to=settings.AUTH_USER_MODEL, verbose_name="更新人")),
                ("document", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="chunks", to="ai_assistant.aiknowledgedocument")),
            ],
            options={"verbose_name": "RAG 文档分块", "verbose_name_plural": "RAG 文档分块", "ordering": ["document_id", "ordinal"]},
        ),
        migrations.AddIndex(model_name="aiknowledgedocument", index=models.Index(fields=["status", "is_public"], name="ai_assistan_status_0d08f1_idx")),
        migrations.AddConstraint(model_name="aiknowledgechunk", constraint=models.UniqueConstraint(fields=("document", "ordinal"), name="unique_rag_chunk_ordinal")),
    ]
