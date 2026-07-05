from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, Product,Cart, CartItem, Order, OrderItem, ProductVariant, Visitor, DailyVisitorStats
from .models import Customer
from django.conf import settings
import requests
import simplejson as json
from django.http import JsonResponse
import json
from django.contrib.auth.models import Group, User
from allauth.account.models import EmailAddress
# from allauth.account.utils import send_email_confirmation
#from allauth.account.utils import send_email_confirmation as allauth_send_email_confirmation
from allauth.account import utils as allauth_utils
from django.contrib import messages
from .forms import SignUpForm, ContactForm
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from decimal import Decimal  # add at the top of your views.py
from payments.services.exchange import get_exchange_rate
from django.template.loader import get_template
from django.core.mail import EmailMessage
from decimal import Decimal
from django.shortcuts import render
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from payments.models import ExchangeRate
from .facebook_capi import send_facebook_event
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt



from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.utils import timezone
import datetime





# Create your views here.
def home(request, category_slug=None):
    category_page = None
    products = None
    if category_slug!=None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.all().filter(available=True)
    active_currency = request.session.get("currency", "NGN")

    return render(request, 'home.html', {'category': category_page, 'products': products, 'currency':active_currency})


def aboutPage(request):

    return render(request, 'about.html')


def clear_shipping_session(request):
    if "shipping" in request.session:
        del request.session["shipping"]



def productPage(request, category_slug, product_slug):
    product = get_object_or_404(Product, category__slug=category_slug, slug=product_slug, available=True)
    variants = product.variants.all()   # related_name='variants'

    # default variant logic
    default_variant = variants.filter(is_default=True).first()
    if not default_variant and variants.exists():
        default_variant = variants.first()

    return render(request, 'product.html', {
        'product': product,
        'variants': variants,
        'default_variant': default_variant
    })




def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart



# def add_cart(request, product_id, variant_id=None):
#     product = Product.objects.get(id=product_id)
#     variant = None
#     if variant_id:
#         variant = ProductVariant.objects.get(id=variant_id)

#     try:
#         cart = Cart.objects.get(cart_id=_cart_id(request))
#     except Cart.DoesNotExist:
#         cart = Cart.objects.create(cart_id=_cart_id(request))
#         cart.save()

#     try:
#         cart_item = CartItem.objects.get(product=product, cart=cart, variant=variant)
#         # Check stock for variant or product
#         available_stock = variant.stock if variant else product.stock
#         if cart_item.quantity < available_stock:
#             cart_item.quantity += 1
#         cart_item.save()
#     except CartItem.DoesNotExist:
#         cart_item = CartItem.objects.create(
#             product=product,
#             variant=variant,
#             quantity=1,
#             cart=cart
#         )
#         cart_item.save()
#     clear_shipping_session(request)


#     # ✅ Facebook CAPI - Add to Cart Event
    
#     if request.user.is_authenticated:
#         send_facebook_event(
#             request,
#             'AddToCart',
#             {
#                 'content_ids': [str(product.id)],
#                 'content_name': product.name,
#                 'content_type': 'product',
#                 'value': str(product.price),
#                 'currency': 'NGN'
#             }
#         )

#     # Add GA4 tracking
#     if not request.session.get('ga_tracked_add_to_cart', False):
#         request.session['ga_tracked_add_to_cart'] = True
#         # The GA4 tag automatically tracks this via enhanced measurement


#     return redirect('cart_detail')


# def add_cart_variant(request, product_id, variant_id):
#     product = get_object_or_404(Product, id=product_id)
#     variant = get_object_or_404(ProductVariant, id=variant_id)


#     if variant.stock <= 0:
#         messages.error(request, "This variant is out of stock.")
#         return redirect(product.get_url())

#     try:
#         cart = Cart.objects.get(cart_id=_cart_id(request))
#     except Cart.DoesNotExist:
#         cart = Cart.objects.create(cart_id=_cart_id(request))
#         cart.save()

    

#     # Check if cart item for this variant exists
#     cart_items = CartItem.objects.filter(product=product, variant=variant, cart=cart)
#     if cart_items.exists():
#         cart_item = cart_items.first()
#         if cart_item.quantity < product.stock:
#             cart_item.quantity += 1
#             cart_item.save()
#     else:
#         cart_item = CartItem.objects.create(
#             product=product,
#             variant=variant,
#             quantity=1,
#             cart=cart
#         )
#         cart_item.save()
#     clear_shipping_session(request)

#     # ✅ Facebook CAPI - Add to Cart Event (with variant)
    
