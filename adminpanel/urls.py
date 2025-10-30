from django.urls import path
from . import views

app_name = 'adminpanel'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.user_management, name='user_management'),
    path('users/approve/<int:user_id>/', views.approve_user, name='approve_user'),
    path('users/reject/<int:user_id>/', views.reject_user, name='reject_user'),
    path('documents/', views.document_verification, name='document_verification'),
    path('land-records/', views.land_records, name='land_records'),
    path('land-records/verify/<int:record_id>/', views.verify_land, name='verify_land'),
    path('storage-slots/', views.storage_slots, name='storage_slots'),
    path('storage-slots/add/', views.add_storage_slot, name='add_storage_slot'),
    path('storage-slots/edit/<int:slot_id>/', views.edit_storage_slot, name='edit_storage_slot'),
    path('storage-slots/delete/<int:slot_id>/', views.delete_storage_slot, name='delete_storage_slot'),
    path('cultivation-slots/', views.cultivation_slots, name='cultivation_slots'),
    path('cultivation-slots/add/', views.add_cultivation_slot, name='add_cultivation_slot'),
    path('cultivation-slots/edit/<int:slot_id>/', views.edit_cultivation_slot, name='edit_cultivation_slot'),
    path('cultivation-slots/delete/<int:slot_id>/', views.delete_cultivation_slot, name='delete_cultivation_slot'),
    path('subsidies/', views.subsidy_schemes, name='subsidy_schemes'),
    path('subsidies/add/', views.add_subsidy_scheme, name='add_subsidy_scheme'),
    path('subsidies/edit/<int:scheme_id>/', views.edit_subsidy_scheme, name='edit_subsidy_scheme'),
    path('subsidies/delete/<int:scheme_id>/', views.delete_subsidy_scheme, name='delete_subsidy_scheme'),
    path('marketplace/', views.marketplace_monitoring, name='marketplace_monitoring'),
]