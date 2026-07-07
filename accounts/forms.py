from django import forms
from django.contrib.auth import get_user_model

User = get_user_model()


class RegisterForm(forms.Form):
    name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={'placeholder': 'Full Name', 'class': 'form-input'})
    )
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+91 9876543210', 'class': 'form-input'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'placeholder': 'Email', 'class': 'form-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Confirm Password', 'class': 'form-input'})
    )

    def clean_phone_number(self):
        phone = self.cleaned_data['phone_number'].strip()
        if User.objects.filter(phone_number=phone).exists():
            raise forms.ValidationError('This phone number is already registered.')
        return phone

    def clean_email(self):
        email = self.cleaned_data['email'].strip()
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError('This email address is already in use.')
        return email

    def clean(self):
        cleaned = super().clean()
        p1 = cleaned.get('password')
        p2 = cleaned.get('confirm_password')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned


class LoginForm(forms.Form):
    phone_number = forms.CharField(
        max_length=15,
        widget=forms.TextInput(attrs={'placeholder': '+91 9876543210', 'class': 'form-input'})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'placeholder': 'Password', 'class': 'form-input'})
    )


class OTPForm(forms.Form):
    otp = forms.CharField(
        max_length=6,
        min_length=6,
        widget=forms.TextInput(attrs={
            'type': 'text',
            'placeholder': '• • • • • •',
            'class': 'form-input otp-input',
            'maxlength': '6',
            'inputmode': 'numeric',
            'autocomplete': 'one-time-code',
        })
    )


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['name', 'email', 'address', 'profile_picture']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-input'}),
            'email': forms.EmailInput(attrs={'class': 'form-input'}),
            'address': forms.Textarea(attrs={'class': 'form-input', 'rows': 3}),
        }


class ChangePasswordForm(forms.Form):
    old_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Current password'})
    )
    new_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'New password'})
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-input', 'placeholder': 'Confirm new password'})
    )

    def clean(self):
        cleaned = super().clean()
        if cleaned.get('new_password') != cleaned.get('confirm_password'):
            raise forms.ValidationError('New passwords do not match.')
        return cleaned

class ForgetPassword(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'Enter your registered email',
            'class': 'form-input'
        })
    )
    
    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if not User.objects.filter(email=email).exists():
            raise forms.ValidationError('Email address not found in our system.')
        return email


class ResetPasswordForm(forms.Form):
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'New password',
            'class': 'form-input'
        })
    )
    confirm_password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm password',
            'class': 'form-input'
        })
    )
    
    def clean(self):
        cleaned = super().clean()
        password = cleaned.get('password')
        confirm = cleaned.get('confirm_password')
        if password and confirm and password != confirm:
            raise forms.ValidationError('Passwords do not match.')
        return cleaned
    
    
    
    