from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AiAssistantConfigViewSet,
    AiChatViewSet,
    AiKnowledgeViewSet,
    AiToolLogViewSet,
    AiToolsViewSet,
)

router = DefaultRouter()
router.register(r"configs", AiAssistantConfigViewSet, basename="ai-config")
router.register(r"chat", AiChatViewSet, basename="ai-chat")
router.register(r"knowledge", AiKnowledgeViewSet, basename="ai-knowledge")
router.register(r"tool-logs", AiToolLogViewSet, basename="ai-tool-log")

urlpatterns = [
    path("tools/", AiToolsViewSet.as_view({"get": "list_tools"}), name="ai-tools-list"),
    path("", include(router.urls)),
]
