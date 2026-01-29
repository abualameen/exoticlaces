from django.db import models

# Create your models here.
from django.db import models
from lacesstore.models import Order

class ShippingMethod(models.Model):
    PROVIDER_CHOICES = (
        ('seller', 'Seller Shipping'),
        ('dhl', 'DHL'),
    )

    name = models.CharField(max_length=100)
    provider = models.CharField(max_length=20, choices=PROVIDER_CHOICES)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.provider})"


class ShippingRate(models.Model):
    method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
    country = models.CharField(max_length=50)
    state = models.CharField(max_length=50, blank=True, null=True)
    price_per_item = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.method.name} - {self.country} - {self.state or 'ALL'}"


class Shipment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE)
    method = models.ForeignKey(ShippingMethod, on_delete=models.SET_NULL, null=True)
    cost = models.DecimalField(max_digits=12, decimal_places=2)
    tracking_number = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=50, default="pending")
    provider_response = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)


# class CartShipping(models.Model):
#     cart_id = models.CharField(max_length=250, unique=True)
#     method = models.ForeignKey(ShippingMethod, on_delete=models.CASCADE)
#     cost = models.DecimalField(max_digits=12, decimal_places=2)
#     data = models.JSONField(blank=True, null=True)
#     updated_at = models.DateTimeField(auto_now=True)

