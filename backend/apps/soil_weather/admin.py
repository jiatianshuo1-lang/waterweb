from django.contrib import admin
from .models import SoilMonitorStation, SoilData, WeatherData, SoilForecast


@admin.register(SoilMonitorStation)
class SoilMonitorStationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'station_type', 'region', 'status', 'is_active', 'last_data_time']
    list_filter = ['station_type', 'status', 'is_active']
    search_fields = ['code', 'name']


@admin.register(SoilData)
class SoilDataAdmin(admin.ModelAdmin):
    list_display = ['station', 'measure_time', 'soil_moisture_avg', 'soil_ph', 'soil_temperature_10', 'is_abnormal']
    list_filter = ['is_abnormal']
    date_hierarchy = 'measure_time'


@admin.register(WeatherData)
class WeatherDataAdmin(admin.ModelAdmin):
    list_display = ['station', 'measure_time', 'temperature', 'humidity', 'rainfall', 'wind_speed']
    date_hierarchy = 'measure_time'


@admin.register(SoilForecast)
class SoilForecastAdmin(admin.ModelAdmin):
    list_display = ['station', 'forecast_type', 'forecast_time', 'risk_level', 'current_moisture']
    list_filter = ['forecast_type', 'risk_level']
    search_fields = ['advice']
