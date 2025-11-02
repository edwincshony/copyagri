from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),  # New auto-entry
    path('generate/', views.generate_report, name='generate_report'),
    path('report/<int:pk>/', views.report_detail, name='report_detail'),
    path('reports/', views.report_list, name='report_list'),  # 👈 New route
    path('user/guidance/', views.user_guidance, name='user_guidance'),
    path('user/weather/', views.weather_alerts, name='weather_alerts'),
    path('user/predictions/', views.crop_predictions, name='crop_predictions'),
]