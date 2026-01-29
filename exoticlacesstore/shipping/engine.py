from .registry import PROVIDERS

# def get_shipping_rates(method, **kwargs):
#     provider = PROVIDERS.get(method)
#     if not provider:
#         raise Exception("Invalid shipping provider")
#     return provider.get_rate(**kwargs)

# def create_provider_shipment(method, order):
#     provider = PROVIDERS.get(method)
#     return provider.create_shipment(order)


def get_shipping_rates(provider, **kwargs):
    if provider == "seller":
        from .services import calculate_seller_shipping

        amount = calculate_seller_shipping(
            kwargs["country"],
            kwargs.get("state"),
            kwargs["total_items"]
        )

        return {
            "provider": "seller",
            "amount": float(amount),
            "currency": "NGN",
            "label": "Seller Shipping"
        }

    if provider == "dhl":
        from .dhl import get_dhl_rate

        res = get_dhl_rate(
            kwargs["origin"],
            kwargs["destination"],
            kwargs["weight"],
            kwargs["dimensions"]
        )

        return {
            "provider": "dhl",
            "amount": float(res.get("price", 0)),
            "currency": "NGN",
            "label": "DHL Express",
            "raw": res
        }

    raise Exception("Invalid shipping provider")


# ✅ Shipment creation engine (used by payments app)
def create_provider_shipment(method, order, shipping_data=None):
    """
    Creates shipment based on provider after order is paid
    """

    if method == "seller":
        return {
            "tracking_number": f"SELLER-{order.id}",
            "provider": "seller",
            "raw": shipping_data or {}
        }

    if method == "dhl":
        # Future DHL shipment API call will go here
        return {
            "tracking_number": f"DHL-{order.id}",
            "provider": "dhl",
            "raw": shipping_data or {}
        }

    raise Exception("Invalid shipping provider")