#     if request.user.is_authenticated:
#         send_facebook_event(
#             request,
#             'AddToCart',
#             {
#                 'content_ids': [str(product.id)],
#                 'content_name': f"{product.name} - {variant.color_name}",
#                 'content_type': 'product',
#                 'value': str(product.price),
#                 'currency': 'NGN',
#                 'variant': variant.color_name  # Optional: track which color
#             }
#         )

#     return redirect('cart_detail')


def add_cart(request, product_id, variant_id=None):
    product = Product.objects.get(id=product_id)
    variant = None
    if variant_id:
        variant = ProductVariant.objects.get(id=variant_id)

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart, variant=variant)
        available_stock = variant.stock if variant else product.stock
        if cart_item.quantity < available_stock:
            cart_item.quantity += 1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product=product,
            variant=variant,
            quantity=1,
            cart=cart
        )
        cart_item.save()
    clear_shipping_session(request)

    # ✅ Facebook CAPI - Add to Cart Event (Works for ALL users)
    # ✅ Always send, even for guests
    import uuid
    event_id = str(uuid.uuid4())
    
    send_facebook_event(
        request,
        'AddToCart',
        {
            'content_ids': [str(product.id)],
            'content_name': product.name,
            'content_type': 'product',
            'value': str(product.price),
            'currency': 'NGN'
        },
        event_id=event_id  # ✅ Pass event_id
    )

    return redirect('cart_detail')


def add_cart_variant(request, product_id, variant_id):
    product = get_object_or_404(Product, id=product_id)
    variant = get_object_or_404(ProductVariant, id=variant_id)

    if variant.stock <= 0:
        messages.error(request, "This variant is out of stock.")
        return redirect(product.get_url())

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(cart_id=_cart_id(request))
        cart.save()

    cart_items = CartItem.objects.filter(product=product, variant=variant, cart=cart)
    if cart_items.exists():
        cart_item = cart_items.first()
        if cart_item.quantity < product.stock:
            cart_item.quantity += 1
            cart_item.save()
    else:
        cart_item = CartItem.objects.create(
            product=product,
            variant=variant,
            quantity=1,
            cart=cart
        )
        cart_item.save()
    clear_shipping_session(request)

    # ✅ Facebook CAPI - Add to Cart Event (Works for ALL users)
    import uuid
    event_id = str(uuid.uuid4())
    
    send_facebook_event(
        request,
        'AddToCart',
        {
            'content_ids': [str(product.id)],
            'content_name': product.name,
            'content_type': 'product',
            'value': str(product.price),
            'currency': 'NGN'
        },
        event_id=event_id  # ✅ Pass event_id
    )

    return redirect('cart_detail')



def cart_detail(request):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)

        total_ngn = Decimal("0.00")
        counter = 0

        # 1️⃣ CART TOTAL (NGN ONLY)
        for item in cart_items:
            total_ngn += item.product.price * item.quantity
            counter += item.quantity

        # 2️⃣ SHIPPING (FROM SESSION)
        shipping_data = request.session.get("shipping", {})
        shipping_cost_ngn = Decimal(str(shipping_data.get("amount_ngn", 0)))
        shipping_label = shipping_data.get("label")

        # 3️⃣ GRAND TOTAL (NGN ONLY)
        grand_total_ngn = total_ngn + shipping_cost_ngn

        # 4️⃣ FX (DISPLAY ONLY)
        active_currency = request.session.get("currency", "NGN")
        fx_rate, rate_source = get_exchange_rate(active_currency)

        total_fx = round(total_ngn * Decimal(str(fx_rate)), 2)
        shipping_fx = round(shipping_cost_ngn * Decimal(str(fx_rate)), 2)
        grand_total_fx = round(grand_total_ngn * Decimal(str(fx_rate)), 2)

    except ObjectDoesNotExist:
        cart_items = []
        total_ngn = Decimal("0.00")
        shipping_cost_ngn = Decimal("0.00")
        grand_total_ngn = Decimal("0.00")
        total_fx = Decimal("0.00")
        shipping_fx = Decimal("0.00")
        grand_total_fx = Decimal("0.00")
        shipping_label = None
        counter = 0
        active_currency = "NGN"

    # 5️⃣ PAYSTACK (ALWAYS NGN)
    paystack_amount = int(grand_total_ngn * 100)

    return render(request, "cart.html", {
        "cart_items": cart_items,

        # NGN (truth)
        "total_ngn": total_ngn,
        "shipping_ngn": shipping_cost_ngn,
        "grand_total_ngn": grand_total_ngn,

        # FX (display)
        "total_fx": total_fx,
        "shipping_fx": shipping_fx,
        "grand_total_fx": grand_total_fx,

        "currency": active_currency,
        "shipping_label": shipping_label,
        "counter": counter,

        "pypaystack_total": paystack_amount,
        "data_key": settings.PAYSTACK_PUBLIC_KEY,
    })






