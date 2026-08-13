from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Max, Min
from django.utils import timezone
from datetime import timedelta

from .models import SoilMonitorStation, SoilData, WeatherData, SoilForecast
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response


class SoilMonitorStationSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = SoilMonitorStation
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'last_data_time']


class SoilDataSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = SoilData
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class WeatherDataSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = WeatherData
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SoilForecastSerializer(serializers.ModelSerializer):
    station_name = serializers.CharField(source='station.name', read_only=True)

    class Meta:
        model = SoilForecast
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class SoilMonitorStationViewSet(viewsets.ModelViewSet):
    queryset = SoilMonitorStation.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station_type', 'region', 'status', 'is_active']
    search_fields = ['code', 'name']
    permission_classes = [IsAuthenticated]
    serializer_class = SoilMonitorStationSerializer


class SoilDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = SoilData.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station', 'source', 'is_abnormal']
    permission_classes = [IsAuthenticated]
    serializer_class = SoilDataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(measure_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(measure_time__lte=end_time)
        return queryset


class WeatherDataViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WeatherData.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station']
    permission_classes = [IsAuthenticated]
    serializer_class = WeatherDataSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(measure_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(measure_time__lte=end_time)
        return queryset


class SoilForecastViewSet(viewsets.ModelViewSet):
    queryset = SoilForecast.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station', 'forecast_type', 'risk_level']
    permission_classes = [IsAuthenticated]
    serializer_class = SoilForecastSerializer

    @action(detail=False, methods=['post'], url_path='generate')
    def generate_forecast(self, request):
        from django.db import transaction
        station_id = request.data.get('station_id')

        stations = SoilMonitorStation.objects.filter(id=station_id) if station_id else SoilMonitorStation.objects.filter(is_active=True)
        count = 0
        with transaction.atomic():
            for station in stations:
                latest_soil = station.soil_data.order_by('-measure_time').first()
                if not latest_soil:
                    continue

                avg_moisture = latest_soil.soil_moisture_avg or (
                    (latest_soil.soil_moisture_0_10 or 0) +
                    (latest_soil.soil_moisture_10_20 or 0) +
                    (latest_soil.soil_moisture_20_40 or 0) +
                    (latest_soil.soil_moisture_40_60 or 0)
                ) / 4 if any([latest_soil.soil_moisture_0_10, latest_soil.soil_moisture_10_20,
                              latest_soil.soil_moisture_20_40, latest_soil.soil_moisture_40_60]) else None

                forecast_type = 'optimal'
                risk_level = 'low'
                advice = '土壤墒情适宜，保持当前灌溉策略'

                if avg_moisture is not None:
                    if avg_moisture < 15:
                        forecast_type = 'drought'
                        risk_level = 'high'
                        advice = '土壤严重干旱，建议立即灌溉'
                    elif avg_moisture < 20:
                        forecast_type = 'drought'
                        risk_level = 'medium'
                        advice = '土壤偏干，建议进行灌溉'
                    elif avg_moisture > 45:
                        forecast_type = 'waterlogging'
                        risk_level = 'high'
                        advice = '土壤过湿，注意排水防涝'
                    elif avg_moisture > 35:
                        forecast_type = 'waterlogging'
                        risk_level = 'medium'
                        advice = '土壤偏湿，注意排水'

                SoilForecast.objects.create(
                    station=station,
                    forecast_type=forecast_type,
                    forecast_time=timezone.now(),
                    forecast_hours=24,
                    current_moisture=avg_moisture,
                    predicted_moisture=avg_moisture,
                    risk_level=risk_level,
                    advice=advice,
                )
                count += 1

        return success_response(data={'count': count}, message=f'成功生成 {count} 条墒情预报')

    @action(detail=False, methods=['get'], url_path='overview')
    def overview(self, request):
        online = SoilMonitorStation.objects.filter(status='online', is_active=True).count()
        total = SoilMonitorStation.objects.filter(is_active=True).count()
        alerts = SoilForecast.objects.filter(risk_level__in=['high', 'critical']).count()

        recent_weather = WeatherData.objects.order_by('-measure_time').first()
        recent_soil = SoilData.objects.order_by('-measure_time').first()

        return success_response(data={
            'stations': {'total': total, 'online': online, 'offline': total - online},
            'alerts': alerts,
            'recent_weather': {
                'temperature': recent_weather.temperature if recent_weather else None,
                'humidity': recent_weather.humidity if recent_weather else None,
                'rainfall': recent_weather.rainfall if recent_weather else None,
                'time': str(recent_weather.measure_time) if recent_weather else None,
            },
            'recent_soil': {
                'moisture_avg': recent_soil.soil_moisture_avg if recent_soil else None,
                'time': str(recent_soil.measure_time) if recent_soil else None,
            },
        })
