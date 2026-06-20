from .models import Category, Cart, CartItem, Order
from.views import _cart_id


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