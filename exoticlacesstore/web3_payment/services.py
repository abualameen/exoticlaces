from web3 import Web3
from eth_account import Account
from decimal import Decimal
from django.conf import settings
from django.utils import timezone
import requests
from web3.middleware import geth_poa_middleware

# Enable HD wallet features
Account.enable_unaudited_hdwallet_features()


class Web3PaymentService:
    """Core service for Web3 payment processing"""
    
    def __init__(self):
        self.networks_cache = {}
        self.tokens_cache = {}
        self._load_configs()
    
    def _load_configs(self):
        """Load network and token configurations"""
        from .models import Web3Network, Web3Token
        try:
            self.networks = {n.chain_id: n for n in Web3Network.objects.filter(is_active=True)}
            self.tokens = {f"{t.network.chain_id}_{t.contract_address}": t for t in Web3Token.objects.filter(is_active=True)}
        except:
            self.networks = {}
            self.tokens = {}
    
    def get_web3_instance(self, chain_id):
        """Get Web3 instance for a network"""
        network = self.networks.get(chain_id)
        if not network:
            raise ValueError(f"Network with chain ID {chain_id} not found")
        
        w3 = Web3(Web3.HTTPProvider(network.rpc_url))
        w3.middleware_onion.inject(geth_poa_middleware, layer=0)
        return w3
    
    def generate_payment_address(self, chain_id=None):
        """Generate a unique payment address"""
        # In production, use HD wallet with deterministic addresses
        # For now, generate a random address
        acc = Account.create()
        return acc.address
    
    def create_payment_uri(self, payment):
        """Generate payment URI for QR code"""
        network = payment.network
        token = payment.token
        
        if token.token_type == 'native':
            uri = f"ethereum:{payment.payment_address}?value={float(payment.amount)}"
        else:
            uri = f"ethereum:{payment.payment_address}?value={float(payment.amount)}&token={token.contract_address}"
        
        # Add network info
        uri += f"&chainId={network.chain_id}"
        
        return uri
    
    def check_payment_status(self, payment):
        """Check if payment has been received on the blockchain"""
        if payment.status in ['confirmed', 'failed', 'expired']:
            return payment.status
        
        # Check if payment has expired
        if timezone.now() > payment.expires_at:
            payment.status = 'expired'
            payment.save()
            return 'expired'
        
        try:
            w3 = self.get_web3_instance(payment.network.chain_id)
            
            # Check balance of payment address
            balance = w3.eth.get_balance(payment.payment_address)
            balance_eth = Web3.from_wei(balance, 'ether')
            
            if balance_eth >= payment.amount:
                # Check for confirmations
                tx_count = w3.eth.get_transaction_count(payment.payment_address)
                if tx_count > 0:
                    payment.status = 'confirming'
                    payment.save()
                    return 'confirming'
            
            return 'pending'
            
        except Exception as e:
            print(f"Error checking payment status: {e}")
            return payment.status
    
    def confirm_payment(self, payment):
        """Confirm the payment after required confirmations"""
        if payment.status != 'confirming':
            return False
        
        try:
            payment.status = 'confirmed'
            payment.confirmed_at = timezone.now()
            payment.save()
            
            # Trigger order fulfillment
            self.fulfill_order(payment)
            return True
            
        except Exception as e:
            print(f"Error confirming payment: {e}")
            return False
    
    def fulfill_order(self, payment):
        """Fulfill the order after payment confirmation"""
        from lacesstore.models import Order
        
        if not payment.order:
            # Create order from session data
            from lacesstore.models import Order, Customer
            from lacesstore.views import _cart_id
            from lacesstore.models import Cart, CartItem, Product, ProductVariant
            
            # Get cart and create order
            try:
                cart = Cart.objects.get(cart_id=_cart_id(payment.user))
                cart_items = CartItem.objects.filter(cart=cart, active=True)
                
                if not cart_items:
                    return
                
                total = Decimal('0.00')
                for item in cart_items:
                    total += item.product.price * item.quantity
                
                # Get customer
                customer = None
                if payment.user:
                    customer, _ = Customer.objects.get_or_create(
                        user=payment.user,
                        defaults={
                            'email': payment.user.email,
                            'firstName': payment.user.first_name,
                            'lastName': payment.user.last_name,
                        }
                    )
                
                # Create order
                order = Order.objects.create(
                    customer=customer,
                    total=total,
                    emailAddress=payment.user.email if payment.user else '',
                    firstName=payment.user.first_name if payment.user else '',
                    lastName=payment.user.last_name if payment.user else '',
                    is_paid=True,
                    payment_method='web3',
                    grand_total=float(total),
                    currency='USD',
                )
                
                # Create order items
                for item in cart_items:
                    OrderItem.objects.create(
                        product=item.product.name,
                        product_image=item.variant.image if item.variant else item.product.image,
                        quantity=item.quantity,
                        price=item.product.price,
                        order=order
                    )
                    
                    # Reduce stock
                    if item.variant:
                        variant = ProductVariant.objects.get(id=item.variant.id)
                        variant.stock -= item.quantity
                        variant.save()
                    else:
                        product = Product.objects.get(id=item.product.id)
                        product.stock -= item.quantity
                        product.save()
                    
                    item.delete()
                
                payment.order = order
                payment.save()
                
                print(f"✅ Order {order.id} created and fulfilled via Web3 payment")
                
            except Exception as e:
                print(f"Error creating order: {e}")
        else:
            # Order already exists, mark as paid
            order = payment.order
            order.is_paid = True
            order.payment_method = 'web3'
            order.save()
            print(f"✅ Order {order.id} marked as paid via Web3 payment")


class Web3PriceService:
    """Service to fetch token prices"""
    
    def __init__(self):
        self.coingecko_api = "https://api.coingecko.com/api/v3"
    
    def get_token_price(self, token_symbol, currency='usd'):
        """Get token price from CoinGecko"""
        try:
            # Map common symbols to CoinGecko IDs
            symbol_map = {
                'USDC': 'usd-coin',
                'USDT': 'tether',
                'ETH': 'ethereum',
                'BTC': 'bitcoin',
                'MATIC': 'matic-network',
                'BNB': 'binancecoin',
            }
            
            token_id = symbol_map.get(token_symbol.upper(), token_symbol.lower())
            url = f"{self.coingecko_api}/simple/price?ids={token_id}&vs_currencies={currency}"
            response = requests.get(url, timeout=10)
            data = response.json()
            price = data.get(token_id, {}).get(currency, 0)
            return Decimal(str(price))
        except Exception as e:
            print(f"Error fetching price for {token_symbol}: {e}")
            return Decimal('0')


class Web3QRCodeGenerator:
    """Generate QR codes for Web3 payments"""
    
    @staticmethod
    def generate_payment_qr(payment_uri):
        """Generate QR code for payment"""
        import qrcode
        from io import BytesIO
        import base64
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(payment_uri)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        buffered = BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        
        return f"data:image/png;base64,{img_str}"