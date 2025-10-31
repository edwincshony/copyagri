from django.db import models
from django.core.validators import MinValueValidator
from accounts.models import CustomUser

class UserDocument(models.Model):
    DOCUMENT_TYPES = [
        ('aadhaar', 'Aadhaar Card'),
        ('land_deed', 'Land Deed'),
        ('bank_passbook', 'Bank Passbook'),
    ]
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role__in': ['farmer', 'buyer']})
    document_type = models.CharField(max_length=20, choices=DOCUMENT_TYPES)
    file = models.FileField(upload_to='documents/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=10, choices=[('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'admin'}, related_name='verified_docs')
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.get_document_type_display()}"

class LandRecord(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, limit_choices_to={'role': 'farmer'})
    survey_number = models.CharField(max_length=50)
    area_acres = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0)])
    location = models.CharField(max_length=200)
    document = models.FileField(upload_to='land_records/')
    is_verified = models.BooleanField(default=False)
    verified_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, blank=True, limit_choices_to={'role': 'admin'}, related_name='verified_lands')
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.survey_number}"

class StorageSlot(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    capacity_tons = models.PositiveIntegerField()
    available_slots = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)])
    price_per_slot = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    slot_type = models.CharField(max_length=20, choices=[('warehouse', 'Warehouse'), ('cold_storage', 'Cold Storage')])
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"

class CultivationSlot(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=200)
    available_area_acres = models.DecimalField(max_digits=5, decimal_places=2, default=0, validators=[MinValueValidator(0)])
    price_per_acre = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    crop_guidance = models.TextField(blank=True)  # Sowing/harvesting reminders
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.location}"

class SubsidyScheme(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()
    eligibility_criteria = models.TextField()
    subsidy_amount = models.DecimalField(max_digits=10, decimal_places=2)
    link = models.URLField(max_length=500, null=False, blank=False, help_text="Provide a valid government scheme URL")  # 👈 New Field
    is_active = models.BooleanField(default=True)
    added_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'admin'})
    added_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
