from django.urls import path
from . import views

app_name = 'vendor_products'

urlpatterns = [
    path('', views.vendor_product_list, name='product_list'),
    path('<int:product_id>/', views.vendor_product_detail, name='product_detail'),
    path('place-order/<int:product_id>/', views.place_order_request, name='place_order'),
    path('order-success/<int:order_id>/', views.order_request_success, name='order_success'),
    path('capture-payment/<int:order_id>/', views.capture_payment, name='capture_payment'),
    path('cancel-order/<int:order_id>/', views.cancel_order_hold, name='cancel_order'),

    path('webhook/paystack/', views.paystack_webhook, name='paystack_webhook'),



]