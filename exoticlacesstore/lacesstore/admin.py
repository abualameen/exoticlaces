from django.contrib import admin
from .models import Category, Product, Order, OrderItem, ProductVariant

# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug'] 
    prepopulated_fields = {'slug': ('name',)}
    
admin.site.register(Category, CategoryAdmin)

# class ProductAdmin(admin.ModelAdmin):
#     list_display = ['name', 'price','stock', 'available', 'created','updated'] 
#     list_editable = ['price', 'stock', 'available']
#     prepopulated_fields = {'slug': ('name',)}
#     list_per_page = 20 

class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1  # How many empty variants to show by default
    fields = ['color_name', 'color_code', 'image', 'stock', 'is_default']
    readonly_fields = []  # make any read-only if needed

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price','stock', 'available', 'created','updated'] 
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20 
    inlines = [ProductVariantInline]  # <--- Add this line


admin.site.register(Product, ProductAdmin)

class OrderItemAdmin(admin.TabularInline):
    model = OrderItem
    fieldsets = [
        ('Product', {'fields': ['product'],}),
        ('Quantity', {'fields': ['quantity'],}),
        ('Price', {'fields': ['price'],}),
        
    ]
    readonly_fields = ['product', 'quantity', 'price']
    can_delete = False
    max_num = 0

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
