from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('admin/reports/', views.admin_reports, name='admin_reports'),
    path('admin/generate/', views.generate_report, name='generate_report'),
    path('admin/report/<int:report_id>/', views.report_detail, name='report_detail'),
    path('user/guidance/', views.user_guidance, name='user_guidance'),
    path('user/weather/', views.weather_alerts, name='weather_alerts'),
    path('user/predictions/', views.crop_predictions, name='crop_predictions'),
]