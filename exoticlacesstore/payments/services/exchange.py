import requests
import logging
from payments.models import ExchangeRate
from payments.constants import FALLBACK_RATES
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger(__name__)

# API_KEY = "7360d27a787aec87a05b9734"
API_URL = f"https://v6.exchangerate-api.com/v6/{settings.EXCHANGE_RATE_API_KEY}/latest/NGN"


def update_exchange_rates():
    """
    Fetch rates from ExchangeRate-API and store in DB.
    """
    try:
        response = requests.get(API_URL, timeout=10)
        data = response.json()

        if data.get("result") != "success":
            raise Exception("Invalid API response")

        rates = data.get("rates", {})

        for currency, rate in rates.items():
            ExchangeRate.objects.update_or_create(
                base="NGN",
                target=currency,
                defaults={"rate": rate}
            )

        return True

    except Exception as e:
        logger.error(f"FX API FAILED: {e}")
        return False

# from decimal import Decimal
# from .models import ExchangeRate

def get_exchange_rate(target_currency):
    """
    Returns:
        (rate: Decimal, source: str)
    """

    if target_currency == "NGN":
        return Decimal("1"), "identity"

    # 1️⃣ DB cached rate
    try:
        fx = ExchangeRate.objects.get(
            base="NGN",
            target=target_currency
        )
        return fx.rate, "db"
    except ExchangeRate.DoesNotExist:
        pass

    # 2️⃣ Fallback
    fallback = FALLBACK_RATES.get(target_currency)
    if fallback:
        return Decimal(str(fallback)), "fallback"

    # 3️⃣ Last resort
    return Decimal("1"), "identity"
