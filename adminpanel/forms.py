from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import (
    UserDocument, LandRecord, StorageSlot, CultivationSlot, SubsidyScheme
)

class UserDocumentForm(forms.ModelForm):
    class Meta:
        model = UserDocument
        fields = ['document_type', 'file']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Upload Document', css_class='btn btn-primary'))

class LandRecordForm(forms.ModelForm):
    class Meta:
        model = LandRecord
        fields = ['survey_number', 'area_acres', 'location', 'document']
        widgets = {'location': forms.Textarea(attrs={'rows': 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Add Land Record', css_class='btn btn-primary'))

class StorageSlotForm(forms.ModelForm):
    class Meta:
        model = StorageSlot
        fields = ['name', 'location', 'capacity_tons', 'available_slots', 'price_per_slot', 'slot_type']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Save Slot', css_class='btn btn-primary'))

class CultivationSlotForm(forms.ModelForm):
    class Meta:
        model = CultivationSlot
        fields = ['name', 'location', 'available_area_acres', 'price_per_acre', 'crop_guidance']
        widgets = {'crop_guidance': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Save Slot', css_class='btn btn-primary'))

class SubsidySchemeForm(forms.ModelForm):
    class Meta:
        model = SubsidyScheme
        fields = ['name', 'description', 'eligibility_criteria', 'subsidy_amount']
        widgets = {'description': forms.Textarea(attrs={'rows': 3}), 'eligibility_criteria': forms.Textarea(attrs={'rows': 3})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Add Scheme', css_class='btn btn-primary'))