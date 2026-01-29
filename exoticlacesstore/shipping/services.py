from .models import ShippingRate, ShippingMethod
from decimal import Decimal

def calculate_seller_shipping(country, state, total_items):
    seller = ShippingMethod.objects.get(provider='seller', active=True)

    rate = ShippingRate.objects.filter(
        method=seller,
        country__iexact=country,
        state__iexact=state
    ).first()

    if not rate:
        rate = ShippingRate.objects.filter(
            method=seller,
            country__iexact=country,
            state="*"
        ).first()

    if not rate:
        raise Exception("No shipping rule for destination")

    return Decimal(rate.price_per_item) * Decimal(total_items)
