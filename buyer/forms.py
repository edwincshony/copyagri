from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from farmer.models import StorageBooking
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Purchase
from farmer.models import Bid
from adminpanel.models import StorageSlot

class BidForm(forms.ModelForm):
    class Meta:
        model = Bid
        fields = ['amount']

    def __init__(self, *args, **kwargs):
        self.listing = kwargs.pop('listing', None)
        super().__init__(*args, **kwargs)
        if self.listing:
            self.instance.listing = self.listing
            # Optional client-side minimum
            self.fields['amount'].min_value = self.listing.price
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Place Bid', css_class='btn btn-primary'))

    def clean_amount(self):
        amount = self.cleaned_data['amount']

        if amount <= 0:
            raise ValidationError('Bid amount must be positive.')

        if self.listing and amount <= self.listing.price:
            raise ValidationError(
                f"Bid must be greater than the base price of ₹{self.listing.price}."
            )

        highest_bid = self.listing.highest_bid()
        if highest_bid and amount <= highest_bid.amount:
            raise ValidationError(f'Your bid must be higher than ₹{highest_bid.amount}.')

        return amount

    def clean(self):
        cleaned_data = super().clean()
        if not self.listing.is_bidding_open():
            raise ValidationError("Bidding has closed for this product.")
        return cleaned_data



class PurchaseForm(forms.ModelForm):
    class Meta:
        model = Purchase
        fields = ['quantity']
        widgets = {'quantity': forms.NumberInput(attrs={'min': 1})}

    def __init__(self, *args, **kwargs):
        listing = kwargs.pop('listing', None)
        super().__init__(*args, **kwargs)
        if listing:
            self.instance.listing = listing
            self.fields['quantity'].max_value = listing.quantity
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Confirm Purchase', css_class='btn btn-success'))

    def clean_quantity(self):
        quantity = self.cleaned_data['quantity']
        if quantity > self.instance.listing.quantity:
            raise ValidationError('Quantity exceeds available stock.')
        return quantity

class StorageBookingForm(forms.ModelForm):  # Reuse from farmer, but for buyer
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

    # Same clean as in farmer/forms.py