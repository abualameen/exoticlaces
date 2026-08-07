from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.urls import reverse
import json
from .models import Web3Payment, Web3Token, Web3Network
from .services import Web3PaymentService, Web3PriceService, Web3QRCodeGenerator


def web3_payment_detail(request, payment_id):
    """Display Web3 payment details with QR code"""
    payment = get_object_or_404(Web3Payment, id=payment_id)
    
    # Check permission
    if payment.user and request.user.is_authenticated and payment.user != request.user:
        messages.error(request, "You don't have permission to view this payment")
        return redirect('home')
    
    # Check payment status
    service = Web3PaymentService()
    status = service.check_payment_status(payment)
    
    if status == 'confirmed':
        service.confirm_payment(payment)
        messages.success(request, "✅ Payment confirmed! Your order is being processed.")
        return redirect('thanks_page', order_id=payment.order.id)
    
    # Generate QR code
    qr_code = Web3QRCodeGenerator.generate_payment_qr(payment.payment_uri)
    
    context = {
        'payment': payment,
        'qr_code': qr_code,
        'status': status,
        'is_expired': timezone.now() > payment.expires_at,
    }
    
    return render(request, 'web3_payment/payment_detail.html', context)


@login_required
def create_web3_payment(request, order_id):
    """Create a Web3 payment for an order"""
    from lacesstore.models import Order
    
    order = get_object_or_404(Order, id=order_id)
    
    # Check permission
    if order.customer and order.customer.user != request.user:
        messages.error(request, "You don't have permission to pay for this order")
        return redirect('home')
    
    if order.is_paid:
        messages.warning(request, "This order is already paid")
        return redirect('order_detail', order_id=order.id)
    
    # Get default token and network
    token = Web3Token.objects.filter(is_active=True).first()
    network = token.network if token else Web3Network.objects.filter(is_active=True).first()
    
    if not token or not network:
        messages.error(request, "Web3 payment is currently unavailable")
        return redirect('order_detail', order_id=order.id)
    
    # Create payment
    service = Web3PaymentService()
    
    # Convert NGN to USD (approximate)
    usd_amount = float(order.grand_total) / 1500
    crypto_amount = usd_amount  # 1 USDC = 1 USD
    
    payment = Web3Payment.objects.create(
        order=order,
        user=request.user,
        token=token,
        network=network,
        amount=crypto_amount,
        usd_amount=usd_amount,
        to_address=service.generate_payment_address(network.chain_id),
        payment_address=service.generate_payment_address(network.chain_id),
        status='pending',
        expires_at=timezone.now() + timezone.timedelta(hours=1),
        required_confirmations=network.confirmations_required,
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Generate payment URI
    payment.payment_uri = service.create_payment_uri(payment)
    payment.save()
    
    return redirect('web3_payment:detail', payment_id=payment.id)


@csrf_exempt
@require_http_methods(["POST"])
def web3_webhook(request):
    """Webhook for blockchain events"""
    try:
        data = json.loads(request.body)
        tx_hash = data.get('tx_hash')
        payment_address = data.get('payment_address')
        
        if not tx_hash or not payment_address:
            return JsonResponse({'error': 'Missing parameters'}, status=400)
        
        payment = Web3Payment.objects.filter(payment_address=payment_address).first()
        if not payment:
            return JsonResponse({'error': 'Payment not found'}, status=404)
        
        service = Web3PaymentService()
        status = service.check_payment_status(payment)
        
        if status == 'confirmed':
            service.confirm_payment(payment)
        
        return JsonResponse({
            'success': True,
            'status': payment.status,
            'payment_id': payment.id,
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def web3_payment_verify(request):
    """Verify Web3 payment and confirm it"""
    if request.method == 'GET':
        payment_id = request.GET.get('payment_id')
        if not payment_id:
            messages.error(request, "Invalid payment ID")
            return redirect('home')
        
        payment = get_object_or_404(Web3Payment, id=payment_id)
        
        # Check payment status
        service = Web3PaymentService()
        status = service.check_payment_status(payment)
        
        if status == 'confirmed':
            service.confirm_payment(payment)
            messages.success(request, "✅ Payment confirmed! Your order is being processed.")
            return redirect('thanks_page', order_id=payment.order.id)
        elif status == 'expired':
            messages.error(request, "Payment expired. Please try again.")
            return redirect('web3_payment:create', order_id=payment.order.id)
        else:
            messages.info(request, "Payment is still processing. Please wait...")
            return redirect('web3_payment:detail', payment_id=payment.id)
    
    return JsonResponse({'error': 'Invalid request'}, status=400)


def web3_payment_status(request, payment_id):
    """Get payment status via AJAX"""
    payment = get_object_or_404(Web3Payment, id=payment_id)
    service = Web3PaymentService()
    status = service.check_payment_status(payment)
    
    # If confirmed, update the payment
    if status == 'confirmed':
        service.confirm_payment(payment)
    
    return JsonResponse({
        'status': status,
        'payment_id': payment.id,
        'order_id': payment.order.id if payment.order else None,
    })


def web3_available_tokens(request):
    """Get available tokens for payment"""
    tokens = Web3Token.objects.filter(is_active=True).values(
        'id', 'symbol', 'name', 'network__name'
    )
    return JsonResponse({'tokens': list(tokens)})