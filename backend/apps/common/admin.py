from django.contrib import admin
from .models import RegionModel, CommonConfig


@admin.register(RegionModel)
class RegionModelAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'region_type', 'parent', 'sort_order']
    list_filter = ['region_type']
    search_fields = ['code', 'name']
    list_select_related = ['parent']


@admin.register(CommonConfig)
class CommonConfigAdmin(admin.ModelAdmin):
    list_display = ['config_type', 'config_key', 'description', 'created_at']
    list_filter = ['config_type']
    search_fields = ['config_key']
