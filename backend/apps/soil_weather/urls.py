from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    SoilMonitorStationViewSet, SoilDataViewSet, WeatherDataViewSet, SoilForecastViewSet
)

router = DefaultRouter()
router.register(r'stations', SoilMonitorStationViewSet, basename='soil-station')
router.register(r'soil-data', SoilDataViewSet, basename='soil-data')
router.register(r'weather-data', WeatherDataViewSet, basename='weather-data')
router.register(r'forecasts', SoilForecastViewSet, basename='soil-forecast')

urlpatterns = [
    path('', include(router.urls)),
]
