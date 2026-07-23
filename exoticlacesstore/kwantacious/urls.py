# kwantacious/urls.py
from django.urls import path
from . import views

app_name = 'kwantacious'

urlpatterns = [
    path('', views.auction_list, name='auction_list'),
    path('<int:auction_id>/', views.auction_detail, name='auction_detail'),
    path('<int:auction_id>/deposit/', views.place_deposit, name='place_deposit'),
    path('<int:auction_id>/bid/', views.place_bid, name='place_bid'),
]