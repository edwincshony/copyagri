from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import CustomPasswordResetForm, CustomSetPasswordForm
from django.http import HttpResponse
from django.views.generic import FormView, UpdateView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView
from django.urls import reverse_lazy
from django.contrib.auth.views import PasswordChangeView
from .forms import (
    CustomUserCreationForm, CustomUserAuthenticationForm,
    CustomUserChangeForm, CustomUserPasswordChangeForm
)
from .models import CustomUser

def home(request):
    return render(request, 'accounts/home.html')

class RegisterView(FormView):
    template_name = 'accounts/registration.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('accounts:pending_approval')

    def form_valid(self, form):
        user = form.save(commit=False)
        user.is_approved = False  # Pending admin approval
        user.save()
        messages.success(self.request, 'Registration successful! Awaiting admin approval.')
        # Email notification can be added here or in admin approval (later)
        return super().form_valid(form)

class LoginView(FormView):
    template_name = 'accounts/login.html'
    form_class = CustomUserAuthenticationForm
    success_url = reverse_lazy('accounts:home')  # fallback

    def form_valid(self, form):
        user = form.get_user()

        # Check if approved (unless admin)
        if not user.is_approved and user.role != 'admin':
            messages.warning(self.request, 'Your account is pending approval. Please wait for admin verification.')
            return redirect('accounts:pending_approval')

        # Log in the user
        login(self.request, user)
        messages.success(self.request, f'Welcome back, {user.username}!')

        # Role-based redirect logic
        if user.role == 'admin':
            return redirect('adminpanel:dashboard')   # create this URL/view
        elif user.role == 'farmer':
            return redirect('farmer:dashboard')  # create this URL/view
        elif user.role == 'buyer':
            return redirect('buyer:dashboard')   # create this URL/view
        else:
            return super().form_valid(form)  # fallback

    def form_invalid(self, form):
        messages.error(self.request, 'Invalid credentials.')
        return super().form_invalid(form)

@login_required
def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('accounts:home')

@login_required
def profile_view(request):
    return render(request, 'accounts/profile.html', {'user': request.user})

class UpdateProfileView(UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'accounts/edit_profile.html'
    success_url = reverse_lazy('accounts:profile')

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, 'Profile updated successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error updating profile.')
        return super().form_invalid(form)

class ChangePasswordView(PasswordChangeView):
    form_class = CustomUserPasswordChangeForm
    template_name = 'accounts/change_password.html'
    success_url = reverse_lazy('accounts:profile')

    def form_valid(self, form):
        user = form.save()
        update_session_auth_hash(self.request, user)
        messages.success(self.request, 'Password changed successfully!')
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, 'Error changing password.')
        return super().form_invalid(form)

def pending_approval_view(request):
    return render(request, 'accounts/pending_approval.html')

# Password reset views (built-in, customized with forms)
class CustomPasswordResetView(PasswordResetView):
    form_class = CustomPasswordResetForm
    success_url = reverse_lazy('accounts:password_reset_done')
    template_name = 'accounts/password_reset.html'
    email_template_name = 'accounts/password_reset_email.html' 

class CustomPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'accounts/password_reset_done.html'

class CustomPasswordResetConfirmView(PasswordResetConfirmView):
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    template_name = 'accounts/password_reset_confirm.html'

class CustomPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'accounts/password_reset_complete.html'