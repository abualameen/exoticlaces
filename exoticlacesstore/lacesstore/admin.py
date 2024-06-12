from django.contrib import admin
from .models import Category, Product, Order, OrderItem
# Register your models here.

class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug'] 
    prepopulated_fields = {'slug': ('name',)}
    
admin.site.register(Category, CategoryAdmin)

class ProductAdmin(admin.ModelAdmin):
    list_display = ['name', 'price','stock', 'available', 'created','updated'] 
    list_editable = ['price', 'stock', 'available']
    prepopulated_fields = {'slug': ('name',)}
    list_per_page = 20 

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