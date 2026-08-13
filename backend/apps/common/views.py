from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django_filters.rest_framework import DjangoFilterBackend

from .models import RegionModel, CommonConfig
from .pagination import StandardPagination


class RegionViewSet(viewsets.ModelViewSet):
    queryset = RegionModel.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['region_type', 'parent']
    search_fields = ['code', 'name']

    def get_serializer_class(self):
        from .serializers import RegionSerializer
        return RegionSerializer

    @action(detail=False, methods=['get'], url_path='tree')
    def tree(self, request):
        from django.db.models import Prefetch
        regions = RegionModel.objects.filter(parent__isnull=True).prefetch_related(
            Prefetch('children', queryset=RegionModel.objects.all())
        )
        serializer = self.get_serializer(regions, many=True)
        return Response({'code': 0, 'message': 'success', 'data': serializer.data})


class CommonConfigViewSet(viewsets.ModelViewSet):
    queryset = CommonConfig.objects.filter(is_deleted=False)
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['config_type']
    search_fields = ['config_key']
    permission_classes = [IsAdminUser]

    def get_serializer_class(self):
        from .serializers import CommonConfigSerializer
        return CommonConfigSerializer


class HealthCheckView(viewsets.ViewSet):
    permission_classes = []

    def list(self, request):
        import django.db
        from django.db import connections
        from django.db.utils import OperationalError

        db_status = 'ok'
        try:
            with connections['default'].cursor() as cursor:
                cursor.execute('SELECT 1')
        except OperationalError:
            db_status = 'error'

        return Response({
            'code': 0,
            'message': 'ok',
            'data': {
                'status': 'healthy',
                'database': db_status,
                'version': '1.0.0',
            }
        })
