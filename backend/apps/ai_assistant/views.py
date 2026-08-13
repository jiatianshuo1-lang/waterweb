import json
import logging
import time
from django.utils import timezone
from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend

from .models import AiAssistantConfig, AiChatSession, AiChatMessage, AiKnowledge
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response
from apps.common.exceptions import BusinessException

logger = logging.getLogger('apps.ai_assistant')


class AiAssistantConfigSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiAssistantConfig
        fields = ['id', 'name', 'provider', 'model_name', 'api_url', 'api_key',
                  'system_prompt', 'temperature', 'max_tokens', 'max_history',
                  'timeout', 'is_active', 'description', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']
        extra_kwargs = {'api_key': {'write_only': True}}


class AiChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiChatMessage
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class AiChatSessionSerializer(serializers.ModelSerializer):
    message_count = serializers.SerializerMethodField()

    class Meta:
        model = AiChatSession
        fields = ['id', 'session_id', 'title', 'config', 'is_active',
                  'last_message_time', 'message_count', 'created_at', 'updated_at']
        read_only_fields = ['session_id', 'created_at', 'updated_at']

    def get_message_count(self, obj):
        return obj.messages.count()


class AiKnowledgeSerializer(serializers.ModelSerializer):
    class Meta:
        model = AiKnowledge
        fields = ['id', 'title', 'knowledge_type', 'content', 'summary', 'tags',
                  'region', 'is_public', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class ChatRequestSerializer(serializers.Serializer):
    session_id = serializers.CharField(required=False)
    message = serializers.CharField()
    config_id = serializers.IntegerField(required=False)
    stream = serializers.BooleanField(default=False)
    include_history = serializers.BooleanField(default=True)


class AiService:
    @staticmethod
    def get_active_config(config_id=None):
        if config_id:
            try:
                return AiAssistantConfig.objects.get(id=config_id, is_active=True)
            except AiAssistantConfig.DoesNotExist:
                raise BusinessException('配置不存在或已禁用')
        return AiAssistantConfig.objects.filter(is_active=True).first()

    @staticmethod
    def build_messages(session, new_user_message, config):
        messages = []
        if config.system_prompt:
            messages.append({'role': 'system', 'content': config.system_prompt})

        history = session.messages.exclude(role='system').order_by('-created_at')[:config.max_history * 2]
        for msg in reversed(history):
            messages.append({'role': msg.role, 'content': msg.content})

        messages.append({'role': 'user', 'content': new_user_message})
        return messages

    @staticmethod
    def get_knowledge_context(query, top_k=3):
        from django.db.models.functions import Lower
        keywords = [kw.strip() for kw in query.replace('？', ' ').replace('?', ' ').split() if len(kw.strip()) > 1]
        if not keywords:
            return []

        q = AiKnowledge.objects.filter(is_public=True)
        from django.db.models import Q
        keyword_query = Q()
        for kw in keywords[:5]:
            keyword_query |= Q(title__icontains=kw) | Q(content__icontains=kw) | Q(tags__icontains=kw)

        docs = q.filter(keyword_query)[:top_k]
        return [{'title': d.title, 'content': d.content[:300], 'type': d.knowledge_type} for d in docs]

    @staticmethod
    def generate_response(messages, config, knowledge_context=None):
        context_text = ''
        if knowledge_context:
            context_text = '\n\n相关知识库内容：\n'
            for i, doc in enumerate(knowledge_context, 1):
                context_text += f"{i}. [{doc['title']}]({doc['type']}): {doc['content']}\n"

        if context_text:
            messages_copy = list(messages)
            messages_copy[-1] = {
                'role': 'user',
                'content': messages_copy[-1]['content'] + context_text + '\n请基于以上上下文回答问题，如上下文中没有相关信息，请根据自身知识回答。'
            }
        else:
            messages_copy = messages

        try:
            response = AiService._call_llm(messages_copy, config)
            return response
        except Exception as e:
            logger.error('AI call failed: %s', str(e))
            return AiService._mock_response(messages_copy)

    @staticmethod
    def _call_llm(messages, config):
        if config.provider == 'openai':
            return AiService._call_openai(messages, config)
        elif config.provider == 'qwen':
            return AiService._call_qwen(messages, config)
        elif config.provider == 'doubao':
            return AiService._call_doubao(messages, config)
        elif config.provider == 'deepseek':
            return AiService._call_deepseek(messages, config)
        elif config.provider == 'ollama':
            return AiService._call_ollama(messages, config)
        return AiService._mock_response(messages)

    @staticmethod
    def _mock_response(messages):
        last_msg = messages[-1]['content'] if messages else ''
        return f'我收到了您的消息："{last_msg[:100]}"...。这是AI助手的模拟回复。在实际部署时，请配置有效的AI模型服务。'

    @staticmethod
    def _call_openai(messages, config):
        try:
            import requests
            api_url = config.api_url or 'https://api.openai.com/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': config.model_name,
                'messages': messages,
                'temperature': config.temperature,
                'max_tokens': config.max_tokens,
            }
            resp = requests.post(api_url, json=data, headers=headers, timeout=config.timeout)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except ImportError:
            return AiService._mock_response(messages)

    @staticmethod
    def _call_qwen(messages, config):
        try:
            import requests
            api_url = config.api_url or 'https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions'
            headers = {
                'Authorization': f'Bearer {config.api_key}',
                'Content-Type': 'application/json',
            }
            data = {
                'model': config.model_name,
                'messages': messages,
                'temperature': config.temperature,
            }
            resp = requests.post(api_url, json=data, headers=headers, timeout=config.timeout)
            resp.raise_for_status()
            return resp.json()['choices'][0]['message']['content']
        except ImportError:
            return AiService._mock_response(messages)

    @staticmethod
    def _call_doubao(messages, config):
        return AiService._call_openai(messages, config)

    @staticmethod
    def _call_deepseek(messages, config):
        config_copy = config
        if not config_copy.api_url:
            config_copy.api_url = 'https://api.deepseek.com/v1/chat/completions'
        return AiService._call_openai(messages, config_copy)

    @staticmethod
    def _call_ollama(messages, config):
        try:
            import requests
            api_url = config.api_url or 'http://localhost:11434/api/chat'
            data = {
                'model': config.model_name,
                'messages': messages,
                'stream': False,
                'options': {
                    'temperature': config.temperature,
                }
            }
            resp = requests.post(api_url, json=data, timeout=config.timeout)
            resp.raise_for_status()
            return resp.json()['message']['content']
        except ImportError:
            return AiService._mock_response(messages)


class AiAssistantConfigViewSet(viewsets.ModelViewSet):
    queryset = AiAssistantConfig.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['provider', 'is_active']
    search_fields = ['name', 'model_name']
    serializer_class = AiAssistantConfigSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [IsAuthenticated()]
        return [IsAuthenticated()]


class AiChatViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['post'], url_path='send')
    def send_message(self, request):
        serializer = ChatRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        config = AiService.get_active_config(data.get('config_id'))

        session_id = data.get('session_id')
        if session_id:
            session = AiChatSession.objects.filter(session_id=session_id, user=request.user).first()

        if not session_id or not session:
            import uuid
            session = AiChatSession.objects.create(
                session_id=str(uuid.uuid4()),
                user=request.user,
                config=config,
                title=data['message'][:30],
            )

        user_message_content = data['message']
        messages = AiService.build_messages(session, user_message_content, config)

        knowledge_context = AiService.get_knowledge_context(user_message_content)

        start_time = time.time()
        assistant_response = AiService.generate_response(messages, config, knowledge_context)
        response_time = time.time() - start_time

        AiChatMessage.objects.create(
            session=session,
            role='user',
            content=user_message_content,
            token_count=len(user_message_content),
        )

        AiChatMessage.objects.create(
            session=session,
            role='assistant',
            content=assistant_response,
            token_count=len(assistant_response),
            response_time=round(response_time, 2),
            source_documents=knowledge_context,
        )

        session.last_message_time = timezone.now()
        session.save(update_fields=['last_message_time'])

        return success_response(data={
            'session_id': session.session_id,
            'response': assistant_response,
            'response_time': round(response_time, 2),
            'knowledge_used': len(knowledge_context),
        })

    @action(detail=False, methods=['get'], url_path='sessions')
    def list_sessions(self, request):
        sessions = request.user.ai_sessions.all()
        serializer = AiChatSessionSerializer(sessions, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['get'], url_path='history')
    def get_history(self, request):
        session_id = request.query_params.get('session_id')
        if not session_id:
            raise BusinessException('请提供session_id')

        session = AiChatSession.objects.filter(session_id=session_id, user=request.user).first()
        if not session:
            raise BusinessException('会话不存在')

        messages = session.messages.exclude(role='system').order_by('created_at')
        return success_response(data=AiChatMessageSerializer(messages, many=True).data)

    @action(detail=False, methods=['post'], url_path='new-session')
    def new_session(self, request):
        import uuid
        config = AiService.get_active_config()
        session = AiChatSession.objects.create(
            session_id=str(uuid.uuid4()),
            user=request.user,
            config=config,
        )
        return success_response(data=AiChatSessionSerializer(session).data)

    @action(detail=False, methods=['delete'], url_path='session')
    def delete_session(self, request):
        session_id = request.query_params.get('session_id') or request.data.get('session_id')
        if not session_id:
            raise BusinessException('请提供session_id')

        session = AiChatSession.objects.filter(session_id=session_id, user=request.user).first()
        if not session:
            raise BusinessException('会话不存在')

        session.messages.all().delete()
        session.delete()
        return success_response(message='会话已删除')


class AiKnowledgeViewSet(viewsets.ModelViewSet):
    queryset = AiKnowledge.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['knowledge_type', 'region', 'is_public']
    search_fields = ['title', 'content', 'tags']
    serializer_class = AiKnowledgeSerializer
    permission_classes = [IsAuthenticated]
