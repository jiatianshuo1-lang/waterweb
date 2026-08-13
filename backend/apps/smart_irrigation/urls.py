from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import IrrigationDeviceViewSet, IrrigationPlanViewSet, IrrigationRecordViewSet

router = DefaultRouter()
router.register(r'devices', IrrigationDeviceViewSet, basename='irrigation-device')
router.register(r'plans', IrrigationPlanViewSet, basename='irrigation-plan')
router.register(r'records', IrrigationRecordViewSet, basename='irrigation-record')

urlpatterns = [
    path('', include(router.urls)),
]
