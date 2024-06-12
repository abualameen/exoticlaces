from django.shortcuts import render, get_object_or_404,redirect
from django.http import HttpResponse
from django.core.exceptions import ObjectDoesNotExist
from .models import Category, Product,Cart, CartItem, Order, OrderItem
from .models import Customerr
from pypaystack import Transaction, Customer,Plan
import pypaystack
from django.conf import settings
import requests
import simplejson as json
from django.http import JsonResponse
import json
from django.contrib.auth.models import Group, User
from allauth.account.utils import send_email_confirmation
from .forms import SignUpForm
from django.template import RequestContext
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required


# Create your views here.
def home(request, category_slug=None):
    category_page = None
    products = None
    if category_slug!=None:
        category_page = get_object_or_404(Category, slug=category_slug)
        products = Product.objects.filter(category=category_page, available=True)
    else:
        products = Product.objects.all().filter(available=True)

    return render(request, 'home.html', {'category': category_page, 'products': products})


def aboutPage(request):

    return render(request, 'about.html')
    #return HttpResponse("<h1> About Page </h1>")

def contactPage(request):

    return render(request, 'contact.html')
    #return HttpResponse("<h1> Contact Page </h1>")
    # return HttpResponse("Hello world")
def productPage(request, category_slug, product_slug):
    try:
        product = Product.objects.get(category__slug=category_slug, slug=product_slug)
    except Exception as e:
        raise e

    return render(request, 'product.html', {'product': product})



def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart

def add_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
    except Cart.DoesNotExist:
        cart = Cart.objects.create(
            cart_id = _cart_id(request)
        )
        cart.save()

    try:
        cart_item = CartItem.objects.get(product=product, cart=cart)
        if cart_item.quantity < cart_item.product.stock:

            cart_item.quantity +=1
        cart_item.save()
    except CartItem.DoesNotExist:
        cart_item = CartItem.objects.create(
            product = product,
            quantity = 1,
            cart = cart
        )
        cart_item.save()

    return redirect('cart_detail')

def cart_detail(request, total=0, counter=0, cart_items=None):
    try:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_items = CartItem.objects.filter(cart=cart, active=True)
        print('great now')
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            total = float(total)
            print('totall', total)
            counter += cart_item.quantity
    except ObjectDoesNotExist:
        pass
    pypaystack_total = int(total) * 100
    data_key = settings.PAYSTACK_PUBLIC_KEY
    if request.method=='POST':
        try:
            transaction = Transaction(authorization_key=settings.PAYSTACK_SECRET_KEY)
            try:
                response = transaction.verify(request.POST.get('referenceid'))
            except Exception as e:
                print(f'An error occurred while verifying the customer: {e}')
                return JsonResponse({'error': 'An error occurred while verifying the customer.'}, status=500)

            data = JsonResponse(response, safe=False)
            try:
                res_tupple1= response[3]
                authorization_code = res_tupple1['authorization']['authorization_code']
                email = request.POST['emailaddress']
                customer, created = Customerr.objects.update_or_create(
                    email=email,
                    defaults={
                        'firstName': request.POST['firstname'],
                        'lastName': request.POST['lastname'],
                        'phonenumber': request.POST['phonenumber'],
                        'authorization_code': authorization_code
                    }
                )
                customer.save()
                costo_email = request.POST['emailaddress']
                customer = get_object_or_404(Customerr, email=costo_email)
                if customer.authorization_code:
                    print('am using the custo author')
                    response = transaction.charge(costo_email, customer.authorization_code, pypaystack_total)
                else:
                    pass
            except Exception as e:
                print(f'An error occurred while charging the customer: {e}')
                return JsonResponse({'error': 'An error occurred while chargeing the customer.'}, status=500)
            res_tupple = response[3]
            if res_tupple['status'] == 'success':
                emailAddress = request.POST['emailaddress']
                firstName = request.POST['firstname']
                lastName = request.POST['lastname']
                country = request.POST['country']
                state = request.POST['state']
                phonenumber = request.POST['phonenumber']
                try:
                
                    order_details = Order.objects.create(
                        total = total,
                        emailAddress = emailAddress,
                        country = country,
                        firstName = firstName,
                        lastName = lastName,
                        state = state,
                        phonenumber = phonenumber
                    )
                    order_details.save()
                    for order_item in cart_items:
                        or_item = OrderItem.objects.create(
                            product = order_item.product.name,
                            quantity = order_item.quantity,
                            price = order_item.product.price,
                            order = order_details
                        )
                        or_item.save()
                        # reduce stock
                        products = Product.objects.get(id=order_item.product.id)
                        products.stock = int(order_item.product.stock - order_item.quantity)
                        products.save()
                        order_item.delete()
                    print('the order has been created')
                    return JsonResponse({'status': 'success', 'order_id': order_details.id})
                except ObjectDoesNotExist:
                    pass
        except:
            print('An error has Occured')
           
    return render(request, 'cart.html', dict(cart_items = cart_items, total = total, counter = counter, data_key = data_key, pypaystack_total=pypaystack_total))

