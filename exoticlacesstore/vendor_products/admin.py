from django.contrib import admin
from django.utils.html import format_html
from .models import Vendor, VendorProduct, VendorProductVariant, VendorOrder

class VendorProductVariantInline(admin.TabularInline):
    model = VendorProductVariant
    extra = 1
    fields = ['color_name', 'color_code', 'image', 'stock', 'is_default']

@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['business_name', 'name', 'email', 'phone', 'is_active']
    search_fields = ['name', 'business_name', 'email']
    list_filter = ['is_active']

@admin.register(VendorProduct)
class VendorProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'vendor', 'price', 'stock', 'available', 'status']
    list_filter = ['status', 'available', 'category', 'vendor']
    search_fields = ['name', 'sku', 'vendor__business_name']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [VendorProductVariantInline]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('vendor', 'category', 'name', 'slug', 'description', 'price', 'vendor_price')
        }),
        ('Specifications (Shariah Compliance)', {
            'fields': ('fabric_type', 'length', 'color', 'weight', 'material', 'origin')
        }),
        ('Images', {
            'fields': ('image', 'additional_images')
        }),
        ('Delivery', {
            'fields': ('estimated_delivery_min', 'estimated_delivery_max')
        }),
        ('YouTube Video', {
            'fields': ('youtube_video_url', 'youtube_video_id'),
            'classes': ('collapse',)
        }),
        ('Inventory & Status', {
            'fields': ('stock', 'available', 'status')
        }),
        ('Timestamps', {
            'fields': ('created', 'updated'),
            'classes': ('collapse',)
        })
    )
    
    def get_thumbnail(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" style="object-fit:cover;" />', obj.image.url)
        return "No Image"
    get_thumbnail.short_description = 'Image'

@admin.register(VendorOrder)
class VendorOrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'product', 'quantity', 'total_amount', 'status', 'payment_status', 'created_at']
    list_filter = ['status', 'payment_status', 'created_at']
    search_fields = ['customer__username', 'product__name', 'paystack_reference']
    readonly_fields = ['created_at', 'updated_at']
    actions = ['mark_as_secured', 'capture_payment_action', 'cancel_order_action']
    
    def mark_as_secured(self, request, queryset):
        queryset.update(status='secured', vendor_confirmed_at=timezone.now())
        self.message_user(request, f"✅ {queryset.count()} orders marked as secured.")
    mark_as_secured.short_description = "Mark selected orders as SECURED (vendor confirmed)"
    
    def capture_payment_action(self, request, queryset):
        self.message_user(request, "✅ Use the 'Capture Payment' button on each order detail page.")
    capture_payment_action.short_description = "Capture payment for selected orders"
    
    def cancel_order_action(self, request, queryset):
        queryset.update(status='cancelled', payment_status='refunded')
        self.message_user(request, f"✅ {queryset.count()} orders cancelled.")
    cancel_order_action.short_description = "Cancel selected orders (vendor cannot fulfill)"