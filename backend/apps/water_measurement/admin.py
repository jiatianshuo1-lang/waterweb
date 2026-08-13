from django.contrib import admin
from .models import MeasureStation, WaterMeasurement, WaterAlarm


@admin.register(MeasureStation)
class MeasureStationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'station_type', 'region', 'status', 'is_active', 'last_data_time']
    list_filter = ['station_type', 'communication', 'region', 'status', 'is_active']
    search_fields = ['code', 'name', 'device_code']


@admin.register(WaterMeasurement)
class WaterMeasurementAdmin(admin.ModelAdmin):
    list_display = ['station', 'measure_time', 'flow_rate', 'water_level', 'total_flow', 'source', 'is_abnormal']
    list_filter = ['source', 'is_abnormal']
    search_fields = ['station__code', 'station__name']
    date_hierarchy = 'measure_time'


@admin.register(WaterAlarm)
class WaterAlarmAdmin(admin.ModelAdmin):
    list_display = ['station', 'alarm_type', 'level', 'title', 'triggered_at', 'is_resolved']
    list_filter = ['alarm_type', 'level', 'is_resolved']
    search_fields = ['title', 'message']
