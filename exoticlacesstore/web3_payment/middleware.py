from django.utils.deprecation import MiddlewareMixin

class Web3PaymentMiddleware(MiddlewareMixin):
    """Middleware to handle Web3 payment related tasks"""
    
    def process_request(self, request):
        # Add Web3 payment context to all requests
        request.web3_enabled = True
        return None