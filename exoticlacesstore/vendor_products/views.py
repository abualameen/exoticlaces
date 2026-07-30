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


def get_or_create_cart(request):
    """Get or create a vendor cart for user or session"""
    if request.user.is_authenticated:
        cart, created = VendorCart.objects.get_or_create(user=request.user, session_key=None)
        # If there's a session cart, merge it
        if request.session.session_key:
            session_cart = VendorCart.objects.filter(session_key=request.session.session_key, user=None).first()
            if session_cart:
                # Move items from session cart to user cart
                for item in session_cart.items.all():
                    item.cart = cart
                    item.save()
                session_cart.delete()
        return cart
    else:
        # Guest user - use session
        if not request.session.session_key:
            request.session.create()
        cart, created = VendorCart.objects.get_or_create(session_key=request.session.session_key, user=None)
        return cart

def clear_vendor_shipping_session(request):
    """Clear shipping session for vendor cart"""
    if "shipping" in request.session:
        # Only clear if it's a vendor cart session
        if request.session.get("shipping", {}).get("is_vendor", False):
            del request.session["shipping"]
            print("✅ Vendor shipping session cleared")



from .models import VendorProduct, VendorOrder, VendorCart, VendorCartItem, VendorProductVariant  # ✅ Add VendorProductVariant

def add_to_cart(request, product_id, variant_id=None):
    """Add vendor product to vendor cart (guest allowed)"""
    from .models import VendorProductVariant
    
    product = get_object_or_404(VendorProduct, id=product_id, status='active')
    
    # Get variant from URL parameter
    variant = None
    if variant_id:
        variant = get_object_or_404(VendorProductVariant, id=variant_id)
    else:
        # Check if variant is passed via query param
        variant_id = request.GET.get('variant')
        if variant_id:
            variant = get_object_or_404(VendorProductVariant, id=variant_id)
    
    # Handle POST request (from form submission)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        shipping_address = request.POST.get('shipping_address', '').strip()
        
        if not shipping_address:
            messages.error(request, "Please provide your shipping address.")
            return redirect('vendor_products:product_detail', product_id=product.id)
        
        # Check stock
        if variant:
            if variant.stock <= 0:
                messages.error(request, "This variant is out of stock.")
                return redirect('vendor_products:product_detail', product_id=product.id)
            if quantity > variant.stock:
                messages.error(request, f"Only {variant.stock} items available for this variant.")
                return redirect('vendor_products:product_detail', product_id=product.id)
        else:
            if product.stock <= 0:
                messages.error(request, "This product is currently out of stock.")
                return redirect('vendor_products:product_detail', product_id=product.id)
            if quantity > product.stock:
                messages.error(request, f"Only {product.stock} items available.")
                return redirect('vendor_products:product_detail', product_id=product.id)
        
        # ✅ Clear shipping session when adding items
        clear_vendor_shipping_session(request)
        
        # Get or create cart using helper
        cart = get_or_create_cart(request)
        
        # Check if item already in cart
        cart_item = VendorCartItem.objects.filter(cart=cart, product=product, variant=variant).first()
        
        if cart_item:
            cart_item.quantity += quantity
            cart_item.shipping_address = shipping_address
            cart_item.save()
            messages.success(request, f"Updated {product.name} quantity in your cart.")
        else:
            VendorCartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=quantity,
                shipping_address=shipping_address
            )
            messages.success(request, f"{product.name} added to your cart!")
        
        return redirect('vendor_products:cart_detail')
    
    # Handle GET request (from variant selection button click)
    if variant:
        # Check stock
        if variant.stock <= 0:
            messages.error(request, "This variant is out of stock.")
            return redirect('vendor_products:product_detail', product_id=product.id)
        
        # ✅ Clear shipping session when adding items
        clear_vendor_shipping_session(request)
        
        quantity = 1
        shipping_address = "Address will be provided during checkout"
        
        # Get or create cart using helper
        cart = get_or_create_cart(request)
        
        # Check if item already in cart
        cart_item = VendorCartItem.objects.filter(cart=cart, product=product, variant=variant).first()
        
        if cart_item:
            cart_item.quantity += 1
            cart_item.save()
            messages.success(request, f"Added another {product.name} ({variant.color_name}) to your cart.")
        else:
            VendorCartItem.objects.create(
                cart=cart,
                product=product,
                variant=variant,
                quantity=1,
                shipping_address=shipping_address
            )
            messages.success(request, f"{product.name} ({variant.color_name}) added to your cart!")
        
        return redirect('vendor_products:cart_detail')
    else:
        # No variant selected, redirect to product detail
        messages.warning(request, "Please select a color variant.")
        return redirect('vendor_products:product_detail', product_id=product.id)


