# kwantacious/models.py
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
from lacesstore.models import Product

class Auction(models.Model):
    """Islamically compliant auction - FREE to join and bid"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('ended', 'Ended'),
        ('cancelled', 'Cancelled'),
    ]
    
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='auctions')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Describe the product and auction terms")
    
    # ✅ Bidding settings (NO ENTRY FEE - completely free to join)
    starting_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        help_text="Minimum bid amount - typically the product's cost price"
    )
    reserve_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        null=True, 
        blank=True,
        help_text="Optional: Minimum price seller will accept. If not met, auction can be cancelled."
    )
    minimum_bid_increment = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=1000,
        help_text="Minimum amount each new bid must increase by"
    )
    
    # ✅ NO ENTRY FEE - removed completely
    # ✅ Security deposit is OPTIONAL and 100% REFUNDABLE
    security_deposit = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        default=0,
        help_text="OPTIONAL: Refundable deposit to ensure serious bidders. 100% refunded to non-winners."
    )
    
    # Timings
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    auto_extend = models.BooleanField(default=True, help_text="Extend auction if bid placed near end")
    auto_extend_minutes = models.IntegerField(default=5)
    
    # Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Tracking
    current_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_winner = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='kwantacious_winning_auctions'
    )
    bid_count = models.IntegerField(default=0)
    
    # Winner payment
    winning_bid = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_paid = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Auction'
        verbose_name_plural = 'Auctions'
    
    def __str__(self):
        return f"{self.title} - {self.product.name}"
    
    def is_active(self):
        now = timezone.now()
        return self.status == 'active' and self.start_time <= now <= self.end_time
    
    def get_bid_count(self):
        return self.bids.count()
    
    def get_winner(self):
        winner_bid = self.bids.order_by('-amount').first()
        if winner_bid:
            return winner_bid.user
        return None
    
    def get_winning_bid_amount(self):
        winner_bid = self.bids.order_by('-amount').first()
        if winner_bid:
            return winner_bid.amount
        return None
    
    def reserve_met(self):
        if self.reserve_price is None:
            return True
        return self.current_bid >= self.reserve_price


class AuctionBid(models.Model):
    """Free bids placed by users - NO PAYMENT REQUIRED TO BID"""
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kwantacious_bids')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    placed_at = models.DateTimeField(auto_now_add=True)
    is_winning = models.BooleanField(default=False)
    
    # ✅ Deposit tracking (only if deposit was placed)
    deposit_held = models.BooleanField(default=False)
    deposit_refunded = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-amount', 'placed_at']
    
    def __str__(self):
        return f"{self.user.username} - ₦{self.amount}"


class AuctionDeposit(models.Model):
    """OPTIONAL: Refundable security deposit (100% refundable to non-winners)"""
    STATUS_CHOICES = [
        ('held', 'Held'),
        ('refunded', 'Refunded'),
        ('forfeited', 'Forfeited'),  # Only if winner fails to pay
    ]
    
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='deposits')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kwantacious_deposits')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='held')
    transaction_ref = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.auction.title} - {self.status}"


class AuctionPayment(models.Model):
    """Winner's final payment only"""
    auction = models.OneToOneField(Auction, on_delete=models.CASCADE, related_name='payment')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='kwantacious_payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    paid_at = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=100, blank=True)
    is_completed = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.username} - {self.auction.title} - ₦{self.amount}"