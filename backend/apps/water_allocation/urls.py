from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import WaterSourceViewSet, WaterAllocationViewSet, WaterTransferViewSet

router = DefaultRouter()
router.register(r'sources', WaterSourceViewSet, basename='water-source')
router.register(r'allocations', WaterAllocationViewSet, basename='water-allocation')
router.register(r'transfers', WaterTransferViewSet, basename='water-transfer')

urlpatterns = [
    path('', include(router.urls)),
]
