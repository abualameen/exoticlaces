from .models import Category, Cart, CartItem, Order, Voucher, FlashSale
from.views import _cart_id
from django.utils import timezone
from django.db import models  # ✅ Add this import






def counter(request):
    item_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                item_count += cart_item.quantity
        except Cart.DoesNotExist:
            item_count = 0
    return dict(item_count=item_count)

def menu_links(request):
    links = Category.objects.all()
    return dict(links=links)


def orderid(request):
    eds = Order.objects.latest('id')
    return dict(eds=eds)




# lacesstore/context_processors.py
def social_links(request):
    return {
        'SOCIAL_LINKS': {
            'facebook': 'https://www.facebook.com/profile.php?id=61573582768272&mibextid=ZbWKwL',
            'instagram': 'https://www.instagram.com/exoticlaces_and_more?igsh=OGQ5ZDc2ODk2ZA==',
            'youtube': 'https://www.youtube.com/channel/UCiET439BjAQNE00DstJWJcw?sub_confirmation=1',
            'tiktok': 'https://www.tiktok.com/@exotic_laces_webstore?_r=1&_t=ZS-97LTPlLQI9n',
            'whatsapp': 'https://wa.me/2347012162731',  # Replace with your WhatsApp number
        }
    }


def facebook_pixel(request):
    return {
        'FACEBOOK_PIXEL_ID': '1333267468229990',  
    }









def sale_context(request):
    """Make flash sales and active vouchers available to all templates"""
    
    now = timezone.now()
    
    # Get active flash sales
    flash_sales = FlashSale.objects.filter(
        is_active=True,
        start_time__lte=now,
        end_time__gte=now
    ).select_related('product')
    
    # Get valid vouchers for the user
    vouchers = Voucher.objects.filter(
        active=True,
        valid_from__lte=now,
        valid_to__gte=now,
        is_flash_sale=False
    ).exclude(used_count__gte=models.F('total_usage_limit'))
    
    # User-specific vouchers
    if request.user.is_authenticated:
        user_vouchers = vouchers.filter(
            models.Q(user_specific__isnull=True) | models.Q(user_specific=request.user)
        )
    else:
        user_vouchers = vouchers.filter(user_specific__isnull=True)
    
    return {
        'active_flash_sales': flash_sales,
        'available_vouchers': user_vouchers[:10],  # Limit to 10
        'has_active_sales': flash_sales.exists() or user_vouchers.exists(),
    }