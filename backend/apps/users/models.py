from django.db import models
from django.contrib.auth.models import AbstractUser, BaseUserManager


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, password, **extra_fields):
        if not username:
            raise ValueError('用户名不能为空')
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, password, **extra_fields)

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('超级用户必须设置 is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('超级用户必须设置 is_superuser=True')

        return self._create_user(username, password, **extra_fields)


class Role(models.TextChoices):
    SUPER_ADMIN = 'super_admin', '超级管理员'
    ADMIN = 'admin', '系统管理员'
    MANAGER = 'manager', '灌区负责人'
    INSPECTOR = 'inspector', '巡检员'
    WORKER = 'worker', '运维人员'
    VIEWER = 'viewer', '只读用户'


class User(AbstractUser):
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    real_name = models.CharField(max_length=50, verbose_name='真实姓名')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.VIEWER, verbose_name='角色')
    phone = models.CharField(max_length=20, blank=True, verbose_name='手机号')
    email = models.EmailField(blank=True, verbose_name='邮箱')
    avatar = models.CharField(max_length=500, blank=True, verbose_name='头像URL')
    region = models.ForeignKey(
        'common.RegionModel', on_delete=models.SET_NULL,
        null=True, blank=True, related_name='users', verbose_name='所属区域'
    )
    department = models.CharField(max_length=100, blank=True, verbose_name='部门')
    position = models.CharField(max_length=50, blank=True, verbose_name='职位')

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    last_login_ip = models.GenericIPAddressField(null=True, blank=True, verbose_name='最后登录IP')

    objects = UserManager()

    class Meta:
        verbose_name = '用户'
        verbose_name_plural = '用户管理'
        ordering = ['-date_joined']

    def __str__(self):
        return self.real_name or self.username

    @property
    def role_display(self):
        return self.get_role_display()


class OperationLog(models.Model):
    LOG_TYPES = [
        ('login', '登录'),
        ('logout', '登出'),
        ('create', '创建'),
        ('update', '更新'),
        ('delete', '删除'),
        ('export', '导出'),
        ('other', '其他'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    log_type = models.CharField(max_length=20, choices=LOG_TYPES, verbose_name='日志类型')
    module = models.CharField(max_length=50, verbose_name='模块')
    action = models.CharField(max_length=100, verbose_name='操作')
    target = models.CharField(max_length=255, blank=True, verbose_name='操作对象')
    ip_address = models.GenericIPAddressField(null=True, blank=True, verbose_name='IP地址')
    user_agent = models.CharField(max_length=500, blank=True, verbose_name='浏览器标识')
    detail = models.JSONField(null=True, blank=True, verbose_name='详情')
    status = models.CharField(max_length=10, default='success', choices=[('success', '成功'), ('failed', '失败')], verbose_name='状态')
    duration = models.FloatField(null=True, blank=True, verbose_name='耗时(秒)')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='操作时间')

    class Meta:
        verbose_name = '操作日志'
        verbose_name_plural = '操作日志管理'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at']),
            models.Index(fields=['module', '-created_at']),
            models.Index(fields=['log_type']),
        ]
