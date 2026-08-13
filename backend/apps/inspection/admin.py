from django.contrib import admin
from .models import Inspection, WorkOrder, WorkOrderLog, InspectionRecord


@admin.register(Inspection)
class InspectionAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'template_type', 'priority', 'region', 'status', 'planned_start', 'result', 'created_at']
    list_filter = ['template_type', 'priority', 'status', 'region']
    search_fields = ['code', 'title', 'description']
    filter_horizontal = ['inspectors']
    list_select_related = ['region', 'created_by']


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'order_type', 'priority', 'region', 'status', 'reporter', 'assignee', 'created_at']
    list_filter = ['order_type', 'priority', 'status', 'region']
    search_fields = ['code', 'title', 'description']
    list_select_related = ['region', 'inspection', 'reporter', 'assignee']


@admin.register(WorkOrderLog)
class WorkOrderLogAdmin(admin.ModelAdmin):
    list_display = ['work_order', 'action', 'from_status', 'to_status', 'operator', 'created_at']
    list_filter = ['action', 'from_status', 'to_status']
    search_fields = ['remark']
    readonly_fields = ['work_order', 'action', 'from_status', 'to_status', 'operator', 'remark', 'created_at']


@admin.register(InspectionRecord)
class InspectionRecordAdmin(admin.ModelAdmin):
    list_display = ['inspection', 'item_name', 'result', 'value', 'standard', 'inspector', 'created_at']
    list_filter = ['result', 'item_type']
    search_fields = ['item_name', 'remark']
    list_select_related = ['inspection', 'inspector']
