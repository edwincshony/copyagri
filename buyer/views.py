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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from adminpanel.models import StorageSlot, SubsidyScheme
from farmer.models import ProductListing, Bid
from .models import Purchase
from .forms import BidForm, PurchaseForm, StorageBookingForm

@login_required
def product_detail(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id)

    bids = Bid.objects.filter(listing=listing).order_by('-amount')
    winner_bid = listing.winning_bid()
    is_winner = bool(winner_bid and request.user == winner_bid.bidder)
    show_winner_pay_cta = bool(
        is_winner
        and (listing.is_bidding_open() or listing.is_within_bid_payment_window())
        and winner_bid.payment_status == 'pending'
    )

    available_for_purchase = listing.is_available_for_regular_purchase()
    available_quantity = listing.available_quantity()

    # Winner: initialize a Purchase for bid and redirect to unified pay page
    if show_winner_pay_cta and request.method == 'GET' and request.GET.get('init_bid_payment') == '1':
        existing = Purchase.objects.filter(
            buyer=request.user,
            listing=listing,
            purchase_type='bid',
            related_bid=winner_bid
        ).first()
        if existing:
            return redirect('buyer:pay', purchase_id=existing.id)
        purchase = Purchase.objects.create(
            buyer=request.user,
            listing=listing,
            purchase_type='bid',
            related_bid=winner_bid,
            quantity=winner_bid.quantity,
            unit_price=winner_bid.amount,
            total_price=winner_bid.total_amount,
            status='pending_payment',
        )
        return redirect('buyer:pay', purchase_id=purchase.id)

    # Regular purchase flow -> create pending Purchase and redirect to unified payments
    purchase_form = None
    if available_for_purchase:
        if request.method == 'POST' and 'purchase_submit' in request.POST:
            purchase_form = PurchaseForm(request.POST, listing=listing)
            if purchase_form.is_valid():
                quantity = purchase_form.cleaned_data['quantity']
                purchase = Purchase.objects.create(
                    buyer=request.user,
                    listing=listing,
                    purchase_type='regular',
                    quantity=quantity,
                    unit_price=listing.price,
                    total_price=listing.price * quantity,
                    status='pending_payment',
                )
                messages.success(request, 'Proceed to payment to confirm your order.')
                return redirect('buyer:pay', purchase_id=purchase.id)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            purchase_form = PurchaseForm(listing=listing)

    context = {
        'listing': listing,
        'bids': bids,
        'winner_bid': winner_bid,
        'is_winner': is_winner,
        'show_winner_pay_cta': show_winner_pay_cta,
        'available_for_purchase': available_for_purchase,
        'available_quantity': available_quantity,
        'purchase_form': purchase_form,
        'now': timezone.now(),
    }
    return render(request, 'buyer/product_detail.html', context)





# buyer/views.py

@login_required
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
            bid.quantity = listing.quantity  # lock to listing.quantity
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
def my_purchases(request):
    purchases = Purchase.objects.filter(buyer=request.user).order_by('-purchase_date')
    page_obj, purchases = paginate_queryset(request, purchases)
    return render(request, 'buyer/my_purchases.html', {'purchases': purchases, 'page_obj': page_obj})

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


# payments/views.py (NEW)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.utils.crypto import get_random_string
from django.contrib import messages
from buyer.models import Purchase
from .models import Payment

@login_required
def pay(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
    if purchase.status == 'payment_completed' and purchase.payment and purchase.payment.status == 'success':
        return redirect('buyer:success', purchase_id=purchase.id)

    # Initialize payment if not exists
    if not purchase.payment:
        payment = Payment.objects.create(
            user=request.user,
            amount=purchase.total_price,
            method='upi',
            status='initiated',
            reference=get_random_string(16)
        )
        purchase.payment = payment
        purchase.save(update_fields=['payment'])

    if request.method == 'POST':
        # Dummy success path
        purchase.payment.mark_success()
        # Finalize purchase
        purchase.status = 'payment_completed'
        purchase.save(update_fields=['status'])

        # For bid purchase, mark bid accepted + completed
        if purchase.purchase_type == 'bid' and purchase.related_bid:
            bid = purchase.related_bid
            bid.payment_status = 'completed'
            bid.is_accepted = True
            bid.save(update_fields=['payment_status', 'is_accepted'])

        messages.success(request, 'Payment successful!')
        return redirect('buyer:success', purchase_id=purchase.id)

    return render(request, 'buyer/pay.html', {'purchase': purchase})

@login_required
def success(request, purchase_id):
    purchase = get_object_or_404(Purchase, id=purchase_id, buyer=request.user)
    return render(request, 'buyer/success.html', {'purchase': purchase})
