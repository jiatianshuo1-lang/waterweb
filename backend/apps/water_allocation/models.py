from django.db import models
from apps.common.models import BaseModel


class WaterSource(BaseModel):
    SOURCE_TYPES = [
        ('reservoir', '水库'),
        ('river', '河流'),
        ('groundwater', '地下水'),
        ('canal', '引水渠'),
        ('recycled', '再生水'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='水源编码')
    name = models.CharField(max_length=100, verbose_name='水源名称')
    source_type = models.CharField(max_length=20, choices=SOURCE_TYPES, verbose_name='水源类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属区域')
    capacity = models.FloatField(null=True, blank=True, verbose_name='总容量(万m³)')
    current_storage = models.FloatField(null=True, blank=True, verbose_name='当前蓄水量(万m³)')
    available = models.FloatField(null=True, blank=True, verbose_name='可用水量(万m³)')
    annual_supply = models.FloatField(null=True, blank=True, verbose_name='年供水量(万m³)')
    min_guaranteed = models.FloatField(null=True, blank=True, verbose_name='最低保障水位')
    description = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '水源'
        verbose_name_plural = '水源管理'
        ordering = ['code']


class WaterAllocation(BaseModel):
    STATUS = [
        ('draft', '草稿'),
        ('submitted', '已提交'),
        ('approved', '已审批'),
        ('rejected', '已驳回'),
        ('executing', '执行中'),
        ('completed', '已完成'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='分配方案编号')
    name = models.CharField(max_length=200, verbose_name='方案名称')
    allocation_type = models.CharField(max_length=30, default='yearly', choices=[
        ('yearly', '年度分配'), ('quarterly', '季度分配'), ('monthly', '月度分配'), ('emergency', '应急调度')
    ], verbose_name='分配类型')
    water_source = models.ForeignKey(WaterSource, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='水源')
    total_amount = models.FloatField(verbose_name='分配总量(万m³)')
    period_start = models.DateField(verbose_name='生效开始日期')
    period_end = models.DateField(verbose_name='生效结束日期')
    priority = models.IntegerField(default=5, verbose_name='优先级(1-10)')
    status = models.CharField(max_length=20, choices=STATUS, default='draft', verbose_name='状态')
    basis = models.TextField(blank=True, verbose_name='分配依据')
    remarks = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '水资源分配方案'
        verbose_name_plural = '水资源分配方案管理'
        ordering = ['-period_start']


class WaterAllocationDetail(BaseModel):
    allocation = models.ForeignKey(WaterAllocation, on_delete=models.CASCADE, related_name='details', verbose_name='分配方案')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='用水区域')
    water_user = models.CharField(max_length=200, verbose_name='用水户/部门')
    user_type = models.CharField(max_length=20, default='agriculture', choices=[
        ('agriculture', '农业'), ('industry', '工业'), ('domestic', '生活'), ('ecology', '生态')
    ], verbose_name='用水类型')
    allocated_amount = models.FloatField(verbose_name='分配水量(万m³)')
    used_amount = models.FloatField(default=0, verbose_name='已用水量(万m³)')
    surplus = models.FloatField(default=0, verbose_name='剩余水量(万m³)')
    ratio = models.FloatField(default=0, verbose_name='分配比例(%)')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '分配明细'
        verbose_name_plural = '分配明细'
        ordering = ['-allocated_amount']


class WaterTransfer(BaseModel):
    TRANSFER_TYPES = [
        ('inter_region', '区域间调水'),
        ('inter_source', '水源间调水'),
        ('emergency', '应急调水'),
    ]

    STATUS = [
        ('planned', '已计划'),
        ('approved', '已批准'),
        ('executing', '执行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='调水编号')
    transfer_type = models.CharField(max_length=20, choices=TRANSFER_TYPES, verbose_name='调水类型')
    from_region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                                     related_name='transfer_from', verbose_name='调出区域')
    to_region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                                   related_name='transfer_to', verbose_name='调入区域')
    amount = models.FloatField(verbose_name='调水量(万m³)')
    reason = models.TextField(verbose_name='调水原因')
    planned_start = models.DateTimeField(verbose_name='计划开始时间')
    planned_end = models.DateTimeField(verbose_name='计划结束时间')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    status = models.CharField(max_length=20, choices=STATUS, default='planned', verbose_name='状态')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='执行操作人')

    class Meta:
        verbose_name = '调水调度'
        verbose_name_plural = '调水调度管理'
        ordering = ['-planned_start']
