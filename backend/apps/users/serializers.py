from rest_framework import serializers
from django.contrib.auth import authenticate
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, OperationLog


class UserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(read_only=True)
    region_name = serializers.CharField(source='region.name', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'real_name', 'role', 'role_display', 'phone', 'email',
            'avatar', 'region', 'region_name', 'department', 'position',
            'is_active', 'last_login', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'last_login', 'created_at', 'updated_at']


class UserCreateSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'password', 'real_name', 'role', 'phone', 'email',
                  'region', 'department', 'position', 'is_active']

    def create(self, validated_data):
        password = validated_data.pop('password')
        user = User.objects.create(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['real_name', 'role', 'phone', 'email', 'region', 'department', 'position', 'is_active']


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(required=True, min_length=3, max_length=32)
    password = serializers.CharField(required=True, min_length=8, max_length=128)
    real_name = serializers.CharField(required=True, max_length=50)
    phone = serializers.CharField(required=False, max_length=20, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, max_length=100, allow_blank=True)
    position = serializers.CharField(required=False, max_length=50, allow_blank=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError('该用户名已被注册')
        return value

    def create(self, validated_data):
        from .models import Role
        password = validated_data.pop('password')
        user = User.objects.create(
            role=Role.VIEWER,
            is_active=True,
            **validated_data,
        )
        user.set_password(password)
        user.save()
        return user


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, min_length=8)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)

        if not user:
            raise serializers.ValidationError('用户名或密码错误')
        if not user.is_active:
            raise serializers.ValidationError('账号已被禁用')

        refresh = RefreshToken.for_user(user)

        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': UserSerializer(user).data,
            '_user': user,
        }


class CurrentUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(read_only=True)
    permissions = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'username', 'real_name', 'role', 'role_display', 'phone', 'email',
                  'avatar', 'department', 'position', 'permissions', 'region']

    def get_permissions(self, obj):
        if obj.role == 'super_admin':
            return ['*']
        return [obj.role]


class OperationLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.real_name', read_only=True)

    class Meta:
        model = OperationLog
        fields = ['id', 'user', 'user_name', 'log_type', 'module', 'action', 'target',
                  'ip_address', 'user_agent', 'detail', 'status', 'duration', 'created_at']
