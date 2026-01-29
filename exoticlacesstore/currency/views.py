from django.shortcuts import render

# Create your views here.
from django.shortcuts import redirect
from django.conf import settings

def set_currency(request):
    currency = request.POST.get("currency")
    if currency in settings.SUPPORTED_CURRENCIES:
        request.session["currency"] = currency
    return redirect(request.META.get("HTTP_REFERER", "/"))
