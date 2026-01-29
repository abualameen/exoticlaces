from decimal import Decimal

# Base currency = NGN
BASE_CURRENCY = "NGN"

CURRENCIES = {
    "NGN": {
        "symbol": "₦",
        "name": "Naira",
        "rate": Decimal("1.0"),
    },
    "GHS": {
        "symbol": "₵",
        "name": "Cedis",
        "rate": Decimal("0.012"),   # placeholder
    },
    "XOF": {
        "symbol": "CFA",
        "name": "CFA Franc",
        "rate": Decimal("0.68"),    # placeholder
    },
    "USD": {
        "symbol": "$",
        "name": "Dollar",
        "rate": Decimal("0.0011"),  # placeholder
    }
}

def convert(amount_ngn: Decimal, to_currency: str) -> Decimal:
    currency = CURRENCIES.get(to_currency, CURRENCIES["NGN"])
    return (amount_ngn * currency["rate"]).quantize(Decimal("0.01"))

def get_symbol(currency: str):
    return CURRENCIES.get(currency, CURRENCIES["NGN"])["symbol"]
