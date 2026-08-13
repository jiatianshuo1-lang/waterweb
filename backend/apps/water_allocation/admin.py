from django.contrib import admin
from .models import WaterSource, WaterAllocation, WaterAllocationDetail, WaterTransfer


@admin.register(WaterSource)
class WaterSourceAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'source_type', 'region', 'capacity', 'current_storage']
    list_filter = ['source_type', 'region']
    search_fields = ['code', 'name']


@admin.register(WaterAllocation)
class WaterAllocationAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'allocation_type', 'water_source', 'total_amount', 'period_start', 'status']
    list_filter = ['allocation_type', 'status']
    search_fields = ['code', 'name']


@admin.register(WaterAllocationDetail)
class WaterAllocationDetailAdmin(admin.ModelAdmin):
    list_display = ['allocation', 'region', 'water_user', 'user_type', 'allocated_amount', 'used_amount', 'ratio']
    list_filter = ['user_type']
    search_fields = ['water_user']


@admin.register(WaterTransfer)
class WaterTransferAdmin(admin.ModelAdmin):
    list_display = ['code', 'transfer_type', 'from_region', 'to_region', 'amount', 'planned_start', 'status']
    list_filter = ['transfer_type', 'status']
    search_fields = ['code', 'reason']
