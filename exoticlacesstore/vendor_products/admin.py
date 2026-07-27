from django.contrib import admin
from .models import Vendor, VendorProduct, VendorOrder

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'email', 'phone', 'is_active']
    search_fields = ['name', 'business_name', 'email']
    list_filter = ['is_active']

@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'vendor', 'price', 'is_available', 'status']
    list_filter = ['status', 'is_available', 'vendor']
    search_fields = ['name', 'sku', 'vendor__business_name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'name', 'sku', 'description', 'price', 'vendor_price')
        }),
        ('Specifications (Shariah Compliance)', {
            'fields': ('fabric_type', 'length', 'color', 'weight', 'material', 'origin')
        }),
        ('Images', {
            'fields': ('main_image', 'additional_images')
        }),
        ('Shipping', {
            'fields': ('shipping_cost', 'estimated_delivery_min', 'estimated_delivery_max')
        }),
        ('Inventory & Status', {
            'fields': ('stock_quantity', 'is_available', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['customer__username', 'product__name', 'paystack_reference']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_secured', 'capture_payment_action', 'cancel_order_action']
    
    def mark_as_secured(self, request, queryset):
        """Mark orders as secured (vendor confirmed stock)"""
        queryset.update(status='secured', vendor_confirmed_at=timezone.now())
        self.message_user(request, f"✅ {queryset.count()} orders marked as secured.")
    mark_as_secured.short_description = "Mark selected orders as SECURED (vendor confirmed)"
    
    def capture_payment_action(self, request, queryset):
        """Capture payment for secured orders"""
        # This would call the capture_payment view
        self.message_user(request, "✅ Use the 'Capture Payment' button on each order detail page.")
    capture_payment_action.short_description = "Capture payment for selected orders"
    
    def cancel_order_action(self, request, queryset):
        """Cancel orders (vendor cannot fulfill)"""
        queryset.update(status='cancelled', payment_status='refunded')
        self.message_user(request, f"✅ {queryset.count()} orders cancelled.")
    cancel_order_action.short_description = "Cancel selected orders (vendor cannot fulfill)"