# def cart_detail(request):
#     """Display vendor cart (guest allowed)"""
#     from decimal import Decimal
#     from payments.services.exchange import get_exchange_rate
    
#     cart = get_or_create_cart(request)
#     cart_items = cart.items.all()
#     total = cart.get_total()
    
#     # ✅ Clear shipping if cart is empty
#     if not cart_items:
#         clear_vendor_shipping_session(request)
    
#     # ✅ Get shipping from session (same as main cart)
#     shipping_data = request.session.get("shipping", {})
#     shipping_cost_ngn = Decimal(str(shipping_data.get("amount_ngn", 0)))
#     shipping_cost_fx = Decimal(str(shipping_data.get("amount_fx", 0)))
#     shipping_label = shipping_data.get("label")
#     shipping_method = shipping_data.get("method")
#     is_vendor_shipping = shipping_data.get("is_vendor", False)
    
#     # ✅ Only use shipping if it's from vendor cart
#     if not is_vendor_shipping:
#         shipping_cost_ngn = Decimal("0.00")
#         shipping_cost_fx = Decimal("0.00")
#         shipping_label = None
#         shipping_method = None
    
#     print(f"📦 Shipping data from session: {shipping_data}")
#     print(f"📦 Shipping cost: {shipping_cost_ngn}")
    
#     # ✅ Calculate grand total with shipping
#     grand_total_ngn = total + shipping_cost_ngn
    
#     # ✅ FX conversion for display
#     active_currency = request.session.get("currency", "NGN")
    
#     # If shipping is in NGN but currency is different, convert
#     if active_currency != "NGN":
#         fx_rate, rate_source = get_exchange_rate(active_currency)
#         total_fx = round(total * Decimal(str(fx_rate)), 2)
#         shipping_fx = round(shipping_cost_ngn * Decimal(str(fx_rate)), 2)
#         grand_total_fx = round(grand_total_ngn * Decimal(str(fx_rate)), 2)
#     else:
#         total_fx = total
#         shipping_fx = shipping_cost_ngn
#         grand_total_fx = grand_total_ngn
    
#     context = {
#         'cart_items': cart_items,
#         'total': total,
#         'total_fx': total_fx,
#         'shipping_cost_ngn': shipping_cost_ngn,
#         'shipping_cost_fx': shipping_fx,
#         'shipping_label': shipping_label,
#         'shipping_method': shipping_method,
#         'grand_total_ngn': grand_total_ngn,
#         'grand_total_fx': grand_total_fx,
#         'currency': active_currency,
#         'total_items': cart.get_total_items(),
#         'has_shipping': shipping_cost_ngn > 0 and is_vendor_shipping,
#     }
#     return render(request, 'vendor_products/cart_detail.html', context)


def cart_detail(request):
    """Display vendor cart (guest allowed)"""
    from decimal import Decimal
    from payments.services.exchange import get_exchange_rate
    
    cart = get_or_create_cart(request)
    cart_items = cart.items.all()
    total = cart.get_total()
    
    # ✅ Clear shipping if cart is empty
    if not cart_items:
        if "shipping" in request.session:
            del request.session["shipping"]
    
    # ✅ Get shipping from session
    shipping_data = request.session.get("shipping", {})
    shipping_cost_ngn = Decimal("0.00")
    shipping_cost_fx = Decimal("0.00")
    shipping_label = None
    shipping_method = None
    has_shipping = False
    
    # ✅ Check if shipping exists and is from vendor cart
    if shipping_data and shipping_data.get("is_vendor", False):
        # ✅ Check if currency has changed since shipping was calculated
        shipping_currency = shipping_data.get("currency", "NGN")
        active_currency = request.session.get("currency", "NGN")
        
        if shipping_currency != active_currency:
            # ✅ Currency changed - clear shipping session
            if "shipping" in request.session:
                del request.session["shipping"]
            print(f"✅ Vendor shipping cleared - currency changed from {shipping_currency} to {active_currency}")
            shipping_data = {}
        else:
            # ✅ Currency matches, use shipping data
            shipping_cost_ngn = Decimal(str(shipping_data.get("amount_ngn", 0)))
            shipping_label = shipping_data.get("label")
            shipping_method = shipping_data.get("method")
            has_shipping = shipping_cost_ngn > 0
    
    # ✅ Calculate grand total with shipping (in NGN)
    grand_total_ngn = total + shipping_cost_ngn
    
    # ✅ FX conversion for display
    active_currency = request.session.get("currency", "NGN")
    
    if active_currency != "NGN":
        fx_rate, rate_source = get_exchange_rate(active_currency)
        total_fx = round(total * Decimal(str(fx_rate)), 2)
        # ✅ Convert shipping cost to FX
        shipping_cost_fx = round(shipping_cost_ngn * Decimal(str(fx_rate)), 2)
        # ✅ Convert grand total to FX
        grand_total_fx = round(grand_total_ngn * Decimal(str(fx_rate)), 2)
    else:
        total_fx = total
        shipping_cost_fx = shipping_cost_ngn
        grand_total_fx = grand_total_ngn
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'total_fx': total_fx,
        'shipping_cost_ngn': shipping_cost_ngn,
        'shipping_cost_fx': shipping_cost_fx,
        'shipping_label': shipping_label,
        'shipping_method': shipping_method,
        'grand_total_ngn': grand_total_ngn,
        'grand_total_fx': grand_total_fx,
        'currency': active_currency,
        'total_items': cart.get_total_items(),
        'has_shipping': has_shipping,
    }
    return render(request, 'vendor_products/cart_detail.html', context)




