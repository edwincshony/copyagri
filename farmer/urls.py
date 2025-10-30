from django.urls import path
from . import views

app_name = 'farmer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('land-records/', views.land_records, name='land_records'),
    path('upload-land-record/', views.upload_land_record, name='upload_land_record'),
    path('upload-document/', views.upload_document, name='upload_document'),
    path('cultivation-slots/', views.cultivation_slots, name='cultivation_slots'),
    path('book-cultivation/<int:slot_id>/', views.book_cultivation, name='book_cultivation'),
    path('storage-slots/', views.storage_slots, name='storage_slots'),
    path('book-storage/<int:slot_id>/', views.book_storage, name='book_storage'),
    path('marketplace-sell/', views.marketplace_sell, name='marketplace_sell'),
    path('create-listing/', views.create_listing, name='create_listing'),
    path('edit-listing/<int:listing_id>/', views.edit_listing, name='edit_listing'),
    path('delete-listing/<int:listing_id>/', views.delete_listing, name='delete_listing'),
    path('subsidies/', views.subsidies, name='subsidies'),
    path('analytics/', views.analytics_guidance, name='analytics'),
    path('notifications/', views.notifications, name='notifications'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
]