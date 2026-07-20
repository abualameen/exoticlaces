from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import datetime
from decimal import Decimal
import uuid

# ... your existing models ...


class Category(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='category', blank=True)

    class Meta:
        ordering = ('name',)
        verbose_name = 'category'
        verbose_name_plural = 'categories'
    def get_url(self):
        return reverse('products_by_category', args=[self.slug])

    def __str__(self) -> str:
        return self.name



class Product(models.Model):
    name = models.CharField(max_length=250, unique=True)
    slug = models.SlugField(max_length=250, unique=True)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    image = models.ImageField(upload_to='product', blank=True)
    stock = models.IntegerField()
    available = models.BooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    youtube_video_url = models.URLField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name="YouTube Video URL",
        help_text="Paste the full YouTube URL (e.g., https://www.youtube.com/watch?v=XXXXXXXXXXX or https://youtu.be/XXXXXXXXXXX)"
    )
    youtube_video_id = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        editable=False,
        verbose_name="YouTube Video ID"
    )
    
    def save(self, *args, **kwargs):
        # Extract YouTube video ID from URL
        if self.youtube_video_url:
            import re
            
            # More comprehensive patterns for all YouTube URL formats
            patterns = [
                # Standard watch URL
                r'(?:youtube\.com\/watch\?v=)([\w-]+)',
                # Shortened youtu.be URL
                r'(?:youtu\.be\/)([\w-]+)',
                # Embed URL
                r'(?:youtube\.com\/embed\/)([\w-]+)',
                # YouTube Shorts
                r'(?:youtube\.com\/shorts\/)([\w-]+)',
                # Mobile URL
                r'(?:youtube\.com\/v\/)([\w-]+)',
                # Live URL
                r'(?:youtube\.com\/live\/)([\w-]+)',
                # Any other youtube.com URL with v parameter
                r'(?:youtube\.com\/.*[?&]v=)([\w-]+)',
            ]
            
            for pattern in patterns:
                match = re.search(pattern, self.youtube_video_url)
                if match:
                    self.youtube_video_id = match.group(1)
                    break
            else:
                # If no pattern matches, try to extract from URL
                if 'youtube.com' in self.youtube_video_url or 'youtu.be' in self.youtube_video_url:
                    # Try to get the last part of the URL
                    parts = self.youtube_video_url.rstrip('/').split('/')
                    if parts:
                        last_part = parts[-1]
                        # Clean up any query parameters
                        if '?' in last_part:
                            last_part = last_part.split('?')[0]
                        if last_part and len(last_part) >= 11:
                            self.youtube_video_id = last_part
                else:
                    self.youtube_video_id = None
        else:
            self.youtube_video_id = None
            
        super().save(*args, **kwargs)

    class Meta:
        ordering = ('name',)
        verbose_name = 'product'
        verbose_name_plural = 'products'

    def get_url(self):
        return reverse('product_detail', args=[self.category.slug, self.slug])


    def __str__(self) -> str:
        return self.name   



class ProductVariant(models.Model):
    product = models.ForeignKey(Product, related_name='variants', on_delete=models.CASCADE)
    color_name = models.CharField(max_length=50)
    color_code = models.CharField(max_length=20, blank=True)  # e.g #FF0000 (optional)
    image = models.ImageField(upload_to='product_variants')
    stock = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)

    class Meta:
        unique_together = ('product', 'color_name')

    def __str__(self):
        return f"{self.product.name} - {self.color_name}"


class Cart(models.Model):
    cart_id = models.CharField(max_length=250, blank=True)
    date_added = models.DateField(auto_now_add=True)
    class Meta:
        db_table= 'Cart'
        ordering = ['date_added']


    def __str__(self):
        return str(self.cart_id)



