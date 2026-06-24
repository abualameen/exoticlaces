# lacesstore/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('category/<slug:category_slug>', views.home, name='products_by_category'),
    path('category/<slug:category_slug>/<slug:product_slug>', views.productPage, name='product_detail'),
    path('cart/add/<int:product_id>', views.add_cart, name='add_cart'),
    path('cart', views.cart_detail, name='cart_detail'),
    path('cart/remove/<int:product_id>', views.cart_remove, name='cart_remove'),
    path('cart/remove/<int:product_id>/<int:variant_id>/', views.cart_remove, name='cart_remove_variant'),
    path('cart/remove_product/<int:product_id>', views.cart_remove_product, name='cart_remove_product'),
    path('cart/remove_product/<int:product_id>/<int:variant_id>/', views.cart_remove_product, name='cart_remove_product_variant'),
    path('thankyou/<int:order_id>', views.thanks_page, name='thanks_page'),
    path('account/create/', views.signupView, name='signup'),
    path('account/signin/', views.signinView, name='signin'),
    path('account/signout/', views.signoutView, name='signout'),
    path('order_history/', views.orderHistory, name='order_history'),
    path('order/<int:order_id>', views.viewOrder, name='order_detail'),
    path('search/', views.search, name='search'),
    path('about/', views.aboutPage, name='aboutPage'),
    path('contact/', views.contactPage, name='contactPage'),
    path('cart/add/<int:product_id>/<int:variant_id>/', views.add_cart_variant, name='add_cart_variant'),
    path('terms/', views.terms, name='terms'),
    path('privacy/', views.privacy, name='privacy'),
    path('refund/', views.refund, name='refund'),
    path('shipping-policy/', views.shipping_policy, name='shipping_policy'),
    path('faq/', views.faq, name='faq'),
    path('wholesale-policy/', views.wholesale_policy, name='wholesale_policy'),
    path('testvid/', views.test_video, name='test_vid'),
    # Remove health_check temporarily
    # path('health/', views.health_check, name='health_check'),
    path('admin/dashboard/', views.dashboard, name='admin_dashboard'),
]  # Make sure there's no trailing comma after the last item