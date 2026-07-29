from django.urls import path
from . import views

app_name = 'vendor_products'

urlpatterns = [
    # Product browsing
    path('', views.vendor_product_list, name='product_list'),
    path('<int:product_id>/', views.vendor_product_detail, name='product_detail'),
    
    # Cart
    path('cart/', views.cart_detail, name='cart_detail'),
    path('add-to-cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('remove-from-cart/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update-cart/<int:item_id>/', views.update_cart_item, name='update_cart'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Order management
    path('place-order/<int:product_id>/', views.place_order_request, name='place_order'),
    path('order-success/<int:order_id>/', views.order_request_success, name='order_success'),
    
    # Admin actions
    path('capture-payment/<int:order_id>/', views.capture_payment, name='capture_payment'),
    path('cancel-order/<int:order_id>/', views.cancel_order_hold, name='cancel_order'),
    
    # Webhook
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),
]