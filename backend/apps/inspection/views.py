import uuid
import logging
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Count, Sum

from .models import Inspection, WorkOrder, WorkOrderLog, InspectionRecord
from .serializers import (
    InspectionSerializer, InspectionCreateSerializer, InspectionUpdateSerializer,
    WorkOrderSerializer, WorkOrderCreateSerializer, WorkOrderAssignSerializer,
    WorkOrderCompleteSerializer, WorkOrderVerifySerializer,
    InspectionRecordSerializer, WorkOrderLogSerializer
)
from apps.common.pagination import StandardPagination
from apps.common.exceptions import NotFoundException, ValidationException, BusinessException
from apps.common.responses import success_response, created_response

logger = logging.getLogger(__name__)


def generate_code(prefix):
    date_str = timezone.now().strftime('%Y%m%d')
    random_str = str(uuid.uuid4())[:6].upper()
    return f'{prefix}{date_str}{random_str}'


class InspectionService:
    STATUS_FLOW = {
        'pending': ['in_progress', 'cancelled'],
        'in_progress': ['completed', 'cancelled'],
        'completed': [],
        'cancelled': [],
        'overdue': ['in_progress', 'cancelled'],
    }

    @staticmethod
    def change_status(inspection, new_status, user=None, remark=''):
        if new_status not in InspectionService.STATUS_FLOW.get(inspection.status, []):
            raise BusinessException(f'无法从 {inspection.get_status_display()} 变更为 {Inspection._meta.get_field("status").choices}')

        inspection.status = new_status
        inspection.updated_by = user
        if new_status == 'in_progress' and not inspection.actual_start:
            inspection.actual_start = timezone.now()
        if new_status == 'completed' and not inspection.actual_end:
            inspection.actual_end = timezone.now()
        inspection.save()
        return inspection

    @staticmethod
    def generate_inspection_report(inspection_id):
        inspection = Inspection.objects.get(id=inspection_id)
        records = inspection.records.all()
        normal_count = records.filter(result='normal').count()
        abnormal_count = records.filter(result='abnormal').count()
        skip_count = records.filter(result='skip').count()

        total = records.count()
        result = 'normal'
        if abnormal_count > 0:
            result = 'abnormal'

        inspection.result = result
        inspection.report = f'共 {total} 项，正常 {normal_count} 项，异常 {abnormal_count} 项，跳过 {skip_count} 项。'
        inspection.save(update_fields=['result', 'report'])
        return inspection

    @staticmethod
    def create_from_template(template_type, region, planned_start, planned_end, inspectors, user, **kwargs):
        title = kwargs.get('title', f'{region.name} {Inspection._meta.get_field("template_type").choices}')
        inspection = Inspection.objects.create(
            code=generate_code('INS'),
            title=title,
            template_type=template_type,
            region=region,
            planned_start=planned_start,
            planned_end=planned_end,
            description=kwargs.get('description', ''),
            checklist=kwargs.get('checklist', []),
            created_by=user,
            updated_by=user,
        )
        if inspectors:
            inspection.inspectors.set(inspectors)
        logger.info('Inspection created: %s by %s', inspection.code, user.username)
        return inspection


class WorkOrderService:
    STATUS_FLOW = {
        'pending': ['assigned', 'rejected'],
        'assigned': ['in_progress', 'rejected'],
        'in_progress': ['completed'],
        'completed': ['verified', 'rejected'],
        'verified': ['closed'],
        'closed': [],
        'rejected': ['pending'],
    }

    @staticmethod
    def change_status(work_order, new_status, user=None, remark=''):
        if new_status not in WorkOrderService.STATUS_FLOW.get(work_order.status, []):
            raise BusinessException(f'无法从 {work_order.get_status_display()} 变更为 {dict(WorkOrder.STATUS_CHOICES).get(new_status, new_status)}')

        from_status = work_order.status
        work_order.status = new_status
        work_order.updated_by = user

        if new_status == 'in_progress' and not work_order.actual_start:
            work_order.actual_start = timezone.now()
        if new_status == 'completed':
            work_order.actual_end = timezone.now()

        work_order.save()

        WorkOrderLog.objects.create(
            work_order=work_order,
            action=_get_action(new_status),
            from_status=from_status,
            to_status=new_status,
            operator=user,
            remark=remark,
        )
        return work_order

    @staticmethod
    def auto_create_from_inspection(inspection, user):
        abnormal_records = inspection.records.filter(result='abnormal')
        if not abnormal_records.exists():
            return None

        work_order = WorkOrder.objects.create(
            code=generate_code('WO'),
            title=f'巡检异常处理 - {inspection.title}',
            order_type='inspection_issue',
            priority='medium',
            status='pending',
            region=inspection.region,
            inspection=inspection,
            reporter=user,
            description=inspection.report or f'巡检发现 {abnormal_records.count()} 项异常项',
            created_by=user,
            updated_by=user,
        )
        WorkOrderLog.objects.create(
            work_order=work_order,
            action='create',
            to_status='pending',
            operator=user,
            remark='从巡检任务自动创建',
        )
        return work_order


