import requests
from django.conf import settings

def init_transaction(email, amount, currency="NGN", reference=None):
    url = f"{settings.PAYSTACK_BASE_URL}/transaction/initialize"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
        "Content-Type": "application/json"
    }
    data = {
        "email": email,
        "amount": amount,
        "currency": currency,
        "reference": reference,  # optional; Paystack will generate if None
        "callback_url": "http://127.0.0.1:8000/payments/verify/"
    }
    resp = requests.post(url, headers=headers, json=data)
    return resp.json()

def verify_transaction(reference):
    url = f"{settings.PAYSTACK_BASE_URL}/transaction/verify/{reference}"
    headers = {
        "Authorization": f"Bearer {settings.PAYSTACK_SECRET_KEY}",
    }
    resp = requests.get(url, headers=headers)
    return resp.json()
