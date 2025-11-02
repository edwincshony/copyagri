from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import ReportForm
from django.core.paginator import Paginator
from django.db.models import Count, Sum, Avg
from datetime import timedelta
from django.utils import timezone
from django.db import connection
from accounts.models import CustomUser
from .models import Report, WeatherAlert
from farmer.models import CultivationBooking, StorageBooking, ProductListing
from buyer.models import Purchase
from adminpanel.models import StorageSlot, CultivationSlot, SubsidyScheme, LandRecord

def admin_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or request.user.role != 'admin':
            messages.warning(request, 'Admins only.')
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
@admin_required
def dashboard(request):
    end = timezone.now().date()
    start = end - timedelta(days=30)
    report, _ = Report.objects.get_or_create(
        title='Last 30-Day Overview',
        report_type='overview',
        start_date=start, end_date=end,
        defaults={'generated_by': request.user, 'is_auto_generated': True}
    )
    report.update_data()
    return render(request, 'analytics/dashboard.html', {'report': report})

@login_required
@admin_required
def generate_report(request):
    if request.method == 'POST':
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            report.save()
            report.update_data()
            messages.success(request, "Report generated successfully.")
            return redirect('analytics:dashboard')
    else:
        form = ReportForm()
    return render(request, 'analytics/generate_report.html', {'form': form})

@login_required
@admin_required
def report_detail(request, pk):
    report = get_object_or_404(Report, pk=pk)
    return render(request, 'analytics/report_detail.html', {'report': report})


@login_required
def report_list(request):
    """Show all generated reports."""
    reports = Report.objects.all().order_by('-generated_at')
    return render(request, 'analytics/report_list.html', {'reports': reports})

@login_required
@user_required
def user_guidance(request):
    alerts = WeatherAlert.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(alerts, 10)
    page_number = request.GET.get('page')
    alerts_paginated = paginator.get_page(page_number)
    # Auto-compute personal prediction based on bookings/land
    user_bookings = CultivationBooking.objects.filter(user=request.user).aggregate(total_area=Sum('booked_area_acres'))
    total_area = user_bookings['total_area'] or LandRecord.objects.filter(user=request.user).aggregate(total=Sum('area_acres'))['total'] or 0
    prediction = f"Expected yield: {total_area * 2.5:.2f} tons (based on {total_area:.2f} acres from bookings/land)."
    return render(request, 'analytics/user_guidance.html', {'alerts': alerts_paginated, 'prediction': prediction})

@login_required
@user_required
def weather_alerts(request):
    user_location = request.user.address  # Geo-based
    # Simulated auto-generation
    if not WeatherAlert.objects.filter(user=request.user, date=timezone.now().date()).exists():
        WeatherAlert.objects.create(
            user=request.user,
            location=user_location,
            alert_type='Daily Forecast',
            description=f'Current conditions in {user_location}: Sunny with 25°C. Optimal for harvesting.',
            severity='low'
        )
    alerts = WeatherAlert.objects.filter(user=request.user).order_by('-date')
    return render(request, 'analytics/weather_alerts.html', {'alerts': alerts})

@login_required
@user_required
def crop_predictions(request):
    # Enhanced with user data
    from adminpanel.models import LandRecord
    total_area = LandRecord.objects.filter(user=request.user, is_verified=True).aggregate(total=Sum('area_acres'))['total'] or 0
    # Simulated trend based on past bookings
    past_bookings = CultivationBooking.objects.filter(user=request.user, booked_at__lt=timezone.now()).count()
    predicted_yield = total_area * (2.5 + (past_bookings * 0.1))  # Adjust based on history
    trend_data = [{'month': 'Current', 'yield': predicted_yield}]  # Expand with queries
    return render(request, 'analytics/crop_predictions.html', {'predicted_yield': predicted_yield, 'total_area': total_area, 'trend_data': trend_data})