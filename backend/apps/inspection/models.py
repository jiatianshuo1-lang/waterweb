from django.db import models
from apps.common.models import BaseModel


class Inspection(BaseModel):
    STATUS_CHOICES = [
        ('pending', '待处理'),
        ('in_progress', '进行中'),
        ('completed', '已完成'),
        ('overdue', '已逾期'),
        ('cancelled', '已取消'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    TEMPLATE_TYPES = [
        ('daily', '日常巡检'),
        ('weekly', '周巡检'),
        ('monthly', '月巡检'),
        ('special', '专项巡检'),
        ('emergency', '应急巡检'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='巡检编号')
    title = models.CharField(max_length=200, verbose_name='巡检标题')
    template_type = models.CharField(max_length=20, choices=TEMPLATE_TYPES, default='daily', verbose_name='巡检类型')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                               related_name='inspections', verbose_name='巡检区域')
    inspectors = models.ManyToManyField('users.User', related_name='assigned_inspections', verbose_name='巡检人员')
    planned_start = models.DateTimeField(verbose_name='计划开始时间')
    planned_end = models.DateTimeField(verbose_name='计划结束时间')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='实际结束时间')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')
    description = models.TextField(blank=True, verbose_name='巡检说明')
    checklist = models.JSONField(default=list, verbose_name='巡检清单')
    photos = models.JSONField(default=list, verbose_name='照片')
    report = models.TextField(blank=True, verbose_name='巡检报告')
    result = models.CharField(max_length=20, choices=[
        ('normal', '正常'), ('abnormal', '异常'), ('need_repair', '需维修')
    ], null=True, blank=True, verbose_name='巡检结果')

    class Meta:
        verbose_name = '巡检任务'
        verbose_name_plural = '巡检任务管理'
        ordering = ['-planned_start', '-created_at']

    def __str__(self):
        return f'{self.code} - {self.title}'


class WorkOrder(BaseModel):
    STATUS_CHOICES = [
        ('pending', '待受理'),
        ('assigned', '已派单'),
        ('in_progress', '处理中'),
        ('completed', '已完成'),
        ('verified', '已验收'),
        ('closed', '已关闭'),
        ('rejected', '已驳回'),
    ]

    PRIORITY_CHOICES = [
        ('low', '低'),
        ('medium', '中'),
        ('high', '高'),
        ('urgent', '紧急'),
    ]

    TYPES = [
        ('inspection_issue', '巡检发现'),
        ('user_report', '用户上报'),
        ('device_fault', '设备故障'),
        ('routine_maintenance', '日常维护'),
        ('emergency', '应急处置'),
        ('other', '其他'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='工单编号')
    title = models.CharField(max_length=200, verbose_name='工单标题')
    order_type = models.CharField(max_length=30, choices=TYPES, default='other', verbose_name='工单类型')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium', verbose_name='优先级')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending', verbose_name='状态')

    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='work_orders', verbose_name='关联区域')
    inspection = models.ForeignKey(Inspection, on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='work_orders', verbose_name='关联巡检')

    reporter = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='reported_orders', verbose_name='上报人')
    assignee = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='assigned_orders', verbose_name='处理人')
    verifier = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                  related_name='verified_orders', verbose_name='验收人')

    description = models.TextField(verbose_name='问题描述')
    location = models.CharField(max_length=200, blank=True, verbose_name='具体位置')
    contact_info = models.CharField(max_length=100, blank=True, verbose_name='联系方式')
    photos = models.JSONField(default=list, verbose_name='问题照片')

    planned_start = models.DateTimeField(null=True, blank=True, verbose_name='计划开始时间')
    planned_end = models.DateTimeField(null=True, blank=True, verbose_name='计划完成时间')
    actual_start = models.DateTimeField(null=True, blank=True, verbose_name='实际开始时间')
    actual_end = models.DateTimeField(null=True, blank=True, verbose_name='实际完成时间')

    solution = models.TextField(blank=True, verbose_name='解决方案')
    cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='费用')
    result_photos = models.JSONField(default=list, verbose_name='处理后照片')
    satisfaction = models.IntegerField(null=True, blank=True, verbose_name='满意度(1-5)')

    class Meta:
        verbose_name = '工单'
        verbose_name_plural = '工单管理'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.code} - {self.title}'


class WorkOrderLog(BaseModel):
    ACTIONS = [
        ('create', '创建'),
        ('assign', '派单'),
        ('start', '开始处理'),
        ('update', '更新'),
        ('complete', '完成处理'),
        ('verify', '验收通过'),
        ('reject', '驳回'),
        ('close', '关闭'),
        ('comment', '备注'),
    ]

    work_order = models.ForeignKey(WorkOrder, on_delete=models.CASCADE, related_name='logs', verbose_name='工单')
    action = models.CharField(max_length=20, choices=ACTIONS, verbose_name='操作')
    from_status = models.CharField(max_length=20, blank=True, verbose_name='原状态')
    to_status = models.CharField(max_length=20, blank=True, verbose_name='新状态')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    remark = models.TextField(blank=True, verbose_name='备注')
    attachments = models.JSONField(default=list, verbose_name='附件')

    class Meta:
        verbose_name = '工单日志'
        verbose_name_plural = '工单日志'
        ordering = ['-created_at']


class InspectionRecord(BaseModel):
    inspection = models.ForeignKey(Inspection, on_delete=models.CASCADE, related_name='records', verbose_name='巡检')
    item_name = models.CharField(max_length=200, verbose_name='巡检项')
    item_type = models.CharField(max_length=50, blank=True, verbose_name='巡检项类型')
    result = models.CharField(max_length=20, choices=[
        ('normal', '正常'), ('abnormal', '异常'), ('skip', '跳过')
    ], verbose_name='检查结果')
    value = models.CharField(max_length=255, blank=True, verbose_name='检查值')
    standard = models.CharField(max_length=255, blank=True, verbose_name='标准值')
    remark = models.TextField(blank=True, verbose_name='备注')
    photos = models.JSONField(default=list, verbose_name='照片')
    inspector = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='检查人')

    class Meta:
        verbose_name = '巡检记录'
        verbose_name_plural = '巡检记录'
        ordering = ['id']
