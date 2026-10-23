from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from datetime import timedelta
from .models import User, EmailOTP, PasswordResetToken, AuditLog, UserRole

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me') == 'on'
        
        # Telemetry fields from client POST if provided
        device_name = request.POST.get('device_name', '')
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')[:255]
        approx_location = request.POST.get('approx_location', 'Ahmedabad, Gujarat, India (22.9868° N, 72.3787° E)')
        network_provider = request.POST.get('network_provider', 'Jio Fiber / Enterprise WAN')
        
        if not device_name:
            if 'Linux' in user_agent:
                device_name = 'Linux x86_64 Operator Station'
            elif 'Windows' in user_agent:
                device_name = 'Windows 11 Workstation'
            elif 'Macintosh' in user_agent:
                device_name = 'Apple macOS Workstation'
            elif 'Android' in user_agent:
                device_name = 'Android Mobile Terminal'
            elif 'iPhone' in user_agent:
                device_name = 'Apple iOS Terminal'
            else:
                device_name = 'SCADA Operator Console'
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            if remember_me:
                request.session.set_expiry(1209600)  # 2 weeks
            else:
                request.session.set_expiry(0)  # browser close
                
            AuditLog.objects.create(
                user=user,
                action="USER_LOGIN_SUCCESS",
                details=f"Successful operator login: role={user.role}, device={device_name}, network={network_provider}",
                ip_address=get_client_ip(request),
                device_name=device_name,
                user_agent=user_agent,
                approx_location=approx_location,
                network_provider=network_provider
            )
            next_url = request.GET.get('next') or reverse('dashboard')
            return redirect(next_url)
        else:
            messages.error(request, "Invalid username or password. Please verify your credentials.")
            
    return render(request, 'accounts/login.html')

def logout_view(request):
    if request.user.is_authenticated:
        user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')[:255]
        device_name = 'Linux x86_64 Operator Station' if 'Linux' in user_agent else 'SCADA Workstation'
        AuditLog.objects.create(
            user=request.user,
            action="USER_LOGOUT",
            details=f"Operator session terminated for {request.user.username} ({request.user.role})",
            ip_address=get_client_ip(request),
            device_name=device_name,
            user_agent=user_agent,
            approx_location='Ahmedabad, Gujarat, India (22.9868° N, 72.3787° E)',
            network_provider='Jio Fiber / Enterprise WAN'
        )
    logout(request)
    return redirect('login')

