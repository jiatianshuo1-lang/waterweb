import json
import logging
import time
import uuid as uuid_mod
from django.utils import timezone
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import AiAssistantConfig, AiChatSession, AiChatMessage, AiKnowledge, AiToolLog
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response
from apps.common.exceptions import BusinessException

logger = logging.getLogger("apps.ai_assistant")


# ---------------------------------------------------------------------------
# Serializers
# ---------------------------------------------------------------------------

class AiAssistantConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiAssistantConfig
        fields = ["id", "name", "provider", "model_name", "api_url", "api_key",
                  "system_prompt", "temperature", "max_tokens", "max_history",
                  "timeout", "is_active", "description", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]
        extra_kwargs = {"api_key": {"write_only": True}}


class AiChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatMessage
        fields = "__all__"
        read_only_fields = ["created_at", "updated_at"]


class AiChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AiChatSession
        fields = ["id", "session_id", "title", "config", "is_active",
                  "last_message_time", "message_count", "created_at", "updated_at"]
        read_only_fields = ["session_id", "created_at", "updated_at"]

    def get_message_count(self, obj):
        return obj.messages.count()


class AiKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiKnowledge
        fields = ["id", "title", "knowledge_type", "content", "summary", "tags",
                  "region", "is_public", "created_at", "updated_at"]
        read_only_fields = ["created_at", "updated_at"]


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False)
    message = serializers.CharField()
    config_id = serializers.IntegerField(required=False)
    stream = serializers.BooleanField(default=False)
    include_history = serializers.BooleanField(default=True)


class AgentChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False)
    message = serializers.CharField()
    config_id = serializers.IntegerField(required=False)


class ToolLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiToolLog
        fields = "__all__"
        read_only_fields = ["created_at"]


# ---------------------------------------------------------------------------
# Legacy AiService（保留用于旧的非 Agent 模式）
# ---------------------------------------------------------------------------

class AiService:
    @staticmethod
    def get_active_config(config_id=None):
        if config_id:
            try:
                return AiAssistantConfig.objects.get(id=config_id, is_active=True)
            except AiAssistantConfig.DoesNotExist:
                raise BusinessException("配置不存在或已禁用")
        return AiAssistantConfig.objects.filter(is_active=True).first()

    @staticmethod
    def build_messages(session, new_user_message, config):
        messages = []
        if config.system_prompt:
            messages.append({"role": "system", "content": config.system_prompt})

        history = session.messages.exclude(role="system").order_by("-created_at")[:config.max_history * 2]
        for msg in reversed(history):
            messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": new_user_message})
        return messages

    @staticmethod
    def generate_response(messages, config):
        try:
            from .agent.core import call_llm
            msg = call_llm(messages, [], config)
            return msg.get("content") or ""
        except Exception as e:
            logger.warning("[Legacy] LLM failed: %s, using fallback", e)
            return f"AI 服务暂不可用：{e}"


# ---------------------------------------------------------------------------
# ViewSets
# ---------------------------------------------------------------------------

class AiAssistantConfigViewSet(viewsets.ModelViewSet):
    queryset = AiAssistantConfig.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["provider", "is_active"]
    search_fields = ["name", "model_name"]
    serializer_class = AiAssistantConfigSerializer
    permission_classes = [IsAuthenticated]


class AiChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def _get_or_create_session(self, request, session_id):
        if session_id:
            session = AiChatSession.objects.filter(
                session_id=session_id, user=request.user
            ).first()
            if session:
                return session
        config = AiService.get_active_config()
        return AiChatSession.objects.create(
            session_id=str(uuid_mod.uuid4()),
            user=request.user,
            config=config,
            title="",
        )

    def _build_history_messages(self, session, max_history):
        msgs = session.messages.exclude(role="system").order_by("-created_at")[:max_history * 4]
        return [{"role": m.role, "content": m.content} for m in reversed(msgs)]

    @action(detail=False, methods=["post"], url_path="agent")
    def agent_chat(self, request):
        """
        Agent 模式主入口：
        - 自动调用 tools（传感器模拟）
        - 融合 RAG 知识库
        - 基于用户角色做权限过滤
        """
        serializer = AgentChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user_message = data["message"]

        session = self._get_or_create_session(request, data.get("session_id"))
        config = session.config or AiService.get_active_config()

        # 历史对话（排除刚发的这条）
        history_msgs = self._build_history_messages(session, config.max_history if config else 10)

        # 调用 Agent
        from .agent.core import run_agent, run_agent_fallback
        from .agent.permissions import TOOL_PERMISSIONS

        role = request.user.role or "viewer"
        role_name = request.user.get_role_display() or "只读用户"

        if config and config.api_key and config.api_key.strip():
            agent_result = run_agent(
                user_message=user_message,
                config=config,
                user_role=role,
                user_role_name=role_name,
                session_history=history_msgs,
                memory_summary=session.memory_summary,
                rag_region=request.user.region_id if hasattr(request.user, "region_id") else None,
            )
        else:
            agent_result = run_agent_fallback(user_message, user_role=role)

        # 持久化对话
        AiChatMessage.objects.create(
            session=session,
            role="user",
            content=user_message,
            token_count=len(user_message),
        )
        AiChatMessage.objects.create(
            session=session,
            role="assistant",
            content=agent_result.final_answer,
            token_count=len(agent_result.final_answer),
            response_time=agent_result.response_time,
            source_documents=agent_result.rag_used,
        )

        # 每轮在本地做受控的长期记忆压缩；不把工具输出、密钥或模型猜测写入记忆。
        from .agent.context import build_memory_summary
        session.memory_summary = build_memory_summary(session.memory_summary, history_msgs + [{"role": "user", "content": user_message}])
        session.memory_updated_at = timezone.now()

        # 持久化工具调用日志
        for tc in agent_result.tool_calls:
            AiToolLog.objects.create(
                user=request.user,
                session=session,
                tool_name=tc["tool"],
                arguments=tc.get("arguments", {}),
                summary=tc.get("summary", ""),
                success=tc.get("success", True),
                is_simulated=True,
            )

        # 更新会话
        if not session.title:
            session.title = user_message[:30]
        session.last_message_time = timezone.now()
        session.save(update_fields=["last_message_time", "title", "memory_summary", "memory_updated_at"])

        return success_response(data={
            "session_id": session.session_id,
            "response": agent_result.final_answer,
            "response_time": agent_result.response_time,
            "iterations": agent_result.iterations,
            "tool_calls": agent_result.tool_calls,
            "rag_used": [
                {"title": d["title"], "type": d["type"], "score": d.get("score", 0)}
                for d in agent_result.rag_used
            ],
            "is_simulated": (not (config and config.api_key and config.api_key.strip())
                             or any(call.get("is_simulated", False) for call in agent_result.tool_calls)),
            "role": role,
            "available_tools": TOOL_PERMISSIONS.get(role, []),
        })

    @action(detail=False, methods=["post"], url_path="send")
    def send_message(self, request):
        """兼容旧版纯 LLM 对话（不走 Agent），已废弃但保留"""
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        session = self._get_or_create_session(request, data.get("session_id"))
        config = session.config or AiService.get_active_config()
        if not config:
            raise BusinessException("请先在后台配置 AI 模型")

        messages = AiService.build_messages(session, data["message"], config)
        start = time.time()
        response = AiService.generate_response(messages, config)
        elapsed = round(time.time() - start, 2)

        AiChatMessage.objects.create(
            session=session, role="user", content=data["message"],
            token_count=len(data["message"]),
        )
        AiChatMessage.objects.create(
            session=session, role="assistant", content=response,
            token_count=len(response), response_time=elapsed,
        )
        session.last_message_time = timezone.now()
        session.save(update_fields=["last_message_time"])

        return success_response(data={
            "session_id": session.session_id,
            "response": response,
            "response_time": elapsed,
        })

    @action(detail=False, methods=["get"], url_path="sessions")
    def list_sessions(self, request):
        sessions = request.user.ai_sessions.all()
        return success_response(data=AiChatSessionSerializer(sessions, many=True).data)

    @action(detail=False, methods=["get"], url_path="history")
    def get_history(self, request):
        session_id = request.query_params.get("session_id")
        if not session_id:
            raise BusinessException("请提供 session_id")

        session = AiChatSession.objects.filter(
            session_id=session_id, user=request.user
        ).first()
        if not session:
            raise BusinessException("会话不存在")

        messages = session.messages.exclude(role="system").order_by("created_at")
        return success_response(data=AiChatMessageSerializer(messages, many=True).data)

    @action(detail=False, methods=["post"], url_path="new-session")
    def new_session(self, request):
        config = AiService.get_active_config()
        session = AiChatSession.objects.create(
            session_id=str(uuid_mod.uuid4()),
            user=request.user,
            config=config,
        )
        return success_response(data=AiChatSessionSerializer(session).data)

    @action(detail=False, methods=["delete"], url_path="session")
    def delete_session(self, request):
        session_id = request.query_params.get("session_id") or request.data.get("session_id")
        if not session_id:
            raise BusinessException("请提供 session_id")

        session = AiChatSession.objects.filter(
            session_id=session_id, user=request.user
        ).first()
        if not session:
            raise BusinessException("会话不存在")

        session.messages.all().delete()
        session.delete()
        return success_response(message="会话已删除")

    @action(detail=False, methods=["get"], url_path="tool-logs")
    def tool_logs(self, request):
        """查询工具调用历史"""
        from django.db.models import Count
        queryset = AiToolLog.objects.filter(user=request.user).order_by("-created_at")[:50]
        stats = AiToolLog.objects.filter(user=request.user).values("tool_name").annotate(
            count=Count("id")
        ).order_by("-count")[:10]
        return success_response(data={
            "logs": ToolLogSerializer(queryset, many=True).data,
            "stats": list(stats),
        })


class AiKnowledgeViewSet(viewsets.ModelViewSet):
    queryset = AiKnowledge.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["knowledge_type", "region", "is_public"]
    search_fields = ["title", "content", "tags"]
    serializer_class = AiKnowledgeSerializer
    permission_classes = [IsAuthenticated]


class AiToolLogViewSet(viewsets.ReadOnlyModelViewSet):
    """管理员可查看所有工具调用日志"""
    queryset = AiToolLog.objects.all()
    pagination_class = StandardPagination
    serializer_class = ToolLogSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.user.is_staff:
            qs = qs.filter(user=self.request.user)
        return qs


# ---------------------------------------------------------------------------
# 工具列表（前端展示可用工具）
# ---------------------------------------------------------------------------

class AiToolsViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=["get"], url_path="list")
    def list_tools(self, request):
        from .agent.tools import get_tool_definitions, TOOL_REGISTRY
        from .agent.permissions import filter_tools_by_role

        role = request.user.role or "viewer"
        available = filter_tools_by_role(role, get_tool_definitions())

        # 精简 schema，前端展示友好
        simplified = []
        for t in available:
            simplified.append({
                "name": t["name"],
                "description": t["description"],
                "parameters": t["parameters"],
            })

        return success_response(data={
            "role": role,
            "role_display": request.user.get_role_display(),
            "total_tools": len(TOOL_REGISTRY),
            "available_tools": simplified,
        })
