

import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from lacesstore.models import Cart, CartItem
from lacesstore.views import _cart_id
from .engine import get_shipping_rates
from payments.services.exchange import get_exchange_rate
from .services import calculate_seller_shipping
from decimal import Decimal

from exoticlacesstore.utils.currency import convert   # 👈 import converter
from django.conf import settings


def shipping_options(request):
    cart = Cart.objects.get(cart_id=_cart_id(request))
    items = CartItem.objects.filter(cart=cart, active=True)

    total_items = sum(i.quantity for i in items)

    country = request.GET.get('country')
    state = request.GET.get('state')

    seller_rate = get_shipping_rates(
        "seller",
        country=country,
        state=state,
        total_items=total_items
    )

    dhl_rate = get_shipping_rates(
        "dhl",
        origin={"country":"NG"},
        destination={"country":country},
        weight=5,
        dimensions={"l":30,"w":30,"h":30}
    )

    return JsonResponse({
        "seller": seller_rate,
        "dhl": dhl_rate
    })


@csrf_exempt
def set_shipping(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid request"}, status=400)

    data = json.loads(request.body)

    method = data.get("method")
    country = data.get("country")
    state = data.get("state")

    if not method:
        return JsonResponse({"error": "Shipping method required"}, status=400)

    # ✅ Get cart - try vendor cart first, then main cart
    from vendor_products.models import VendorCart
    from vendor_products.views import get_or_create_cart
    
    cart = None
    total_items = 0
    is_vendor_cart = False
    
    # Check if we're in the vendor cart context
    try:
        vendor_cart = get_or_create_cart(request)
        if vendor_cart and vendor_cart.items.exists():
            cart = vendor_cart
            total_items = sum(item.quantity for item in vendor_cart.items.all())
            is_vendor_cart = True
            print(f"✅ Using vendor cart: {total_items} items")
    except:
        pass
    
    # If no vendor cart, use main cart
    if not cart or total_items == 0:
        try:
            from lacesstore.models import Cart, CartItem
            from lacesstore.views import _cart_id
            main_cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=main_cart, active=True)
            total_items = sum(i.quantity for i in cart_items)
            print(f"✅ Using main cart: {total_items} items")
        except:
            print("⚠️ No cart found")
    
    # If still no items, use a default
    if total_items == 0:
        total_items = 1
        print("⚠️ No items found, using default: 1")

    # -------- RATE ENGINE --------
    if method == "seller":
        from .services import calculate_seller_shipping
        shipping_cost = calculate_seller_shipping(country, state, total_items)
        rate_data = {
            "amount": float(shipping_cost),
            "label": "Seller Shipping"
        }
    elif method == "dhl":
        # DHL calculation
        rate_data = {
            "amount": 5000.00,
            "label": "DHL Express"
        }
    else:
        return JsonResponse({"error": "Invalid shipping method"}, status=400)

    # ✅ BASE SHIPPING COST (NGN)
    shipping_cost_ngn = rate_data["amount"]

    # 🔹 2. ACTIVE CURRENCY (UI ONLY)
    active_currency = request.session.get("currency", "NGN")

    # 🔹 3. GET FX RATE (SAFE)
    from payments.services.exchange import get_exchange_rate
    fx_rate, rate_source = get_exchange_rate(active_currency)

    # 🔹 4. CONVERT FOR DISPLAY
    shipping_cost_fx = round(float(shipping_cost_ngn) * float(fx_rate), 2)

    print(f"✅ Shipping calculated: {shipping_cost_ngn} NGN, {shipping_cost_fx} {active_currency}")

    # 🔹 5. SINGLE SOURCE OF TRUTH (SESSION)
    request.session["shipping"] = {
        "method": method,
        "amount_ngn": float(shipping_cost_ngn),
        "amount_fx": shipping_cost_fx,
        "label": rate_data["label"],
        "currency": active_currency,
        "is_vendor": True, 
    }

    # 🔹 6. RETURN CONSISTENT STRUCTURE
    return JsonResponse({
        "shipping": request.session["shipping"]
    })