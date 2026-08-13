from django.db import models
from apps.common.models import BaseModel


class MeasureStation(BaseModel):
    STATION_TYPES = [
        ('flow', '流量站'),
        ('water_level', '水位站'),
        ('quality', '水质站'),
        ('multifunction', '多功能站'),
    ]

    COMMUNICATION = [
        ('gprs', 'GPRS'),
        ('4g', '4G'),
        ('lora', 'LoRa'),
        ('ethernet', '以太网'),
        ('manual', '人工录入'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='测站编码')
    name = models.CharField(max_length=100, verbose_name='测站名称')
    station_type = models.CharField(max_length=20, choices=STATION_TYPES, verbose_name='测站类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='measure_stations', verbose_name='所属区域')
    location = models.CharField(max_length=200, blank=True, verbose_name='具体位置')
    longitude = models.FloatField(null=True, blank=True, verbose_name='经度')
    latitude = models.FloatField(null=True, blank=True, verbose_name='纬度')
    elevation = models.FloatField(null=True, blank=True, verbose_name='海拔(m)')
    communication = models.CharField(max_length=20, choices=COMMUNICATION, default='4g', verbose_name='通讯方式')
    device_code = models.CharField(max_length=50, blank=True, verbose_name='设备编号')
    device_model = models.CharField(max_length=100, blank=True, verbose_name='设备型号')
    install_date = models.DateField(null=True, blank=True, verbose_name='安装日期')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    last_data_time = models.DateTimeField(null=True, blank=True, verbose_name='最后数据时间')
    status = models.CharField(max_length=20, default='offline', choices=[
        ('online', '在线'), ('offline', '离线'), ('fault', '故障'), ('maintenance', '维护中')
    ], verbose_name='运行状态')
    description = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '量测水测站'
        verbose_name_plural = '量测水测站管理'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class WaterMeasurement(BaseModel):
    station = models.ForeignKey(MeasureStation, on_delete=models.CASCADE, related_name='measurements', verbose_name='测站')
    measure_time = models.DateTimeField(verbose_name='测量时间')

    flow_rate = models.FloatField(null=True, blank=True, verbose_name='瞬时流量(m³/s)')
    water_level = models.FloatField(null=True, blank=True, verbose_name='水位(m)')
    total_flow = models.FloatField(null=True, blank=True, verbose_name='累计流量(m³)')
    velocity = models.FloatField(null=True, blank=True, verbose_name='流速(m/s)')
    area = models.FloatField(null=True, blank=True, verbose_name='过水面积(m²)')
    water_quality = models.FloatField(null=True, blank=True, verbose_name='水质等级')
    temperature = models.FloatField(null=True, blank=True, verbose_name='水温(℃)')
    ph = models.FloatField(null=True, blank=True, verbose_name='pH值')
    conductivity = models.FloatField(null=True, blank=True, verbose_name='电导率(μS/cm)')
    turbidity = models.FloatField(null=True, blank=True, verbose_name='浊度(NTU)')

    source = models.CharField(max_length=20, default='auto', choices=[
        ('auto', '自动采集'), ('manual', '人工录入'), ('import', '批量导入')
    ], verbose_name='数据来源')
    is_abnormal = models.BooleanField(default=False, verbose_name='是否异常')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '量测水数据'
        verbose_name_plural = '量测水数据'
        ordering = ['-measure_time']
        indexes = [
            models.Index(fields=['station', '-measure_time']),
            models.Index(fields=['-measure_time']),
        ]

    def __str__(self):
        return f'{self.station.code} @ {self.measure_time}'


class WaterAlarm(BaseModel):
    ALARM_TYPES = [
        ('flow_high', '流量过高'),
        ('flow_low', '流量过低'),
        ('level_high', '水位过高'),
        ('level_low', '水位过低'),
        ('quality_abnormal', '水质异常'),
        ('station_offline', '测站离线'),
        ('device_fault', '设备故障'),
    ]

    LEVELS = [
        ('info', '提示'),
        ('warning', '警告'),
        ('critical', '严重'),
        ('emergency', '紧急'),
    ]

    station = models.ForeignKey(MeasureStation, on_delete=models.CASCADE, related_name='alarms', verbose_name='测站')
    alarm_type = models.CharField(max_length=30, choices=ALARM_TYPES, verbose_name='告警类型')
    level = models.CharField(max_length=20, choices=LEVELS, default='warning', verbose_name='告警级别')
    title = models.CharField(max_length=200, verbose_name='告警标题')
    message = models.TextField(verbose_name='告警描述')
    threshold = models.JSONField(null=True, blank=True, verbose_name='阈值配置')
    current_value = models.FloatField(null=True, blank=True, verbose_name='当前值')
    triggered_at = models.DateTimeField(verbose_name='触发时间')
    is_resolved = models.BooleanField(default=False, verbose_name='是否已处理')
    resolved_at = models.DateTimeField(null=True, blank=True, verbose_name='处理时间')
    resolved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='处理人')
    resolution = models.TextField(blank=True, verbose_name='处理说明')

    class Meta:
        verbose_name = '水量告警'
        verbose_name_plural = '水量告警管理'
        ordering = ['-triggered_at']
