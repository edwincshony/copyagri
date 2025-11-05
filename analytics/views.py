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
from django.db.models import Sum, F
from farmer.models import Bid  # you forgot this import


def is_admin(user):
    return user.is_superuser

@user_passes_test(is_admin)
def analytics_dashboard(request):
    return render(request, 'analytics/dashboard.html')

@user_passes_test(is_admin)
def get_analytics_data(request):
    # Force regenerate analytics data to get fresh numbers
    latest_data = generate_analytics_data()
    
    # Calculate current revenue components
    cultivation_revenue = CultivationBooking.objects.filter(
        status__in=['approved', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    storage_revenue = StorageBooking.objects.filter(
        status__in=['approved', 'completed']
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    purchase_revenue = Purchase.objects.filter(
        status='payment_completed',
        purchase_type='regular'
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    bid_revenue = Bid.objects.filter(
        is_accepted=True,
        payment_status='completed'
    ).aggregate(total=Sum(F('amount') * F('quantity')))['total'] or 0
    
    total_revenue = float(cultivation_revenue) + float(storage_revenue) + float(purchase_revenue) + float(bid_revenue or 0)
    
    data = {
        'total_users': CustomUser.objects.filter(is_superuser=False, is_approved=True).count(),
        'total_revenue': total_revenue,
        'total_bookings': latest_data.total_bookings,
        'total_listings': latest_data.total_listings,
        'farmer_count': latest_data.farmer_count,
        'buyer_count': latest_data.buyer_count,
        'storage_bookings': latest_data.storage_bookings,
        'cultivation_bookings': latest_data.cultivation_bookings,
        'active_listings': latest_data.active_listings,
        'revenue_breakdown': {
            'purchases': float(purchase_revenue),
            'bids': float(bid_revenue or 0),
            'cultivation': float(cultivation_revenue),
            'storage': float(storage_revenue)
        }
    }
    
    return JsonResponse(data)

@user_passes_test(is_admin)
def get_filtered_data(request):
    period = request.GET.get('period', '30')  # Default to last 30 days
    days = int(period)
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days)
    
    # Calculate revenue from cultivation bookings
    cultivation_revenue = CultivationBooking.objects.filter(
        status__in=['approved', 'completed'],
        booked_at__date__range=[start_date, end_date]
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Calculate revenue from storage bookings
    storage_revenue = StorageBooking.objects.filter(
        status__in=['approved', 'completed'],
        booked_at__date__range=[start_date, end_date]
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Calculate revenue from regular purchases (excluding bids)
    purchase_revenue = Purchase.objects.filter(
        status='payment_completed',
        purchase_type='regular',
        purchase_date__date__range=[start_date, end_date]
    ).aggregate(total=Sum('total_price'))['total'] or 0
    
    # Calculate revenue from bids
    bid_revenue = Bid.objects.filter(
        is_accepted=True,
        payment_status='completed',
        created_at__date__range=[start_date, end_date]
    ).aggregate(total=Sum(F('amount') * F('quantity')))['total'] or 0
    
    # Calculate total revenue
    purchase_revenue_total = float(purchase_revenue + (bid_revenue or 0))
    total_revenue = purchase_revenue_total + float(cultivation_revenue) + float(storage_revenue)
    
    data = AnalyticsData.objects.filter(
        date__range=[start_date, end_date]
    ).order_by('date')
    
    response_data = {
        'labels': [item.date.strftime('%Y-%m-%d') for item in data],
        'users': [item.total_users for item in data],
        'revenue': [float(item.total_revenue) for item in data],
        'bookings': [item.total_bookings for item in data],
        'listings': [item.total_listings for item in data],
        'total_revenue': float(total_revenue),
        'revenue_breakdown': {
            'purchases': float(purchase_revenue),
            'bids': float(bid_revenue or 0),
            'cultivation': float(cultivation_revenue),
            'storage': float(storage_revenue)
        }
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
from django.db import models
from django.db.models import Sum, F
from buyer.models import Purchase
from farmer.models import CultivationBooking, StorageBooking, Bid

def calculate_total_revenue():
    # Get cultivation revenue
    cultivation_rev = CultivationBooking.objects.filter(
        status__in=["approved", "completed"]
    ).aggregate(total=Sum("total_price"))["total"] or 0

    # Get storage revenue
    storage_rev = StorageBooking.objects.filter(
        status__in=["approved", "completed"]
    ).aggregate(total=Sum("total_price"))["total"] or 0

    # Get regular purchase revenue (exclude bid type purchases to avoid duplicate count)
    purchase_rev = Purchase.objects.filter(
        status="payment_completed",
        purchase_type="regular"
    ).aggregate(total=Sum("total_price"))["total"] or 0

    # Get bid revenue
    bid_rev = Bid.objects.filter(
        is_accepted=True,
        payment_status="completed"
    ).aggregate(total=Sum(F("amount") * F("quantity")))["total"] or 0

    return float(cultivation_rev + storage_rev + purchase_rev + bid_rev)