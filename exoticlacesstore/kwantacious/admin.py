# kwantacious/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Auction, AuctionBid, AuctionDeposit, AuctionPayment

@admin.register(Auction)
class AuctionAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'title', 'product', 'starting_price', 'current_bid', 
        'bid_count', 'status_badge', 'start_time', 'end_time'
    ]
    list_filter = ['status']
    search_fields = ['title', 'product__name']
    readonly_fields = ['current_bid', 'current_winner', 'bid_count', 'winning_bid']
    
    # ✅ Make status editable in the change form
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
            'fields': ('status', 'current_bid', 'current_winner', 'bid_count'),
            'description': 'Change status to "Active" to make this auction live.'
        }),
    )
    
    # ✅ Status badge for list display
    def status_badge(self, obj):
        colors = {
            'draft': 'gray',
            'active': 'green',
            'ended': 'blue',
            'cancelled': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold; background: #f0f0f0; padding: 2px 8px; border-radius: 4px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    # ✅ Add actions to change status
    actions = ['make_active', 'make_ended', 'make_cancelled']
    
    def make_active(self, request, queryset):
        queryset.update(status='active')
        self.message_user(request, f"{queryset.count()} auction(s) marked as Active.")
    make_active.short_description = "Mark selected auctions as Active"
    
    def make_ended(self, request, queryset):
        queryset.update(status='ended')
        self.message_user(request, f"{queryset.count()} auction(s) marked as Ended.")
    make_ended.short_description = "Mark selected auctions as Ended"
    
    def make_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f"{queryset.count()} auction(s) marked as Cancelled.")
    make_cancelled.short_description = "Mark selected auctions as Cancelled"


@admin.register(AuctionBid)
class AuctionBidAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'placed_at']
    list_filter = ['placed_at', 'auction']
    search_fields = ['auction__title', 'user__username']
    readonly_fields = ['auction', 'user', 'amount', 'placed_at']


@admin.register(AuctionDeposit)
class AuctionDepositAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'status_badge', 'created_at']
    list_filter = ['status', 'auction']
    search_fields = ['auction__title', 'user__username']
    readonly_fields = ['auction', 'user', 'amount', 'created_at']
    
    # ✅ Status badge for deposits
    def status_badge(self, obj):
        colors = {
            'held': 'blue',
            'refunded': 'green',
            'forfeited': 'red',
        }
        color = colors.get(obj.status, 'gray')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    # ✅ Actions for deposits
    actions = ['mark_refunded', 'mark_forfeited']
    
    def mark_refunded(self, request, queryset):
        queryset.update(status='refunded')
        self.message_user(request, f"{queryset.count()} deposit(s) marked as Refunded.")
    mark_refunded.short_description = "Mark selected deposits as Refunded"
    
    def mark_forfeited(self, request, queryset):
        queryset.update(status='forfeited')
        self.message_user(request, f"{queryset.count()} deposit(s) marked as Forfeited.")
    mark_forfeited.short_description = "Mark selected deposits as Forfeited"


@admin.register(AuctionPayment)
class AuctionPaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'auction', 'user', 'amount', 'paid_at', 'is_completed_badge']
    list_filter = ['is_completed', 'paid_at']
    search_fields = ['auction__title', 'user__username']
    readonly_fields = ['auction', 'user', 'amount', 'paid_at', 'transaction_ref']
    
    # ✅ Status badge for payments
    def is_completed_badge(self, obj):
        if obj.is_completed:
            return format_html('<span style="color: green; font-weight: bold;">✅ Complete</span>')
        return format_html('<span style="color: orange; font-weight: bold;">⏳ Pending</span>')
    is_completed_badge.short_description = 'Status'
    
    # ✅ Actions for payments
    actions = ['mark_completed']
    
    def mark_completed(self, request, queryset):
        queryset.update(is_completed=True)
        self.message_user(request, f"{queryset.count()} payment(s) marked as Completed.")
    mark_completed.short_description = "Mark selected payments as Completed"