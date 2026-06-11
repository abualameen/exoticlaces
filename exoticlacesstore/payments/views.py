import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from decimal import Decimal
from lacesstore.models import Cart, CartItem
from lacesstore.models import Product, ProductVariant, Order, OrderItem
from .models import Transaction
from lacesstore.views import _cart_id  # adjust 'store' to your actual app name
from django.urls import reverse
import uuid

from django.core.mail import send_mail
# In payments/views.py
from lacesstore.views import sendEmail
from shipping.engine import create_provider_shipment
from shipping.models import Shipment, ShippingMethod


# from shipping.models import CartShipping


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# Helper to get cart
def get_cart(request):
    return Cart.objects.get(cart_id=_cart_id(request))

# Initialize Payment
# def init_payment(request):

#     shipping = request.session.get("shipping")

#     if not shipping:
#         return JsonResponse({
#             "status": False,
#             "message": "Shipping method not selected"
#         }, status=400)

#     if request.method != 'POST':
#         return JsonResponse({"status": False, "message": "Invalid request"}, status=400)
    
#     email = request.POST.get('email')
#     currency = request.POST.get('currency', 'NGN')
#     amount = Decimal(request.POST.get('amount', 0))

#     if request.method == "POST":
#         request.session['checkout_data'] = {
#             'email': request.POST.get('email'),
#             'phonenumber': request.POST.get('phonenumber'),
#             'firstName': request.POST.get('firstName'),
#             'lastName': request.POST.get('lastName'),
#             'country': request.POST.get('country'),
#             'state': request.POST.get('state'),
#         }

    
#     if not email or amount <= 0:
#         return JsonResponse({"status": False, "message": "Email and valid amount required"})

#     # Initialize transaction in Paystack
#     headers = {
#         "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
#         "Content-Type": "application/json",
#     }
#     ref = f"EXOTIC-{uuid.uuid4().hex[:12]}"

#     data = {
#         "email": email,
#         "amount": int(amount),  # in kobo / cent
#         "currency": currency,
#         #"callback_url": request.build_absolute_uri("/payments/verify/")
#         "reference": ref,  # ✅ CONTROLLED REF
#         "callback_url": request.build_absolute_uri(reverse('verify_payment'))

#     }

#     response = requests.post(
#         "https://api.paystack.co/transaction/initialize",
#         headers=headers,
#         json=data
#     ).json()

#     # if response.get('status'):
#     #     # Save transaction locally
#     #     Transaction.objects.create(
#     #         reference=response['data']['reference'],
#     #         email=email,
#     #         amount=amount,  # convert back to major unit
#     #         currency=currency,
#     #         status='pending'
#     #     )

#     #     return JsonResponse(response)
#     if response.get('status') and response.get('data'):
#         ref = ref
#         print("PAYSTACK REF:", ref)   # ✅ DEBUG
#         Transaction.objects.create(
#             reference=ref,
#             email=email,
#             amount=amount / 100,  # store in kobo for consistency
#             currency=currency,
#             status='pending'
#         )
#         return JsonResponse(response)
#     else:
#         return JsonResponse({
#             "status": False,
#             "message": "Paystack init failed",
#             "paystack_response": response
#         }, status=400)

#     cart_id = _cart_id(request)
#     # shipping = CartShipping.objects.filter(cart_id=cart_id).first()

#     shipping_cost = shipping.cost if shipping else 0
#     print( 'shipping cost',shipping_cost)
#     total = cart_total + shipping_cost
    
#     print('total', total)

    
#     return JsonResponse({"status": False, "message": "Paystack initialization failed"})


# payments/views.py

from decimal import Decimal
import uuid
import requests
from django.conf import settings
from django.http import JsonResponse
from django.urls import reverse
from lacesstore.models import CartItem
from lacesstore.views import _cart_id
from lacesstore.models import Cart
from .models import Transaction


def init_payment(request):
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "Invalid request"}, status=400)

    # 🔹 Require shipping selection
    shipping = request.session.get("shipping")
    if not shipping:
        return JsonResponse({
            "status": False,
            "message": "Select shipping method first"
        }, status=400)

    # 🔹 Get user info
    email = request.POST.get('email')
    print('this email:', email)
    currency = request.POST.get('currency', 'NGN')
    print("this is currency0", currency)

    if not email:
        return JsonResponse({"status": False, "message": "Email required"}, status=400)

    # # 🔹 Save checkout form to session
    # request.session['checkout_data'] = {
    #     'email': request.POST.get('email'),
    #     'phonenumber': request.POST.get('phonenumber'),
    #     'firstName': request.POST.get('firstName'),
    #     'lastName': request.POST.get('lastName'),
    #     'country': request.POST.get('country'),
    #     'state': request.POST.get('state'),
    # }


    
    checkout_data = {
        'phonenumber': request.POST.get('phonenumber'),
        'firstName': request.POST.get('firstName'),
        'lastName': request.POST.get('lastName'),
        'country': request.POST.get('country'),
        'state': request.POST.get('state'),
    }
    
    # Force use of logged-in user's email
    if request.user.is_authenticated:
        checkout_data['email'] = request.user.email
        print(f"Using authenticated user email: {request.user.email}")
    else:
        checkout_data['email'] = request.POST.get('email')
    
    request.session['checkout_data'] = checkout_data

    

    # 🔹 Calculate totals SERVER-SIDE
    cart = Cart.objects.get(cart_id=_cart_id(request))
    cart_items = CartItem.objects.filter(cart=cart, active=True)

    cart_total = Decimal('0.00')
    for item in cart_items:
        cart_total += Decimal(item.product.price * item.quantity)

    # shipping_cost = Decimal(shipping.get("amount", 0))
    shipping_cost = Decimal(shipping.get("amount_ngn", 0))  # NGN

    grand_total = cart_total + shipping_cost
    amount_kobo = int(grand_total * Decimal('100'))  # convert to kobo


    # 🔹 DEBUG
    print("\n========== PAYSTACK INIT DEBUG ==========")
    print("CART TOTAL (NGN):", cart_total)
    print("SHIPPING COST (NGN):", shipping_cost)
    print("GRAND TOTAL (NGN):", grand_total)
    print("PAYSTACK AMOUNT (KOBO):", amount_kobo)
    print("ACTIVE CURRENCY (UI):", currency)
    print("SHIPPING METHOD:", shipping.get("method"))
    print("========================================\n")


    # 🔹 Init Paystack
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }

    ref = f"EXOTIC-{uuid.uuid4().hex[:12]}"

    data = {
        "email": email,
        "amount": amount_kobo,
        "currency": currency,
        "reference": ref,
        "callback_url": request.build_absolute_uri(reverse('verify_payment'))
    }

    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers=headers,
        json=data
    ).json()

    if not response.get("status"):
        return JsonResponse({
            "status": False,
            "message": "Paystack init failed",
            "paystack": response
        }, status=400)

    # 🔹 Save transaction locally
    Transaction.objects.create(
        reference=ref,
        email=email,
        amount=grand_total,
        currency=currency,
        status='pending'
    )

    print("PAYSTACK REF:", ref)

    # ✅ RETURN AUTHORIZATION URL
    return JsonResponse({
        "status": True,
        "paystack_url": response["data"]["authorization_url"]
    })


