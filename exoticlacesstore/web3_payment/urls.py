from django.urls import path
from . import views

app_name = 'web3_payment'

urlpatterns = [
    path('payment/<int:payment_id>/', views.web3_payment_detail, name='detail'),
    path('create/<int:order_id>/', views.create_web3_payment, name='create'),
    path('verify/', views.web3_payment_verify, name='verify'),
    path('status/<int:payment_id>/', views.web3_payment_status, name='status'),
    path('webhook/', views.web3_webhook, name='webhook'),
    path('tokens/', views.web3_available_tokens, name='tokens'),
]