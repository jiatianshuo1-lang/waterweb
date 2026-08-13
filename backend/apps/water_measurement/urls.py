from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MeasureStationViewSet, WaterMeasurementViewSet, WaterAlarmViewSet

router = DefaultRouter()
router.register(r'stations', MeasureStationViewSet, basename='station')
router.register(r'measurements', WaterMeasurementViewSet, basename='measurement')
router.register(r'alarms', WaterAlarmViewSet, basename='alarm')

urlpatterns = [
    path('', include(router.urls)),
]
