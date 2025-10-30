from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
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
    context = {
        'total_purchases': Purchase.objects.filter(buyer=request.user).count(),
        'active_bids': Bid.objects.filter(bidder=request.user, is_accepted=False).count(),
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
    # Location filter placeholder: if request.GET.get('location'): listings = listings.filter(location__icontains=...)
    paginator = Paginator(listings, 10)
    page_number = request.GET.get('page')
    listings_paginated = paginator.get_page(page_number)
    return render(request, 'buyer/marketplace_buy.html', {'listings': listings_paginated})

@login_required
@buyer_required
def product_detail(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, is_active=True)
    bids = Bid.objects.filter(listing=listing).order_by('-amount')
    return render(request, 'buyer/product_detail.html', {'listing': listing, 'bids': bids})

@login_required
@buyer_required
def place_bid(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, is_active=True)
    if request.method == 'POST':
        form = BidForm(request.POST, listing=listing)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.bidder = request.user
            bid.save()
            messages.success(request, 'Bid placed successfully!')
            return redirect('buyer:product_detail', listing_id=listing.id)
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
def my_purchases(request):
    purchases = Purchase.objects.filter(buyer=request.user).order_by('-purchase_date')
    paginator = Paginator(purchases, 10)
    page_number = request.GET.get('page')
    purchases_paginated = paginator.get_page(page_number)
    return render(request, 'buyer/my_purchases.html', {'purchases': purchases_paginated})

@login_required
@buyer_required
def storage_slots(request):
    slots = StorageSlot.objects.filter(available_slots__gt=0, is_active=True).order_by('location')
    paginator = Paginator(slots, 10)
    page_number = request.GET.get('page')
    slots_paginated = paginator.get_page(page_number)
    return render(request, 'buyer/storage_slots.html', {'slots': slots_paginated})

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
    return render(request, 'buyer/subsidies.html', {'schemes': schemes})

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