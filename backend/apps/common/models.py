from django.db import models
import uuid


class BaseModel(models.Model):
    id = models.BigAutoField(primary_key=True)
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    created_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_created', verbose_name='创建人'
    )
    updated_by = models.ForeignKey(
        'users.User', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='%(class)s_updated', verbose_name='更新人'
    )
    is_deleted = models.BooleanField(default=False, verbose_name='软删除')

    class Meta:
        abstract = True


class RegionModel(models.Model):
    REGION_TYPES = [
        ('area', '灌区'),
        ('branch', '干支渠'),
        ('canal', '斗农渠'),
        ('section', '渠段'),
        ('pump_station', '泵站'),
        ('gate', '闸门'),
        ('reservoir', '水库'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='编码')
    name = models.CharField(max_length=100, verbose_name='名称')
    region_type = models.CharField(max_length=20, choices=REGION_TYPES, verbose_name='区域类型')
    parent = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='children', verbose_name='上级区域'
    )
    geometry = models.JSONField(null=True, blank=True, verbose_name='地理坐标')
    description = models.TextField(blank=True, verbose_name='描述')
    sort_order = models.IntegerField(default=0, verbose_name='排序')

    class Meta:
        verbose_name = '灌区区域'
        verbose_name_plural = '灌区区域管理'
        ordering = ['sort_order', 'code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class CommonConfig(BaseModel):
    CONFIG_TYPES = [
        ('system', '系统配置'),
        ('water', '水文配置'),
        ('device', '设备配置'),
        ('notification', '通知配置'),
        ('ai', 'AI配置'),
    ]

    config_type = models.CharField(max_length=20, choices=CONFIG_TYPES, verbose_name='配置类型')
    config_key = models.CharField(max_length=100, verbose_name='配置键')
    config_value = models.JSONField(verbose_name='配置值')
    description = models.CharField(max_length=255, blank=True, verbose_name='说明')

    class Meta:
        verbose_name = '公共配置'
        verbose_name_plural = '公共配置管理'
        unique_together = [('config_type', 'config_key')]

    def __str__(self):
        return f'{self.config_type}: {self.config_key}'

    @classmethod
    def get_config(cls, config_type, config_key, default=None):
        try:
            config = cls.objects.get(config_type=config_type, config_key=config_key)
            return config.config_value
        except cls.DoesNotExist:
            return default
