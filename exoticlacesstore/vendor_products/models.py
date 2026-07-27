from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal

class Vendor(models.Model):
    """Business partner/vendor who supplies products"""
    name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00, help_text="Commission percentage for each sale")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.business_name
    
    class Meta:
        ordering = ['business_name']


class VendorProduct(models.Model):
    """Products from vendors (dropshipping model)"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    
    # Product details
    name = models.CharField(max_length=255)
    sku = models.CharField(max_length=100, unique=True)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price (includes your profit)")
    vendor_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price you pay to vendor")
    
    # Product specifications (for Shariah compliance - eliminate Gharar)
    fabric_type = models.CharField(max_length=100, blank=True)
    length = models.CharField(max_length=50, blank=True, help_text="e.g., 6 yards, 5 meters")
    color = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    origin = models.CharField(max_length=100, blank=True, help_text="Country of origin")
    
    # Images
    main_image = models.ImageField(upload_to='vendor_products/')
    additional_images = models.JSONField(default=list, blank=True, help_text="List of additional image URLs")
    
    # Shipping
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    estimated_delivery_min = models.IntegerField(default=5, help_text="Minimum delivery days")
    estimated_delivery_max = models.IntegerField(default=10, help_text="Maximum delivery days")
    
    # Inventory
    stock_quantity = models.IntegerField(default=0)
    is_available = models.BooleanField(default=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} ({self.vendor.business_name})"
    
    def get_delivery_range(self):
        """Return delivery range for display"""
        return f"{self.estimated_delivery_min} - {self.estimated_delivery_max} business days"
    
    def get_commission(self):
        """Calculate commission for this product"""
        return (self.price - self.vendor_price) * Decimal('0.01') * self.vendor.commission_rate
    
    def is_in_stock(self):
        return self.stock_quantity > 0 and self.is_available
    
    class Meta:
        ordering = ['-created_at']


class VendorOrder(models.Model):
    """Order requests for vendor products (Wa'ad model)"""
    STATUS_CHOICES = [
        ('pending', 'Pending - Awaiting Vendor Confirmation'),
        ('secured', 'Secured - Item Purchased from Vendor'),
        ('shipped', 'Shipped to Customer'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled - Item Unavailable'),
        ('failed', 'Failed - Vendor Could Not Fulfill'),
    ]
    
    PAYMENT_STATUS_CHOICES = [
        ('authorized', 'Authorized - Funds on Hold'),
        ('captured', 'Captured - Funds Collected'),
        ('refunded', 'Refunded'),
        ('failed', 'Failed'),
    ]
    
    # Customer information
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vendor_orders')
    product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE, related_name='orders')
    
    # Order details
    quantity = models.IntegerField(default=1)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Paystack preauthorization
    paystack_reference = models.CharField(max_length=100, blank=True)
    paystack_access_code = models.CharField(max_length=100, blank=True)
    payment_intent_id = models.CharField(max_length=255, blank=True)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='authorized')
    
    # Vendor fulfillment
    vendor_order_id = models.CharField(max_length=100, blank=True, help_text="Vendor's order reference")
    vendor_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Shipping
    shipping_address = models.TextField()
    tracking_number = models.CharField(max_length=100, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Order #{self.id} - {self.customer.username} - {self.product.name}"
    
    def can_capture_payment(self):
        """Check if payment can be captured (item secured)"""
        return self.status == 'secured' and self.payment_status == 'authorized'
    
    def is_completed(self):
        return self.status == 'delivered' and self.payment_status == 'captured'
    
    class Meta:
        ordering = ['-created_at']