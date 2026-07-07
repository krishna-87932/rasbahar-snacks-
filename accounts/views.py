from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.http import require_POST
import json
import math

from .forms import RegisterForm, LoginForm, OTPForm, ProfileForm, ChangePasswordForm, ForgetPassword, ResetPasswordForm
from .models import OTPRecord, generate_otp
from .otp_verifiction_manager import send_gmail_otp
User = get_user_model()


def _send_otp(recipient_email, otp, purpose):
    """In production, integrate with SMS gateway (Twilio, MSG91, etc.)"""
    print(f"\n{'='*40}")
    print(f"[OTP EMAIL] To: {recipient_email}")
    print(f"[OTP EMAIL] Purpose: {purpose}")
    print(f"[OTP EMAIL] Code: {otp}")
    send_gmail_otp(otp_subject=purpose, user_otp=otp, consumer=recipient_email)
    print(f"{'='*40}\n")

def register_view(request):
    if request.user.is_authenticated:
        return redirect('menu:home')

    form = RegisterForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        # Store registration data in session, redirect to location check
        request.session['pending_register'] = {
            'name': data['name'],
            'phone_number': data['phone_number'],
            'email': data['email'],
            'password': data['password'],
        }
        return redirect('accounts:register_location')

    return render(request, 'accounts/register.html', {'form': form})


def register_location_view(request):
    """GPS location check page — shown after register form, before OTP."""
    if request.user.is_authenticated:
        return redirect('menu:home')

    pending = request.session.get('pending_register')
    if not pending:
        messages.error(request, 'Session expired. Please register again.')
        return redirect('accounts:register')

    return render(request, 'accounts/register_location.html', {
        'restaurant_lat': settings.RESTAURANT_LAT,
        'restaurant_lng': settings.RESTAURANT_LNG,
        'max_radius_km': settings.MAX_DELIVERY_RADIUS_KM,
    })


@require_POST
def register_check_location_api(request):
    """AJAX endpoint — checks GPS distance and sends OTP if within range."""
    pending = request.session.get('pending_register')
    if not pending:
        return JsonResponse({'success': False, 'error': 'Session expired. Please register again.'}, status=400)

    try:
        data = json.loads(request.body)
        lat = float(data.get('latitude', 0))
        lng = float(data.get('longitude', 0))
        address = data.get('address', '').strip()
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    if not lat or not lng:
        return JsonResponse({'success': False, 'error': 'Could not get your location.'}, status=400)

    # Haversine distance calculation
    R = 6371  # Earth radius in km
    lat1 = math.radians(settings.RESTAURANT_LAT)
    lat2 = math.radians(lat)
    dlat = math.radians(lat - settings.RESTAURANT_LAT)
    dlng = math.radians(lng - settings.RESTAURANT_LNG)
    a = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlng / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance_km = round(R * c, 2)
    in_range = distance_km <= settings.MAX_DELIVERY_RADIUS_KM

    if in_range:
        # Save coordinates in session and send OTP
        pending['latitude'] = lat
        pending['longitude'] = lng
        pending['address'] = address
        request.session['pending_register'] = pending
        request.session.modified = True

        record = OTPRecord.create_otp(
            pending['phone_number'],
            OTPRecord.PURPOSE_REGISTER,
            expiry_minutes=getattr(settings, 'OTP_EXPIRY_MINUTES', 10)
        )
        _send_otp(pending['email'], record.otp, 'Registration')

    return JsonResponse({
        'success': True,
        'in_range': in_range,
        'distance_km': distance_km,
        'max_radius_km': settings.MAX_DELIVERY_RADIUS_KM,
    })

def verify_otp_view(request, purpose):
    if request.user.is_authenticated:
        return redirect('menu:home')

    # Validate purpose
    valid_purposes = [OTPRecord.PURPOSE_REGISTER, OTPRecord.PURPOSE_LOGIN, OTPRecord.PURPOSE_RESET]
    if purpose not in valid_purposes:
        return redirect('accounts:login')

    session_key = f'pending_{purpose}'
    pending = request.session.get(session_key) or request.session.get('pending_register')

    if not pending:
        messages.error(request, 'Session expired. Please start again.')
        return redirect('accounts:register' if purpose == 'register' else 'accounts:login')

    phone_number = pending.get('phone_number')
    email = pending.get('email')
    form = OTPForm(request.POST or None)

    if request.method == 'POST' and form.is_valid():
        otp = form.cleaned_data['otp']
        record, error = OTPRecord.verify_otp(phone_number, otp, purpose)

        if error:
            messages.error(request, error)
        else:
            if purpose == OTPRecord.PURPOSE_REGISTER:
                pending_data = request.session.pop('pending_register', {})
                user = User.objects.create_user(
                    phone_number=pending_data['phone_number'],
                    name=pending_data['name'],
                    password=pending_data['password'],
                    email=pending_data['email'],
                    address=pending_data.get('address', ''),
                    latitude=pending_data.get('latitude'),
                    longitude=pending_data.get('longitude'),
                    is_active=True,
                ) # type: ignore
                login(request, user)
                messages.success(request, f"Welcome to Rasbahar Snacks, {user.name}! 🎉")
                return redirect('menu:home')

            elif purpose == OTPRecord.PURPOSE_LOGIN:
                pending_data = request.session.pop('pending_login', {})
                try:
                    user = User.objects.get(phone_number=pending_data['phone_number'])
                    login(request, user)
                    messages.success(request, f"Welcome back, {user.name}!")
                    return redirect(request.GET.get('next', 'menu:home'))
                except User.DoesNotExist:
                    messages.error(request, 'User not found.')

    # Resend OTP
    if request.method == 'POST' and 'resend' in request.POST:
        record = OTPRecord.create_otp(phone_number, purpose)
        # We need the email to send the OTP. It should be in the session.
        recipient_email = pending.get('email')
        if recipient_email:
            _send_otp(recipient_email, record.otp, purpose)

        messages.info(request, 'New OTP sent.')

    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'phone_number': phone_number,
        'email':email,
        'purpose': purpose,
    })

