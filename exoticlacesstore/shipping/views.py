
# from django.http import JsonResponse
# from lacesstore.models import Cart, CartItem
# from lacesstore.views import _cart_id
# from .engine import get_shipping_rates


# import json
# from django.views.decorators.csrf import csrf_exempt
# from .models import CartShipping, ShippingMethod
# from .engine import get_shipping_rates
# from lacesstore.views import _cart_id
# from lacesstore.models import Cart, CartItem
# from django.http import JsonResponse


# def shipping_options(request):
#     cart = Cart.objects.get(cart_id=_cart_id(request))
#     items = CartItem.objects.filter(cart=cart, active=True)

#     total_items = sum(i.quantity for i in items)

#     country = request.GET.get('country')
#     state = request.GET.get('state')

#     seller_rate = get_shipping_rates(
#         "seller",
#         country=country,
#         state=state,
#         total_items=total_items
#     )

#     dhl_rate = get_shipping_rates(
#         "dhl",
#         origin={"country":"NG"},
#         destination={"country":country},
#         weight=5,
#         dimensions={"l":30,"w":30,"h":30}
#     )

#     return JsonResponse({
#         "seller": seller_rate,
#         "dhl": dhl_rate
#     })




# @csrf_exempt
# def set_shipping(request):
#     if request.method != "POST":
#         return JsonResponse({"error":"Invalid method"}, status=400)

#     data = json.loads(request.body)
#     method_code = data.get("method")
#     country = data.get("country")
#     state = data.get("state")

#     cart_id = _cart_id(request)
#     cart = Cart.objects.get(cart_id=cart_id)
#     items = CartItem.objects.filter(cart=cart, active=True)

#     total_items = sum(i.quantity for i in items)
#    # total_weight = sum([(i.product.weight or 1) * i.quantity for i in items])

#     rate = get_shipping_rates(
#         method_code,
#         country=country,
#         state=state,
#         total_items=total_items,
#         origin={"country":"NG"},
#         destination={"country":country},
#         # weight=total_weight,
#         dimensions={"l":30,"w":30,"h":30}
#     )

#     method = ShippingMethod.objects.get(provider=method_code)

#     CartShipping.objects.update_or_create(
#         cart_id=cart_id,
#         defaults={
#             "method": method,
#             "cost": rate["amount"],
#             "data": rate
#         }
#     )

#     return JsonResponse({
#         "shipping": rate
#     })



import json
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from lacesstore.models import Cart, CartItem
from lacesstore.views import _cart_id
from .engine import get_shipping_rates


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
        return JsonResponse({"error": "Invalid method"}, status=400)

    data = json.loads(request.body)

    method = data.get("method")
    country = data.get("country")
    state = data.get("state")

    cart = Cart.objects.get(cart_id=_cart_id(request))
    items = CartItem.objects.filter(cart=cart, active=True)
    total_items = sum(i.quantity for i in items)

    # -------- RATE ENGINE --------
    if method == "seller":
        rate = get_shipping_rates(
            "seller",
            country=country,
            state=state,
            total_items=total_items
        )

    elif method == "dhl":
        rate = get_shipping_rates(
            "dhl",
            origin={"country":"NG"},
            destination={"country":country},
            weight=5,
            dimensions={"l":30,"w":30,"h":30}
        )
    else:
        return JsonResponse({"error": "Invalid shipping method"}, status=400)

    # -------- STORE IN SESSION (SOURCE OF TRUTH) --------
    request.session["shipping"] = {
        "method": method,
        "amount": float(rate["amount"]),
        "label": rate["label"],
        "raw": rate
    }

    # return JsonResponse({
    #     "shipping": rate
    # })
    return JsonResponse({
        "shipping": request.session["shipping"]
    })