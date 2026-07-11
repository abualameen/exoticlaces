from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone
import datetime


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
