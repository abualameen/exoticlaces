class ShippingProvider:
    def get_rate(self, *args, **kwargs):
        raise NotImplementedError()

    def create_shipment(self, *args, **kwargs):
        raise NotImplementedError()

    def track(self, *args, **kwargs):
        raise NotImplementedError()
