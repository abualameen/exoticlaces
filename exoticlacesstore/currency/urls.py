from django.urls import path
from .views import set_currency

urlpatterns = [
    path("set/", set_currency, name="set_currency"),
]
