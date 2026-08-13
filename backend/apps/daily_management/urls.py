from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NoticeViewSet, MeetingViewSet, AssetViewSet, DocumentViewSet

router = DefaultRouter()
router.register(r'notices', NoticeViewSet, basename='notice')
router.register(r'meetings', MeetingViewSet, basename='meeting')
router.register(r'assets', AssetViewSet, basename='asset')
router.register(r'documents', DocumentViewSet, basename='document')

urlpatterns = [
    path('', include(router.urls)),
]
