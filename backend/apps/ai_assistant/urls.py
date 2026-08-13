from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AiAssistantConfigViewSet, AiChatViewSet, AiKnowledgeViewSet

router = DefaultRouter()
router.register(r'configs', AiAssistantConfigViewSet, basename='ai-config')
router.register(r'chat', AiChatViewSet, basename='ai-chat')
router.register(r'knowledge', AiKnowledgeViewSet, basename='ai-knowledge')

urlpatterns = [
    path('', include(router.urls)),
]
