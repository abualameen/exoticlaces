from django.urls import path
from . import views

urlpatterns = [
    path('init/', views.init_payment, name='init_payment'),
    path('verify/', views.verify_payment, name='verify_payment'),
]