def login_view(request):
    if request.user.is_authenticated:
        return redirect('menu:home')

    form = LoginForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        phone = form.cleaned_data['phone_number']
        password = form.cleaned_data['password']
        user = authenticate(request, username=phone, password=password)

        if user:
            login(request, user)
            messages.success(request, f"Welcome back, {user.name}! 🙌")
            return redirect(request.GET.get('next', 'menu:home'))
        else:
            messages.error(request, 'Invalid phone number or password.')

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    if request.method == 'POST':
        logout(request)
        messages.success(request, 'Logged out successfully.')
    return redirect('accounts:login')

@login_required
def profile_view(request):
    form = ProfileForm(request.POST or None, request.FILES or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        user = form.save(commit=False)
        # If address changed, clear old coordinates so user re-verifies location
        if 'address' in form.changed_data:
            user.latitude = None
            user.longitude = None
        user.save()
        messages.success(request, 'Profile updated successfully!')
        if not user.has_location:
            messages.info(request, 'Please update your delivery location.')
            return redirect('accounts:add_address')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html', {'form': form})

@login_required
def change_password_view(request):
    form = ChangePasswordForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        data = form.cleaned_data
        if not request.user.check_password(data['old_password']):
            messages.error(request, 'Current password is incorrect.')
        else:
            request.user.set_password(data['new_password'])
            request.user.save()
            messages.success(request, 'Password changed. Please log in again.')
            return redirect('accounts:login')
    return render(request, 'accounts/change_password.html', {'form': form})


@login_required
def add_address_view(request):
    """GPS-based address / location page — shown after registration."""
    user = request.user
    return render(request, 'accounts/add_address.html', {
        'user': user,
        'restaurant_lat': settings.RESTAURANT_LAT,
        'restaurant_lng': settings.RESTAURANT_LNG,
        'max_radius_km': settings.MAX_DELIVERY_RADIUS_KM,
    })


@login_required
@require_POST
def save_location_api(request):
    """AJAX endpoint — saves GPS coordinates and checks delivery range."""
    try:
        data = json.loads(request.body)
        lat = float(data.get('latitude', 0))
        lng = float(data.get('longitude', 0))
        address = data.get('address', '').strip()
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({'success': False, 'error': 'Invalid data.'}, status=400)

    if not lat or not lng:
        return JsonResponse({'success': False, 'error': 'Could not get your location.'}, status=400)

    user = request.user
    user.latitude = lat
    user.longitude = lng
    if address:
        user.address = address
    user.save()

    distance = user.distance_from_restaurant_km
    in_range = user.is_within_delivery_range

    return JsonResponse({
        'success': True,
        'in_range': in_range,
        'distance_km': distance,
        'max_radius_km': settings.MAX_DELIVERY_RADIUS_KM,
    })


#----- Forget Password ------

def forget_password(request):
    if request.method == "POST":
        form = ForgetPassword(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            try:
                user = User.objects.get(email=email)
                otp = generate_otp()
                request.session['reset_otp'] = str(otp)
                request.session['reset_email'] = email
                _send_otp(email, otp, 'Password Reset')
                messages.info(request, f"OTP sent to {email}. Valid for 10 minutes.")
                return redirect('accounts:forget_otp_verify')
            except User.DoesNotExist:
                form.add_error('email', 'Email address not found in our system.')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = ForgetPassword()
    return render(request, 'accounts/forger_password.html', {'form': form})

def forget_pass_otp_verify(request):
    email = request.session.get('reset_email')
    if not email:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('accounts:forget_password')
    
    form = OTPForm(request.POST or None)
    
    if request.method == "POST" and 'otp' in request.POST and form.is_valid():
        entered_otp = form.cleaned_data['otp']
        if entered_otp == request.session.get('reset_otp'):
            request.session['otp_verified'] = True
            return redirect('accounts:reset_password')
        messages.error(request, 'Invalid OTP. Please try again.')
    
    # Resend OTP
    if request.method == 'POST' and 'resend' in request.POST:
        otp = generate_otp()
        request.session['reset_otp'] = str(otp)
        try:
            user = User.objects.get(email=email)
            _send_otp(email, otp, 'Password Reset')
            messages.info(request, 'New OTP sent to your email.')
        except User.DoesNotExist:
            messages.error(request, 'Could not resend OTP. User not found.')
    
    return render(request, 'accounts/verify_otp.html', {
        'form': form,
        'email': email,
        'purpose': 'reset'
    })

def reset_password(request):
    email = request.session.get('reset_email')
    otp_verified = request.session.get('otp_verified')
    if not email or not otp_verified:
        messages.error(request, 'Session expired. Please try again.')
        return redirect('accounts:forget_password')
    
    if request.method == 'POST':
        form = ResetPasswordForm(request.POST)
        if form.is_valid():
            password = form.cleaned_data['password']
            try:
                user = User.objects.get(email=email)
                user.set_password(password)
                user.save()
                # Clear session data
                for key in ['reset_otp', 'reset_email', 'otp_verified']:
                    request.session.pop(key, None)
                messages.success(request, 'Password reset successfully! Please log in with your new password.')
                return redirect('accounts:login')
            except User.DoesNotExist:
                messages.error(request, 'User not found.')
        else:
            messages.error(request, 'Passwords do not match.')
    else:
        form = ResetPasswordForm()
    
    return render(request, 'accounts/reset_password.html', {'form': form})