class CartItem(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    variant = models.ForeignKey('ProductVariant', null=True, blank=True, on_delete=models.CASCADE)
    cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
    quantity = models.IntegerField()
    active = models.BooleanField(default=True)

    class Meta:
        db_table = 'CartItem'

    def sub_total(self):
        return self.product.price * self.quantity


    
    def __str__(self):
        if self.variant:
            return f"{self.product.name} - {self.variant.color_name}"
        return f"{self.product.name}"


    def item_price(self):
        return self.quantity * self.product.price

    def image_url(self):
        # Return the variant image if exists, else default product image
        if self.variant and self.variant.image:
            return self.variant.image.url
        return self.product.image.url




# Create your models here.
# ORDER MODEL
class Order(models.Model):
    customer = models.ForeignKey(
        'Customer', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='orders'
    )
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='NGN Order Total')
    emailAddress = models.EmailField(max_length=250, blank=True, verbose_name='Email Adress')
    created = models.DateTimeField(auto_now_add=True)
    firstName = models.CharField(max_length=250, blank=True)
    lastName = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=250, blank=True)
    state = models.CharField(max_length=250, blank=True)
    phonenumber = models.CharField(max_length=20, blank=True, null=True)
    shipping_method = models.CharField(max_length=50, null=True, blank=True)
    shipping_cost = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    currency = models.CharField(max_length=15, default='NGN')

    class Meta:
        db_table = 'Order'
        ordering = ['-created']
    
    def __str__(self):
        return str(self.id)

# class OrderItem(models.Model):
#     product = models.CharField(max_length=250)
#     quantity = models.IntegerField()
#     price = models.DecimalField(max_digits=10, decimal_places=2,verbose_name='NGN price')
#     order = models.ForeignKey(Order, on_delete= models.CASCADE) 

#     class Meta:
#         db_table = 'OrderItem'

#     def sub_total(self):
#         return self.quantity * self.price

#     def __str__(self):
#         return self.product


class OrderItem(models.Model):
    product = models.CharField(max_length=250)
    product_image = models.ImageField(
        upload_to="ordered_products/",
        blank=True,
        null=True
    )

    quantity = models.IntegerField()
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='NGN price'
    )

    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE
    )

    class Meta:
        db_table = 'OrderItem'

    def sub_total(self):
        return self.quantity * self.price

    def __str__(self):
        return self.product
        


class Customer(models.Model):
    user = models.OneToOneField(
        User, 
        on_delete=models.CASCADE, 
        related_name='customer',
        null=True,  # ✅ Allow null
        blank=True  # ✅ Allow blank in forms
    )
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=250, blank=True)
    lastName = models.CharField(max_length=250, blank=True)
    phonenumber = models.CharField(max_length=20, blank=True, null=True)  # Allows leading zeros, + signs, etc.
    authorization_code = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'Customer'

    def __str__(self):
        return self.email





##################################implememnting number of user on site at any point in time###################################


