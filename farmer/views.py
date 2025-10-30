from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import Http404
from django.db.models import Sum, F, DecimalField, Q, Value
from django.db.models.functions import Coalesce
from django.core.paginator import Paginator
from django.db import models
from django.db.models.functions import Coalesce
from django.contrib import messages
from adminpanel.forms import LandRecordForm
from django.core.paginator import Paginator
from adminpanel.models import LandRecord, UserDocument
from adminpanel.forms import UserDocumentForm
from django.utils import timezone
from adminpanel.models import CultivationSlot, StorageSlot, SubsidyScheme
from .models import CultivationBooking, StorageBooking, ProductListing, Bid
from .forms import CultivationBookingForm, StorageBookingForm, ProductListingForm

def farmer_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'farmer':
            messages.warning(request, 'No permission to access this page.')
            return redirect('accounts:home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@farmer_required
def dashboard(request):
    context = {
        'pending_bookings': CultivationBooking.objects.filter(user=request.user, status='pending').count() + StorageBooking.objects.filter(user=request.user, status='pending').count(),
        'active_listings': ProductListing.objects.filter(user=request.user, is_active=True).count(),
        'schemes_count': SubsidyScheme.objects.count(),  # Add this line

    }
    return render(request, 'farmer/dashboard.html', context)

@login_required
@farmer_required
def profile(request):
    # Extend accounts profile with land/docs
    land_records = LandRecord.objects.filter(user=request.user)  # From adminpanel
    documents = UserDocument.objects.filter(user=request.user)
    return render(request, 'farmer/profile.html', {'land_records': land_records, 'documents': documents})

@login_required
@farmer_required
def land_records(request):
    records = LandRecord.objects.filter(user=request.user)
    paginator = Paginator(records, 5)
    page_number = request.GET.get('page')
    records_paginated = paginator.get_page(page_number)
    return render(request, 'farmer/land_records.html', {'records': records_paginated})

@login_required
@farmer_required
def upload_land_record(request):
    if request.method == 'POST':
        form = LandRecordForm(request.POST, request.FILES)
        if form.is_valid():
            land_record = form.save(commit=False)
            land_record.user = request.user  # Assign current farmer
            land_record.save()
            messages.success(request, 'Land record uploaded successfully!')
            return redirect('farmer:land_records')  # Redirect to the list view
    else:
        form = LandRecordForm()

    return render(request, 'farmer/upload_land_record.html', {'form': form})


@login_required
@farmer_required
def upload_document(request):
    if request.method == 'POST':
        form = UserDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            doc = form.save(commit=False)
            doc.user = request.user
            doc.save()
            messages.success(request, 'Document uploaded for verification.')
            return redirect('farmer:dashboard')
    else:
        form = UserDocumentForm()
    return render(request, 'farmer/upload_document.html', {'form': form})

from django.db.models import Sum, F, Value, Q
from django.db.models.functions import Coalesce

@login_required
@farmer_required
def cultivation_slots(request):
    slots = CultivationSlot.objects.filter(is_active=True).annotate(
        pending_booked=Coalesce(
            Sum('bookings__booked_area_acres', filter=Q(bookings__status='pending')),
            Value(0, output_field=DecimalField())  # <-- set output_field to DecimalField
        )
    ).annotate(
        effective_available=F('available_area_acres') - F('pending_booked')
    ).filter(effective_available__gt=0).order_by('location')

    paginator = Paginator(slots, 10)
    page_number = request.GET.get('page')
    slots_paginated = paginator.get_page(page_number)
    return render(request, 'farmer/cultivation_slots.html', {'slots': slots_paginated})

@login_required
@farmer_required
def my_cultivation_bookings(request):
    # Filter bookings for the logged-in farmer
    bookings = CultivationBooking.objects.filter(user=request.user).order_by('-booked_at')

    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    bookings_paginated = paginator.get_page(page_number)

    return render(request, 'farmer/my_cultivation_bookings.html', {'bookings': bookings_paginated})

@login_required
@farmer_required
def book_cultivation(request, slot_id):
    slot = get_object_or_404(CultivationSlot, id=slot_id)
    if request.method == 'POST':
        form = CultivationBookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.slot = slot
            # Explicitly set total_price here
            booking.total_price = booking.booked_area_acres * slot.price_per_acre
            booking.save()
            messages.success(request, 'Cultivation slot booked successfully! Awaiting approval.')
            return redirect('farmer:dashboard')
    else:
        form = CultivationBookingForm(user=request.user, initial={'slot': slot})
    return render(request, 'farmer/book_cultivation.html', {'form': form, 'slot': slot})


@login_required
@farmer_required
def storage_slots(request):
    # Base queryset for active storage slots
    slots = StorageSlot.objects.filter(is_active=True).annotate(
        pending_booked=Coalesce(
            Sum('storagebooking__booked_slots', filter=models.Q(storagebooking__status='pending')),
            Value(0)
        )
    ).annotate(
        effective_available=F('available_slots') - F('pending_booked')
    ).filter(effective_available__gt=0).order_by('location')

    paginator = Paginator(slots, 10)
    page_number = request.GET.get('page')
    slots_paginated = paginator.get_page(page_number)
    return render(request, 'farmer/storage_slots.html', {'slots': slots_paginated})

@login_required
@farmer_required
def my_storage_bookings(request):
    # Filter bookings for the logged-in farmer
    bookings = StorageBooking.objects.filter(user=request.user).order_by('-booked_at')

    # Pagination
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    bookings_paginated = paginator.get_page(page_number)

    return render(request, 'farmer/my_storage_bookings.html', {'bookings': bookings_paginated})

@login_required
@farmer_required
def book_storage(request, slot_id):
    slot = (
        StorageSlot.objects.filter(id=slot_id, is_active=True)
        .annotate(
            pending_booked=Coalesce(
                Sum('storagebooking__booked_slots', filter=models.Q(storagebooking__status='pending')),
                Value(0)
            )
        )
        .annotate(
            effective_available=F('available_slots') - F('pending_booked')
        )
        .first()
    )

    if not slot:
        raise Http404("Storage slot not found or inactive.")

    if request.method == 'POST':
        form = StorageBookingForm(request.POST, user=request.user)
        if form.is_valid():
            booking = form.save(commit=False)
            booking.user = request.user
            booking.slot = slot
            booking.total_price = booking.booked_slots * slot.price_per_slot
            booking.save()
            messages.success(request, 'Storage slot booked successfully! Awaiting approval.')
            return redirect('farmer:dashboard')
    else:
        form = StorageBookingForm(user=request.user, initial={'slot': slot})

    return render(request, 'farmer/book_storage.html', {'form': form, 'slot': slot})



@login_required
@farmer_required
def marketplace_sell(request):
    listings = ProductListing.objects.filter(user=request.user, is_active=True)
    paginator = Paginator(listings, 10)
    page_number = request.GET.get('page')
    listings_paginated = paginator.get_page(page_number)
    return render(request, 'farmer/marketplace_sell.html', {'listings': listings_paginated})

@login_required
@farmer_required
def create_listing(request):
    if request.method == 'POST':
        form = ProductListingForm(request.POST, request.FILES)
        if form.is_valid():
            listing = form.save(commit=False)
            listing.user = request.user
            listing.save()
            messages.success(request, 'Product listing created.')
            return redirect('farmer:marketplace_sell')
    else:
        form = ProductListingForm(initial={'location': request.user.address})
    return render(request, 'farmer/create_listing.html', {'form': form})

@login_required
@farmer_required
def edit_listing(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, user=request.user)
    if request.method == 'POST':
        form = ProductListingForm(request.POST, request.FILES, instance=listing)
        if form.is_valid():
            form.save()
            messages.success(request, 'Listing updated.')
            return redirect('farmer:marketplace_sell')
    else:
        form = ProductListingForm(instance=listing)
    return render(request, 'farmer/edit_listing.html', {'form': form})

@login_required
@farmer_required
def delete_listing(request, listing_id):
    listing = get_object_or_404(ProductListing, id=listing_id, user=request.user)
    listing.delete()
    messages.success(request, 'Listing deleted.')
    return redirect('farmer:marketplace_sell')

@login_required
@farmer_required
def subsidies(request):
    schemes = SubsidyScheme.objects.filter(is_active=True)
    return render(request, 'farmer/subsidies.html', {'schemes': schemes})

@login_required
@farmer_required
def analytics_guidance(request):
    # Placeholder: AI predictions, weather
    context = {'message': 'Analytics and guidance features coming soon. Weather alerts and crop predictions will be here.'}
    return render(request, 'farmer/analytics_guidance.html', context)

@login_required
@farmer_required
def notifications(request):
    # Placeholder: Fetch from notifications app later
    context = {'message': 'Notifications for weather, schemes, and slot updates will appear here.'}
    return render(request, 'farmer/notifications.html', context)

@login_required
@farmer_required
def booking_detail(request, booking_id):
    # Generic for cult/storage; detect type
    try:
        booking = get_object_or_404(CultivationBooking, id=booking_id, user=request.user)
        booking_type = 'cultivation'
    except:
        booking = get_object_or_404(StorageBooking, id=booking_id, user=request.user)
        booking_type = 'storage'
    return render(request, 'farmer/booking_detail.html', {'booking': booking, 'type': booking_type})