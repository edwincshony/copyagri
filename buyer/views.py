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
    # Filter by buyer_type if needed (wholesaler bulk, etc.)
    listings = ProductListing.objects.filter(is_active=True).order_by('-created_at')
    page_obj, listings = paginate_queryset(request, listings)
    # Location filter placeholder: if request.GET.get('location'): listings = listings.filter(location__icontains=...)
    return render(request, 'buyer/marketplace_buy.html', {'listings': listings,     'page_obj': page_obj})

from django.utils import timezone
from buyer.models import Purchase

@login_required
@buyer_required
def product_detail(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id)

    # ✅ Auto-close expired listing (redundant safety, won't duplicate purchases)
    if listing.is_active and listing.bid_end_time and listing.bid_end_time < timezone.now():
        highest_bid = listing.highest_bid()
        if highest_bid:
            highest_bid.is_accepted = True
            highest_bid.save(update_fields=["is_accepted"])

            # Use same duplicate-safe pattern
            Purchase.objects.get_or_create(
                buyer=highest_bid.bidder,
                listing=listing,
                defaults={
                    "quantity": listing.quantity,
                    "total_price": highest_bid.amount,
                },
            )

        listing.is_active = False
        listing.save(update_fields=["is_active"])

    # Get all bids (sorted highest to lowest)
    bids = Bid.objects.filter(listing=listing).order_by('-amount')

    # Determine winner
    winner_bid = None
    is_winner = False

    if not listing.is_active and bids.exists():
        winner_bid = bids.first()
        if request.user == winner_bid.bidder:
            is_winner = True

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

    # Always pick the most recent purchase for that listing and user
    purchase = Purchase.objects.filter(buyer=request.user, listing=listing).order_by('-id').first()

    if not purchase:
        messages.error(request, "No purchase record found for this bid.")
        return redirect('buyer:product_detail', listing_id=listing.id)

    # If already paid or confirmed, don't allow double payment
    if purchase.status.lower() in ["paid", "confirmed"]:
        messages.info(request, f"This purchase is already marked as '{purchase.status}'.")
        return redirect('buyer:my_purchases')

    if request.method == "POST":
        purchase.status = "Paid"
        purchase.save(update_fields=["status"])
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
    purchases = Purchase.objects.filter(buyer=request.user).order_by('-purchase_date')
    page_obj, purchases = paginate_queryset(request, purchases)
    return render(request, 'buyer/my_purchases.html', {'purchases': purchases , 'page_obj': page_obj})

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