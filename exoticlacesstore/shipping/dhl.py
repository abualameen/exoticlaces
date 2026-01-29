from .providers import ShippingProvider

class DHLProvider(ShippingProvider):

    def get_rate(self, origin, destination, weight, dimensions):
        # MOCK MODE (until creds)
        return {
            "provider": "dhl",
            "service": "DHL Express Worldwide",
            "currency": "NGN",
            "amount": 35000,  # mock price
            "delivery_days": 3,
            "raw": {}
        }

    def create_shipment(self, order):
        return {
            "tracking_number": "DHL-MOCK-123456",
            "label_url": None,
            "raw": {}
        }

    def track(self, tracking_number):
        return {
            "status": "in_transit",
            "location": "Lagos Facility"
        }
