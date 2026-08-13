from django.contrib import admin
from .models import IrrigationDevice, IrrigationLog, IrrigationPlan, IrrigationRecord


@admin.register(IrrigationDevice)
class IrrigationDeviceAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'device_type', 'region', 'control_mode', 'status', 'is_active']
    list_filter = ['device_type', 'control_mode', 'region', 'status', 'is_active']
    search_fields = ['code', 'name', 'device_model']


@admin.register(IrrigationLog)
class IrrigationLogAdmin(admin.ModelAdmin):
    list_display = ['device', 'action', 'value', 'operator', 'operate_time', 'result']
    list_filter = ['action', 'result']
    search_fields = ['device__code', 'device__name']


@admin.register(IrrigationPlan)
class IrrigationPlanAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'plan_type', 'region', 'start_time', 'end_time', 'status']
    list_filter = ['plan_type', 'status']
    search_fields = ['code', 'name']
    filter_horizontal = ['devices']


@admin.register(IrrigationRecord)
class IrrigationRecordAdmin(admin.ModelAdmin):
    list_display = ['region', 'device', 'start_time', 'end_time', 'water_used', 'energy_used']
    list_filter = ['region']
    date_hierarchy = 'start_time'