def _get_action(status):
    mapping = {
        'pending': 'create',
        'assigned': 'assign',
        'in_progress': 'start',
        'completed': 'complete',
        'verified': 'verify',
        'closed': 'close',
        'rejected': 'reject',
    }
    return mapping.get(status, 'update')


class InspectionViewSet(viewsets.ModelViewSet):
    queryset = Inspection.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['template_type', 'priority', 'status', 'region', 'inspectors']
    search_fields = ['code', 'title', 'description']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return InspectionCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return InspectionUpdateSerializer
        return InspectionSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role not in ['super_admin', 'admin', 'manager']:
            queryset = queryset.filter(
                Q(inspectors=user) | Q(created_by=user)
            ).distinct()
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(
            code=generate_code('INS'),
            created_by=self.request.user,
            updated_by=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='start')
    def start_inspection(self, request, pk=None):
        inspection = self.get_object()
        InspectionService.change_status(inspection, 'in_progress', request.user)
        return success_response(data=InspectionSerializer(inspection).data, message='巡检已开始')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete_inspection(self, request, pk=None):
        inspection = self.get_object()
        InspectionService.change_status(inspection, 'completed', request.user,
                                       remark=request.data.get('remark', ''))
        InspectionService.generate_inspection_report(inspection.id)

        create_wo = request.data.get('create_work_order', True)
        if create_wo:
            WorkOrderService.auto_create_from_inspection(inspection, request.user)

        return success_response(data=InspectionSerializer(inspection).data, message='巡检已完成')

    @action(detail=True, methods=['post'], url_path='cancel')
    def cancel_inspection(self, request, pk=None):
        inspection = self.get_object()
        InspectionService.change_status(inspection, 'cancelled', request.user,
                                       remark=request.data.get('remark', ''))
        return success_response(message='巡检已取消')

    @action(detail=True, methods=['get'], url_path='records')
    def list_records(self, request, pk=None):
        inspection = self.get_object()
        records = inspection.records.all()
        serializer = InspectionRecordSerializer(records, many=True)
        return success_response(data=serializer.data)

    @action(detail=True, methods=['post'], url_path='records/batch')
    def batch_create_records(self, request, pk=None):
        inspection = self.get_object()
        records_data = request.data.get('records', [])
        if not records_data:
            raise ValidationException('请提供巡检记录')

        records = []
        for item in records_data:
            records.append(InspectionRecord(
                inspection=inspection,
                item_name=item.get('item_name', ''),
                item_type=item.get('item_type', ''),
                result=item.get('result', 'normal'),
                value=item.get('value', ''),
                standard=item.get('standard', ''),
                remark=item.get('remark', ''),
                photos=item.get('photos', []),
                inspector=request.user,
            ))
        InspectionRecord.objects.bulk_create(records)
        return created_response(data={'count': len(records)}, message=f'成功创建 {len(records)} 条巡检记录')

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'total': Inspection.objects.filter(is_deleted=False).count(),
            'pending': Inspection.objects.filter(status='pending').count(),
            'in_progress': Inspection.objects.filter(status='in_progress').count(),
            'completed_today': Inspection.objects.filter(actual_end__date=today).count(),
            'completed_month': Inspection.objects.filter(actual_end__date__gte=month_start).count(),
            'overdue': Inspection.objects.filter(
                status__in=['pending', 'in_progress'],
                planned_end__lt=timezone.now()
            ).count(),
            'by_priority': dict(Inspection.objects.values_list('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_result': dict(Inspection.objects.values_list('result').annotate(count=Count('id')).values_list('result', 'count')),
        }
        return success_response(data=stats)


class InspectionRecordViewSet(viewsets.ModelViewSet):
    queryset = InspectionRecord.objects.all()
    pagination_class = StandardPagination
    serializer_class = InspectionRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['inspection', 'result', 'inspector']


class WorkOrderViewSet(viewsets.ModelViewSet):
    queryset = WorkOrder.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['order_type', 'priority', 'status', 'region', 'assignee', 'inspection']
    search_fields = ['code', 'title', 'description']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return WorkOrderCreateSerializer
        elif self.action == 'assign':
            return WorkOrderAssignSerializer
        elif self.action == 'complete':
            return WorkOrderCompleteSerializer
        elif self.action == 'verify':
            return WorkOrderVerifySerializer
        return WorkOrderSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if user.role not in ['super_admin', 'admin', 'manager']:
            queryset = queryset.filter(
                Q(assignee=user) | Q(reporter=user) | Q(verifier=user)
            ).distinct()
        return queryset

    def perform_create(self, serializer):
        instance = serializer.save(
            code=generate_code('WO'),
            reporter=self.request.user,
            created_by=self.request.user,
            updated_by=self.request.user,
        )
        WorkOrderLog.objects.create(
            work_order=instance,
            action='create',
            to_status='pending',
            operator=self.request.user,
        )

    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user)

    @action(detail=True, methods=['post'], url_path='assign')
    def assign(self, request, pk=None):
        work_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_order.assignee_id = serializer.validated_data['assignee']
        if serializer.validated_data.get('planned_start'):
            work_order.planned_start = serializer.validated_data['planned_start']
        if serializer.validated_data.get('planned_end'):
            work_order.planned_end = serializer.validated_data['planned_end']
        work_order.updated_by = request.user
        work_order.save()

        WorkOrderService.change_status(work_order, 'assigned', request.user,
                                       remark=serializer.validated_data.get('remark', ''))
        return success_response(data=WorkOrderSerializer(work_order).data, message='工单已派单')

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        work_order = self.get_object()
        WorkOrderService.change_status(work_order, 'in_progress', request.user,
                                       remark=request.data.get('remark', ''))
        return success_response(data=WorkOrderSerializer(work_order).data, message='工单处理中')

    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        work_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        work_order.solution = serializer.validated_data.get('solution', '')
        work_order.cost = serializer.validated_data.get('cost')
        work_order.result_photos = serializer.validated_data.get('result_photos', [])
        work_order.updated_by = request.user
        work_order.save()

        WorkOrderService.change_status(work_order, 'completed', request.user,
                                       remark=serializer.validated_data.get('remark', ''))
        return success_response(data=WorkOrderSerializer(work_order).data, message='工单已完成')

    @action(detail=True, methods=['post'], url_path='verify')
    def verify(self, request, pk=None):
        work_order = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not serializer.validated_data.get('satisfied', True):
            WorkOrderService.change_status(work_order, 'rejected', request.user,
                                           remark=serializer.validated_data.get('remark', ''))
            return success_response(message='已驳回')

        work_order.verifier = request.user
        if serializer.validated_data.get('satisfaction'):
            work_order.satisfaction = serializer.validated_data['satisfaction']
        work_order.updated_by = request.user
        work_order.save()

        WorkOrderService.change_status(work_order, 'verified', request.user,
                                       remark=serializer.validated_data.get('remark', ''))
        return success_response(data=WorkOrderSerializer(work_order).data, message='验收通过')

    @action(detail=True, methods=['post'], url_path='close')
    def close(self, request, pk=None):
        work_order = self.get_object()
        WorkOrderService.change_status(work_order, 'closed', request.user,
                                       remark=request.data.get('remark', ''))
        return success_response(message='工单已关闭')

    @action(detail=True, methods=['get'], url_path='logs')
    def list_logs(self, request, pk=None):
        work_order = self.get_object()
        logs = work_order.logs.all()
        return success_response(data=WorkOrderLogSerializer(logs, many=True).data)

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        today = timezone.now().date()
        month_start = today.replace(day=1)

        stats = {
            'total': WorkOrder.objects.filter(is_deleted=False).count(),
            'pending': WorkOrder.objects.filter(status='pending').count(),
            'assigned': WorkOrder.objects.filter(status='assigned').count(),
            'in_progress': WorkOrder.objects.filter(status='in_progress').count(),
            'completed_today': WorkOrder.objects.filter(actual_end__date=today).count(),
            'completed_month': WorkOrder.objects.filter(actual_end__date__gte=month_start).count(),
            'by_priority': dict(WorkOrder.objects.values_list('priority').annotate(count=Count('id')).values_list('priority', 'count')),
            'by_type': dict(WorkOrder.objects.values_list('order_type').annotate(count=Count('id')).values_list('order_type', 'count')),
        }
        return success_response(data=stats)
