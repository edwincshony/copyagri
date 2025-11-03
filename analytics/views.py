from django.shortcuts import render
from django.db.models import Sum
from buyer.models import Purchase
from django.http import JsonResponse
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Count
from django.utils import timezone
from datetime import datetime, timedelta
from .models import AnalyticsData
from accounts.models import CustomUser
from farmer.models import ProductListing
from farmer.models import CultivationBooking, StorageBooking

def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def analytics_dashboard(request):
    return render(request, 'analytics/dashboard.html')

@user_passes_test(is_admin)
def get_analytics_data(request):
    # Get the latest analytics data
    latest_data = AnalyticsData.objects.first()
    
    if not latest_data:
        # Generate new data if none exists
        latest_data = generate_analytics_data()
    
    data = {
        'total_users' : CustomUser.objects.filter(is_superuser=False).count(),
        'total_revenue': float(latest_data.total_revenue),
        'total_bookings': latest_data.total_bookings,
        'total_listings': latest_data.total_listings,
        'farmer_count': latest_data.farmer_count,
        'buyer_count': latest_data.buyer_count,
        'storage_bookings': latest_data.storage_bookings,
        'cultivation_bookings': latest_data.cultivation_bookings,
        'active_listings': latest_data.active_listings,
    }
    
    return JsonResponse(data)

@user_passes_test(is_admin)
def get_filtered_data(request):
    period = request.GET.get('period', '30')  # Default to last 30 days
    days = int(period)
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    data = AnalyticsData.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    response_data = {
        'labels': [item.date.strftime('%Y-%m-%d') for item in data],
        'users': [item.total_users for item in data],
        'revenue': [float(item.total_revenue) for item in data],
        'bookings': [item.total_bookings for item in data],
        'listings': [item.total_listings for item in data],
    }
    
    return JsonResponse(response_data)

def generate_analytics_data():
    """Generate analytics data for the current day"""
    today = timezone.now().date()
    
    # Get counts
    total_users = CustomUser.objects.count()
    farmer_count = CustomUser.objects.filter(role='farmer').count()
    buyer_count = CustomUser.objects.filter(role='buyer').count()
    
    # Get bookings
    storage_bookings = StorageBooking.objects.count()
    cultivation_bookings = CultivationBooking.objects.count()
    total_bookings = storage_bookings + cultivation_bookings
    
    # Get listings
    total_listings = ProductListing.objects.count()
    active_listings = ProductListing.objects.filter(is_active=True).count()
    
    # Calculate total revenue (you'll need to adjust this based on your business logic)
    total_revenue = calculate_total_revenue()
    
    # Create or update analytics data
    analytics_data, created = AnalyticsData.objects.get_or_create(
        date=today,
        defaults={
            'total_users': total_users,
            'total_revenue': total_revenue,
            'total_bookings': total_bookings,
            'total_listings': total_listings,
            'farmer_count': farmer_count,
            'buyer_count': buyer_count,
            'storage_bookings': storage_bookings,
            'cultivation_bookings': cultivation_bookings,
            'active_listings': active_listings,
        }
    )
    
    if not created:
        # Update existing record
        analytics_data.total_users = total_users
        analytics_data.total_revenue = total_revenue
        analytics_data.total_bookings = total_bookings
        analytics_data.total_listings = total_listings
        analytics_data.farmer_count = farmer_count
        analytics_data.buyer_count = buyer_count
        analytics_data.storage_bookings = storage_bookings
        analytics_data.cultivation_bookings = cultivation_bookings
        analytics_data.active_listings = active_listings
        analytics_data.save()
    
    return analytics_data

def calculate_total_revenue():
    """Calculate total revenue from all confirmed or paid purchases."""
    total = Purchase.objects.filter(status__in=["confirmed", "paid"]).aggregate(
        total=Sum("total_price")
    )["total"] or 0
    return float(total)