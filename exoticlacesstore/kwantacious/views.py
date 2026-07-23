# kwantacious/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import models
from decimal import Decimal
from .models import Auction, AuctionBid, AuctionDeposit, AuctionPayment
from django.utils import timezone


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


def auction_detail(request, auction_id):
    """View auction details - FREE for everyone"""
    auction = get_object_or_404(Auction, id=auction_id)
    user = request.user
    
    # User's deposit (if any)
    user_deposit = None
    has_deposit = False
    if user.is_authenticated:
        user_deposit = AuctionDeposit.objects.filter(auction=auction, user=user).first()
        has_deposit = user_deposit is not None
    
    # User's bids
    user_bids = AuctionBid.objects.filter(auction=auction, user=user).order_by('-amount')
    has_bid = user_bids.exists() if user.is_authenticated else False
    
    # Top bids
    top_bids = AuctionBid.objects.filter(auction=auction).order_by('-amount')[:10]
    
    # ✅ Auction stats
    reserve_met = auction.reserve_met()
    
    # ✅ Get currency from session like home view
    active_currency = request.session.get("currency", "NGN")
    
    context = {
        'auction': auction,
        'has_deposit': has_deposit,
        'has_bid': has_bid,
        'user_bids': user_bids,
        'top_bids': top_bids,
        'reserve_met': reserve_met,
        'is_winner': auction.current_winner == user if user.is_authenticated else False,
        'bid_count': auction.get_bid_count(),
        'security_deposit': auction.security_deposit,
        'deposit_optional': auction.security_deposit > 0,
        'currency': active_currency,  # ✅ Add this
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

# kwantacious/views.py
@login_required
def place_bid(request, auction_id):
    """Place a bid - COMPLETELY FREE, no payment required"""
    auction = get_object_or_404(Auction, id=auction_id)
    user = request.user
    
    if not auction.is_active():
        return JsonResponse({
            'success': False, 
            'message': 'Auction is not active.'
        }, status=400)
    
    if request.method == 'POST':
        amount = Decimal(request.POST.get('amount', 0))
        current_max = auction.bids.aggregate(max_bid=models.Max('amount'))['max_bid'] or auction.starting_price
        
        # Validate bid
        if amount <= current_max:
            return JsonResponse({
                'success': False, 
                'message': f'Bid must be higher than current bid of ₦{current_max:,.2f}'
            }, status=400)
        
        if amount - current_max < auction.minimum_bid_increment:
            return JsonResponse({
                'success': False, 
                'message': f'Minimum bid increment is ₦{auction.minimum_bid_increment:,.2f}'
            }, status=400)
        
        # Create bid
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
        extended = False
        if auction.auto_extend:
            time_left = (auction.end_time - timezone.now()).total_seconds() / 60
            if time_left < auction.auto_extend_minutes:
                auction.end_time = timezone.now() + timezone.timedelta(minutes=auction.auto_extend_minutes)
                auction.save()
                extended = True
        
        # ✅ Get updated top bids for display
        top_bids = AuctionBid.objects.filter(auction=auction).order_by('-amount')[:10]
        user_bids = AuctionBid.objects.filter(auction=auction, user=user).order_by('-amount')
        
        # ✅ Prepare bid history for rendering
        bid_history = []
        for b in top_bids:
            bid_history.append({
                'username': b.user.username,
                'amount': str(b.amount),
                'is_winner': b.user == auction.current_winner,
                'is_user': b.user == user,
                'placed_at': b.placed_at.strftime('%H:%M:%S %d/%m/%Y'),
            })
        
        # ✅ Check if auction is fully funded (if reserve met)
        reserve_met = auction.reserve_met()
        
        return JsonResponse({
            'success': True,
            'message': f'✅ Bid of ₦{amount:,.2f} placed successfully!',
            'current_bid': str(amount),
            'current_winner': user.username,
            'current_winner_avatar': user.email[:1].upper() if user.email else 'U',
            'time_remaining': (auction.end_time - timezone.now()).total_seconds(),
            'bid_count': auction.get_bid_count(),
            'is_highest_bidder': True,
            'extended': extended,
            'reserve_met': reserve_met,
            'user_bids': [
                {'amount': str(b.amount), 'placed_at': b.placed_at.strftime('%H:%M:%S')}
                for b in user_bids[:5]
            ],
            'top_bids': bid_history,
        })
    
    return JsonResponse({
        'success': False, 
        'message': 'Invalid request method.'
    }, status=400)