from django.urls import path
from . import views

urlpatterns = [
    path('init/', views.init_payment, name='init_payment'),
    path('init-web3-payment/', views.init_web3_payment, name='init_web3_payment'),  # Add this
    path('verify/', views.verify_payment, name='verify_payment'),
]