# def verifyy(request, id):
#     transaction = Transaction(authorization_key=settings.PAYSTACK_SECRET_KEY)
#     response = transaction.verify(id)
#     print('res',response)
 
#     data = JsonResponse(response, safe=False)
#     print('data',data)
#     return data



def cart_remove(request, product_id):
    cart = Cart.objects.get(cart_id =_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart= cart)
    if cart_item.quantity > 1:
        cart_item.quantity -=1
        cart_item.save()
    else:
        cart_item.delete()
    return redirect('cart_detail')

def cart_remove_product(request, product_id):
    cart = Cart.objects.get(cart_id =_cart_id(request))
    product = get_object_or_404(Product, id=product_id)
    cart_item = CartItem.objects.get(product=product, cart= cart)
    cart_item.delete()
    return redirect('cart_detail')


def thanks_page(request, order_id):
    if order_id:
        customer_order = get_object_or_404(Order, id=order_id)
    return render(request, 'thankyou.html', {'customer_order': customer_order})



def signupView(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            if User.objects.filter(email=email).exists():
                return render(request, 'signup.html', {'form': form, 'email_exists': True, 'email': email})
                # messages.error(request, 'An account with this email already exists.')
            
            user = form.save(commit=False)
            user.is_active = False  # Deactivate account until email confirmation
            user.save()
            #form.save()
            username = form.cleaned_data.get('username')
            signup_user = User.objects.get(username=username)
            customer_group = Group.objects.get(name='Customer')
            customer_group.user_set.add(signup_user)

            send_email_confirmation(request, user)  # Send confirmation email
            return redirect('email_confirmation')  # Redirect to a page indicating that email verification is sent
    else:
        form = SignUpForm()
    return render(request, 'signup.html', {'form': form} )
        # return render(request, 'signup.html',
        #    context_instance=RequestContext(request))

def email_confirmation(request):
    return render(request, 'account/email_confirmation.html')

def signinView(request):
    if request.method == 'POST':
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = request.POST['username']
            password = request.POST['password']
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request,user)
                return redirect('home')
            else:
                return redirect('signup')
    else:
        form = AuthenticationForm()
    return render(request, 'signin.html', {'form': form})


def signoutView(request):
    logout(request)
    return redirect('signin')


@login_required(redirect_field_name='next', login_url='signin')
def orderHistory(request):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order_details = Order.objects.filter(emailAddress=email)
    return render(request, 'orders_list.html', {'order_details': order_details})

@login_required(redirect_field_name='next', login_url='signin')
def viewOrder(request, order_id):
    if request.user.is_authenticated:
        email = str(request.user.email)
        order = Order.objects.get(id=order_id, emailAddress=email)
        order_items = OrderItem.objects.filter(order=order)
    return render(request, 'order_detail.html', {'order_items': order_items})


def search(request):
    products = Product.objects.filter(name__contains=request.GET['title'])
    return render(request, 'home.html', {'products': products})