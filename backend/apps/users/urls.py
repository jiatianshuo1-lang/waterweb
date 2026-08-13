from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UserViewSet, OperationLogViewSet

router = DefaultRouter()
router.register(r'users', UserViewSet, basename='user')
router.register(r'logs', OperationLogViewSet, basename='operation-log')

urlpatterns = [
    path('', include(router.urls)),
]
