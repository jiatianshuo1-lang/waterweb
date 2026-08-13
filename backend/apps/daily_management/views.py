from rest_framework import serializers
from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Count
from django.utils import timezone

from .models import Notice, Meeting, Asset, Document
from apps.common.pagination import StandardPagination
from apps.common.responses import success_response, created_response
from apps.common.exceptions import BusinessException


class NoticeSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = Notice
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'views_count']


class MeetingSerializer(serializers.ModelSerializer):
    host_name = serializers.CharField(source='host.real_name', read_only=True)
    participant_names = serializers.SerializerMethodField()

    class Meta:
        model = Meeting
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']

    def get_participant_names(self, obj):
        return [u.real_name or u.username for u in obj.participants.all()]


class AssetSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)
    responsible_name = serializers.CharField(source='responsible.real_name', read_only=True)

    class Meta:
        model = Asset
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at']


class DocumentSerializer(serializers.ModelSerializer):
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = Document
        fields = '__all__'
        read_only_fields = ['created_at', 'updated_at', 'downloads']


class NoticeViewSet(viewsets.ModelViewSet):
    queryset = Notice.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['notice_type', 'region', 'is_top', 'status']
    search_fields = ['title', 'summary']
    permission_classes = [IsAuthenticated]
    serializer_class = NoticeSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.action in ['list', 'retrieve']:
            queryset = queryset.filter(status='published')
        return queryset

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated:
            instance.views_count += 1
            instance.save(update_fields=['views_count'])
        return super().retrieve(request, *args, **kwargs)

    @action(detail=True, methods=['post'], url_path='publish')
    def publish(self, request, pk=None):
        notice = self.get_object()
        if notice.status != 'draft':
            raise BusinessException('只有草稿可以发布')
        notice.status = 'published'
        notice.published_at = timezone.now()
        notice.save()
        return success_response(message='已发布')


class MeetingViewSet(viewsets.ModelViewSet):
    queryset = Meeting.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['meeting_type', 'status']
    search_fields = ['title', 'location']
    permission_classes = [IsAuthenticated]
    serializer_class = MeetingSerializer

    @action(detail=True, methods=['post'], url_path='start')
    def start(self, request, pk=None):
        meeting = self.get_object()
        meeting.status = 'ongoing'
        meeting.actual_start = timezone.now()
        meeting.save()
        return success_response(message='会议开始')

    @action(detail=True, methods=['post'], url_path='end')
    def end(self, request, pk=None):
        meeting = self.get_object()
        meeting.status = 'completed'
        meeting.actual_end = timezone.now()
        meeting.save()
        return success_response(message='会议结束')


class AssetViewSet(viewsets.ModelViewSet):
    queryset = Asset.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['asset_type', 'region', 'status']
    search_fields = ['code', 'name', 'model']
    permission_classes = [IsAuthenticated]
    serializer_class = AssetSerializer

    @action(detail=False, methods=['get'], url_path='statistics')
    def statistics(self, request):
        return success_response(data={
            'total': Asset.objects.count(),
            'by_type': dict(Asset.objects.values_list('asset_type').annotate(count=Count('id')).values_list('asset_type', 'count')),
            'by_status': dict(Asset.objects.values_list('status').annotate(count=Count('id')).values_list('status', 'count')),
        })


class DocumentViewSet(viewsets.ModelViewSet):
    queryset = Document.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['doc_type', 'region', 'is_public']
    search_fields = ['title', 'description', 'tags']
    permission_classes = [IsAuthenticated]
    serializer_class = DocumentSerializer

    @action(detail=True, methods=['post'], url_path='download')
    def download(self, request, pk=None):
        doc = self.get_object()
        doc.downloads += 1
        doc.save(update_fields=['downloads'])
        return success_response(data={'url': doc.file_url})
