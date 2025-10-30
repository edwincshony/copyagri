from django.db import models
from accounts.models import CustomUser

class Notification(models.Model):
    NOTIFICATION_TYPES = [
        ('approval', 'Approval/Rejection'),
        ('booking', 'Booking Update'),
        ('marketplace', 'Marketplace Transaction'),
        ('scheme', 'New Scheme Alert'),
        ('weather', 'Weather Alert'),
        ('custom', 'Custom'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    message = models.TextField()
    notification_type = models.CharField(max_length=20, choices=NOTIFICATION_TYPES)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    related_id = models.PositiveIntegerField(null=True, blank=True)  # e.g., booking ID
    related_model = models.CharField(max_length=50, null=True, blank=True)  # e.g., 'CultivationBooking'

    def __str__(self):
        return f"{self.user.username} - {self.title}"

    class Meta:
        ordering = ['-created_at']