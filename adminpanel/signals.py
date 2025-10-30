from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mail
from django.conf import settings
from accounts.models import CustomUser
from .models import UserDocument

@receiver(post_save, sender=CustomUser)
def send_approval_email(sender, instance, created, **kwargs):
    if not created and instance.is_approved != instance._state.adding:  # Changed
        status = 'approved' if instance.is_approved else 'rejected'
        send_mail(
            f'Account {status.title()}',
            f'Your AgriLeader account has been {status}.',
            settings.DEFAULT_FROM_EMAIL,
            [instance.email],
            fail_silently=True,
        )