# kwantacious/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Auction, AuctionBid, AuctionDeposit, AuctionPayment

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'product', 'starting_price', 'current_bid', 
        'bid_count', 'status', 'start_time', 'end_time', 'status_badge'
    ]
    list_filter = ['status']
    search_fields = ['title', 'product__name']
    readonly_fields = ['current_bid', 'current_winner', 'bid_count', 'winning_bid']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'title', 'description')
        }),
        ('Pricing', {
            'fields': ('starting_price', 'reserve_price', 'minimum_bid_increment')
        }),
        ('Security Deposit', {
            'fields': ('security_deposit',),
            'description': 'Refundable deposit to ensure serious bidders. 100% refunded to non-winners.'
        }),
        ('Timing', {
            'fields': ('start_time', 'end_time', 'auto_extend', 'auto_extend_minutes')
        }),
        ('Status', {
            'fields': ('status', 'current_bid', 'current_winner', 'bid_count')
        }),
    )
    
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'active': 'green',
            'ended': 'blue',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'

@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'placed_at']
    list_filter = ['placed_at']
    search_fields = ['auction__title', 'user__username']

@admin.register(AuctionDeposit)
class AuctionDepositAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'status', 'created_at']
    list_filter = ['status']
    search_fields = ['auction__title', 'user__username']

@admin.register(AuctionPayment)
class AuctionPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'paid_at', 'is_completed']
    list_filter = ['is_completed']
    search_fields = ['auction__title', 'user__username']