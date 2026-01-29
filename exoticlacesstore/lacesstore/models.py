from django.db import models
from django.urls import reverse


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

# class CartItem(models.Model):
#     product = models.ForeignKey(Product, on_delete=models.CASCADE)
#     variant = models.ForeignKey(ProductVariant, null=True, blank=True, on_delete=models.SET_NULL)
#     cart = models.ForeignKey(Cart, on_delete=models.CASCADE)
#     quantity = models.IntegerField()
#     active = models.BooleanField(default=True)

#     class Meta:
#         db_table = 'CartItem'

#     def sub_total(self):
#         return self.product.price * self.quantity

#     def __str__(self):
#         return self.product

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


    # def __str__(self):
    #     return self.product
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
   
    total = models.DecimalField(max_digits=10, decimal_places=2, verbose_name='NGN Order Total')
    emailAddress = models.EmailField(max_length=250, blank=True, verbose_name='Email Adress')
    created = models.DateTimeField(auto_now_add=True)
    firstName = models.CharField(max_length=250, blank=True)
    lastName = models.CharField(max_length=250, blank=True)
    country = models.CharField(max_length=250, blank=True)
    state = models.CharField(max_length=250, blank=True)
    phonenumber = models.IntegerField( blank=True)
    shipping_method = models.CharField(max_length=50, null=True, blank=True)
    shipping_cost = models.FloatField(default=0)
    grand_total = models.FloatField(default=0)
    # billingName = models.CharField(max_length=250, blank=True)
    # billingAddress1 = models.CharField(max_length=250, blank=True)
    # billingCity = models.CharField(max_length=250, blank=True)
    # billingPostcode = models.CharField(max_length=250, blank=True)
    # billingCountry = models.CharField(max_length=250, blank=True)
    # shippingName = models.CharField(max_length=250, blank=True)
    # shippingAdress1 = models.CharField(max_length=250, blank=True)
    # shippingCity = models.CharField(max_length=250, blank=True)
    # shippingPostcode = models.CharField(max_length=250, blank=True)
    # shippingCountry = models.CharField(max_length=250, blank=True)

    class Meta:
        db_table = 'Order'
        ordering = ['-created']
    
    def __str__(self):
        return str(self.id)

class OrderItem(models.Model):
    product = models.CharField(max_length=250)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2,verbose_name='NGN price')
    order = models.ForeignKey(Order, on_delete= models.CASCADE) 

    class Meta:
        db_table = 'OrderItem'

    def sub_total(self):
        return self.quantity * self.price

    def __str__(self):
        return self.product
        


class Customerr(models.Model):
    email = models.EmailField(unique=True)
    firstName = models.CharField(max_length=250, blank=True)
    lastName = models.CharField(max_length=250, blank=True)
    phonenumber = models.IntegerField( blank=True)
    authorization_code = models.CharField(max_length=255, blank=True, null=True)

    class Meta:
        db_table = 'Customerr'

    def __str__(self):
        return self.email
