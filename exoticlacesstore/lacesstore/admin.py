from django.contrib import admin
from .models import Category, Product, Order, OrderItem, ProductVariant, Customer, Visitor, DailyVisitorStats
from django.utils.html import format_html
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
from django.utils import timezone
import datetime
from .models import Voucher, UserVoucherUsage, FlashSale



# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug'] 
    prepopulated_fields = {'slug': ('name',)}
    
admin.site.register(Category, CategoryAdmin)



class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # How many empty variants to show by default
    fields = ['color_name', 'color_code', 'image', 'stock', 'is_default']
    readonly_fields = []  # make any read-only if needed

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price','stock', 'available', 'created','updated'] 
#     list_editable = ['price', 'stock', 'available']
#     prepopulated_fields = {'slug': ('name',)}
#     list_per_page = 20 
#     inlines = [ProductVariantInline]  # <--- Add this line


# admin.site.register(Product, ProductAdmin)

# lacesstore/admin.py
from django.contrib import admin

# lacesstore/admin.py
from django.contrib import admin

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price', 'stock', 'available', 'created', 'updated', 'youtube_video_id']
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20
    inlines = [ProductVariantInline]
    
    # Add YouTube fields without is_featured
    fieldsets = (
        (None, {
            'fields': ('name', 'category', 'description', 'price', 'stock', 'available', 'image')
        }),
        ('YouTube Video', {
            'fields': ('youtube_video_url', 'youtube_video_id'),
            'classes': ('collapse',),
            'description': 'Paste the YouTube video URL (e.g., https://www.youtube.com/watch?v=XXXXXXXXXXX)'
        }),
        ('SEO', {
            'fields': ('slug',),
            'classes': ('collapse',),
        }),
    )
    
    readonly_fields = ['youtube_video_id']


admin.site.register(Product, ProductAdmin)









class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    extra = 0
    can_delete = False
    max_num = 0

    readonly_fields = [
        'product',
        'quantity',
        'price',
        'image_preview',
    ]

    fields = [
        'product',
        'quantity',
        'price',
        'image_preview',
    ]

    def image_preview(self, obj):
        if obj.product_image:
            return format_html(
                '<img src="{}" width="80" height="80" style="object-fit:cover;border-radius:5px;" />',
                obj.product_image.url
            )
        return "No Image"

    image_preview.short_description = "Product Image"

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'firstName', 'emailAddress', 'created']
    list_display_links = ('id','firstName')
    search_fields = ['id', 'firstName', 'emailAddress']
    readonly_fields = ['id', 'total', 'emailAddress', 'created', 'firstName','lastName','phonenumber','country','state']

    fieldsets = [
        ('ORDER INFORMATION', {'fields': ['id', 'total','created']}),
        ('BILLING INFORMATION', {'fields': ['firstName','lastName','phonenumber','country','state', 'emailAddress']})
    ]

    inlines = [
        OrderItemAdmin,
    ]

    def has_delete_permission(self, request, obj=None):
        return False

    def has_add_permission(self, request):
        return False


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # How many empty variants to show by default
    fields = ['color_name', 'color_code', 'image', 'stock', 'is_default']
    readonly_fields = []  # make any read-only if needed






class CustomerInline(admin.StackedInline):
    model = Customer
    can_delete = False
    verbose_name_plural = 'Customer Profile'

class CustomUserAdmin(UserAdmin):
    inlines = (CustomerInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'has_customer_profile')
    
    def has_customer_profile(self, obj):
        return hasattr(obj, 'customer')
    has_customer_profile.boolean = True
    has_customer_profile.short_description = 'Has Customer Profile'

# Unregister the default User admin
admin.site.unregister(User)
# Register the custom User admin
admin.site.register(User, CustomUserAdmin)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'firstName', 'lastName', 'phonenumber', 'user')
    search_fields = ('email', 'firstName', 'lastName', 'phonenumber')
    list_filter = ('user__is_staff',)





######################usres onsite on any time ########################################



@admin.register(Visitor)
class VisitorAdmin(admin.ModelAdmin):
    list_display = ['session_key', 'user', 'ip_address', 'last_visit', 'visit_count', 'time_online']
    list_filter = ['first_visit']
    search_fields = ['session_key', 'ip_address', 'user__username', 'user__email']
    readonly_fields = ['session_key', 'ip_address', 'user_agent', 'referer', 'first_visit', 'last_visit', 'visit_count']
    date_hierarchy = 'last_visit'
    
    def time_online(self, obj):
        """Show how long since last visit"""
        delta = timezone.now() - obj.last_visit
        if delta.seconds < 60:
            return f"{delta.seconds} seconds ago"
        elif delta.seconds < 3600:
            return f"{delta.seconds // 60} minutes ago"
        elif delta.seconds < 86400:
            return f"{delta.seconds // 3600} hours ago"
        else:
            return f"{delta.days} days ago"
    time_online.short_description = "Last Activity"
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(DailyVisitorStats)
class DailyVisitorStatsAdmin(admin.ModelAdmin):
    list_display = ['date', 'unique_visitors', 'registered_users', 'guest_users', 'total_page_views']
    list_filter = ['date']
    search_fields = ['date']
    date_hierarchy = 'date'
    ordering = ['-date']
    
    def get_actions(self, request):
        actions = super().get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False






@admin.register(Voucher)
class VoucherAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'discount_type', 'discount_value', 'valid_from', 'valid_to',
        'active', 'used_count', 'total_usage_limit', 'is_flash_sale'
    ]
    list_filter = ['active', 'discount_type', 'is_flash_sale']
    search_fields = ['code']
    filter_horizontal = ['applicable_to', 'user_specific']
    readonly_fields = ['used_count', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'discount_type', 'discount_value', 'is_flash_sale', 'flash_sale_title')
        }),
        ('Validity', {
            'fields': ('valid_from', 'valid_to', 'active')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'total_usage_limit', 'used_count')
        }),
        ('Restrictions', {
            'fields': ('min_order_amount', 'max_discount_amount', 'applicable_to', 'user_specific')
        }),
    )


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'product', 'discount_percentage', 'start_time', 'end_time',
        'is_active', 'sold_count', 'status_badge'
    ]
    list_filter = ['is_active', 'product__category']
    search_fields = ['title', 'product__name']
    readonly_fields = ['sold_count', 'created_at', 'updated_at']
    
    def status_badge(self, obj):
        now = timezone.now()
        if not obj.is_active:
            return format_html('<span style="color: gray;">Inactive</span>')
        elif obj.start_time > now:
            return format_html('<span style="color: blue;">Upcoming</span>')
        elif obj.start_time <= now <= obj.end_time:
            if obj.max_quantity == 0 or obj.sold_count < obj.max_quantity:
                return format_html('<span style="color: green;">Active</span>')
            else:
                return format_html('<span style="color: orange;">Sold Out</span>')
        else:
            return format_html('<span style="color: red;">Expired</span>')
    
    status_badge.short_description = 'Status'


@admin.register(UserVoucherUsage)
class UserVoucherUsageAdmin(admin.ModelAdmin):
    list_display = ['user', 'voucher', 'order', 'discount_amount', 'used_at']
    list_filter = ['used_at']
    search_fields = ['user__username', 'voucher__code', 'order__id']