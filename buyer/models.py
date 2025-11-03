from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import CustomUser
from django.utils import timezone
from farmer.models import ProductListing, Bid, StorageBooking  # Reuse


class Payment(models.Model):
    METHOD_CHOICES = [
        ('card', 'Card'),
        ('upi', 'UPI'),
        ('netbanking', 'Netbanking'),
        ('cod', 'Cash on Delivery'),
    ]
    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=METHOD_CHOICES, default='upi')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='initiated')
    reference = models.CharField(max_length=64, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    def mark_success(self):
        self.status = 'success'
        self.paid_at = timezone.now()
        self.save(update_fields=['status', 'paid_at'])

class Purchase(models.Model):
    TYPE_CHOICES = [
        ('regular', 'Regular'),
        ('bid', 'Bid'),
    ]
    buyer = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'buyer'})
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE)
    purchase_type = models.CharField(max_length=10, choices=TYPE_CHOICES, default='regular')
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_price = models.DecimalField(max_digits=12, decimal_places=2)
    purchase_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('pending_payment', 'Pending Payment'),
        ('payment_completed', 'Payment Completed'),
        ('cancelled', 'Cancelled')
    ], default='pending_payment')
    payment = models.OneToOneField(Payment, on_delete=models.SET_NULL, null=True, blank=True)
    related_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.buyer.username} - {self.listing.name}"

    @property
    def is_paid(self):
        return self.payment and self.payment.status == 'success'



