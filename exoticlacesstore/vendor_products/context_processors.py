# vendor_products/context_processors.py
from .models import VendorCart
from .views import get_or_create_cart

def vendor_cart_count(request):
    """Add vendor cart item count to context"""
    try:
        cart = get_or_create_cart(request)
        count = cart.get_total_items() if cart else 0
        return {
            'vendor_cart_count': count,
            'has_vendor_cart_items': count > 0,
        }
    except:
        return {
            'vendor_cart_count': 0,
            'has_vendor_cart_items': False,
        }