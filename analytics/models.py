from django.db import models
from django.utils import timezone

class AnalyticsData(models.Model):
    date = models.DateField(default=timezone.now)
    total_users = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_bookings = models.IntegerField(default=0)
    total_listings = models.IntegerField(default=0)
    
    # Additional metrics
    farmer_count = models.IntegerField(default=0)
    buyer_count = models.IntegerField(default=0)
    storage_bookings = models.IntegerField(default=0)
    cultivation_bookings = models.IntegerField(default=0)
    active_listings = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-date']
        verbose_name_plural = 'Analytics Data'
        
    def __str__(self):
        return f'Analytics for {self.date}'