@csrf_exempt
def verify_payment(request):

    checkout_data = request.session.get('checkout_data', {})
    

    email = checkout_data.get('email')
    phonenumber = checkout_data.get('phonenumber')
    firstName = checkout_data.get('firstName')
    lastName = checkout_data.get('lastName')
    country = checkout_data.get('country')
    state = checkout_data.get('state')

    reference = request.GET.get('reference')
    if not reference:
        return JsonResponse({"status": False, "message": "Reference not provided"}, status=400)

    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }

    res = requests.get(f"https://api.paystack.co/transaction/verify/{reference}", headers=headers).json()
    if not res.get('status') or res['data']['status'] != 'success':
        return JsonResponse({"status": False, "message": "Transaction failed or not verified"})

    # Retrieve cart
    cart = get_cart(request)
    cart_items = CartItem.objects.filter(cart=cart, active=True)

    # Calculate total
    total = Decimal('0.00')
    for item in cart_items:
        total += item.product.price * item.quantity

    # Update Transaction
    # transaction = get_object_or_404(Transaction, reference=reference)
    transaction = Transaction.objects.filter(reference=reference).first()

    if not transaction:
        return JsonResponse({
            "status": False,
            "message": "Transaction reference not found in local database"
        }, status=404)

    transaction.status = 'success'
    transaction.authorization_code = res['data']['authorization'].get('authorization_code')
    transaction.save()

    # Create Order
    shipping = request.session.get("shipping", {})
    shipping_amount = shipping.get("amount_ngn", 0)
    print("SESSION SHIPPING:", request.session.get("shipping"))

   
    order = Order.objects.create(
    total=total,
    emailAddress=email,
    firstName=firstName,
    lastName=lastName,
    country=country,
    state=state,
    phonenumber=phonenumber,
    shipping_method=shipping.get("method"),
    shipping_cost=shipping_amount,
    grand_total=total + int(shipping_amount),
    currency=request.session.get("currency", "NGN"),
    )
    
    # After successful order creation
    
    # try:
    #     email_sent = sendEmail(order.id)

    #     print("Customer notified via email")
    # except IOError as e:
    #     return e

        


    # Save order items & reduce stock
    for item in cart_items:
        OrderItem.objects.create(
            product=item.product.name,
            quantity=item.quantity,
            price=item.product.price,
            order=order
        )

        if item.variant:
            variant = ProductVariant.objects.get(id=item.variant.id)
            variant.stock -= item.quantity
            variant.save()
        else:
            product = Product.objects.get(id=item.product.id)
            product.stock -= item.quantity
            product.save()

        item.delete()

   ###########################################################################
    
    #After successful order creation
    email_sent = sendEmail(request, order.id)
    if email_sent:
        print("Customer notified via email")
    else:
        print("Failed to send email notification")
    
##################################################################################




    
    shipping = request.session.get("shipping", {})

    # 🔹 call provider (seller or dhl)
    shipment_data = create_provider_shipment(
        shipping["method"],
        order
    )

    method_obj = ShippingMethod.objects.get(provider=shipping["method"])

    Shipment.objects.create(
        order=order,
        method=method_obj,
        cost=shipping.get("amount", 0),
        tracking_number=shipment_data.get("tracking_number"),
        status="CREATED",
        provider_response=shipment_data   # ✅ now defined
    )
   

    if "shipping" in request.session:
        del request.session["shipping"]

   

    return redirect('thanks_page', order_id=order.id)




@csrf_exempt
def paystack_webhook(request):
    payload = json.loads(request.body)
    event = payload.get('event')

    if event == 'charge.success':
        reference = payload['data']['reference']
        transaction = Transaction.objects.filter(reference=reference).first()
        if transaction and transaction.status != 'success':
            transaction.status = 'success'
            transaction.save()
            # Optionally reconcile stock or notify admin

    return HttpResponse(status=200)
