from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from lacesstore.models import Category  

class Vendor(models.Model):
    """Business partner/vendor who supplies products"""
    name = models.CharField(max_length=200)
    business_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField(blank=True)
    website = models.URLField(blank=True)
    is_active = models.BooleanField(default=True)
    commission_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.business_name
    
    class Meta:
        ordering = ['business_name']


class VendorProduct(models.Model):
    """Products from vendors (dropshipping model) with full product features"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    # ✅ Vendor relationship
    vendor = models.ForeignKey(Vendor, on_delete=models.CASCADE, related_name='products')
    
    # ✅ Category from main app
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='vendor_products')
    
    # ✅ Product details (matches main Product model)
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    
    # ✅ Pricing
    price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Selling price (includes your profit)")
    vendor_price = models.DecimalField(max_digits=10, decimal_places=2, help_text="Price you pay to vendor")
    
    # ✅ Product specifications (for Shariah compliance - eliminate Gharar)
    fabric_type = models.CharField(max_length=100, blank=True)
    length = models.CharField(max_length=50, blank=True, help_text="e.g., 6 yards, 5 meters")
    color = models.CharField(max_length=50, blank=True)
    weight = models.CharField(max_length=50, blank=True)
    material = models.CharField(max_length=100, blank=True)
    origin = models.CharField(max_length=100, blank=True, help_text="Country of origin")
    
    # ✅ Images (matches main product)
    image = models.ImageField(upload_to='vendor_products/', blank=True)
    additional_images = models.JSONField(default=list, blank=True, help_text="List of additional image URLs")
    
    # ✅ Stock
    stock = models.IntegerField(default=0)
    available = models.BooleanField(default=True)
    
    # ✅ YouTube Video (matches main product)
    youtube_video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="YouTube Video URL",
        help_text="Paste the full YouTube URL (e.g., https://www.youtube.com/watch?v=XXXXXXXXXXX)"
    )
    youtube_video_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        editable=False,
        verbose_name="YouTube Video ID"
    )
    
    # ✅ Delivery window (for Shariah compliance)
    estimated_delivery_min = models.IntegerField(default=5, help_text="Minimum delivery days")
    estimated_delivery_max = models.IntegerField(default=10, help_text="Maximum delivery days")
    
    # ✅ Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # ✅ Timestamps
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        # Extract YouTube video ID from URL
        if self.youtube_video_url:
            import re
            patterns = [
                r'(?:youtube\.com\/watch\?v=)([\w-]+)',
                r'(?:youtu\.be\/)([\w-]+)',
                r'(?:youtube\.com\/embed\/)([\w-]+)',
                r'(?:youtube\.com\/shorts\/)([\w-]+)',
                r'(?:youtube\.com\/v\/)([\w-]+)',
                r'(?:youtube\.com\/live\/)([\w-]+)',
                r'(?:youtube\.com\/.*[?&]v=)([\w-]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, self.youtube_video_url)
                if match:
                    self.youtube_video_id = match.group(1)
                    break
            else:
                if 'youtube.com' in self.youtube_video_url or 'youtu.be' in self.youtube_video_url:
                    parts = self.youtube_video_url.rstrip('/').split('/')
                    if parts:
                        last_part = parts[-1]
                        if '?' in last_part:
                            last_part = last_part.split('?')[0]
                        if last_part and len(last_part) >= 11:
                            self.youtube_video_id = last_part
                else:
                    self.youtube_video_id = None
        else:
            self.youtube_video_id = None
            
        super().save(*args, **kwargs)
    
    def get_url(self):
        from django.urls import reverse
        return reverse('vendor_products:product_detail', args=[self.id])
    
    def get_delivery_range(self):
        """Return delivery range for display"""
        return f"{self.estimated_delivery_min} - {self.estimated_delivery_max} business days"
    
    def get_commission(self):
        """Calculate commission for this product"""
        return (self.price - self.vendor_price) * Decimal('0.01') * self.vendor.commission_rate
    
    def is_in_stock(self):
        return self.stock > 0 and self.available
    
    class Meta:
        ordering = ('name',)
        verbose_name = 'Vendor Product'
        verbose_name_plural = 'Vendor Products'
    
    def __str__(self):
        return f"{self.name} ({self.vendor.business_name})"


class VendorProductVariant(models.Model):
    """Product variants for vendor products like main abb (like main app)"""
    product = models.ForeignKey(VendorProduct, related_name='variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=20, blank=True)
    image = models.ImageField(upload_to='vendor_product_variants')
    stock = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)
    
    class Meta:
        unique_together = ('product', 'color_name')
    
    def __str__(self):
        return f"{self.product.name} - {self.color_name}"


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
    variant = models.ForeignKey(VendorProductVariant, on_delete=models.SET_NULL, null=True, blank=True)
    
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
    vendor_order_id = models.CharField(max_length=100, blank=True)
    vendor_confirmed_at = models.DateTimeField(null=True, blank=True)
    
    # Shipping (using existing shipping system)
    shipping_address = models.TextField()
    country = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    shipping_method = models.CharField(max_length=50, blank=True)
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    
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




class VendorCart(models.Model):
    """Cart for vendor products (supports guests)"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='vendor_carts')
    session_key = models.CharField(max_length=40, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'session_key')  # One cart per user or session
    
    def __str__(self):
        if self.user:
            return f"Vendor Cart - {self.user.username}"
        return f"Vendor Cart - Session {self.session_key}"
    
    def get_total(self):
        total = 0
        for item in self.items.all():
            total += item.product.price * item.quantity
        return total
    
    def get_total_items(self):
        return sum(item.quantity for item in self.items.all())
    
    def clear(self):
        self.items.all().delete()


class VendorCartItem(models.Model):
    """Items in vendor cart"""
    cart = models.ForeignKey(VendorCart, on_delete=models.CASCADE, related_name='items')
    product = models.ForeignKey(VendorProduct, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    shipping_address = models.TextField()
    added_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity}"
    
    def get_subtotal(self):
        return self.product.price * self.quantity