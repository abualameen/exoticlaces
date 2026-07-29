from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
import requests
import json
from decimal import Decimal

from .models import VendorProduct, VendorOrder, VendorCart, VendorCartItem
from lacesstore.models import Customer
from exoticlacesstore.utils.currency import get_symbol


def vendor_product_list(request):
    """Display all active vendor products"""
    products = VendorProduct.objects.filter(status='active', available=True)
    
    # Get currency
    active_currency = request.session.get("currency", "NGN")
    
    context = {
        'vendor_products': products,
        'currency': active_currency,
        'is_vendor_section': True,
    }
    return render(request, 'vendor_products/product_list.html', context)


def vendor_product_detail(request, product_id):
    """Display single vendor product detail"""
    product = get_object_or_404(VendorProduct, id=product_id, status='active')
    
    # Get currency
    active_currency = request.session.get("currency", "NGN")
    
    context = {
        'product': product,
        'currency': active_currency,
        'currency_symbol': get_symbol(active_currency),
    }
    return render(request, 'vendor_products/product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    """Add vendor product to vendor cart"""
    product = get_object_or_404(VendorProduct, id=product_id, status='active')
    
    if product.stock <= 0:
        messages.error(request, "This product is currently out of stock.")
        return redirect('vendor_products:product_detail', product_id=product.id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        shipping_address = request.POST.get('shipping_address', '').strip()
        
        if not shipping_address:
            messages.error(request, "Please provide your shipping address.")
            return redirect('vendor_products:product_detail', product_id=product.id)
        
        if quantity > product.stock:
            messages.error(request, f"Only {product.stock} items available.")
            return redirect('vendor_products:product_detail', product_id=product.id)
        
        # Get or create vendor cart
        cart, created = VendorCart.objects.get_or_create(user=request.user)
        
        # Check if item already in cart
        cart_item = VendorCartItem.objects.filter(cart=cart, product=product).first()
        
        if cart_item:
            # Update existing item
            cart_item.quantity += quantity
            cart_item.shipping_address = shipping_address
            cart_item.save()
            messages.success(request, f"Updated {product.name} quantity in your cart.")
        else:
            # Add new item
            VendorCartItem.objects.create(
                cart=cart,
                product=product,
                quantity=quantity,
                shipping_address=shipping_address
            )
            messages.success(request, f"{product.name} added to your cart!")
        
        return redirect('vendor_products:cart_detail')
    
    return redirect('vendor_products:product_detail', product_id=product.id)


@login_required
def cart_detail(request):
    """Display vendor cart"""
    cart = VendorCart.objects.filter(user=request.user).first()
    
    if not cart:
        cart = VendorCart.objects.create(user=request.user)
    
    cart_items = cart.items.all()
    total = cart.get_total()
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'currency': request.session.get("currency", "NGN"),
        'total_items': cart.get_total_items(),
    }
    return render(request, 'vendor_products/cart_detail.html', context)


@login_required
def remove_from_cart(request, item_id):
    """Remove item from vendor cart"""
    cart_item = get_object_or_404(VendorCartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('vendor_products:cart_detail')


@login_required
def update_cart_item(request, item_id):
    """Update quantity of cart item"""
    cart_item = get_object_or_404(VendorCartItem, id=item_id, cart__user=request.user)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cart updated.")
    
    return redirect('vendor_products:cart_detail')


@login_required
def checkout(request):
    """Checkout vendor cart - Wa'ad model with Paystack preauthorization"""
    cart = VendorCart.objects.filter(user=request.user).first()
    
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('vendor_products:product_list')
    
    if request.method == 'POST':
        cart_items = cart.items.all()
        total = cart.get_total()
        
        # Create a single order for all items
        order = VendorOrder.objects.create(
            customer=request.user,
            product=cart_items.first().product,  # Primary product
            quantity=sum(item.quantity for item in cart_items),
            total_amount=total,
            shipping_address=cart_items.first().shipping_address,
            status='pending',
            payment_status='authorized'
        )
        
        # Initialize Paystack Preauthorization
        try:
            paystack_data = initialize_paystack_hold(
                amount=total,
                email=request.user.email,
                reference=f"VENDOR-{order.id}-{int(timezone.now().timestamp())}",
                order_id=order.id
            )
            
            if paystack_data.get('status'):
                order.paystack_reference = paystack_data['data']['reference']
                order.paystack_access_code = paystack_data['data']['access_code']
                order.payment_intent_id = paystack_data['data']['reference']
                order.save()
                
                # Clear the cart
                cart.clear()
                
                # Redirect to Paystack
                return redirect(paystack_data['data']['authorization_url'])
            else:
                messages.error(request, "Payment initialization failed. Please try again.")
                order.delete()
                return redirect('vendor_products:cart_detail')
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            order.delete()
            return redirect('vendor_products:cart_detail')
    
    return redirect('vendor_products:cart_detail')


@login_required
def place_order_request(request, product_id):
    """
    Wa'ad (Promise to Purchase) - Customer places order request
    Payment is AUTHORIZED (hold) not captured
    (Legacy - kept for compatibility)
    """
    product = get_object_or_404(VendorProduct, id=product_id, status='active')
    
    if product.stock <= 0 or not product.available:
        messages.error(request, "This product is currently out of stock.")
        return redirect('vendor_products:product_detail', product_id=product.id)
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        shipping_address = request.POST.get('shipping_address')
        
        if not shipping_address:
            messages.error(request, "Please provide your shipping address.")
            return redirect('vendor_products:product_detail', product_id=product.id)
        
        # Calculate total
        total_amount = product.price * quantity
        
        # Create order request
        order = VendorOrder.objects.create(
            customer=request.user,
            product=product,
            quantity=quantity,
            total_amount=total_amount,
            shipping_address=shipping_address,
            status='pending',
            payment_status='authorized'
        )
        
        # Initialize Paystack Preauthorization (Hold)
        try:
            paystack_data = initialize_paystack_hold(
                amount=total_amount,
                email=request.user.email,
                reference=f"VENDOR-{order.id}-{int(timezone.now().timestamp())}",
                order_id=order.id
            )
            
            if paystack_data.get('status'):
                order.paystack_reference = paystack_data['data']['reference']
                order.paystack_access_code = paystack_data['data']['access_code']
                order.payment_intent_id = paystack_data['data']['reference']
                order.save()
                
                return redirect(paystack_data['data']['authorization_url'])
            else:
                messages.error(request, "Payment initialization failed. Please try again.")
                order.delete()
                return redirect('vendor_products:product_detail', product_id=product.id)
                
        except Exception as e:
            messages.error(request, f"An error occurred: {str(e)}")
            order.delete()
            return redirect('vendor_products:product_detail', product_id=product.id)
    
    return redirect('vendor_products:product_detail', product_id=product.id)


def initialize_paystack_hold(amount, email, reference, order_id):
    """Initialize Paystack Preauthorization (hold funds)"""
    url = "https://api.paystack.co/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "amount": int(amount * 100),  # Paystack uses kobo
        "email": email,
        "reference": reference,
        "metadata": {
            "order_id": order_id,
            "payment_type": "preauthorization",
            "custom_fields": [
                {
                    "display_name": "Payment Action",
                    "variable_name": "action",
                    "value": "preauth"
                }
            ]
        },
        "channels": ["card"],
        "expire_after_days": 7
    }
    
    response = requests.post(url, json=payload, headers=headers)
    return response.json()


@login_required
def order_request_success(request, order_id):
    """Order request success page after Paystack redirect"""
    order = get_object_or_404(VendorOrder, id=order_id, customer=request.user)
    
    if order.paystack_reference:
        verification = verify_paystack_payment(order.paystack_reference)
        if verification.get('status'):
            messages.success(request, "✅ Your order request has been placed! A temporary hold has been placed on your card. We'll confirm availability within 24 hours.")
        else:
            messages.warning(request, "Your order was placed but we're verifying payment status.")
    
    context = {
        'order': order,
        'product': order.product,
        'is_vendor_section': True,
    }
    return render(request, 'vendor_products/order_success.html', context)


def verify_paystack_payment(reference):
    """Verify Paystack payment status"""
    url = f"https://api.paystack.co/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    
    response = requests.get(url, headers=headers)
    return response.json()


@login_required
def capture_payment(request, order_id):
    """
    Admin/Staff only: Capture the held payment after vendor confirms stock
    This completes the Islamic contract (Wa'ad)
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('vendor_products:product_list')
    
    order = get_object_or_404(VendorOrder, id=order_id)
    
    if not order.can_capture_payment():
        messages.error(request, "This order cannot be captured. Status must be 'secured' and payment authorized.")
        return redirect('vendor_products:product_list')
    
    url = "https://api.paystack.co/transaction/capture"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "reference": order.paystack_reference,
        "amount": int(order.total_amount * 100)
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get('status'):
            order.payment_status = 'captured'
            order.status = 'shipped'
            order.save()
            messages.success(request, f"✅ Payment of ₦{order.total_amount:,.2f} captured successfully for Order #{order.id}")
        else:
            messages.error(request, f"Payment capture failed: {data.get('message', 'Unknown error')}")
            
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('vendor_products:product_list')


@login_required
def cancel_order_hold(request, order_id):
    """
    Admin/Staff only: Cancel the payment hold if vendor cannot fulfill
    No money leaves the customer's account - perfectly Islamic
    """
    if not request.user.is_staff:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('vendor_products:product_list')
    
    order = get_object_or_404(VendorOrder, id=order_id)
    
    if order.payment_status != 'authorized':
        messages.error(request, "This payment is not in authorized status.")
        return redirect('vendor_products:product_list')
    
    url = "https://api.paystack.co/transaction/void"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "reference": order.paystack_reference
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        if data.get('status'):
            order.payment_status = 'refunded'
            order.status = 'cancelled'
            order.save()
            messages.success(request, f"✅ Payment hold cancelled for Order #{order.id}. No funds were charged.")
        else:
            messages.error(request, f"Failed to cancel hold: {data.get('message', 'Unknown error')}")
            
    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
    
    return redirect('vendor_products:product_list')


def vendor_products_home_context(request):
    """Context processor to add vendor products to home page"""
    products = VendorProduct.objects.filter(status='active', available=True)[:8]
    return {
        'vendor_products': products,
        'has_vendor_products': products.exists(),
    }


@csrf_exempt
def paystack_webhook(request):
    """Handle Paystack webhook events"""
    if request.method == 'POST':
        try:
            payload = json.loads(request.body)
            event = payload.get('event')
            
            if event == 'charge.success':
                reference = payload['data']['reference']
                try:
                    order = VendorOrder.objects.get(paystack_reference=reference)
                    order.payment_status = 'captured'
                    order.save()
                    print(f"✅ Payment captured for order {order.id}")
                except VendorOrder.DoesNotExist:
                    print(f"⚠️ Order not found for reference {reference}")
            
            return JsonResponse({'status': 'success'})
        except Exception as e:
            print(f"Webhook error: {str(e)}")
            return JsonResponse({'status': 'error'}, status=400)
    
    return JsonResponse({'status': 'failed'}, status=405)