from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from utils.pagination import paginate_queryset  # make sure path is correct
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from adminpanel.models import StorageSlot, SubsidyScheme
from farmer.models import ProductListing, Bid, StorageBooking
from .models import Purchase
from .forms import BidForm, PurchaseForm, StorageBookingForm

def buyer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'buyer':
            messages.warning(request, 'No permission to access this page.')
            return redirect('accounts:home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@buyer_required
def dashboard(request):
    now = timezone.now()

    total_purchases = Purchase.objects.filter(buyer=request.user).count()

    # ✅ Only include bids on active listings where bidding hasn't ended
    active_bids = Bid.objects.filter(
        bidder=request.user,
        is_accepted=False,
        listing__is_active=True,
        listing__bid_end_time__gt=now
    ).count()

    context = {
        'total_purchases': total_purchases,
        'active_bids': active_bids,
    }
    return render(request, 'buyer/dashboard.html', context)

@login_required
@buyer_required
def profile(request):
    # Similar to farmer, but no land/docs
    purchases = Purchase.objects.filter(buyer=request.user)
    return render(request, 'buyer/profile.html', {'purchases': purchases})

@login_required
@buyer_required
def marketplace_buy(request):
    now = timezone.now()
    
    # Get all active listings
    listings = ProductListing.objects.filter(is_active=True).order_by('-created_at')
    
    # Split listings into bidding and direct purchase
    bidding_listings = []
    direct_purchase_listings = []
    
    for listing in listings:
        if listing.is_bidding_open():
            bidding_listings.append(listing)
        elif listing.is_available_for_regular_purchase():
            direct_purchase_listings.append(listing)
    
    # Paginate both lists
    bidding_page_obj, bidding_listings = paginate_queryset(request, bidding_listings)
    direct_page_obj, direct_purchase_listings = paginate_queryset(request, direct_purchase_listings)
    
    context = {
        'bidding_listings': bidding_listings,
        'bidding_page_obj': bidding_page_obj,
        'direct_purchase_listings': direct_purchase_listings,
        'direct_page_obj': direct_page_obj,
    }
    
    return render(request, 'buyer/marketplace_buy.html', context)

from django.utils import timezone
from buyer.models import Purchase

@login_required
@buyer_required
def product_detail(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id)
    now = timezone.now()

    # Handle bidding end
    if listing.is_active and listing.bid_end_time and listing.bid_end_time < now:
        highest_bid = listing.highest_bid()
        if highest_bid and highest_bid.payment_status == 'completed':
            highest_bid.is_accepted = True
            highest_bid.save(update_fields=["is_accepted"])

            # Create purchase for winning bid
            Purchase.objects.get_or_create(
                buyer=highest_bid.bidder,
                listing=listing,
                defaults={
                    "quantity": highest_bid.quantity,
                    "total_price": highest_bid.total_amount,
                    "payment_completed": True,
                },
            )

    # Get bid information
    bids = Bid.objects.filter(listing=listing).order_by('-amount')
    winner_bid = listing.winning_bid()
    is_winner = winner_bid and request.user == winner_bid.bidder

    # Check if available for regular purchase
    available_for_purchase = listing.is_available_for_regular_purchase()
    available_quantity = listing.available_quantity() if available_for_purchase else 0

    # Handle regular purchase form
    purchase_form = None
    if available_for_purchase:
        if request.method == 'POST' and 'purchase_submit' in request.POST:
            purchase_form = PurchaseForm(request.POST)
            if purchase_form.is_valid():
                quantity = purchase_form.cleaned_data['quantity']
                if quantity <= available_quantity:
                    purchase = purchase_form.save(commit=False)
                    purchase.buyer = request.user
                    purchase.listing = listing
                    purchase.total_price = listing.price * quantity
                    purchase.payment_completed = True  # Mark payment as completed for regular purchases
                    purchase.status = 'payment_completed'  # Update status immediately for regular purchases
                    purchase.save()
                    
                    messages.success(request, 'Purchase confirmed!')
                    return redirect('buyer:marketplace_buy')
                else:
                    messages.error(request, f'Only {available_quantity} units available.')
        else:
            purchase_form = PurchaseForm()

    context = {
        'listing': listing,
        'bids': bids,
        'winner_bid': winner_bid,
        'is_winner': is_winner,
        'now': timezone.now(),
    }
    return render(request, 'buyer/product_detail.html', context)




# buyer/views.py

@login_required
@buyer_required
def place_bid(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, is_active=True)

    if not listing.is_bidding_open():
        messages.error(request, "Bidding for this listing has ended.")
        return redirect('buyer:product_detail', listing_id=listing.id)

    if request.method == 'POST':
        form = BidForm(request.POST, listing=listing)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.bidder = request.user
            bid.quantity = listing.quantity  # automatically assign
            bid.save()

            messages.success(request, 'Bid placed successfully!')
            return redirect('buyer:product_detail', listing_id=listing.id)
        else:
            messages.error(request, 'There was an error with your bid.')
    else:
        form = BidForm(listing=listing)

    return render(request, 'buyer/place_bid.html', {'form': form, 'listing': listing})



@login_required
@buyer_required
def purchase_product(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, is_active=True)
    if request.method == 'POST':
        form = PurchaseForm(request.POST, listing=listing)
        if form.is_valid():
            purchase = form.save(commit=False)
            purchase.buyer = request.user
            purchase.save()
            # Update listing quantity
            listing.quantity -= purchase.quantity
            if listing.quantity <= 0:
                listing.is_active = False
            listing.save()
            messages.success(request, 'Purchase confirmed!')
            return redirect('buyer:my_purchases')
    else:
        form = PurchaseForm(listing=listing)
    return render(request, 'buyer/purchase_product.html', {'form': form, 'listing': listing})

@login_required
@buyer_required
def make_bid_payment(request, bid_id):
    bid = get_object_or_404(Bid, id=bid_id, bidder=request.user)
    listing = bid.listing

    # Create or get the purchase record for this bid
    purchase, created = Purchase.objects.get_or_create(
        buyer=request.user,
        listing=listing,
        defaults={
            'quantity': bid.quantity,
            'total_price': bid.total_amount,  # Use total_amount which is amount * quantity
            'status': 'pending_payment'
        }
    )

    # If already paid, don't allow double payment
    if purchase.payment_completed or bid.payment_status == 'completed':
        messages.info(request, "This bid has already been paid for.")
        return redirect('buyer:my_purchases')

    if request.method == "POST":
        # Update both purchase and bid status
        purchase.payment_completed = True
        purchase.status = 'payment_completed'
        purchase.save()
        
        bid.payment_status = 'completed'
        bid.is_accepted = True
        bid.save()
        
        # Update listing status
        listing.save()  # This will trigger quantity check
        
        messages.success(request, "✅ Payment successful for your winning bid!")
        return redirect('buyer:my_purchases')

    return render(
        request,
        "buyer/make_bid_payment.html",
        {"purchase": purchase, "listing": listing, "bid": bid},
    )





@login_required
@buyer_required
def my_purchases(request):
    # Get regular purchases
    purchases = Purchase.objects.filter(buyer=request.user).order_by('-purchase_date')
    
    # Get winning bids
    winning_bids = Bid.objects.filter(
        bidder=request.user,
        is_accepted=True
    ).select_related('listing').order_by('-placed_at')
    
    # Combine purchase info
    purchase_info = []
    
    # Add regular purchases
    for purchase in purchases:
        purchase_info.append({
            'date': purchase.purchase_date,
            'type': 'regular',
            'listing': purchase.listing,
            'quantity': purchase.quantity,
            'amount': purchase.total_price,
            'status': purchase.status,
            'payment_completed': purchase.payment_completed,
            'purchase': purchase
        })
    
    # Add winning bids
    for bid in winning_bids:
        purchase_info.append({
            'date': bid.placed_at,
            'type': 'bid',
            'listing': bid.listing,
            'quantity': bid.quantity,
            'amount': bid.total_amount,
            'status': 'Payment Completed' if bid.payment_status == 'completed' else 'Pending Payment',
            'payment_completed': bid.payment_status == 'completed',
            'bid': bid
        })
    
    # Sort by date, newest first
    purchase_info.sort(key=lambda x: x['date'], reverse=True)
    
    page_obj, purchase_info = paginate_queryset(request, purchase_info)
    return render(request, 'buyer/my_purchases.html', {
        'purchases': purchase_info,
        'page_obj': page_obj
    })

@login_required
@buyer_required
def storage_slots(request):
    slots = StorageSlot.objects.filter(available_slots__gt=0, is_active=True).order_by('location')
    page_obj, slots = paginate_queryset(request, slots)
    return render(request, 'buyer/storage_slots.html', {'slots': slots, 'page_obj': page_obj})

@login_required
@buyer_required
def book_storage(request, slot_id):
    slot = get_object_or_404(StorageSlot, id=slot_id)
    if request.method == 'POST':
        form = StorageBookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.slot = slot
            booking.save()
            messages.success(request, 'Storage slot booked! Awaiting approval.')
            return redirect('buyer:dashboard')
    else:
        form = StorageBookingForm(user=request.user, initial={'slot': slot})
    return render(request, 'buyer/book_storage.html', {'form': form, 'slot': slot})

@login_required
@buyer_required
def subsidies(request):
    schemes = SubsidyScheme.objects.filter(is_active=True)
    page_obj, schemes = paginate_queryset(request, schemes)
    return render(request, 'buyer/subsidies.html', {'schemes': schemes, 'page_obj': page_obj})

@login_required
@buyer_required
def notifications(request):
    context = {'message': 'Notifications for weather, schemes, and updates will appear here.'}
    return render(request, 'buyer/notifications.html', context)

@login_required
@buyer_required
def booking_detail(request, booking_id):
    booking = get_object_or_404(StorageBooking, id=booking_id, user=request.user)
    return render(request, 'buyer/booking_detail.html', {'booking': booking})