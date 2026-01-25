
# webhooks.py (Automatic confirmation from Paystack)

from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json
from .models import Payment

@csrf_exempt
def paystack_webhook(request):
    payload = json.loads(request.body)

    event = payload.get("event")
    data = payload.get("data")

    if event == "charge.success":
        ref = data.get("reference")
        try:
            payment = Payment.objects.get(reference=ref)
            payment.status = "success"
            payment.verified = True
            payment.paystack_response = payload
            payment.save()
        except:
            pass

    return HttpResponse(status=200)

