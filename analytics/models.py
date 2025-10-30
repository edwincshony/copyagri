from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from farmer.models import CultivationBooking, StorageBooking, ProductListing
from buyer.models import Purchase
from adminpanel.models import StorageSlot, CultivationSlot

class Report(models.Model):
    REPORT_TYPES = [
        ('user_growth', 'User Growth'),
        ('booking_stats', 'Booking Statistics'),
        ('marketplace_sales', 'Marketplace Sales'),
        ('storage_usage', 'Storage Usage'),
    ]
    title = models.CharField(max_length=100)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPES)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    start_date = models.DateField()
    end_date = models.DateField()
    data_summary = models.TextField(blank=True)  # JSON-like summary
    generated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.report_type}"

class WeatherAlert(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role__in': ['farmer', 'buyer']})
    location = models.CharField(max_length=200)
    alert_type = models.CharField(max_length=50)  # e.g., 'rain', 'drought'
    description = models.TextField()
    date = models.DateField()
    severity = models.CharField(max_length=20, choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='low')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.alert_type} on {self.date}"