from django import forms
from django.core.exceptions import ValidationError
from crispy_forms.helper import FormHelper
from django.utils import timezone
from crispy_forms.layout import Submit
from .models import CultivationBooking, StorageBooking, ProductListing
from adminpanel.models import CultivationSlot, StorageSlot

class CultivationBookingForm(forms.ModelForm):
    class Meta:
        model = CultivationBooking
        fields = ['slot', 'booked_area_acres', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['slot'].queryset = CultivationSlot.objects.filter(available_area_acres__gt=0, is_active=True)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Book Slot', css_class='btn btn-primary'))

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise ValidationError('End date must be after start date.')
        slot = cleaned_data.get('slot')
        area = cleaned_data.get('booked_area_acres')
        if slot and area > slot.available_area_acres:
            raise ValidationError('Booked area exceeds availability.')
        if slot:
            cleaned_data['total_price'] = area * slot.price_per_acre
        return cleaned_data

class StorageBookingForm(forms.ModelForm):
    class Meta:
        model = StorageBooking
        fields = ['slot', 'booked_slots', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'min': timezone.now().date()}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        self.fields['slot'].queryset = StorageSlot.objects.filter(available_slots__gt=0, is_active=True)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Book Slot', css_class='btn btn-primary'))

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise ValidationError('End date must be after start date.')
        slot = cleaned_data.get('slot')
        slots = cleaned_data.get('booked_slots')
        if slot and slots > slot.available_slots:
            raise ValidationError('Booked slots exceed availability.')
        if slot:
            cleaned_data['total_price'] = slots * slot.price_per_slot
        return cleaned_data

class ProductListingForm(forms.ModelForm):
    class Meta:
        model = ProductListing
        fields = ['name', 'description', 'quantity', 'price', 'crop_type', 'location', 'image']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Create Listing', css_class='btn btn-primary'))

    def clean_location(self):
        location = self.cleaned_data['location']
        # Placeholder geocoder: In real, use geopy to suggest/validate
        return location