class Visitor(models.Model):
    """Track unique visitors to the site"""
    session_key = models.CharField(max_length=40, unique=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    first_visit = models.DateTimeField(auto_now_add=True)
    last_visit = models.DateTimeField(auto_now=True)
    visit_count = models.IntegerField(default=1)
    user_agent = models.TextField(blank=True, null=True)
    referer = models.URLField(max_length=2000, blank=True, null=True)
    
    class Meta:
        ordering = ['-last_visit']
    
    def __str__(self):
        return f"{self.session_key} - {self.last_visit}"
    
    @classmethod
    def get_active_visitors(cls, minutes=15):
        """Get visitors active within the last X minutes"""
        cutoff = timezone.now() - datetime.timedelta(minutes=minutes)
        return cls.objects.filter(last_visit__gte=cutoff).count()
    
    @classmethod
    def get_today_visitors(cls):
        """Get unique visitors for today"""
        today = timezone.now().date()
        return cls.objects.filter(first_visit__date=today).count()
    
    @classmethod
    def get_total_visitors(cls):
        """Get total unique visitors ever"""
        return cls.objects.count()

class DailyVisitorStats(models.Model):
    """Store daily visitor statistics"""
    date = models.DateField(unique=True)
    unique_visitors = models.IntegerField(default=0)
    total_page_views = models.IntegerField(default=0)
    registered_users = models.IntegerField(default=0)
    guest_users = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = "Daily Visitor Stats"
    
    def __str__(self):
        return f"{self.date} - {self.unique_visitors} visitors"
    
    @classmethod
    def create_daily_stats(cls, date=None):
        """Create stats for a specific date"""
        if not date:
            date = timezone.now().date()
        
        # Get visitors for this date
        visitors = Visitor.objects.filter(first_visit__date=date)
        unique_count = visitors.count()
        registered_count = visitors.exclude(user__isnull=True).count()
        guest_count = visitors.filter(user__isnull=True).count()
        
        # Get page views (you'll need to track these separately)
        # For now, we'll just count visitors
        stats, created = cls.objects.get_or_create(
            date=date,
            defaults={
                'unique_visitors': unique_count,
                'total_page_views': unique_count * 3,  # Estimate: 3 pages per visit
                'registered_users': registered_count,
                'guest_users': guest_count,
            }
        )
        
        if not created:
            stats.unique_visitors = unique_count
            stats.registered_users = registered_count
            stats.guest_users = guest_count
            stats.save()
        
        return stats





class Voucher(models.Model):
    """Discount voucher/coupon code"""
    
    DISCOUNT_TYPES = [
        ('percentage', 'Percentage (%)'),
        ('fixed', 'Fixed Amount (₦)'),
        ('free_shipping', 'Free Shipping'),
    ]
    
    code = models.CharField(max_length=50, unique=True)
    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPES, default='percentage')
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount or percentage")
    
    # Validity
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)
    
    # Usage limits
    usage_limit = models.PositiveIntegerField(default=1, help_text="Max uses per customer")
    total_usage_limit = models.PositiveIntegerField(default=100, help_text="Max total uses")
    used_count = models.PositiveIntegerField(default=0)
    
    # Restrictions
    min_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    max_discount_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    applicable_to = models.ManyToManyField('Product', blank=True, help_text="Leave blank for all products")
    user_specific = models.ManyToManyField(User, blank=True, help_text="Leave blank for all users")
    
    # Flash sale specific
    is_flash_sale = models.BooleanField(default=False)
    flash_sale_title = models.CharField(max_length=200, blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return self.code
    
    def is_valid(self):
        """Check if voucher is currently valid"""
        now = timezone.now()
        return (
            self.active and
            self.valid_from <= now <= self.valid_to and
            self.used_count < self.total_usage_limit
        )
    
    def is_valid_for_user(self, user):
        """Check if voucher is valid for a specific user"""
        if not self.user_specific.exists():
            return True
        return user in self.user_specific.all()
    
    def apply_discount(self, total):
        """Calculate discount amount based on product total ONLY"""
        if not self.is_valid():
            return 0
        
        # ✅ Only apply to product total, not shipping
        if self.min_order_amount > total:
            return 0
        
        if self.discount_type == 'percentage':
            discount = total * (self.discount_value / 100)
            if self.max_discount_amount:
                discount = min(discount, self.max_discount_amount)
        elif self.discount_type == 'fixed':
            discount = min(self.discount_value, total)
        else:  # free_shipping
            return 0
        
        # ✅ Round to 2 decimal places
        return round(discount, 2)
    
    def increment_usage(self):
        self.used_count += 1
        self.save()


class UserVoucherUsage(models.Model):
    """Track voucher usage per user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    voucher = models.ForeignKey(Voucher, on_delete=models.CASCADE)
    order = models.ForeignKey('Order', on_delete=models.CASCADE)
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2)
    used_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'voucher', 'order']


class FlashSale(models.Model):
    """Flash sale model for time-limited discounts"""
    
    title = models.CharField(max_length=200)
    product = models.ForeignKey('Product', on_delete=models.CASCADE, related_name='flash_sales')
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, help_text="Discount percentage (e.g., 20.00)")
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    max_quantity = models.PositiveIntegerField(default=0, help_text="0 for unlimited")
    sold_count = models.PositiveIntegerField(default=0)
    show_countdown = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} - {self.product.name}"
    
    def is_active_sale(self):
        now = timezone.now()
        return (
            self.is_active and
            self.start_time <= now <= self.end_time and
            (self.max_quantity == 0 or self.sold_count < self.max_quantity)
        )
    
    def get_discounted_price(self):
        if self.product:
            return self.product.price * (1 - self.discount_percentage / 100)
        return 0
    
    def get_remaining_quantity(self):
        if self.max_quantity == 0:
            return None
        return self.max_quantity - self.sold_count
    
    def get_time_remaining(self):
        now = timezone.now()
        if now < self.start_time:
            return self.start_time - now
        elif now < self.end_time:
            return self.end_time - now
        return None
