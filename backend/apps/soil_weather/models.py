from django.db import models
from apps.common.models import BaseModel


class SoilMonitorStation(BaseModel):
    STATION_TYPES = [
        ('soil', '墒情监测站'),
        ('weather', '气象监测站'),
        ('comprehensive', '综合监测站'),
    ]

    code = models.CharField(max_length=50, unique=True, verbose_name='测站编码')
    name = models.CharField(max_length=100, verbose_name='测站名称')
    station_type = models.CharField(max_length=20, choices=STATION_TYPES, default='comprehensive', verbose_name='测站类型')
    region = models.ForeignKey('common.RegionModel', on_delete=models.SET_NULL, null=True, blank=True, verbose_name='所属区域')
    location = models.CharField(max_length=200, blank=True, verbose_name='具体位置')
    longitude = models.FloatField(null=True, blank=True, verbose_name='经度')
    latitude = models.FloatField(null=True, blank=True, verbose_name='纬度')
    soil_type = models.CharField(max_length=50, blank=True, verbose_name='土壤类型')
    crop_type = models.CharField(max_length=50, blank=True, verbose_name='主要作物')
    device_code = models.CharField(max_length=50, blank=True, verbose_name='设备编号')
    is_active = models.BooleanField(default=True, verbose_name='是否启用')
    last_data_time = models.DateTimeField(null=True, blank=True, verbose_name='最后数据时间')
    status = models.CharField(max_length=20, default='offline', choices=[
        ('online', '在线'), ('offline', '离线'), ('fault', '故障')
    ], verbose_name='运行状态')
    description = models.TextField(blank=True, verbose_name='备注')

    class Meta:
        verbose_name = '墒情气象测站'
        verbose_name_plural = '墒情气象测站管理'
        ordering = ['code']


class SoilData(BaseModel):
    station = models.ForeignKey(SoilMonitorStation, on_delete=models.CASCADE, related_name='soil_data', verbose_name='测站')
    measure_time = models.DateTimeField(verbose_name='测量时间')

    soil_moisture_0_10 = models.FloatField(null=True, blank=True, verbose_name='0-10cm含水率(%)')
    soil_moisture_10_20 = models.FloatField(null=True, blank=True, verbose_name='10-20cm含水率(%)')
    soil_moisture_20_40 = models.FloatField(null=True, blank=True, verbose_name='20-40cm含水率(%)')
    soil_moisture_40_60 = models.FloatField(null=True, blank=True, verbose_name='40-60cm含水率(%)')
    soil_moisture_avg = models.FloatField(null=True, blank=True, verbose_name='平均含水率(%)')

    soil_temperature_10 = models.FloatField(null=True, blank=True, verbose_name='10cm地温(℃)')
    soil_temperature_20 = models.FloatField(null=True, blank=True, verbose_name='20cm地温(℃)')
    soil_salinity = models.FloatField(null=True, blank=True, verbose_name='土壤盐度(dS/m)')
    soil_ph = models.FloatField(null=True, blank=True, verbose_name='土壤pH值')

    source = models.CharField(max_length=20, default='auto', verbose_name='数据来源')
    is_abnormal = models.BooleanField(default=False, verbose_name='是否异常')

    class Meta:
        verbose_name = '墒情数据'
        verbose_name_plural = '墒情数据'
        ordering = ['-measure_time']
        indexes = [
            models.Index(fields=['station', '-measure_time']),
        ]


class WeatherData(BaseModel):
    station = models.ForeignKey(SoilMonitorStation, on_delete=models.CASCADE, related_name='weather_data', verbose_name='测站')
    measure_time = models.DateTimeField(verbose_name='测量时间')

    temperature = models.FloatField(null=True, blank=True, verbose_name='气温(℃)')
    humidity = models.FloatField(null=True, blank=True, verbose_name='相对湿度(%)')
    pressure = models.FloatField(null=True, blank=True, verbose_name='大气压(hPa)')
    wind_speed = models.FloatField(null=True, blank=True, verbose_name='风速(m/s)')
    wind_direction = models.CharField(max_length=10, blank=True, verbose_name='风向')
    rainfall = models.FloatField(null=True, blank=True, verbose_name='降水量(mm)')
    solar_radiation = models.FloatField(null=True, blank=True, verbose_name='太阳辐射(W/m²)')
    evapotranspiration = models.FloatField(null=True, blank=True, verbose_name='蒸发量(mm)')

    source = models.CharField(max_length=20, default='auto', verbose_name='数据来源')

    class Meta:
        verbose_name = '气象数据'
        verbose_name_plural = '气象数据'
        ordering = ['-measure_time']
        indexes = [
            models.Index(fields=['station', '-measure_time']),
        ]


class SoilForecast(BaseModel):
    FORECAST_TYPES = [
        ('drought', '干旱预警'),
        ('waterlogging', '涝渍预警'),
        ('optimal', '适宜状态'),
    ]

    station = models.ForeignKey(SoilMonitorStation, on_delete=models.SET_NULL, null=True, blank=True, verbose_name='测站')
    forecast_type = models.CharField(max_length=20, choices=FORECAST_TYPES, verbose_name='预报类型')
    forecast_time = models.DateTimeField(verbose_name='预报时间')
    forecast_hours = models.IntegerField(default=24, verbose_name='预报时长(小时)')
    current_moisture = models.FloatField(null=True, blank=True, verbose_name='当前含水率(%)')
    predicted_moisture = models.FloatField(null=True, blank=True, verbose_name='预测含水率(%)')
    risk_level = models.CharField(max_length=20, default='low', choices=[
        ('low', '低风险'), ('medium', '中风险'), ('high', '高风险'), ('critical', '极高风险')
    ], verbose_name='风险等级')
    advice = models.TextField(blank=True, verbose_name='建议措施')
    trigger_value = models.JSONField(null=True, blank=True, verbose_name='触发指标')

    class Meta:
        verbose_name = '墒情预报'
        verbose_name_plural = '墒情预报管理'
        ordering = ['-forecast_time']
