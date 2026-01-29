from .services import calculate_seller_shipping

class SellerProvider:
    def get_rate(self, **kwargs):
        country = kwargs.get("country")
        state = kwargs.get("state")
        total_items = kwargs.get("total_items")
        cost = calculate_seller_shipping(country, state, total_items)
        return {
            "provider": "seller",
            "service": "Seller Shipping",
            "currency": "NGN",
            "amount": float(cost),
            "delivery_days": 2
        }

    def create_shipment(self, order, **kwargs):
        return {
            "tracking_number": f"WAYBILL-{order.id}",
            "label_url": None,
            "raw": {}
        }
