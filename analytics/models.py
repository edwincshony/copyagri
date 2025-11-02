from datetime import datetime, time
from django.utils import timezone
from accounts.models import CustomUser
from django.db import models

class Report(models.Model):
    REPORT_TYPES = [
        ('overview', 'Overall Summary'),
        ('bookings', 'Cultivation & Storage Bookings'),
        ('revenue', 'Total Revenue'),
        ('market', 'Marketplace Performance'),
        ('users', 'User Statistics'),
    ]

    title = models.CharField(max_length=120)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(
        'accounts.CustomUser',
        on_delete=models.SET_NULL,
        null=True,
        limit_choices_to={'role': 'admin'},
        related_name='generated_reports'
    )
    start_date = models.DateField()
    end_date = models.DateField()
    data_summary = models.JSONField(default=dict, blank=True)
    chart_data = models.JSONField(default=dict, blank=True)
    generated_at = models.DateTimeField(auto_now_add=True)
    is_auto_generated = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.title} - {self.report_type}"

    from datetime import datetime, time
    from django.utils import timezone

    def update_data(self):
        """Auto-aggregates core metrics for selected report types."""
        from datetime import datetime, time
        from django.utils import timezone
        from django.db.models import Count, Sum, Q
        from farmer.models import CultivationBooking, StorageBooking, ProductListing
        from buyer.models import Purchase, Bid
        from accounts.models import CustomUser

        # --- ✅ Convert date fields into timezone-aware datetimes ---
        def make_aware_date(d):
            if isinstance(d, datetime):
                return timezone.make_aware(d) if timezone.is_naive(d) else d
            dt = datetime.combine(d, time.min)
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            return dt

        start = make_aware_date(self.start_date)
        end = make_aware_date(self.end_date)

        # === REPORT LOGIC ===
        if self.report_type == 'overview':
            users = CustomUser.objects.aggregate(
                total=Count('id'),
                farmers=Count('id', filter=Q(role='farmer')),
                buyers=Count('id', filter=Q(role='buyer')),
            )

            bookings = (CultivationBooking.objects.filter(booked_at__range=[start, end]).count() +
                        StorageBooking.objects.filter(booked_at__range=[start, end]).count())

            revenue = (
                (CultivationBooking.objects.filter(booked_at__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
                + (StorageBooking.objects.filter(booked_at__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
                + (Purchase.objects.filter(purchase_date__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
            )

            self.data_summary = {'users': users, 'bookings': bookings, 'revenue': revenue}
            self.chart_data = {
                'labels': ['Farmers', 'Buyers', 'Bookings', 'Revenue'],
                'data': [users['farmers'], users['buyers'], bookings, revenue]
            }

        elif self.report_type == 'bookings':
            cult = CultivationBooking.objects.filter(booked_at__range=[start, end]).count()
            stor = StorageBooking.objects.filter(booked_at__range=[start, end]).count()
            self.data_summary = {'cultivation_bookings': cult, 'storage_bookings': stor, 'total': cult + stor}
            self.chart_data = {'labels': ['Cultivation', 'Storage'], 'data': [cult, stor]}

        elif self.report_type == 'revenue':
            total_revenue = (
                (CultivationBooking.objects.filter(booked_at__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
                + (StorageBooking.objects.filter(booked_at__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
                + (Purchase.objects.filter(purchase_date__range=[start, end]).aggregate(Sum('total_price'))['total_price__sum'] or 0)
            )
            self.data_summary = {'total_revenue': total_revenue}
            self.chart_data = {'labels': ['Revenue'], 'data': [total_revenue]}

        elif self.report_type == 'market':
            total_sales = Purchase.objects.filter(purchase_date__range=[start, end]).count()
            total_bids = Bid.objects.filter(placed_at__range=[start, end]).count()
            total_products = ProductListing.objects.filter(listed_at__range=[start, end]).count()
            self.data_summary = {
                'products_listed': total_products,
                'bids_placed': total_bids,
                'sales_made': total_sales
            }
            self.chart_data = {'labels': ['Products', 'Bids', 'Sales'], 'data': [total_products, total_bids, total_sales]}

        elif self.report_type == 'users':
            users = CustomUser.objects.filter(date_joined__range=[start, end])
            farmers = users.filter(role='farmer').count()
            buyers = users.filter(role='buyer').count()
            self.data_summary = {'farmers': farmers, 'buyers': buyers, 'total_new_users': farmers + buyers}
            self.chart_data = {'labels': ['Farmers', 'Buyers'], 'data': [farmers, buyers]}

        self.save()





class WeatherAlert(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role__in': ['farmer', 'buyer']})
    location = models.CharField(max_length=200)
    alert_type = models.CharField(max_length=50)
    description = models.TextField()
    date = models.DateField(default=timezone.now)
    severity = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.alert_type}"