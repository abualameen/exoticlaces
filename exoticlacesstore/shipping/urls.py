from django.urls import path
from . import views

# urlpatterns = [
#     path('options/', views.shipping_options, name='shipping_options'),
# ]




from django.urls import path
from .views import shipping_options, set_shipping

urlpatterns = [
    path("options/", shipping_options, name="shipping_options"),
    path("set-shipping/", set_shipping, name="set_shipping"),
]
