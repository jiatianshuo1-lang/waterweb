from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count
from django.utils import timezone
from datetime import timedelta

from .models import IrrigationDevice, IrrigationLog, IrrigationPlan, IrrigationRecord
from .serializers import (
    IrrigationDeviceSerializer, IrrigationLogSerializer,
    IrrigationPlanSerializer, IrrigationRecordSerializer
)
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response
from apps.common.exceptions import BusinessException
import logging

logger = logging.getLogger('apps.smart_irrigation')


class IrrigationDeviceViewSet(viewsets.ModelViewSet):
    queryset = IrrigationDevice.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['device_type', 'control_mode', 'region', 'status', 'is_active']
    search_fields = ['code', 'name', 'device_code']
    permission_classes = [IsAuthenticated]
    serializer_class = IrrigationDeviceSerializer

    @action(detail=True, methods=['post'], url_path='control')
    def control(self, request, pk=None):
        device = self.get_object()
        action = request.data.get('action', '')
        value = request.data.get('value', '')

        if not action:
            raise BusinessException('请指定控制动作')

        IrrigationLog.objects.create(
            device=device,
            action=action,
            value=str(value),
            operator=request.user,
            operate_time=timezone.now(),
            result='success',
        )

        logger.info('Device %s control: %s=%s by %s', device.code, action, value, request.user.username)
        return success_response(message='控制指令已发送')


class IrrigationPlanViewSet(viewsets.ModelViewSet):
    queryset = IrrigationPlan.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['plan_type', 'region', 'status']
    search_fields = ['code', 'name']
    permission_classes = [IsAuthenticated]
    serializer_class = IrrigationPlanSerializer

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        plan = self.get_object()
        if plan.status not in ['draft', 'paused']:
            raise BusinessException('当前状态无法启动')
        plan.status = 'active'
        plan.save()
        logger.info('Irrigation plan %s started by %s', plan.code, request.user.username)
        return success_response(data=self.get_serializer(plan).data, message='计划已启动')

    @action(detail=True, methods=['post'], url_path='pause')
    def pause(self, request, pk=None):
        plan = self.get_object()
        if plan.status != 'active':
            raise BusinessException('只有执行中的计划可以暂停')
        plan.status = 'paused'
        plan.save()
        return success_response(message='计划已暂停')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        plan = self.get_object()
        plan.status = 'completed'
        plan.save()
        return success_response(message='计划已完成')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel(self, request, pk=None):
        plan = self.get_object()
        plan.status = 'cancelled'
        plan.save()
        return success_response(message='计划已取消')


class IrrigationRecordViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = IrrigationRecord.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region', 'device', 'plan']
    permission_classes = [IsAuthenticated]
    serializer_class = IrrigationRecordSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        start_time = self.request.query_params.get('start_time')
        end_time = self.request.query_params.get('end_time')
        if start_time:
            queryset = queryset.filter(start_time__gte=start_time)
        if end_time:
            queryset = queryset.filter(start_time__lte=end_time)
        return queryset

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        days = int(request.query_params.get('days', 7))
        start_date = timezone.now() - timedelta(days=days)

        stats = IrrigationRecord.objects.filter(start_time__gte=start_date).aggregate(
            total_water=Sum('water_used'),
            total_energy=Sum('energy_used'),
            total_area=Sum('area_irrigated'),
            count=Count('id'),
        )
        return success_response(data={
            'total_water': stats['total_water'] or 0,
            'total_energy': stats['total_energy'] or 0,
            'total_area': stats['total_area'] or 0,
            'count': stats['count'] or 0,
            'device_online': IrrigationDevice.objects.filter(status__in=['online', 'running']).count(),
            'device_total': IrrigationDevice.objects.filter(is_active=True).count(),
            'active_plans': IrrigationPlan.objects.filter(status='active').count(),
        })
