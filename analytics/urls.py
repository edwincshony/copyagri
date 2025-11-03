from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    path('', views.analytics_dashboard, name='dashboard'),
    path('api/data/', views.get_analytics_data, name='get_data'),
    path('api/filter-data/', views.get_filtered_data, name='filter_data'),
]