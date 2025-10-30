from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm, PasswordChangeForm
from crispy_forms.helper import FormHelper
from django.contrib.auth.forms import UserCreationForm, PasswordResetForm, SetPasswordForm, PasswordChangeForm
from crispy_forms.layout import Submit
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.RadioSelect)
    mobile = forms.CharField(max_length=10)
    address = forms.CharField(widget=forms.Textarea)
    profile_picture = forms.ImageField(required=False)
    buyer_type = forms.ChoiceField(
        choices=[('', 'Select Type')] + list(CustomUser._meta.get_field('buyer_type').choices),
        required=False,
        widget=forms.Select
    )

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'role', 'mobile', 'address', 'profile_picture', 'buyer_type', 'password1', 'password2')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Register', css_class='btn btn-primary'))
        # Conditional display for buyer_type
        self.fields['buyer_type'].widget.attrs['style'] = 'display: none;'  # JS will show/hide

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
            raise forms.ValidationError('Mobile must be exactly 10 digits starting with 6, 7, 8, or 9.')
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get('role')
        buyer_type = cleaned_data.get('buyer_type')
        if role == 'buyer' and not buyer_type:
            raise forms.ValidationError('Buyer type is required for buyers.')
        if role == 'farmer':
            cleaned_data['buyer_type'] = None
        return cleaned_data

class CustomUserAuthenticationForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Login', css_class='btn btn-primary'))

class CustomUserChangeForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'mobile', 'address', 'profile_picture', 'buyer_type')
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Update Profile', css_class='btn btn-primary'))

    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if not mobile.isdigit() or len(mobile) != 10 or mobile[0] not in '6789':
            raise forms.ValidationError('Mobile must be exactly 10 digits starting with 6, 7, 8, or 9.')
        return mobile

class CustomUserPasswordChangeForm(PasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Change Password', css_class='btn btn-primary'))

class CustomPasswordResetForm(PasswordResetForm):
    pass  # Extend if needed


class CustomSetPasswordForm(SetPasswordForm):
    pass  # Extend if needed


class CustomPasswordChangeForm(PasswordChangeForm):
    pass  # Extend if needed