def remove_from_cart(request, item_id):
    """Remove item from vendor cart (guest allowed)"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(VendorCartItem, id=item_id, cart=cart)
    cart_item.delete()
    
    # ✅ Clear shipping session when removing items
    clear_vendor_shipping_session(request)
    
    messages.success(request, "Item removed from cart.")
    return redirect('vendor_products:cart_detail')


def update_cart_item(request, item_id):
    """Update quantity of cart item (guest allowed)"""
    cart = get_or_create_cart(request)
    cart_item = get_object_or_404(VendorCartItem, id=item_id, cart=cart)
    
    # Check if quantity is passed via GET (for +/- buttons)
    if request.method == 'GET':
        quantity = request.GET.get('quantity')
        if quantity:
            quantity = int(quantity)
            if quantity <= 0:
                cart_item.delete()
                messages.success(request, "Item removed from cart.")
            else:
                cart_item.quantity = quantity
                cart_item.save()
                messages.success(request, "Cart updated.")
                
            # ✅ Clear shipping session when updating items
            clear_vendor_shipping_session(request)
            
        return redirect('vendor_products:cart_detail')
    
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        
        if quantity <= 0:
            cart_item.delete()
            messages.success(request, "Item removed from cart.")
        else:
            cart_item.quantity = quantity
            cart_item.save()
            messages.success(request, "Cart updated.")
        
        # ✅ Clear shipping session when updating items
        clear_vendor_shipping_session(request)
    
    return redirect('vendor_products:cart_detail')


def checkout(request):
    """Checkout vendor cart - Wa'ad model with Paystack preauthorization (guest allowed)"""
    cart = get_or_create_cart(request)
    
    if not cart or not cart.items.exists():
        messages.error(request, "Your cart is empty.")
        return redirect('vendor_products:product_list')
    
    if request.method == 'POST':
        cart_items = cart.items.all()
        total = cart.get_total()
        
        # Get customer info from POST
        email = request.POST.get('email')
        first_name = request.POST.get('first_name', '')
        last_name = request.POST.get('last_name', '')
        phonenumber = request.POST.get('phonenumber', '')
        country = request.POST.get('country', '')
        state = request.POST.get('state', '')
        shipping_method = request.POST.get('shipping_method', 'seller')
        
        if not email:
            messages.error(request, "Please provide your email address.")
            return redirect('vendor_products:cart_detail')
        
        # Get shipping address from first item
        shipping_address = cart_items.first().shipping_address
        
        # Get shipping cost from session if available
        shipping_data = request.session.get('shipping', {})
        shipping_cost = Decimal(str(shipping_data.get('amount_ngn', 0)))
        
        # Create order - allow null customer for guests
        order = VendorOrder.objects.create(
            customer=request.user if request.user.is_authenticated else None,
            customer_email=email if not request.user.is_authenticated else None,
            customer_name=f"{first_name} {last_name}".strip() if not request.user.is_authenticated else None,
            product=cart_items.first().product,
            variant=cart_items.first().variant,
            quantity=sum(item.quantity for item in cart_items),
            total_amount=total + shipping_cost,
            shipping_address=shipping_address,
            country=country,
            state=state,
            shipping_method=shipping_method,
            shipping_cost=shipping_cost,
            status='pending',
            payment_status='authorized'
        )
        
        # Initialize Paystack Preauthorization (Wa'ad model - hold funds)
        try:
            paystack_data = initialize_paystack_hold(
                amount=total + shipping_cost,
                email=email,
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