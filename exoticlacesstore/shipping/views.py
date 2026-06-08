

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


    cart = Cart.objects.get(cart_id=_cart_id(request))
    items = CartItem.objects.filter(cart=cart, active=True)
    total_items = sum(i.quantity for i in items)

    # -------- RATE ENGINE --------
    if method == "seller":
        rate_data = get_shipping_rates(
            "seller",
            country=country,
            state=state,
            total_items=total_items
        )


    # ✅ BASE SHIPPING COST (NGN)
    shipping_cost_ngn = rate_data["amount"]

    # 🔹 2. ACTIVE CURRENCY (UI ONLY)
    active_currency = request.session.get("currency", "NGN")

    # 🔹 3. GET FX RATE (SAFE)
    fx_rate, rate_source = get_exchange_rate(active_currency)

    # 🔹 4. CONVERT FOR DISPLAY
    shipping_cost_fx = round(float(shipping_cost_ngn) * float(fx_rate), 2)

    print(f"FX RATE USED: {fx_rate} ({rate_source})")


    # 🔹 5. SINGLE SOURCE OF TRUTH (SESSION)
    request.session["shipping"] = {
        "method": method,
        "amount_ngn": float(shipping_cost_ngn),
        "amount_fx": shipping_cost_fx,
        "label": rate_data["label"],
        "currency": active_currency,
    }

    # 🔹 6. RETURN CONSISTENT STRUCTURE
    return JsonResponse({
        "shipping": request.session["shipping"]
    })