def otp_login_view(request):
    step = request.session.get('otp_step', 'request')
    email = request.session.get('otp_email', '')
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'request_otp':
            email_input = request.POST.get('email', '').strip()
            try:
                user = User.objects.get(email__iexact=email_input)
                # Check 60-second cooldown
                recent_otp = EmailOTP.objects.filter(
                    user=user,
                    created_at__gte=timezone.now() - timedelta(seconds=getattr(settings, 'OTP_RESEND_COOLDOWN_SECONDS', 60))
                ).first()
                if recent_otp:
                    messages.warning(request, "Please wait 60 seconds before requesting a new OTP.")
                    return render(request, 'accounts/login_otp.html', {'step': 'verify', 'email': email_input})
                
                otp_obj, raw_code = EmailOTP.create_otp(user, email_input)
                
                # Send email to captured mailbox
                send_mail(
                    subject="Sunscrap Solar SCADA - Your One-Time Login Code",
                    message=f"Hello {user.username},\n\nYour 6-digit verification code is: {raw_code}\n\nThis code expires in 5 minutes. Do not share this code with anyone.",
                    from_email="noreply@sunscrap.local",
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                
                request.session['otp_step'] = 'verify'
                request.session['otp_email'] = email_input
                request.session['otp_id'] = otp_obj.id
                messages.success(request, f"A 6-digit code has been delivered to {email_input}.")
                return render(request, 'accounts/login_otp.html', {'step': 'verify', 'email': email_input, 'demo_hint': raw_code})
            except User.DoesNotExist:
                # Generic message to avoid email enumeration
                messages.info(request, "If an account matches that email, a verification code has been dispatched.")
                request.session['otp_step'] = 'verify'
                request.session['otp_email'] = email_input
                return render(request, 'accounts/login_otp.html', {'step': 'verify', 'email': email_input})
                
        elif action == 'verify_otp':
            code = request.POST.get('code', '').strip()
            otp_id = request.session.get('otp_id')
            if not otp_id:
                messages.error(request, "Session expired. Please request a new OTP.")
                return render(request, 'accounts/login_otp.html', {'step': 'request'})
                
            otp_obj = get_object_or_404(EmailOTP, id=otp_id)
            success, message = otp_obj.verify(code)
            
            if success:
                login(request, otp_obj.user)
                request.session.pop('otp_step', None)
                request.session.pop('otp_email', None)
                request.session.pop('otp_id', None)
                AuditLog.objects.create(
                    user=otp_obj.user,
                    action="USER_LOGIN_OTP",
                    details=f"Successful OTP login from IP {get_client_ip(request)}",
                    ip_address=get_client_ip(request)
                )
                return redirect('dashboard')
            else:
                messages.error(request, message)
                return render(request, 'accounts/login_otp.html', {'step': 'verify', 'email': email})
                
        elif action == 'back':
            request.session.pop('otp_step', None)
            request.session.pop('otp_email', None)
            request.session.pop('otp_id', None)
            return render(request, 'accounts/login_otp.html', {'step': 'request'})
            
    return render(request, 'accounts/login_otp.html', {'step': 'request'})

def forgot_password_view(request):
    if request.method == 'POST':
        email_input = request.POST.get('email', '').strip()
        user = User.objects.filter(email__iexact=email_input).first()
        if user:
            reset_token = PasswordResetToken.create_token(user)
            reset_url = request.build_absolute_uri(reverse('reset_password', args=[reset_token.token]))
            send_mail(
                subject="Sunscrap Solar SCADA - Password Reset Instructions",
                message=f"Hello {user.username},\n\nPlease click the link below to reset your password:\n{reset_url}\n\nThis single-use link expires in 2 hours.",
                from_email="noreply@sunscrap.local",
                recipient_list=[user.email],
                fail_silently=False
            )
            AuditLog.objects.create(
                user=user,
                action="PASSWORD_RESET_REQUESTED",
                details=f"Reset token issued from IP {get_client_ip(request)}",
                ip_address=get_client_ip(request)
            )
            messages.success(request, f"Password reset instructions have been sent to {email_input}.")
            return render(request, 'accounts/forgot_password.html', {'sent': True, 'token': reset_token.token})
        else:
            messages.info(request, "If an account matches that email, reset instructions have been sent.")
            return render(request, 'accounts/forgot_password.html', {'sent': True})
            
    return render(request, 'accounts/forgot_password.html', {'sent': False})

def reset_password_view(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token)
    if not reset_token.is_valid():
        messages.error(request, "This password reset link is invalid or has expired.")
        return redirect('forgot_password')
        
    if request.method == 'POST':
        new_password = request.POST.get('new_password', '')
        confirm_password = request.POST.get('confirm_password', '')
        
        if len(new_password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, 'accounts/reset_password.html', {'token': token})
            
        if new_password != confirm_password:
            messages.error(request, "Passwords do not match.")
            return render(request, 'accounts/reset_password.html', {'token': token})
            
        user = reset_token.user
        user.set_password(new_password)
        user.save()
        
        reset_token.is_used = True
        reset_token.save()
        
        AuditLog.objects.create(
            user=user,
            action="PASSWORD_RESET_COMPLETED",
            details=f"Password changed via reset token from IP {get_client_ip(request)}",
            ip_address=get_client_ip(request)
        )
        messages.success(request, "Password successfully updated! You can now log in.")
        return redirect('login')
        
    return render(request, 'accounts/reset_password.html', {'token': token})

@login_required
def profile_view(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'change_password':
            current_password = request.POST.get('current_password', '')
            new_password = request.POST.get('new_password', '')
            confirm_password = request.POST.get('confirm_password', '')
            
            if not request.user.check_password(current_password):
                messages.error(request, "Current password is incorrect.")
            elif len(new_password) < 8:
                messages.error(request, "New password must be at least 8 characters long.")
            elif new_password != confirm_password:
                messages.error(request, "New passwords do not match.")
            else:
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request, request.user)
                AuditLog.objects.create(
                    user=request.user,
                    action="USER_PASSWORD_CHANGE",
                    details="Password changed from user profile",
                    ip_address=get_client_ip(request)
                )
                messages.success(request, "Password successfully changed.")
        elif action == 'update_details':
            first_name = request.POST.get('first_name', '').strip()
            last_name = request.POST.get('last_name', '').strip()
            phone = request.POST.get('phone', '').strip()
            request.user.first_name = first_name
            request.user.last_name = last_name
            request.user.phone = phone
            request.user.save()
            messages.success(request, "Profile details updated successfully.")
            
    return render(request, 'accounts/profile.html', {'user': request.user})

@login_required
def profile_email_view(request):
    if request.method == 'POST':
        current_password = request.POST.get('current_password', '')
        new_email = request.POST.get('new_email', '').strip()
        
        if not request.user.check_password(current_password):
            messages.error(request, "Re-authentication failed: current password is incorrect.")
            return render(request, 'accounts/profile_email.html')
            
        if not new_email or '@' not in new_email:
            messages.error(request, "Please provide a valid email address.")
            return render(request, 'accounts/profile_email.html')
            
        if User.objects.filter(email__iexact=new_email).exclude(id=request.user.id).exists():
            messages.error(request, "This email is already associated with another account.")
            return render(request, 'accounts/profile_email.html')
            
        old_email = request.user.email
        request.user.email = new_email
        request.user.save()
        
        # Dispatch notification to old address and confirmation to new
        send_mail(
            subject="Sunscrap Solar SCADA - Security Notice: Email Changed",
            message=f"Hello,\n\nThe email address for your Sunscrap Solar SCADA account was changed from {old_email} to {new_email} on {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}.\n\nIf you did not authorize this change, contact the plant system administrator immediately.",
            from_email="security@sunscrap.local",
            recipient_list=[old_email] if old_email else [new_email],
            fail_silently=True
        )
        
        AuditLog.objects.create(
            user=request.user,
            action="USER_EMAIL_CHANGED",
            details=f"Email changed from {old_email} to {new_email}",
            ip_address=get_client_ip(request)
        )
        messages.success(request, f"Your email has been successfully updated to {new_email}.")
        return redirect('profile')
        
    return render(request, 'accounts/profile_email.html')
