from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from utils.pagination import paginate_queryset  # make sure path is correct
from django.core.paginator import Paginator
from django.db.models import Count, Sum
from django.utils import timezone
from django.db.models import Avg
from django.db import connection
from accounts.models import CustomUser
from .models import Report, WeatherAlert
from .forms import ReportGenerationForm
from farmer.models import CultivationBooking, StorageBooking
from buyer.models import Purchase
from adminpanel.models import StorageSlot, CultivationSlot

def admin_required(view_func):
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
@admin_required
def admin_reports(request):
    reports = Report.objects.all().order_by('-generated_at')
    page_obj, slots = paginate_queryset(request, reports)
    return render(request, 'analytics/admin_reports.html', {'reports': reports ,'page_obj': page_obj})

@login_required
@admin_required
def generate_report(request):
    if request.method == 'POST':
        form = ReportGenerationForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.generated_by = request.user
            report.save()
            # Generate summary data
            start = report.start_date
            end = report.end_date
            if report.report_type == 'user_growth':
                data = CustomUser.objects.filter(date_joined__range=[start, end]).aggregate(total=Count('id'))
                report.data_summary = f"New users: {data['total']}"
            elif report.report_type == 'booking_stats':
                data = CultivationBooking.objects.filter(booked_at__range=[start, end]).aggregate(total_bookings=Count('id'), total_revenue=Sum('total_price'))
                report.data_summary = f"Bookings: {data['total_bookings']}, Revenue: ₹{data['total_revenue'] or 0}"
            elif report.report_type == 'marketplace_sales':
                data = Purchase.objects.filter(purchase_date__range=[start, end]).aggregate(total_sales=Count('id'), total_revenue=Sum('total_price'))
                report.data_summary = f"Sales: {data['total_sales']}, Revenue: ₹{data['total_revenue'] or 0}"
            elif report.report_type == 'storage_usage':
                data = StorageSlot.objects.aggregate(avg_usage=Avg('available_slots'))
                report.data_summary = f"Avg available slots: {data['avg_usage']}"
            report.save()
            messages.success(request, 'Report generated successfully.')
            return redirect('analytics:admin_reports')
    else:
        form = ReportGenerationForm()
    return render(request, 'analytics/generate_report.html', {'form': form})

@login_required
@admin_required
def report_detail(request, report_id):
    report = get_object_or_404(Report, id=report_id)
    # Query for chart data (e.g., bookings per day)
    if report.report_type == 'booking_stats':
        cursor = connection.cursor()
        cursor.execute("""
            SELECT DATE(booked_at) as date, COUNT(*) as count
            FROM farmer_cultivationbooking
            WHERE booked_at BETWEEN %s AND %s
            GROUP BY DATE(booked_at)
            ORDER BY date
        """, [report.start_date, report.end_date])
        chart_data = cursor.fetchall()  # [(date, count), ...]
    else:
        chart_data = []
    return render(request, 'analytics/report_detail.html', {'report': report, 'chart_data': chart_data})

@login_required
@user_required
def user_guidance(request):
    alerts = WeatherAlert.objects.filter(user=request.user).order_by('-created_at')
    paginator = Paginator(alerts, 10)
    page_number = request.GET.get('page')
    alerts_paginated = paginator.get_page(page_number)
    # Placeholder crop prediction: Simple based on user land area (from land records)
    prediction = "Expected yield: High (based on verified land records)."
    return render(request, 'analytics/user_guidance.html', {'alerts': alerts_paginated, 'prediction': prediction})

@login_required
@user_required
def weather_alerts(request):
    # Simulated alerts based on location
    user_location = request.user.address.split(',')[-1].strip()  # e.g., state
    # Placeholder: In real, fetch from API; here static
    alerts = WeatherAlert.objects.filter(location__icontains=user_location)[:5]
    return render(request, 'analytics/weather_alerts.html', {'alerts': alerts})

@login_required
@user_required
def crop_predictions(request):
    # Placeholder AI: Simple calc, e.g., yield = area * avg_yield
    # Fetch from land records (adminpanel)
    from adminpanel.models import LandRecord
    total_area = LandRecord.objects.filter(user=request.user, is_verified=True).aggregate(total=Sum('area_acres'))['total'] or 0
    predicted_yield = total_area * 2.5  # Tons/acre avg
    return render(request, 'analytics/crop_predictions.html', {'predicted_yield': predicted_yield, 'total_area': total_area})