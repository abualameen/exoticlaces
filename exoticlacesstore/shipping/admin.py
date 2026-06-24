

# Register your models here.
# shipping/admin.py
from django.contrib import admin
from .models import ShippingMethod, ShippingRate, Shipment

@admin.register(ShippingMethod)
class ShippingMethodAdmin(admin.ModelAdmin):
    list_display = ['id', 'name', 'provider', 'active']
    list_filter = ['active', 'provider']
    search_fields = ['name', 'provider']

@admin.register(ShippingRate)
class ShippingRateAdmin(admin.ModelAdmin):
    list_display = ['id', 'method', 'country', 'state', 'price_per_item', 'is_active']
    list_filter = ['method', 'country']
    search_fields = ['country', 'state']
    
    def is_active(self, obj):
        return obj.method.active
    is_active.boolean = True
    is_active.short_description = "Active"

@admin.register(Shipment)
class ShipmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'method', 'cost', 'tracking_number', 'status', 'created_at']
    list_filter = ['status', 'method']
    search_fields = ['tracking_number', 'order__id']
    readonly_fields = ['created_at']