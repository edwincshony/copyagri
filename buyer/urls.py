from django.urls import path
from . import views

app_name = 'buyer'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('marketplace-buy/', views.marketplace_buy, name='marketplace_buy'),
    path('product/<int:listing_id>/', views.product_detail, name='product_detail'),
    path('bid/<int:listing_id>/', views.place_bid, name='place_bid'),
    path('purchase/<int:listing_id>/', views.purchase_product, name='purchase_product'),
    path('my-purchases/', views.my_purchases, name='my_purchases'),
    path('storage-slots/', views.storage_slots, name='storage_slots'),
    path('book-storage/<int:slot_id>/', views.book_storage, name='book_storage'),
    path('subsidies/', views.subsidies, name='subsidies'),
    path('notifications/', views.notifications, name='notifications'),
    path('booking/<int:booking_id>/', views.booking_detail, name='booking_detail'),
    path('pay/<int:purchase_id>/', views.pay, name='pay'),
    path('success/<int:purchase_id>/', views.success, name='success'),

]