from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import CustomUser
from adminpanel.models import StorageSlot, CultivationSlot, SubsidyScheme
# farmer/models.py (UPDATED core methods)


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



from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from accounts.models import CustomUser

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from accounts.models import CustomUser

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
        return self.bid_start_time <= now and (not self.bid_end_time or now <= self.bid_end_time)
    
    def has_bidding_ended(self):
        now = timezone.now()
        return bool(self.bid_end_time and now > self.bid_end_time)
    
    def payment_deadline(self):
        if not self.bid_end_time:
            return None
        return self.bid_end_time + timezone.timedelta(hours=6)
    
    def is_within_bid_payment_window(self):
        dl = self.payment_deadline()
        return bool(dl and timezone.now() <= dl)
    
    @property
    def highest_bid(self):
        return self.bids.order_by('-amount').first()
    
    @property
    def winning_bid_candidate(self):
        """Returns highest bid if bidding ended"""
        if not self.has_bidding_ended():
            return None
        return self.highest_bid
    
    @property
    def winning_bid(self):
        """Show winner when either paid or still within 6-hour grace"""
        candidate = self.winning_bid_candidate
        if not candidate:
            return None
        if candidate.payment_status == 'completed':
            return candidate
        if self.is_within_bid_payment_window():
            return candidate
        return None
    
    @property
    def locked_bid_quantity(self):
        """Lock the highest bid quantity while bidding is open or within 6-hour winner window"""
        hb = self.highest_bid
        if not hb:
            return 0
        
        # Lock during bidding or payment window
        if self.is_bidding_open() or self.is_within_bid_payment_window():
            return min(getattr(hb, 'quantity', 0), self.quantity)
        
        # Lock after completed payment
        if hb.payment_status == 'completed' or getattr(hb, 'is_accepted', False):
            return min(getattr(hb, 'quantity', 0), self.quantity)
        
        return 0
    
    @property
    def sold_regular_quantity(self):
        """Count only completed regular purchases"""
        from buyer.models import Purchase
        return Purchase.objects.filter(
            listing=self,
            purchase_type='regular',
            status='payment_completed'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def sold_bid_quantity(self):
        """Count only completed bid payments"""
        return self.bids.filter(
            is_accepted=True,
            payment_status='completed'
        ).aggregate(total=models.Sum('quantity'))['total'] or 0
    
    @property
    def available_quantity(self):
        """Available for regular purchase = Total - Sold - Locked bid qty"""
        locked = self.locked_bid_quantity
        sold = self.sold_regular_quantity + self.sold_bid_quantity
        return max(self.quantity - sold - locked, 0)
    
    @property
    def is_available_for_regular_purchase(self):
        """Available for regular purchase if active and stock remains"""
        if not self.is_active:
            return False
        return self.available_quantity > 0
    
    @property
    def bid_revenue(self):
        """Include only completed winning bid revenue"""
        wb = self.winning_bid_candidate  # Use candidate, not winning_bid
        if wb and wb.payment_status == 'completed':
            total_amount = getattr(wb, 'total_amount', None)
            if total_amount is not None:
                return total_amount
            return (wb.amount or 0) * (getattr(wb, 'quantity', 0) or 0)
        return 0
    
    @property
    def regular_sales_revenue(self):
        """Include only completed regular purchases"""
        from buyer.models import Purchase
        return Purchase.objects.filter(
            listing=self,
            purchase_type='regular',
            status='payment_completed'
        ).aggregate(total=models.Sum('total_price'))['total'] or 0
    
    @property
    def total_revenue(self):
        """Total completed revenue only"""
        return (self.bid_revenue or 0) + (self.regular_sales_revenue or 0)
    
    def __str__(self):
        return self.name


class Bid(models.Model):
    listing = models.ForeignKey(ProductListing, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'buyer'})
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    placed_at = models.DateTimeField(auto_now_add=True)
    is_accepted = models.BooleanField(default=False)
    payment_status = models.CharField(
        max_length=20,
        choices=[('pending', 'Pending Payment'), ('completed', 'Payment Completed')],
        default='pending'
    )
    
    @property
    def total_amount(self):
        return self.amount * self.quantity
    
    def __str__(self):
        return f"Bid on {self.listing.name} - ₹{self.amount}"
