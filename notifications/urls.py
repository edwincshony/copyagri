from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('admin/', views.admin_notifications, name='admin_notifications'),
    path('admin/send/', views.send_notification, name='send_notification'),
    path('farmer/', views.farmer_notifications, name='farmer_notifications'),
    path('buyer/', views.buyer_notifications, name='buyer_notifications'),
    path('mark-read/<int:notif_id>/', views.mark_read, name='mark_read'),
    # path('weather/', views.generate_weather_alert, name='generate_weather'),  # Call via cron
]