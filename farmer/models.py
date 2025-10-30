from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import CustomUser
from adminpanel.models import StorageSlot, CultivationSlot, SubsidyScheme

class CultivationBooking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    slot = models.ForeignKey(CultivationSlot, on_delete=models.CASCADE)
    booked_area_acres = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0.01)])
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='pending')
    guidance_notes = models.TextField(blank=True)  # Reminders
    booked_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'admin'}, related_name='approved_cult_bookings')

    def __str__(self):
        return f"{self.user.username} - {self.slot.name}"

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(start_date__lte=models.F('end_date')), name='cultivation_valid_dates'),
        ]

class StorageBooking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    slot = models.ForeignKey(StorageSlot, on_delete=models.CASCADE)
    booked_slots = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    start_date = models.DateField()
    end_date = models.DateField()
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('completed', 'Completed')], default='pending')
    booked_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'admin'}, related_name='approved_storage_bookings')

    def __str__(self):
        return f"{self.user.username} - {self.slot.name}"

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(start_date__lte=models.F('end_date')), name='storage_valid_dates'),
        ]

class ProductListing(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    name = models.CharField(max_length=100)
    description = models.TextField()
    quantity = models.PositiveIntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    crop_type = models.CharField(max_length=50)
    location = models.CharField(max_length=200)  # Geo-suggested
    image = models.ImageField(upload_to='listings/', blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.name}"

class Bid(models.Model):
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'buyer'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    placed_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)

    def __str__(self):
        return f"Bid on {self.listing.name} - ₹{self.amount}"