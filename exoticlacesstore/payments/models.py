from django.db import models
from django.conf import settings
from decimal import Decimal


class Transaction(models.Model):
    CURRENCY_CHOICES = [
        ('NGN', 'Naira'),
        ('USD', 'US Dollar'),
        ('GHS', 'Cedi'),
        ('XOF', 'CFA'),
        ('EUR', 'EURO')
    ]

    reference = models.CharField(max_length=100, unique=True)
    email = models.EmailField()
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    currency = models.CharField(max_length=3, choices=CURRENCY_CHOICES, default='NGN')
    status = models.CharField(max_length=20, default='pending')  # pending, success, failed
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_id = models.IntegerField(null=True, blank=True)  # Link to your Order model

    def __str__(self):
        return f"{self.reference} - {self.status}"





class ExchangeRate(models.Model):
    base = models.CharField(max_length=10, default="NGN")
    target = models.CharField(max_length=10)
    rate = models.FloatField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("base", "target")

    def __str__(self):
        return f"{self.base} → {self.target}: {self.rate}"

