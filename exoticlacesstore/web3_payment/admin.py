from django.contrib import admin
from .models import (
    Web3Network, Web3Token, Web3Wallet, 
    Web3Payment, Web3TransactionLog, Web3PriceCache
)

@admin.register(Web3Network)
class Web3NetworkAdmin(admin.ModelAdmin):
    list_display = ['name', 'chain_id', 'symbol', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'chain_id']

@admin.register(Web3Token)
class Web3TokenAdmin(admin.ModelAdmin):
    list_display = ['symbol', 'name', 'network', 'is_active']
    list_filter = ['network', 'is_active', 'token_type']
    search_fields = ['symbol', 'name', 'contract_address']

@admin.register(Web3Wallet)
class Web3WalletAdmin(admin.ModelAdmin):
    list_display = ['name', 'network', 'address', 'is_active']
    list_filter = ['network', 'is_active']
    search_fields = ['name', 'address']

@admin.register(Web3Payment)
class Web3PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'order', 'user', 'status', 'amount', 'created_at']
    list_filter = ['status', 'network']
    search_fields = ['order__id', 'user__username', 'tx_hash']
    readonly_fields = ['payment_address', 'tx_hash']
    date_hierarchy = 'created_at'

@admin.register(Web3TransactionLog)
class Web3TransactionLogAdmin(admin.ModelAdmin):
    list_display = ['tx_hash', 'payment', 'block_number', 'status']
    list_filter = ['status']
    search_fields = ['tx_hash', 'payment__order__id']

@admin.register(Web3PriceCache)
class Web3PriceCacheAdmin(admin.ModelAdmin):
    list_display = ['token', 'price', 'source', 'updated_at']
    list_filter = ['source']
    search_fields = ['token__symbol']