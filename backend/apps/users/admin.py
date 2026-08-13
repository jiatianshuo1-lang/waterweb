from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, OperationLog


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'real_name', 'role', 'phone', 'email', 'region', 'is_active', 'last_login']
    list_filter = ['role', 'region', 'is_active', 'department']
    search_fields = ['username', 'real_name', 'phone', 'email']
    list_select_related = ['region']
    fieldsets = BaseUserAdmin.fieldsets + (
        ('扩展信息', {'fields': ('real_name', 'role', 'phone', 'avatar', 'region', 'department', 'position')}),
    )


@admin.register(OperationLog)
class OperationLogAdmin(admin.ModelAdmin):
    list_display = ['user', 'log_type', 'module', 'action', 'target', 'ip_address', 'status', 'created_at']
    list_filter = ['log_type', 'module', 'status']
    search_fields = ['action', 'target']
    readonly_fields = ['user', 'log_type', 'module', 'action', 'target', 'ip_address', 'user_agent', 'detail', 'status', 'duration', 'created_at']
