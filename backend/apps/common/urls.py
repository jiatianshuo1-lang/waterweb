from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RegionViewSet, CommonConfigViewSet, HealthCheckView

router = DefaultRouter()
router.register(r'regions', RegionViewSet, basename='region')
router.register(r'configs', CommonConfigViewSet, basename='config')
router.register(r'health', HealthCheckView, basename='health')

urlpatterns = [
    path('', include(router.urls)),
]
