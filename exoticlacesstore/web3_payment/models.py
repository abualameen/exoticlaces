from django.db import models
from django.contrib.auth.models import User
from decimal import Decimal
from django.utils import timezone
from django.core.validators import MinValueValidator

class Web3Network(models.Model):
    """Supported blockchain networks"""
    name = models.CharField(max_length=50)
    chain_id = models.IntegerField(unique=True)
    rpc_url = models.URLField()
    explorer_url = models.URLField()
    symbol = models.CharField(max_length=10, default='ETH')
    is_active = models.BooleanField(default=True)
    confirmations_required = models.IntegerField(default=12)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} (Chain ID: {self.chain_id})"

    class Meta:
        verbose_name = 'Web3 Network'
        verbose_name_plural = 'Web3 Networks'


class Web3Token(models.Model):
    """Supported tokens"""
    TOKEN_TYPES = [
        ('native', 'Native Token'),
        ('erc20', 'ERC-20'),
        ('erc721', 'ERC-721'),
        ('erc1155', 'ERC-1155'),
    ]
    
    name = models.CharField(max_length=100)
    symbol = models.CharField(max_length=20)
    contract_address = models.CharField(max_length=100, blank=True, null=True)
    network = models.ForeignKey(Web3Network, on_delete=models.CASCADE, related_name='tokens')
    token_type = models.CharField(max_length=20, choices=TOKEN_TYPES, default='erc20')
    decimals = models.IntegerField(default=18)
    usd_price = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['contract_address', 'network']
        verbose_name = 'Web3 Token'
        verbose_name_plural = 'Web3 Tokens'

    def __str__(self):
        return f"{self.symbol} on {self.network.name}"


class Web3Wallet(models.Model):
    """Store merchant wallet information"""
    name = models.CharField(max_length=100)
    network = models.ForeignKey(Web3Network, on_delete=models.CASCADE)
    address = models.CharField(max_length=100, unique=True)
    private_key = models.CharField(max_length=255)  # Will be encrypted in production
    is_active = models.BooleanField(default=True)
    balance = models.DecimalField(max_digits=20, decimal_places=8, default=0)
    last_balance_check = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} - {self.network.name}"

    class Meta:
        verbose_name = 'Web3 Wallet'
        verbose_name_plural = 'Web3 Wallets'


class Web3Payment(models.Model):
    """Track Web3 payments"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirming', 'Confirming'),
        ('confirmed', 'Confirmed'),
        ('failed', 'Failed'),
        ('expired', 'Expired'),
    ]
    
    order = models.ForeignKey('lacesstore.Order', on_delete=models.SET_NULL, null=True, blank=True, related_name='web3_payments')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    token = models.ForeignKey(Web3Token, on_delete=models.SET_NULL, null=True)
    network = models.ForeignKey(Web3Network, on_delete=models.SET_NULL, null=True)
    
    # Payment details
    amount = models.DecimalField(max_digits=20, decimal_places=8, validators=[MinValueValidator(0)])
    usd_amount = models.DecimalField(max_digits=20, decimal_places=2, validators=[MinValueValidator(0)])
    
    # Blockchain transaction
    tx_hash = models.CharField(max_length=100, unique=True, blank=True, null=True)
    from_address = models.CharField(max_length=100, blank=True)
    to_address = models.CharField(max_length=100)
    
    # Payment address (unique per order)
    payment_address = models.CharField(max_length=100, unique=True)
    payment_uri = models.TextField(blank=True)
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    confirmations = models.IntegerField(default=0)
    required_confirmations = models.IntegerField(default=12)
    expires_at = models.DateTimeField()
    
    # Metadata
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Payment #{self.id} - Order #{self.order.id if self.order else 'None'} - {self.status}"

    class Meta:
        verbose_name = 'Web3 Payment'
        verbose_name_plural = 'Web3 Payments'


class Web3TransactionLog(models.Model):
    """Log all blockchain transactions for auditing"""
    payment = models.ForeignKey(Web3Payment, on_delete=models.CASCADE, related_name='logs')
    tx_hash = models.CharField(max_length=100)
    block_number = models.IntegerField()
    block_hash = models.CharField(max_length=100)
    from_address = models.CharField(max_length=100)
    to_address = models.CharField(max_length=100)
    value = models.DecimalField(max_digits=20, decimal_places=8)
    gas_price = models.DecimalField(max_digits=20, decimal_places=8)
    gas_used = models.IntegerField()
    status = models.BooleanField(default=True)
    timestamp = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Tx {self.tx_hash[:10]}..."

    class Meta:
        verbose_name = 'Web3 Transaction Log'
        verbose_name_plural = 'Web3 Transaction Logs'


class Web3PriceCache(models.Model):
    """Cache token prices to avoid excessive API calls"""
    token = models.ForeignKey(Web3Token, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=20, decimal_places=8)
    source = models.CharField(max_length=100)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['token', 'source']
        verbose_name = 'Web3 Price Cache'
        verbose_name_plural = 'Web3 Price Caches'