from django.conf import settings
# from utils.currency import CURRENCIES

from exoticlacesstore.utils.currency import CURRENCIES

def currency_context(request):
    currency = request.session.get("currency", settings.DEFAULT_CURRENCY)
    return {
        "ACTIVE_CURRENCY": currency,
        "CURRENCIES": CURRENCIES,
    }
