import uuid
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Sum, Count, Q

from .models import WaterSource, WaterAllocation, WaterAllocationDetail, WaterTransfer
from .serializers import (
    WaterSourceSerializer, WaterAllocationSerializer, WaterTransferSerializer
)
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response
from apps.common.exceptions import BusinessException


def generate_code(prefix):
    date_str = timezone.now().strftime('%Y%m%d')
    return f'{prefix}{date_str}{str(uuid.uuid4())[:6].upper()}'


class WaterSourceViewSet(viewsets.ModelViewSet):
    queryset = WaterSource.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['source_type', 'region']
    search_fields = ['code', 'name']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterSourceSerializer


class WaterAllocationViewSet(viewsets.ModelViewSet):
    queryset = WaterAllocation.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['allocation_type', 'water_source', 'status']
    search_fields = ['code', 'name']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterAllocationSerializer

    def perform_create(self, serializer):
        instance = serializer.save(
            code=generate_code('ALLOC'),
            created_by=self.request.user,
        )

    @action(detail=True, methods=['post'], url_path='submit')
    def submit(self, request, pk=None):
        obj = self.get_object()
        if obj.status != 'draft':
            raise BusinessException('只有草稿可以提交')
        obj.status = 'submitted'
        obj.save()
        return success_response(message='方案已提交审批')

    @action(detail=True, methods=['post'], url_path='approve')
    def approve(self, request, pk=None):
        obj = self.get_object()
        if obj.status != 'submitted':
            raise BusinessException('只有已提交的方案可以审批')
        obj.status = 'approved'
        obj.save()
        return success_response(message='方案已审批通过')

    @action(detail=True, methods=['post'], url_path='execute')
    def execute(self, request, pk=None):
        obj = self.get_object()
        if obj.status != 'approved':
            raise BusinessException('只有已审批的方案可以执行')
        obj.status = 'executing'
        obj.save()
        return success_response(message='方案开始执行')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        total_allocated = WaterAllocationDetail.objects.aggregate(total=Sum('allocated_amount'))['total'] or 0
        total_used = WaterAllocationDetail.objects.aggregate(total=Sum('used_amount'))['total'] or 0

        stats = {
            'water_sources': WaterSource.objects.count(),
            'total_capacity': WaterSource.objects.aggregate(total=Sum('capacity'))['total'] or 0,
            'current_storage': WaterSource.objects.aggregate(total=Sum('current_storage'))['total'] or 0,
            'total_allocated': total_allocated,
            'total_used': total_used,
            'usage_rate': round(total_used / total_allocated * 100, 2) if total_allocated > 0 else 0,
            'allocations_active': WaterAllocation.objects.filter(status__in=['approved', 'executing']).count(),
        }
        return success_response(data=stats)


class WaterTransferViewSet(viewsets.ModelViewSet):
    queryset = WaterTransfer.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['transfer_type', 'status']
    search_fields = ['code', 'reason']
    permission_classes = [IsAuthenticated]
    serializer_class = WaterTransferSerializer

    def perform_create(self, serializer):
        instance = serializer.save(
            code=generate_code('TRF'),
            operator=self.request.user,
        )
