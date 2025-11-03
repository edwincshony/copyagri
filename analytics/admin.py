from django.contrib import admin
from .models import AnalyticsData

@admin.register(AnalyticsData)
class AnalyticsDataAdmin(admin.ModelAdmin):
    list_display = ('date', 'total_users', 'total_revenue', 'total_bookings', 'total_listings')
    list_filter = ('date',)
    date_hierarchy = 'date'