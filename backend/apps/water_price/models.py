from django.db import models
from apps.common.models import BaseModel


class WaterPricePolicy(BaseModel):
    POLICY_TYPES = [
        ('domestic', '居民生活用水'),
        ('agriculture', '农业用水'),
        ('industry', '工业用水'),
        ('commercial', '商业用水'),
        ('special', '特种用水'),
    ]

    PRICING_MODES = [
        ('flat', '单一水价'),
        ('阶梯', '阶梯水价'),
        ('seasonal', '季节性水价'),
        ('comprehensive', '综合计价'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='政策编号')
    name = models.CharField(max_length=200, verbose_name='政策名称')
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPES, verbose_name='用水类型')
    pricing_mode = models.CharField(max_length=20, choices=PRICING_MODES, default='flat', verbose_name='计价模式')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='适用区域')
    start_date = models.DateField(verbose_name='生效日期')
    end_date = models.DateField(null=True, blank=True, verbose_name='失效日期')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    base_price = models.DecimalField(max_digits=8, decimal_places=4, verbose_name='基础水价(元/m³)')
    tiers = models.JSONField(default=list, verbose_name='阶梯价配置')
    subsidies = models.JSONField(default=list, verbose_name='补贴配置')
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0, verbose_name='税率(%)')
    description = models.TextField(blank=True, verbose_name='政策说明')

    class Meta:
        verbose_name = '水价政策'
        verbose_name_plural = '水价政策管理'
        ordering = ['-start_date']


class WaterUser(BaseModel):
    USER_TYPES = [
        ('agriculture', '农业用水户'),
        ('industrial', '工业用水户'),
        ('commercial', '商业用水户'),
        ('domestic', '居民用户'),
        ('public', '公共设施'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='用户编号')
    name = models.CharField(max_length=200, verbose_name='用户名称')
    user_type = models.CharField(max_length=20, choices=USER_TYPES, verbose_name='用户类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属区域')
    contact_person = models.CharField(max_length=50, blank=True, verbose_name='联系人')
    contact_phone = models.CharField(max_length=20, blank=True, verbose_name='联系电话')
    address = models.CharField(max_length=300, blank=True, verbose_name='地址')
    water_meter = models.CharField(max_length=50, blank=True, verbose_name='水表编号')
    policy = models.ForeignKey(WaterPricePolicy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='适用水价政策')
    contract_info = models.JSONField(default=dict, verbose_name='合同信息')
    is_active = models.BooleanField(default=True, verbose_name='是否正常')

    class Meta:
        verbose_name = '用水户'
        verbose_name_plural = '用水户管理'
        ordering = ['code']


class WaterBill(BaseModel):
    STATUS = [
        ('pending', '待缴费'),
        ('partial', '部分缴费'),
        ('paid', '已缴费'),
        ('overdue', '已逾期'),
        ('waived', '已减免'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='账单编号')
    user = models.ForeignKey(WaterUser, on_delete=models.CASCADE, related_name='bills', verbose_name='用水户')
    policy = models.ForeignKey(WaterPricePolicy, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='水价政策')
    billing_period_start = models.DateField(verbose_name='计费期开始')
    billing_period_end = models.DateField(verbose_name='计费期结束')
    previous_reading = models.FloatField(verbose_name='上次读数')
    current_reading = models.FloatField(verbose_name='本次读数')
    usage = models.FloatField(verbose_name='用水量(m³)')
    base_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='基础水费')
    tier_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='阶梯水费')
    tax_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='税费')
    subsidy = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='补贴金额')
    total_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='应缴总额')
    paid_fee = models.DecimalField(max_digits=12, decimal_places=2, default=0, verbose_name='已缴金额')
    status = models.CharField(max_length=20, choices=STATUS, default='pending', verbose_name='缴费状态')
    due_date = models.DateField(verbose_name='缴费截止日期')
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name='缴费时间')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '水费账单'
        verbose_name_plural = '水费账单管理'
        ordering = ['-billing_period_end']


class WaterPayment(BaseModel):
    PAYMENT_METHODS = [
        ('cash', '现金'),
        ('bank_transfer', '银行转账'),
        ('alipay', '支付宝'),
        ('wechat', '微信支付'),
        ('bank_card', '银行卡'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='缴费编号')
    bill = models.ForeignKey(WaterBill, on_delete=models.CASCADE, related_name='payments', verbose_name='账单')
    amount = models.DecimalField(max_digits=12, decimal_places=2, verbose_name='缴费金额')
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHODS, verbose_name='缴费方式')
    payment_time = models.DateTimeField(verbose_name='缴费时间')
    operator = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='操作人')
    transaction_id = models.CharField(max_length=100, blank=True, verbose_name='交易流水号')
    remark = models.CharField(max_length=255, blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '缴费记录'
        verbose_name_plural = '缴费记录'
        ordering = ['-payment_time']
