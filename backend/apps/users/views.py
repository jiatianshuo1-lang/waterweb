import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q

from .models import User, OperationLog
from .serializers import (
    UserSerializer, UserCreateSerializer, UserUpdateSerializer,
    PasswordChangeSerializer, LoginSerializer, RegisterSerializer,
    CurrentUserSerializer, OperationLogSerializer
)
from apps.common.pagination import StandardPagination
from apps.common.exceptions import BusinessException, NotFoundException, ValidationException
from apps.common.responses import success_response, created_response

logger = logging.getLogger(__name__)


class AuthViewSet(viewsets.ViewSet):
    permission_classes = [AllowAny]

    @action(detail=False, methods=['post'], url_path='login')
    def login(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        user = data['_user']

        OperationLog.objects.create(
            user=user,
            log_type='login',
            module='auth',
            action='用户登录',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            status='success',
        )
        user.last_login_ip = request.META.get('REMOTE_ADDR')
        user.save(update_fields=['last_login_ip'])

        return success_response(data={
            'refresh': data['refresh'],
            'access': data['access'],
            'user': data['user'],
        }, message='登录成功')

    @action(detail=False, methods=['post'], url_path='register')
    def register(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        OperationLog.objects.create(
            user=user,
            log_type='create',
            module='auth',
            action='用户注册',
            target=f'用户: {user.username}',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:500],
            status='success',
        )

        login_data = LoginSerializer(data=request.data)
        login_data.is_valid(raise_exception=True)

        return success_response(data={
            'refresh': login_data.validated_data['refresh'],
            'access': login_data.validated_data['access'],
            'user': login_data.validated_data['user'],
        }, message='注册成功', status_code=201)

    @action(detail=False, methods=['get'], url_path='me')
    def me(self, request):
        serializer = CurrentUserSerializer(request.user)
        return success_response(data=serializer.data)

    @action(detail=False, methods=['post'], url_path='change-password', permission_classes=[IsAuthenticated])
    def change_password(self, request):
        serializer = PasswordChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        if not request.user.check_password(serializer.validated_data['old_password']):
            raise ValidationException('原密码错误')

        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()

        OperationLog.objects.create(
            user=request.user,
            log_type='update',
            module='auth',
            action='修改密码',
            ip_address=request.META.get('REMOTE_ADDR'),
            status='success',
        )
        return success_response(message='密码修改成功')

    @action(detail=False, methods=['post'], url_path='logout', permission_classes=[IsAuthenticated])
    def logout(self, request):
        try:
            from rest_framework_simplejwt.tokens import RefreshToken
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        OperationLog.objects.create(
            user=request.user,
            log_type='logout',
            module='auth',
            action='用户登出',
            ip_address=request.META.get('REMOTE_ADDR'),
            status='success',
        )
        return success_response(message='登出成功')

    @action(detail=False, methods=['post'], url_path='refresh')
    def refresh(self, request):
        from rest_framework_simplejwt.serializers import TokenRefreshSerializer
        serializer = TokenRefreshSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(data=serializer.validated_data, message='刷新成功')

    @action(detail=False, methods=['post'], url_path='verify')
    def verify(self, request):
        from rest_framework_simplejwt.serializers import TokenVerifySerializer
        serializer = TokenVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return success_response(message='token有效')


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['role', 'region', 'is_active', 'department']
    search_fields = ['username', 'real_name', 'phone', 'email']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

    def get_permissions(self):
        if self.action in ['list', 'create', 'destroy']:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role != 'super_admin':
            queryset = queryset.exclude(role='super_admin')
        return queryset

    def perform_create(self, serializer):
        user = serializer.save()
        OperationLog.objects.create(
            user=self.request.user,
            log_type='create',
            module='user',
            action='创建用户',
            target=f'用户: {user.username}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            status='success',
        )

    def perform_destroy(self, instance):
        OperationLog.objects.create(
            user=self.request.user,
            log_type='delete',
            module='user',
            action='删除用户',
            target=f'用户: {instance.username}',
            ip_address=self.request.META.get('REMOTE_ADDR'),
            status='success',
        )
        instance.delete()


class OperationLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = OperationLog.objects.all()
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['log_type', 'module', 'status', 'user']
    search_fields = ['action', 'target']
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        return OperationLogSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        if self.request.user.role not in ['super_admin', 'admin']:
            queryset = queryset.filter(user=self.request.user)
        return queryset
