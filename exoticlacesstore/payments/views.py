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

# Helper to get cart
def get_cart(request):
    return Cart.objects.get(cart_id=_cart_id(request))

# Initialize Payment
def init_payment(request):
    if request.method != 'POST':
        return JsonResponse({"status": False, "message": "Invalid request"}, status=400)
    
    email = request.POST.get('email')
    currency = request.POST.get('currency', 'NGN')
    amount = Decimal(request.POST.get('amount', 0))

    if request.method == "POST":
        request.session['checkout_data'] = {
            'email': request.POST.get('email'),
            'phonenumber': request.POST.get('phonenumber'),
            'firstName': request.POST.get('firstName'),
            'lastName': request.POST.get('lastName'),
            'country': request.POST.get('country'),
            'state': request.POST.get('state'),
        }

    
    if not email or amount <= 0:
        return JsonResponse({"status": False, "message": "Email and valid amount required"})

    # Initialize transaction in Paystack
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json",
    }
    ref = f"EXOTIC-{uuid.uuid4().hex[:12]}"

    data = {
        "email": email,
        "amount": int(amount),  # in kobo / cent
        "currency": currency,
        #"callback_url": request.build_absolute_uri("/payments/verify/")
        "reference": ref,  # ✅ CONTROLLED REF
        "callback_url": request.build_absolute_uri(reverse('verify_payment'))

    }

    response = requests.post(
        "https://api.paystack.co/transaction/initialize",
        headers=headers,
        json=data
    ).json()

    # if response.get('status'):
    #     # Save transaction locally
    #     Transaction.objects.create(
    #         reference=response['data']['reference'],
    #         email=email,
    #         amount=amount,  # convert back to major unit
    #         currency=currency,
    #         status='pending'
    #     )

    #     return JsonResponse(response)
    if response.get('status') and response.get('data'):
        ref = ref
        print("PAYSTACK REF:", ref)   # ✅ DEBUG
        Transaction.objects.create(
            reference=ref,
            email=email,
            amount=amount / 100,  # store in kobo for consistency
            currency=currency,
            status='pending'
        )
        return JsonResponse(response)
    else:
        return JsonResponse({
            "status": False,
            "message": "Paystack init failed",
            "paystack_response": response
        }, status=400)

    
    return JsonResponse({"status": False, "message": "Paystack initialization failed"})



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
    order = Order.objects.create(
        total=total,
        emailAddress=transaction.email,
        country=country, state=state, firstName=firstName, lastName=lastName, phonenumber=phonenumber
    )

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

    # Send Email receipt
    # send_mail(
    #     subject=f"Order #{order.id} Confirmation",
    #     message=f"Thank you for your order. Your order ID is {order.id}. Total: {order.total} {transaction.currency}.",
    #     from_email=settings.DEFAULT_FROM_EMAIL,
    #     recipient_list=[transaction.email],
    #     fail_silently=True
    # )

    return redirect('thanks_page', order_id=order.id)


import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse

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
