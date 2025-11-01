from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from utils.pagination import paginate_queryset  # make sure path is correct
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Notification
from .forms import CustomNotificationForm
from accounts.models import CustomUser

def admin_required(view_func):
    # Reuse from analytics/adminpanel
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.warning(request, 'No permission to access this page.')
            return redirect('accounts:home')
        return view_func(request, *args, **kwargs)
    return wrapper

def user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role not in ['farmer', 'buyer']:
            messages.warning(request, 'No permission to access this page.')
            return redirect('accounts:home')
        return view_func(request, *args, **kwargs)
    return wrapper

@login_required
def dashboard(request):
    notifications = Notification.objects.filter(user=request.user, is_read=False).count()
    return render(request, 'notifications/dashboard.html', {'unread_count': notifications})

@login_required
@admin_required
def admin_notifications(request):
    # Get all notifications
    all_notifications = Notification.objects.all().order_by('-created_at')

    # Use global pagination utility
    page_obj, notifications = paginate_queryset(request, all_notifications)

    return render(request, 'notifications/admin_notifications.html', {
        'notifications': notifications,  # paginated list for the table
        'page_obj': page_obj              # for rendering pagination controls
    })


@login_required
@user_required
def farmer_notifications(request):
    # Farmer-specific, e.g., filter by type
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    page_obj, notifs = paginate_queryset(request, notifs)
    return render(request, 'notifications/farmer_notifications.html', {'notifications': notifs , 'page_obj': page_obj})

@login_required
@user_required
def buyer_notifications(request):
    # Similar to farmer
    notifs = Notification.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(notifs, 10)
    page_number = request.GET.get('page')
    notifs_paginated = paginator.get_page(page_number)
    return render(request, 'notifications/buyer_notifications.html', {'notifications': notifs_paginated})

@login_required
def mark_read(request, notif_id):
    notif = get_object_or_404(Notification, id=notif_id, user=request.user)
    notif.is_read = True
    notif.save()
    messages.success(request, 'Notification marked as read.')

    # Redirect based on user role
    user = request.user
    if hasattr(user, 'role'):  # assuming you have a 'role' field on the user model
        if user.role == 'farmer':
            return redirect('notifications:farmer_notifications')
        elif user.role == 'admin':
            return redirect('notifications:admin_notifications')
        elif user.role == 'buyer':
            return redirect('notifications:buyer_notifications')

    # Default fallback
    return redirect('notifications:dashboard')


@login_required
@admin_required
def send_notification(request):
    if request.method == 'POST':
        form = CustomNotificationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notification sent.')
            return redirect('notifications:admin_notifications')
    else:
        form = CustomNotificationForm()
    return render(request, 'notifications/send_notification.html', {'form': form})

# Placeholder for auto-weather/scheme
@login_required
@user_required
def generate_weather_alert(request):
    # Cron-like: Create alert based on location
    from analytics.models import WeatherAlert  # Reuse or create
    # Simulated
    alert = WeatherAlert.objects.create(
        user=request.user,
        location=request.user.address,
        alert_type='Rain Forecast',
        description='Heavy rain expected in your area.',
        date=timezone.now().date(),
        severity='medium'
    )
    Notification.objects.create(
        user=request.user,
        title='Weather Alert',
        message=alert.description,
        notification_type='weather'
    )
    messages.success(request, 'Weather alert generated.')
    return redirect('notifications:dashboard')