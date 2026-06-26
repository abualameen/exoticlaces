import requests
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from decimal import Decimal
from lacesstore.models import Cart, CartItem
from lacesstore.models import Product, ProductVariant, Order, OrderItem, Customer 
from .models import Transaction
from lacesstore.views import _cart_id  # adjust 'store' to your actual app name
from django.urls import reverse
import uuid
from django.core.mail import send_mail
# In payments/views.py
from lacesstore.views import sendEmail
from shipping.engine import create_provider_shipment
from shipping.models import Shipment, ShippingMethod
from lacesstore.facebook_capi import send_facebook_event


# from shipping.models import CartShipping


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

# Helper to get cart
def get_cart(request):
    return Cart.objects.get(cart_id=_cart_id(request))



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

    # if not response.get("status"):
    #     return JsonResponse({
    #         "status": False,
    #         "message": "Paystack init failed",
    #         "paystack": response
    #     }, status=400)
    # 🔥 DEBUG: Print the FULL response
    print("=" * 50)
    print("PAYSTACK RESPONSE:")
    print(response)
    print("=" * 50)
    
    if not response.get("status"):
        return JsonResponse({
            "status": False,
            "message": response.get("message", "Paystack init failed"),
            "paystack": response  # Include full response for debugging
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
    # cart = get_cart(request)
    # cart_items = CartItem.objects.filter(cart=cart, active=True)
    try:
        cart = get_cart(request)
        cart_items = CartItem.objects.filter(cart=cart, active=True)
    except Cart.DoesNotExist:
        # If cart doesn't exist, check if this is a duplicate callback
        reference = request.GET.get('reference')
        if Transaction.objects.filter(reference=reference, status='success').exists():
            # Already processed, redirect to home
            return redirect('home')
        # Otherwise, create an empty cart
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart_items = []

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

    customer = None
    
    if request.user.is_authenticated:
        # Try to get existing customer, or create one
        customer, created = Customer.objects.get_or_create(
            user=request.user,
            defaults={
                'email': request.user.email,
                'firstName': request.user.first_name,
                'lastName': request.user.last_name,
                'phonenumber': phonenumber,
            }
        )
    else:
        # Guest user - create customer by email
        customer, created = Customer.objects.get_or_create(
            email=email,
            defaults={
                'firstName': firstName,
                'lastName': lastName,
                'phonenumber': phonenumber,
            }
        )


    order = Order.objects.create(
    customer=customer,
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
            product_image=item.variant.image if item.variant else item.product.image,
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


    if request.user.is_authenticated:
        send_facebook_event(
            request,
            'Purchase',
            {
                'content_ids': [str(item.id) for item in cart_items],
                'content_type': 'product',
                'value': str(order.grand_total),
                'currency': 'NGN',
                'transaction_id': str(order.id)
            }
        )

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
