from django import template
from decimal import Decimal
from utils.currency import convert, get_symbol

register = template.Library()

@register.filter
def money(amount, currency):
    if amount is None:
        return ""
    converted = convert(Decimal(amount), currency)
    symbol = get_symbol(currency)
    return f"{symbol}{converted}"
