from django.db import models
from apps.common.models import BaseModel


class IrrigationDevice(BaseModel):
    DEVICE_TYPES = [
        ('gate', '闸门'),
        ('pump', '水泵'),
        ('valve', '阀门'),
        ('drip_control', '滴灌控制器'),
        ('sprinkler', '喷灌设备'),
        ('sensor', '传感器组'),
    ]

    STATUS = [
        ('online', '在线'),
        ('offline', '离线'),
        ('running', '运行中'),
        ('stopped', '已停止'),
        ('fault', '故障'),
        ('maintenance', '维护中'),
    ]

    control_mode = [
        ('manual', '手动'),
        ('auto', '自动'),
        ('smart', '智能'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='设备编码')
    name = models.CharField(max_length=100, verbose_name='设备名称')
    device_type = models.CharField(max_length=20, choices=DEVICE_TYPES, verbose_name='设备类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='irrigation_devices', verbose_name='所属区域')
    location = models.CharField(max_length=200, blank=True, verbose_name='安装位置')
    device_model = models.CharField(max_length=100, blank=True, verbose_name='设备型号')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='制造商')
    install_date = models.DateField(null=True, blank=True, verbose_name='安装日期')
    control_mode = models.CharField(max_length=10, choices=control_mode, default='auto', verbose_name='控制模式')
    status = models.CharField(max_length=20, choices=STATUS, default='offline', verbose_name='运行状态')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    params = models.JSONField(default=dict, verbose_name='设备参数')
    last_heartbeat = models.DateTimeField(null=True, blank=True, verbose_name='最后心跳')
    description = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '灌溉设备'
        verbose_name_plural = '灌溉设备管理'
        ordering = ['code']

    def __str__(self):
        return f'{self.code} - {self.name}'


class IrrigationLog(BaseModel):
    device = models.ForeignKey(IrrigationDevice, on_delete=models.CASCADE, related_name='logs', verbose_name='设备')
    action = models.CharField(max_length=50, verbose_name='操作动作')
    value = models.CharField(max_length=255, blank=True, verbose_name='操作值')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    operate_time = models.DateTimeField(verbose_name='操作时间')
    result = models.CharField(max_length=20, default='success', choices=[
        ('success', '成功'), ('failed', '失败'), ('timeout', '超时')
    ], verbose_name='执行结果')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '灌溉操作日志'
        verbose_name_plural = '灌溉操作日志'
        ordering = ['-operate_time']


class IrrigationPlan(BaseModel):
    PLAN_TYPES = [
        ('schedule', '定时灌溉'),
        ('trigger', '触发灌溉'),
        ('manual', '手动灌溉'),
        ('smart', '智能灌溉'),
    ]

    STATUS = [
        ('draft', '草稿'),
        ('active', '执行中'),
        ('paused', '已暂停'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='计划编号')
    name = models.CharField(max_length=200, verbose_name='计划名称')
    plan_type = models.CharField(max_length=20, choices=PLAN_TYPES, default='smart', verbose_name='计划类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='irrigation_plans', verbose_name='适用区域')
    devices = models.ManyToManyField(IrrigationDevice, blank=True, verbose_name='控制设备')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    duration = models.IntegerField(null=True, blank=True, verbose_name='灌溉时长(分钟)')
    flow_rate = models.FloatField(null=True, blank=True, verbose_name='目标流量(m³/s)')
    total_water = models.FloatField(null=True, blank=True, verbose_name='目标水量(m³)')
    trigger_conditions = models.JSONField(default=list, verbose_name='触发条件')
    control_params = models.JSONField(default=dict, verbose_name='控制参数')
    status = models.CharField(max_length=20, choices=STATUS, default='draft', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='说明')

    class Meta:
        verbose_name = '灌溉计划'
        verbose_name_plural = '灌溉计划管理'
        ordering = ['-start_time']


class IrrigationRecord(BaseModel):
    plan = models.ForeignKey(IrrigationPlan, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联计划')
    device = models.ForeignKey(IrrigationDevice, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='设备')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='区域')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(null=True, blank=True, verbose_name='结束时间')
    duration = models.FloatField(null=True, blank=True, verbose_name='灌溉时长(分钟)')
    water_used = models.FloatField(null=True, blank=True, verbose_name='用水量(m³)')
    energy_used = models.FloatField(null=True, blank=True, verbose_name='用电量(kWh)')
    area_irrigated = models.FloatField(null=True, blank=True, verbose_name='灌溉面积(亩)')
    avg_flow_rate = models.FloatField(null=True, blank=True, verbose_name='平均流量(m³/s)')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '灌溉记录'
        verbose_name_plural = '灌溉记录'
        ordering = ['-start_time']
