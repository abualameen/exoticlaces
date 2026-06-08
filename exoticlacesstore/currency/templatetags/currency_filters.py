
from decimal import Decimal
from django import template
from payments.services.exchange import get_exchange_rate
from exoticlacesstore.utils.currency import get_symbol

register = template.Library()

@register.filter
def money(amount, currency="NGN"):
    try:
        amount = Decimal(amount)
    except Exception:
        return amount

    # 🔒 Always convert from NGN
    rate, rate_source = get_exchange_rate(currency)
    converted = (amount * Decimal(str(rate))).quantize(Decimal("0.01"))

    symbol = get_symbol(currency)
    return f"{symbol}{converted:,.2f}"





