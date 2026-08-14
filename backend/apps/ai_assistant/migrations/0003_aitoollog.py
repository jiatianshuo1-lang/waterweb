from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="AiToolLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("tool_name", models.CharField(max_length=50, verbose_name="工具名称")),
                ("arguments", models.JSONField(default=dict, verbose_name="调用参数")),
                ("summary", models.CharField(blank=True, max_length=500, verbose_name="执行摘要")),
                ("success", models.BooleanField(default=True, verbose_name="是否成功")),
                ("response_data", models.JSONField(blank=True, null=True, verbose_name="工具返回数据")),
                ("is_simulated", models.BooleanField(default=True, verbose_name="是否模拟数据")),
                ("created_at", models.DateTimeField(auto_now_add=True, verbose_name="调用时间")),
                ("session", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="tool_logs", to="ai_assistant.aichatsession")),
                ("user", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="ai_tool_logs", to="users.user")),
            ],
            options={
                "verbose_name": "Agent工具日志",
                "verbose_name_plural": "Agent工具日志",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="aitoollog",
            index=models.Index(fields=["tool_name", "-created_at"], name="ai_tool_log_tool_5b7b4d_idx"),
        ),
        migrations.AddIndex(
            model_name="aitoollog",
            index=models.Index(fields=["user", "-created_at"], name="ai_tool_log_user_0e5908_idx"),
        ),
        migrations.AlterField(
            model_name="aiknowledge",
            name="knowledge_type",
            field=models.CharField(choices=[("document", "文档"), ("qa", "问答对"), ("faq", "常见问题"), ("procedure", "操作流程"), ("policy", "政策制度"), ("emergency", "应急预案")], default="document", max_length=20, verbose_name="知识类型"),
        ),
        migrations.AlterField(
            model_name="aiassistantconfig",
            name="model_name",
            field=models.CharField(default="deepseek-chat", max_length=100, verbose_name="模型名称"),
        ),
        migrations.AlterField(
            model_name="aiassistantconfig",
            name="provider",
            field=models.CharField(choices=[("local", "本地模型"), ("openai", "OpenAI"), ("azure", "Azure OpenAI"), ("qwen", "阿里云百炼"), ("doubao", "豆包"), ("deepseek", "DeepSeek"), ("ollama", "Ollama")], default="deepseek", max_length=20, verbose_name="服务商"),
        ),
    ]
