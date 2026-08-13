from django.db import models
from apps.common.models import BaseModel


class Notice(BaseModel):
    NOTICE_TYPES = [
        ('announcement', '公告'),
        ('notice', '通知'),
        ('policy', '政策文件'),
        ('emergency', '紧急通知'),
    ]

    STATUS = [
        ('draft', '草稿'),
        ('published', '已发布'),
        ('offline', '已下架'),
    ]

    title = models.CharField(max_length=200, verbose_name='标题')
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPES, default='notice', verbose_name='类型')
    content = models.TextField(verbose_name='内容')
    summary = models.CharField(max_length=500, blank=True, verbose_name='摘要')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='发布区域')
    is_top = models.BooleanField(default=False, verbose_name='是否置顶')
    status = models.CharField(max_length=20, choices=STATUS, default='draft', verbose_name='状态')
    published_at = models.DateTimeField(null=True, blank=True, verbose_name='发布时间')
    views_count = models.IntegerField(default=0, verbose_name='浏览量')
    attachments = models.JSONField(default=list, verbose_name='附件')

    class Meta:
        verbose_name = '通知公告'
        verbose_name_plural = '通知公告管理'
        ordering = ['-is_top', '-published_at', '-created_at']


class Meeting(BaseModel):
    MEETING_TYPES = [
        ('regular', '例会'),
        ('emergency', '紧急会议'),
        ('training', '培训'),
        ('other', '其他'),
    ]

    STATUS = [
        ('planned', '已安排'),
        ('ongoing', '进行中'),
        ('completed', '已完成'),
        ('cancelled', '已取消'),
    ]

    title = models.CharField(max_length=200, verbose_name='会议主题')
    meeting_type = models.CharField(max_length=20, choices=MEETING_TYPES, default='regular', verbose_name='会议类型')
    start_time = models.DateTimeField(verbose_name='开始时间')
    end_time = models.DateTimeField(verbose_name='结束时间')
    location = models.CharField(max_length=200, verbose_name='会议地点')
    host = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                            related_name='hosted_meetings', verbose_name='主持人')
    participants = models.ManyToManyField('users.User', blank=True, related_name='participated_meetings', verbose_name='参会人员')
    status = models.CharField(max_length=20, choices=STATUS, default='planned', verbose_name='状态')
    agenda = models.TextField(blank=True, verbose_name='会议议程')
    minutes = models.TextField(blank=True, verbose_name='会议纪要')
    attachments = models.JSONField(default=list, verbose_name='附件')

    class Meta:
        verbose_name = '会议管理'
        verbose_name_plural = '会议管理'
        ordering = ['-start_time']


class Asset(BaseModel):
    ASSET_TYPES = [
        ('water_pump', '水泵'),
        ('gate', '闸门'),
        ('pipe', '管道'),
        ('meter', '计量设备'),
        ('sensor', '传感器'),
        ('office', '办公设备'),
        ('vehicle', '车辆'),
        ('other', '其他'),
    ]

    STATUS = [
        ('working', '正常使用'),
        ('maintenance', '维修中'),
        ('scrapped', '已报废'),
        ('storage', '库存'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='资产编号')
    name = models.CharField(max_length=200, verbose_name='资产名称')
    asset_type = models.CharField(max_length=20, choices=ASSET_TYPES, verbose_name='资产类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属区域')
    model = models.CharField(max_length=100, blank=True, verbose_name='规格型号')
    manufacturer = models.CharField(max_length=100, blank=True, verbose_name='制造商')
    purchase_date = models.DateField(null=True, blank=True, verbose_name='购置日期')
    purchase_price = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, verbose_name='购置价格')
    useful_life = models.IntegerField(null=True, blank=True, verbose_name='使用年限(年)')
    status = models.CharField(max_length=20, choices=STATUS, default='working', verbose_name='使用状态')
    responsible = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='责任人')
    description = models.TextField(blank=True, verbose_name='备注')
    photos = models.JSONField(default=list, verbose_name='照片')

    class Meta:
        verbose_name = '固定资产'
        verbose_name_plural = '固定资产管理'
        ordering = ['code']


class Document(BaseModel):
    DOC_TYPES = [
        ('contract', '合同'),
        ('report', '报告'),
        ('drawing', '图纸'),
        ('policy', '制度文件'),
        ('manual', '操作手册'),
        ('other', '其他'),
    ]

    title = models.CharField(max_length=200, verbose_name='文档标题')
    doc_type = models.CharField(max_length=20, choices=DOC_TYPES, default='other', verbose_name='文档类型')
    file_url = models.CharField(max_length=500, verbose_name='文件URL')
    file_name = models.CharField(max_length=200, verbose_name='原始文件名')
    file_size = models.BigIntegerField(verbose_name='文件大小(字节)')
    file_ext = models.CharField(max_length=20, blank=True, verbose_name='文件扩展名')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='关联区域')
    description = models.TextField(blank=True, verbose_name='描述')
    tags = models.JSONField(default=list, verbose_name='标签')
    is_public = models.BooleanField(default=True, verbose_name='是否公开')
    downloads = models.IntegerField(default=0, verbose_name='下载次数')

    class Meta:
        verbose_name = '文档资料'
        verbose_name_plural = '文档资料管理'
        ordering = ['-created_at']
