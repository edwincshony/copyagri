from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import CustomUser
from adminpanel.models import StorageSlot, CultivationSlot, SubsidyScheme

class CultivationBooking(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    slot = models.ForeignKey(CultivationSlot, on_delete=models.CASCADE,related_name='bookings')
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
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='listings/', blank=True)
    bid_start_time = models.DateTimeField(default=timezone.now)
    bid_end_time = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def is_bidding_open(self):
        now = timezone.now()
        return self.bid_start_time <= now < (self.bid_end_time or now)

    def has_bidding_ended(self):
        now = timezone.now()
        return self.bid_end_time and now >= self.bid_end_time

    def highest_bid(self):
        return self.bids.order_by('-amount').first() if hasattr(self, 'bids') else None

    def winning_bid(self):
        now = timezone.now()
        if self.has_bidding_ended():
            winning = self.highest_bid()
            if winning:
                # Allow 6 hours after bid end time for payment
                payment_deadline = self.bid_end_time + timezone.timedelta(hours=6)
                if winning.payment_status == 'completed' or now <= payment_deadline:
                    return winning
        return None
        
    def is_available_for_regular_purchase(self):
        """Check if the product can be purchased directly"""
        now = timezone.now()
        available_qty = self.available_quantity()
        
        # First check if there's any stock available
        if not self.is_active or available_qty <= 0:
            return False
            
        # If there's no bidding or bidding hasn't started yet
        if not self.bid_end_time or now < self.bid_start_time:
            return True
            
        # During active bidding, the product is not available for direct purchase
        if self.is_bidding_open():
            return False
            
        # If bidding has ended
        if self.has_bidding_ended():
            winning_bid = self.highest_bid()
            if winning_bid:
                # Check if within 6-hour payment window for winner
                payment_deadline = self.bid_end_time + timezone.timedelta(hours=6)
                if now <= payment_deadline:
                    return False  # Not available during winner's payment window
                    
                # After payment window and winning bid payment completed,
                # the remaining stock (if any) becomes available for direct purchase
                if winning_bid.payment_status == 'completed':
                    return available_qty > 0
            
            # If no winning bid or payment window expired without payment,
            # the product is available for direct purchase
            return True
            
        return True

    def available_quantity(self):
        from buyer.models import Purchase
        # Calculate quantity sold through completed regular purchases
        regular_sales = Purchase.objects.filter(
            listing=self,
            payment_completed=True
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        # Calculate quantity sold through completed bid sales
        bid_sales = self.bids.filter(
            is_accepted=True,
            payment_status='completed'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
        
        return self.quantity - (regular_sales + bid_sales)

    def bid_revenue(self):
        """Only count revenue from completed payments"""
        bid = self.winning_bid()
        if bid and bid.payment_status == 'completed':
            return bid.total_amount
        return 0
        
    def regular_sales_revenue(self):
        """Only count revenue from completed payments"""
        from buyer.models import Purchase
        purchases = Purchase.objects.filter(
            listing=self,
            payment_completed=True
        )
        return purchases.aggregate(total=models.Sum('total_price'))['total'] or 0
        
    def total_revenue(self):
        return self.bid_revenue() + self.regular_sales_revenue()
        
    def pending_revenue(self):
        """Calculate expected revenue from pending payments"""
        from buyer.models import Purchase
        # Pending regular purchases
        pending_purchases = Purchase.objects.filter(
            listing=self,
            payment_completed=False
        ).aggregate(total=models.Sum('total_price'))['total'] or 0
        
        # Pending bid payments
        bid = self.winning_bid()
        pending_bid = bid.total_amount if bid and bid.payment_status == 'pending' else 0
        
        return pending_purchases + pending_bid

    def __str__(self):
        return f"{self.user.username} - {self.name}"





class Bid(models.Model):
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'buyer'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    placed_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    payment_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Payment'),
        ('completed', 'Payment Completed')
    ], default='pending')
    
    @property
    def total_amount(self):
        return self.amount * self.quantity

    def __str__(self):
        return f"Bid on {self.listing.name} - ₹{self.amount}"