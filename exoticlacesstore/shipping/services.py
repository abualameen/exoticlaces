from .models import ShippingRate, ShippingMethod
from decimal import Decimal


# COUNTRY_CODE_MAP = {
#     # Major
#     "NG": "Nigeria",
#     "US": "United States",
#     "GB": "United Kingdom",
#     "AU": "Australia",
#     "CA": "Canada",
#     "GH": "Ghana",
#     "AT": "Austria",

#     # CFA – West Africa (XOF)
#     "BJ": "Benin",
#     "BF": "Burkina Faso",
#     "CI": "Côte d’Ivoire",
#     "GW": "Guinea-Bissau",
#     "ML": "Mali",
#     "NE": "Niger",
#     "SN": "Senegal",
#     "TG": "Togo",

#     # CFA – Central Africa (XAF)
#     "CM": "Cameroon",
#     "CF": "Central African Republic",
#     "TD": "Chad",
#     "CG": "Republic of the Congo",
#     "GQ": "Equatorial Guinea",
#     "GA": "Gabon",

#     # Europe & Middle East (from shipping DB)
#     "DE": "Germany",
#     "FR": "France",
#     "NL": "Netherlands",
#     "IT": "Italy",
#     "ES": "Spain",
#     "AE": "UAE",
#     "SA": "Saudi Arabia",
#     "QA": "Qatar",
#     "ZA": "South Africa",
# }






def calculate_seller_shipping(country, state, total_items):
    seller = ShippingMethod.objects.get(provider='seller', active=True)
    # ✅ Normalize country (ISO → DB name)
    # country_name = COUNTRY_CODE_MAP.get(country, country)
    print("country_name", country)
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
