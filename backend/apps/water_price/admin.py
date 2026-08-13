from django.contrib import admin
from .models import WaterPricePolicy, WaterUser, WaterBill, WaterPayment


@admin.register(WaterPricePolicy)
class WaterPricePolicyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'policy_type', 'pricing_mode', 'base_price', 'region', 'start_date', 'is_active']
    list_filter = ['policy_type', 'pricing_mode', 'is_active']
    search_fields = ['code', 'name']


@admin.register(WaterUser)
class WaterUserAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'user_type', 'region', 'water_meter', 'policy', 'contact_person', 'is_active']
    list_filter = ['user_type', 'is_active']
    search_fields = ['code', 'name', 'water_meter']


@admin.register(WaterBill)
class WaterBillAdmin(admin.ModelAdmin):
    list_display = ['code', 'user', 'billing_period_start', 'billing_period_end', 'usage', 'total_fee', 'paid_fee', 'status']
    list_filter = ['status']
    search_fields = ['code', 'user__name']
    date_hierarchy = 'billing_period_end'


@admin.register(WaterPayment)
class WaterPaymentAdmin(admin.ModelAdmin):
    list_display = ['code', 'bill', 'amount', 'payment_method', 'payment_time', 'operator']
    list_filter = ['payment_method']
    search_fields = ['code', 'transaction_id']
    date_hierarchy = 'payment_time'
