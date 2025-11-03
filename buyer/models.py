from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import CustomUser
from farmer.models import ProductListing, Bid, StorageBooking  # Reuse

class Purchase(models.Model):
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'buyer'})
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending_payment', 'Pending Payment'),
        ('payment_completed', 'Payment Completed'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered')
    ], default='pending_payment')
    payment_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.buyer.username} - {self.listing.name}"

    def save(self, *args, **kwargs):
        self.total_price = self.quantity * self.listing.price
        super().save(*args, **kwargs)