def cart_remove(request, product_id, variant_id=None):
    # cart = Cart.objects.get(cart_id =_cart_id(request))

    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        # If cart doesn't exist, redirect to cart page
        return redirect('cart_detail')

    product = get_object_or_404(Product, id=product_id)
    if variant_id:
        cart_items = CartItem.objects.filter(product=product, cart=cart, variant_id=variant_id)
    else:
        cart_items = CartItem.objects.filter(product=product, cart= cart)
    for cart_item in cart_items:

        if cart_item.quantity > 1:
            cart_item.quantity -=1
            cart_item.save()
        else:
            cart_item.delete()
    clear_shipping_session(request)
    return redirect('cart_detail')


def cart_remove_product(request, product_id, variant_id=None):
    #cart = Cart.objects.get(cart_id=_cart_id(request))
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        return redirect('cart_detail')


    product = get_object_or_404(Product, id=product_id)

    if variant_id:
        cart_items = CartItem.objects.filter(product=product, cart=cart, variant_id=variant_id)
    else:
        cart_items = CartItem.objects.filter(product=product, cart=cart)

    cart_items.delete()
    clear_shipping_session(request)
    return redirect('cart_detail')



def thanks_page(request, order_id):
    order = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    
    print(f"Order ID: {order.id}")  # Debug
    print(f"Order Items: {order_items.count()}")  # Debug
    
    return render(request, 'thankyou.html', {
        'eds': order,
        'order_items': order_items,
    })





def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                return render(request, 'signup.html', {'form': form, 'email_exists': True, 'email': email})
                # messages.error(request, 'An account with this email already exists.')
            
            user = form.save(commit=False)
            #user.is_active = False  # Deactivate account until email confirmation
            user.save()


            customer = Customer.objects.create(
                user=user,  # Link to the User
                email=email,
                firstName=form.cleaned_data.get('first_name', ''),
                lastName=form.cleaned_data.get('last_name', ''),
                phonenumber=form.cleaned_data.get('phonenumber', ''),
            )
            #form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)


            # ✅ Send confirmation email using EmailAddress method
            email_address = EmailAddress.objects.add_email(request, user, email)
            email_address.send_confirmation(request)
            
            

           
            # Immediately remove the message that was just added
            storage = messages.get_messages(request)
            print('storage:', storage)
            storage.used = True  # Clear all messages from this request


            request.session['confirmation_email'] = email
            
    else:
        form = SignUpForm()
    email = request.session.get('confirmation_email', '')
    return render(request, 'signup.html', {'form': form, 'email': email} )



def signinView(request):
    if request.method == 'POST':
        print("=" * 50)
        print("POST data received:", request.POST)
        form = AuthenticationForm(request, data=request.POST)
        
        if form.is_valid():
            print("Form is valid")
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            print(f"Username: {username}")
            print(f"Password provided: {'*' * len(password) if password else 'None'}")
            
            user = authenticate(username=username, password=password)
            if user is not None:
                print(f"User authenticated: {user.username}")
                login(request, user)
                print("User logged in, redirecting to home")
                messages.success(request, f"Welcome back, {username}!")
                return redirect('home')
            else:
                print("Authentication failed - user is None")
                messages.error(request, "Invalid username or password.")
        else:
            print("Form is invalid")
            print("Form errors:", form.errors)
            messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    
    print("Rendering login page again")
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')



@login_required(redirect_field_name='next', login_url='signin')
def orderHistory(request):
    if request.user.is_authenticated:
        # Get orders by customer
        customer = Customer.objects.filter(user=request.user).first()
        if customer:
            order_details = Order.objects.filter(customer=customer)
        else:
            order_details = []
    return render(request, 'orders_list.html', {'order_details': order_details})

@login_required(redirect_field_name='next', login_url='signin')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)



    
        order = Order.objects.get(id=order_id)
        order_items = OrderItem.objects.filter(order=order)

        active_currency = request.session.get("currency", order.currency or "NGN")
        print('active_currency:',active_currency )

        context = {
            "edss": order,
            "order_items": order_items,
            "currency": active_currency,
        }

    return render(request, "order_detail.html", context)



