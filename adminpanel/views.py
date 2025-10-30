from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from farmer.models import CultivationBooking, StorageBooking
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser
from .models import (
    UserDocument, LandRecord, StorageSlot, CultivationSlot, SubsidyScheme
)
from .forms import (
    UserDocumentForm, LandRecordForm, StorageSlotForm, CultivationSlotForm, SubsidySchemeForm
)

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.warning(request, 'No permission to access this page.')
            return redirect('accounts:home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
@admin_required
def dashboard(request):
    context = {
        'total_users': CustomUser.objects.exclude(is_superuser=True).count(),
        'pending_approvals': CustomUser.objects.filter(is_approved=False, role__in=['farmer', 'buyer']).count(),
        'pending_docs': UserDocument.objects.filter(status='pending').count(),
        'total_storage_slots': StorageSlot.objects.filter(is_active=True).count(),
        'total_cultivation_slots': CultivationSlot.objects.filter(is_active=True).count(),
        'total_schemes': SubsidyScheme.objects.filter(is_active=True).count(),
    }
    return render(request, 'adminpanel/dashboard.html', context)

@login_required
@admin_required
def user_management(request):
    users = CustomUser.objects.filter(role__in=['farmer', 'buyer']).order_by('-date_joined')
    paginator = Paginator(users, 10)
    page_number = request.GET.get('page')
    users_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/user_management.html', {'users': users_paginated})

@login_required
@admin_required
def approve_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_approved = True
    user.save()
    send_mail(
        'Account Approved',
        'Your AgriLeader account has been approved.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
    messages.success(request, f'User {user.username} approved.')
    return redirect('adminpanel:user_management')

@login_required
@admin_required
def reject_user(request, user_id):
    user = get_object_or_404(CustomUser, id=user_id)
    user.is_approved = False
    user.save()
    send_mail(
        'Account Rejected',
        'Your AgriLeader account has been rejected. Please contact support.',
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=True,
    )
    messages.error(request, f'User {user.username} rejected.')
    return redirect('adminpanel:user_management')

@login_required
@admin_required
def document_verification(request):
    docs = UserDocument.objects.filter(status='pending').order_by('-uploaded_at')
    paginator = Paginator(docs, 10)
    page_number = request.GET.get('page')
    docs_paginated = paginator.get_page(page_number)
    if request.method == 'POST':
        doc_id = request.POST.get('doc_id')
        action = request.POST.get('action')
        doc = get_object_or_404(UserDocument, id=doc_id)
        doc.status = 'approved' if action == 'approve' else 'rejected'
        doc.verified_by = request.user
        doc.verified_at = timezone.now()
        doc.save()
        messages.success(request, f'Document {action}d for {doc.user.username}.')
        return redirect('adminpanel:document_verification')
    return render(request, 'adminpanel/document_verification.html', {'docs': docs_paginated})

@login_required
@admin_required
def land_records(request):
    records = LandRecord.objects.all().order_by('-created_at')
    paginator = Paginator(records, 10)
    page_number = request.GET.get('page')
    records_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/land_records.html', {'records': records_paginated})

@login_required
@admin_required
def verify_land(request, record_id):
    record = get_object_or_404(LandRecord, id=record_id)
    record.is_verified = True
    record.verified_by = request.user
    record.verified_at = timezone.now()
    record.save()
    messages.success(request, f'Land record verified for {record.user.username}.')
    return redirect('adminpanel:land_records')

@login_required
@admin_required
def storage_slots(request):
    slots = StorageSlot.objects.all().order_by('-created_at')
    paginator = Paginator(slots, 10)
    page_number = request.GET.get('page')
    slots_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/storage_slots.html', {'slots': slots_paginated})

@login_required
@admin_required
def add_storage_slot(request):
    if request.method == 'POST':
        form = StorageSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.created_by = request.user
            slot.save()
            messages.success(request, 'Storage slot added.')
            return redirect('adminpanel:storage_slots')
    else:
        form = StorageSlotForm()
    return render(request, 'adminpanel/add_storage_slot.html', {'form': form})

@login_required
@admin_required
def edit_storage_slot(request, slot_id):
    slot = get_object_or_404(StorageSlot, id=slot_id)
    if request.method == 'POST':
        form = StorageSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Storage slot updated.')
            return redirect('adminpanel:storage_slots')
    else:
        form = StorageSlotForm(instance=slot)
    return render(request, 'adminpanel/edit_storage_slot.html', {'form': form})

@login_required
@admin_required
def delete_storage_slot(request, slot_id):
    slot = get_object_or_404(StorageSlot, id=slot_id)
    slot.delete()
    messages.success(request, 'Storage slot deleted.')
    return redirect('adminpanel:storage_slots')

# Similar for CultivationSlot
@login_required
@admin_required
def cultivation_slots(request):
    slots = CultivationSlot.objects.all().order_by('-created_at')
    paginator = Paginator(slots, 10)
    page_number = request.GET.get('page')
    slots_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/cultivation_slots.html', {'slots': slots_paginated})

@login_required
@admin_required
def add_cultivation_slot(request):
    if request.method == 'POST':
        form = CultivationSlotForm(request.POST)
        if form.is_valid():
            slot = form.save(commit=False)
            slot.created_by = request.user
            slot.save()
            messages.success(request, 'Cultivation slot added.')
            return redirect('adminpanel:cultivation_slots')
    else:
        form = CultivationSlotForm()
    return render(request, 'adminpanel/add_cultivation_slot.html', {'form': form})

@login_required
@admin_required
def edit_cultivation_slot(request, slot_id):
    slot = get_object_or_404(CultivationSlot, id=slot_id)
    if request.method == 'POST':
        form = CultivationSlotForm(request.POST, instance=slot)
        if form.is_valid():
            form.save()
            messages.success(request, 'Cultivation slot updated.')
            return redirect('adminpanel:cultivation_slots')
    else:
        form = CultivationSlotForm(instance=slot)
    return render(request, 'adminpanel/edit_cultivation_slot.html', {'form': form})

@login_required
@admin_required
def delete_cultivation_slot(request, slot_id):
    slot = get_object_or_404(CultivationSlot, id=slot_id)
    slot.delete()
    messages.success(request, 'Cultivation slot deleted.')
    return redirect('adminpanel:cultivation_slots')

@login_required
@admin_required
def subsidy_schemes(request):
    schemes = SubsidyScheme.objects.all().order_by('-added_at')
    paginator = Paginator(schemes, 10)
    page_number = request.GET.get('page')
    schemes_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/subsidy_schemes.html', {'schemes': schemes_paginated})

@login_required
@admin_required
def add_subsidy_scheme(request):
    if request.method == 'POST':
        form = SubsidySchemeForm(request.POST)
        if form.is_valid():
            scheme = form.save(commit=False)
            scheme.added_by = request.user
            scheme.save()
            messages.success(request, 'Subsidy scheme added.')
            return redirect('adminpanel:subsidy_schemes')
    else:
        form = SubsidySchemeForm()
    return render(request, 'adminpanel/add_subsidy_scheme.html', {'form': form})

@login_required
@admin_required
def edit_subsidy_scheme(request, scheme_id):
    scheme = get_object_or_404(SubsidyScheme, id=scheme_id)
    if request.method == 'POST':
        form = SubsidySchemeForm(request.POST, instance=scheme)
        if form.is_valid():
            form.save()
            messages.success(request, 'Subsidy scheme updated.')
            return redirect('adminpanel:subsidy_schemes')
    else:
        form = SubsidySchemeForm(instance=scheme)
    return render(request, 'adminpanel/edit_subsidy_scheme.html', {'form': form})

@login_required
@admin_required
def delete_subsidy_scheme(request, scheme_id):
    scheme = get_object_or_404(SubsidyScheme, id=scheme_id)
    scheme.delete()
    messages.success(request, 'Subsidy scheme deleted.')
    return redirect('adminpanel:subsidy_schemes')

@login_required
@admin_required
def marketplace_monitoring(request):
    # Placeholder: Later integrate with marketplace models
    context = {'message': 'Marketplace monitoring coming soon. View product listings and transactions here.'}
    return render(request, 'adminpanel/marketplace_monitoring.html', context)


@login_required
@admin_required
def approve_cultivation_booking(request, booking_id):
    booking = get_object_or_404(CultivationBooking, id=booking_id)
    if booking.status != 'approved':
        booking.status = 'approved'
        booking.approved_by = request.user
        booking.save()
        messages.success(request, f'{booking.user.username}\'s booking has been approved.')
    else:
        messages.info(request, 'Booking already approved.')
    return redirect('adminpanel:cultivation_bookings')


@login_required
@admin_required
def reject_cultivation_booking(request, booking_id):
    booking = get_object_or_404(CultivationBooking, id=booking_id)
    if booking.status != 'rejected':
        booking.status = 'rejected'
        booking.save()
        messages.warning(request, f'{booking.user.username}\'s booking has been rejected.')
    return redirect('adminpanel:cultivation_bookings')


@login_required
@admin_required
def approve_storage_booking(request, booking_id):
    booking = get_object_or_404(StorageBooking, id=booking_id)
    if booking.status != 'approved':
        booking.status = 'approved'
        booking.approved_by = request.user
        booking.save()
        messages.success(request, f'{booking.user.username}\'s storage booking has been approved.')
    else:
        messages.info(request, 'Booking already approved.')
    return redirect('adminpanel:storage_bookings')


@login_required
@admin_required
def reject_storage_booking(request, booking_id):
    booking = get_object_or_404(StorageBooking, id=booking_id)
    if booking.status != 'rejected':
        booking.status = 'rejected'
        booking.save()
        messages.warning(request, f'{booking.user.username}\'s storage booking has been rejected.')
    return redirect('adminpanel:storage_bookings')

@login_required
@admin_required
def cultivation_bookings(request):
    bookings = CultivationBooking.objects.all().order_by('-booked_at')
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    bookings_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/cultivation_bookings.html', {'bookings': bookings_paginated})


@login_required
@admin_required
def storage_bookings(request):
    bookings = StorageBooking.objects.all().order_by('-booked_at')
    paginator = Paginator(bookings, 10)
    page_number = request.GET.get('page')
    bookings_paginated = paginator.get_page(page_number)
    return render(request, 'adminpanel/storage_bookings.html', {'bookings': bookings_paginated})
