from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from accounts.models import CustomUser  
from .models import Notification

class CustomNotificationForm(forms.ModelForm):
    recipients = forms.ModelMultipleChoiceField(queryset=CustomUser.objects.filter(role__in=['farmer', 'buyer']))

    class Meta:
        model = Notification
        fields = ['title', 'message', 'notification_type']
        exclude = ['user', 'is_read', 'created_at', 'related_id', 'related_model']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Send Notification', css_class='btn btn-primary'))

    def save(self, commit=True):
        instance = super().save(commit=False)
        for recipient in self.cleaned_data['recipients']:
            notif = instance
            notif.pk = None  # New instance per user
            notif.user = recipient
            if commit:
                notif.save()
        return instance