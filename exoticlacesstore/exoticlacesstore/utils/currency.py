from decimal import Decimal
from payments.services.exchange import get_exchange_rate

# Base currency = NGN
BASE_CURRENCY = "NGN"

CURRENCIES = {
    "NGN": {
        "symbol": "₦",
        "name": "Naira",
        # "rate": Decimal("1.0"),
    },
    "GHS": {
        "symbol": "₵",
        "name": "Cedis",
        # "rate": Decimal("0.012"),   # placeholder
    },
    "XOF": {
        "symbol": "CFA",
        "name": "CFA Franc",
        # "rate": Decimal("0.68"),    # placeholder
    },
    "USD": {
        "symbol": "$",
        "name": "Dollar",
        # "rate": Decimal("0.0011"),  # placeholder
    },

    "EUR": {
        "symbol": "€", 
        "name": "Euro",
        
    },   # ✅ ADD THIS
}

# def convert(amount_ngn: Decimal, to_currency: str) -> Decimal:
#     currency = CURRENCIES.get(to_currency, CURRENCIES["NGN"])
#     return (amount_ngn * currency["rate"]).quantize(Decimal("0.01"))


def convert(amount_ngn: Decimal, to_currency: str) -> Decimal:
    """
    Convert from NGN to target currency using live FX
    """
    if to_currency == "NGN":
        return amount_ngn.quantize(Decimal("0.01"))

    rate = Decimal(str(get_exchange_rate(to_currency)))
    return (amount_ngn * rate).quantize(Decimal("0.01"))

def get_symbol(currency: str):
    return CURRENCIES.get(currency, CURRENCIES["NGN"])["symbol"]


