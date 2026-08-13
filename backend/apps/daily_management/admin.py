from django.contrib import admin
from .models import Notice, Meeting, Asset, Document


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ['title', 'notice_type', 'region', 'is_top', 'status', 'published_at', 'views_count']
    list_filter = ['notice_type', 'status', 'is_top']
    search_fields = ['title', 'summary']


@admin.register(Meeting)
class MeetingAdmin(admin.ModelAdmin):
    list_display = ['title', 'meeting_type', 'start_time', 'location', 'host', 'status']
    list_filter = ['meeting_type', 'status']
    search_fields = ['title', 'location']
    filter_horizontal = ['participants']


@admin.register(Asset)
class AssetAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'asset_type', 'region', 'status', 'purchase_date', 'responsible']
    list_filter = ['asset_type', 'status']
    search_fields = ['code', 'name']


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ['title', 'doc_type', 'file_name', 'file_size', 'region', 'downloads', 'created_at']
    list_filter = ['doc_type']
    search_fields = ['title', 'description']
