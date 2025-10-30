from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import Report

class ReportGenerationForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ['title', 'report_type', 'start_date', 'end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Generate Report', css_class='btn btn-primary'))

    def clean(self):
        cleaned_data = super().clean()
        start = cleaned_data.get('start_date')
        end = cleaned_data.get('end_date')
        if start and end and start > end:
            raise forms.ValidationError('End date must be after start date.')
        return cleaned_data