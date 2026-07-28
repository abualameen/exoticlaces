from django.urls import path
from . import views

app_name = 'vendor_products'

urlpatterns = [
    # Product browsing
    path('', views.vendor_product_list, name='product_list'),
    path('category/<slug:category_slug>/', views.vendor_products_by_category, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>/', views.vendor_product_detail, name='product_detail'),
    
    # Order management
    path('place-order/<int:product_id>/', views.place_order_request, name='place_order'),
    path('order-success/<int:order_id>/', views.order_request_success, name='order_success'),
    
    # Admin actions
    path('capture-payment/<int:order_id>/', views.capture_payment, name='capture_payment'),
    path('cancel-order/<int:order_id>/', views.cancel_order_hold, name='cancel_order'),
    
    # Webhook
    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),
]