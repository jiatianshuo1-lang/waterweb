from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Max, Min, Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import MeasureStation, WaterMeasurement, WaterAlarm
from .serializers import MeasureStationSerializer, WaterMeasurementSerializer, WaterAlarmSerializer
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response
import logging

logger = logging.getLogger('apps.water_measurement')


class MeasureStationViewSet(viewsets.ModelViewSet):
    queryset = MeasureStation.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station_type', 'communication', 'region', 'is_active', 'status']
    search_fields = ['code', 'name', 'device_code']
    permission_classes = [IsAuthenticated]
    serializer_class = MeasureStationSerializer


class WaterMeasurementViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WaterMeasurement.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station', 'source', 'is_abnormal']
    search_fields = ['remark']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterMeasurementSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(measure_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(measure_time__lte=end_time)
        return queryset

    @action(detail=False, methods=['get'], url_path='realtime')
    def realtime(self, request):
        station_id = request.query_params.get('station_id')
        if station_id:
            measurements = WaterMeasurement.objects.filter(station_id=station_id).order_by('-measure_time')[:1]
        else:
            station_ids = list(MeasureStation.objects.filter(is_active=True).values_list('id', flat=True))
            measurements = WaterMeasurement.objects.filter(station_id__in=station_ids).order_by('-measure_time')
            station_data = {}
            for m in measurements:
                if m.station_id not in station_data:
                    station_data[m.station_id] = m
            measurements = list(station_data.values())

        serializer = self.get_serializer(measurements, many=True)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        total_flow = WaterMeasurement.objects.filter(
            measure_time__gte=start_date
        ).aggregate(total=Sum('total_flow'))['total'] or 0

        stats = {
            'active_stations': MeasureStation.objects.filter(is_active=True, status='online').count(),
            'offline_stations': MeasureStation.objects.filter(is_active=True, status='offline').count(),
            'fault_stations': MeasureStation.objects.filter(status='fault').count(),
            'total_flow_days': total_flow,
            'alerts_unresolved': WaterAlarm.objects.filter(is_resolved=False).count(),
        }
        return success_response(data=stats)


class WaterAlarmViewSet(viewsets.ModelViewSet):
    queryset = WaterAlarm.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['station', 'alarm_type', 'level', 'is_resolved']
    search_fields = ['title', 'message']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterAlarmSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.query_params.get('unresolved'):
            queryset = queryset.filter(is_resolved=False)
        return queryset

    @action(detail=True, methods=['post'], url_path='resolve')
    def resolve(self, request, pk=None):
        alarm = self.get_object()
        alarm.is_resolved = True
        alarm.resolved_at = timezone.now()
        alarm.resolved_by = request.user
        alarm.resolution = request.data.get('resolution', '')
        alarm.save()
        logger.info('Alarm %s resolved by %s', alarm.id, request.user.username)
        return success_response(data=self.get_serializer(alarm).data, message='告警已处理')
