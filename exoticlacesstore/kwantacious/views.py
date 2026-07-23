# kwantacious/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from decimal import Decimal
from .models import Auction, AuctionBid, AuctionDeposit, AuctionPayment
from exoticlacesstore.utils.currency import get_symbol



def auction_list(request):
    """List all auctions - FREE to view and participate"""
    now = timezone.now()
    active_auctions = Auction.objects.filter(
        status='active',
        start_time__lte=now,
        end_time__gte=now
    ).select_related('product')
    
    upcoming_auctions = Auction.objects.filter(
        status='active',
        start_time__gt=now
    ).select_related('product')
    
    ended_auctions = Auction.objects.filter(
        status='ended'
    ).select_related('product')[:10]
    
    # ✅ Get currency from session like home view
    active_currency = request.session.get("currency", "NGN")
    
    context = {
        'active_auctions': active_auctions,
        'upcoming_auctions': upcoming_auctions,
        'ended_auctions': ended_auctions,
        'currency': active_currency,  # ✅ Add this
    }
    return render(request, 'kwantacious/auction_list.html', context)


# kwantacious/views.py
def auction_detail(request, auction_id):
    """View auction details - FREE for everyone"""
    auction = get_object_or_404(Auction, id=auction_id)
    user = request.user
    
    # ✅ Get user's currency preference
    active_currency = request.session.get('currency', 'NGN')
    
    # Get user's deposit if any
    user_deposit = None
    has_deposit = False
    if user.is_authenticated:
        user_deposit = AuctionDeposit.objects.filter(auction=auction, user=user).first()
        has_deposit = user_deposit is not None
    
    # Get user's bids
    user_bids = AuctionBid.objects.filter(auction=auction, user=user).order_by('-amount')
    has_bid = user_bids.exists() if user.is_authenticated else False
    
    # Get top bids
    top_bids = AuctionBid.objects.filter(auction=auction).order_by('-amount')[:10]
    
    # ✅ Format amounts with currency
    from currency.context_processors import currency_context
    currency_data = currency_context(request)
    
    context = {
        'auction': auction,
        'has_deposit': has_deposit,
        'has_bid': has_bid,
        'user_bids': user_bids,
        'top_bids': top_bids,
        'reserve_met': auction.reserve_met(),
        'is_winner': auction.current_winner == user if user.is_authenticated else False,
        'bid_count': auction.get_bid_count(),
        'security_deposit': auction.security_deposit,
        'deposit_optional': auction.security_deposit > 0,
        # ✅ Currency support
        'currency': active_currency,
        'currency_symbol': get_symbol(active_currency),
        'time_remaining': (auction.end_time - timezone.now()).total_seconds(),
    }
    return render(request, 'kwantacious/auction_detail.html', context)


@login_required
def place_deposit(request, auction_id):
    """OPTIONAL: Place a refundable security deposit (100% refundable)"""
    auction = get_object_or_404(Auction, id=auction_id)
    user = request.user
    
    if not auction.is_active():
        messages.error(request, "This auction is not active.")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    # ✅ No deposit required - it's optional
    if auction.security_deposit <= 0:
        messages.info(request, "No deposit required for this auction.")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    if AuctionDeposit.objects.filter(auction=auction, user=user).exists():
        messages.info(request, "You have already placed a deposit.")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    if request.method == 'POST':
        deposit = AuctionDeposit.objects.create(
            auction=auction,
            user=user,
            amount=auction.security_deposit,
            status='held',
            transaction_ref=f"DEP-{auction.id}-{user.id}-{timezone.now().timestamp()}"
        )
        
        messages.success(request, f"Security deposit of ₦{auction.security_deposit:,.2f} placed! (100% refundable if you don't win)")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    # ✅ Get currency from session
    active_currency = request.session.get("currency", "NGN")
    
    return render(request, 'kwantacious/place_deposit.html', {
        'auction': auction,
        'currency': active_currency,  # ✅ Add this
    })











@login_required
def place_bid(request, auction_id):
    """Place a bid - COMPLETELY FREE, no payment required"""
    auction = get_object_or_404(Auction, id=auction_id)
    user = request.user
    
    if not auction.is_active():
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'message': 'Auction is not active.'}, status=400)
        messages.error(request, "This auction is not active.")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    # Check deposit if required
    if auction.security_deposit > 0:
        has_deposit = AuctionDeposit.objects.filter(auction=auction, user=user, status='held').exists()
        if not has_deposit:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'Please place a refundable deposit of ₦{auction.security_deposit:,.2f} first.'
                }, status=400)
            messages.warning(request, f"Please place a refundable deposit of ₦{auction.security_deposit:,.2f} first.")
            return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        current_max = auction.bids.aggregate(max_bid=models.Max('amount'))['max_bid'] or auction.starting_price
        
        # Validate bid
        if amount <= current_max:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'Bid must be higher than current bid of ₦{current_max:,.2f}'
                }, status=400)
            messages.error(request, f"Bid must be higher than current bid of ₦{current_max:,.2f}")
            return redirect('kwantacious:auction_detail', auction_id=auction.id)
        
        if amount - current_max < auction.minimum_bid_increment:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False, 
                    'message': f'Minimum bid increment is ₦{auction.minimum_bid_increment:,.2f}'
                }, status=400)
            messages.error(request, f"Minimum bid increment is ₦{auction.minimum_bid_increment:,.2f}")
            return redirect('kwantacious:auction_detail', auction_id=auction.id)
        
        # ✅ Create bid
        bid = AuctionBid.objects.create(
            auction=auction,
            user=user,
            amount=amount
        )
        
        # Update auction
        auction.current_bid = amount
        auction.current_winner = user
        auction.bid_count += 1
        auction.save()
        
        # Auto-extend
        if auction.auto_extend:
            time_left = (auction.end_time - timezone.now()).total_seconds() / 60
            if time_left < auction.auto_extend_minutes:
                auction.end_time = timezone.now() + timezone.timedelta(minutes=auction.auto_extend_minutes)
                auction.save()
                extend_message = " Auction extended by 5 minutes!"
            else:
                extend_message = ""
        
        # ✅ For AJAX requests, return JSON with success and redirect URL
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': f'✅ Bid of ₦{amount:,.2f} placed successfully!{extend_message}',
                'current_bid': str(amount),
                'current_winner': user.username,
                'redirect_url': reverse('kwantacious:auction_detail', args=[auction.id]),
                'time_remaining': (auction.end_time - timezone.now()).total_seconds(),
            })
        
        # ✅ For regular form submission, redirect to detail page
        messages.success(request, f"✅ Bid of ₦{amount:,.2f} placed successfully!{extend_message}")
        return redirect('kwantacious:auction_detail', auction_id=auction.id)
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'}, status=400)