def search(request):
    products = Product.objects.filter(name__contains=request.GET['title'])
    
    # Get currency from session or default
    currency = request.session.get('currency', 'NGN')
    
    # Add any other context processors you need
    context = {
        'products': products,
        'currency': currency,
    }
    
    return render(request, 'home.html', context)



from django.core.mail import EmailMessage
from django.template.loader import get_template
from django.core.mail import get_connection

def sendEmail(request, order_id):
    transaction = Order.objects.get(id=order_id)
    order_items = OrderItem.objects.filter(order=transaction)
    print('orderitem:', order_items)
    print('transaction:', transaction)
    
    try:
        subject = f"Exotic Laces - New Order #{transaction.id}"
        to = [transaction.emailAddress]  # Simplified
        from_email = settings.DEFAULT_FROM_EMAIL  # Fixed variable name

        active_currency = request.session.get("currency", "NGN")
        
        order_information = {
            'transaction': transaction,
            'order_items': order_items,
            'ACTIVE_CURRENCY': active_currency,
        }
        
        message = get_template('email/email.html').render(order_information)
        
        msg = EmailMessage(subject, message, to=to, from_email=from_email)
        msg.content_subtype = 'html'  
        msg.send()

        print(f"Order confirmation email sent for order {order_id}")
        
        return True  # Return success indicator
        
    except Exception as e:
        # Log the error for debugging
        print(f"Email sending failed for order {order_id}: {str(e)}")
        return False  # Return failure indicator




def contactPage(request):
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            subject = form.cleaned_data.get('subject')
            user_email = form.cleaned_data.get('from_email')
            message = form.cleaned_data.get('message')
            name = form.cleaned_data.get('name')
            to = 'exoticlacesandmore@gmail.com'
            massage_format = "{0} has sent you a new message: \n\n{1}".format(name, message)
            msg = EmailMessage(subject, message, to=[to], from_email=settings.DEFAULT_FROM_EMAIL, reply_to=[user_email],)
            msg.send()
            return render(request, 'contact_success.html')
    else:
        form = ContactForm()
    return render(request, 'contact.html', {'form': form})




# lacesstore/views.py

def terms(request):
    return render(request, 'terms.html')

def privacy(request):
    return render(request, 'privacy.html')

def refund(request):
    return render(request, 'refund.html')

def shipping_policy(request):
    return render(request, 'shipping_policy.html')

def faq(request):
    return render(request, 'faq.html')

def wholesale_policy(request):
    return render(request, 'wholesale_policy.html')



################################### knowing numbers of visitors########################################

# lacesstore/views.py


@staff_member_required
def dashboard(request):
    """Admin dashboard with visitor statistics"""
    # Active visitors (last 15 minutes)
    active_visitors = Visitor.get_active_visitors(15)
    active_users = Visitor.objects.filter(last_visit__gte=timezone.now() - datetime.timedelta(minutes=15)).exclude(user__isnull=True).count()
    active_guests = active_visitors - active_users
    
    # Today's stats
    today = timezone.now().date()
    today_visitors = Visitor.objects.filter(first_visit__date=today).count()
    
    # Get daily stats for the last 7 days
    last_7_days = []
    for i in range(7):
        date = today - datetime.timedelta(days=i)
        stats, created = DailyVisitorStats.objects.get_or_create(date=date)
        last_7_days.append({
            'date': date.strftime('%b %d'),
            'visitors': stats.unique_visitors,
        })
    
    context = {
        'active_visitors': active_visitors,
        'active_users': active_users,
        'active_guests': active_guests,
        'today_visitors': today_visitors,
        'total_visitors': Visitor.objects.count(),
        'last_7_days': last_7_days,
        'today': today.strftime('%B %d, %Y'),
    }
    
    return render(request, 'admin/dashboard.html', context)




    # views.py
def test_video(request):
    return render(request, 'videotest.html', {'video_id': 'CfVYbB6I8Ew'})




def csrf_failure(request, reason=""):
    """Custom CSRF failure view - returns user-friendly error"""
    # If it's an AJAX request, return JSON
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({
            'status': 'error',
            'message': 'Session expired. Please refresh the page and try again.',
            'csrf_error': True
        }, status=403)
    
    # For regular requests, show a friendly page
    return render(request, 'csrf_error.html', {
        'reason': reason,
        'message': 'Your session has expired or your browser cookies have been cleared. Please refresh the page and try again.'
    }, status=403)