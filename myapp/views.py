from django.contrib.auth import logout
from django.shortcuts import render, redirect
import hashlib
import random
import re
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import CustomUser, OTP, LoginLog, ActivityLog

def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

def calculate_risk_score(email, ip_address):
    score = 0
    # Rule 1: Email contains numbers like "123"
    if re.search(r'\d', email):
        score += 1
        
    # Rule 2: Multiple OTP requests (>3)
    otp_count = OTP.objects.filter(email=email).count()
    if otp_count > 3:
        score += 2
        
    # Rule 3: Same IP created multiple accounts (>2)
    ip_accounts = CustomUser.objects.filter(created_ip=ip_address).count()
    if ip_accounts > 2:
        score += 3
        
    if score <= 1:
        return 'Normal'
    elif score <= 3:
        return 'Medium Risk'
    else:
        return 'High Risk'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def register_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip().lower()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')

        if not first_name or not last_name or not email or not password or not confirm_password:
            return render(request, 'myapp/register.html', {'error': 'All fields are required.'})

        if password != confirm_password:
            return render(request, 'myapp/register.html', {'error': 'Passwords do not match.'})

        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'myapp/register.html', {'error': 'Email already exists'})

        hashed_password = hash_password(password)

        otp_code = str(random.randint(100000, 999999))
        OTP.objects.create(email=email, otp=otp_code)

        request.session['reg_first_name'] = first_name
        request.session['reg_last_name'] = last_name
        request.session['reg_email'] = email
        request.session['reg_password'] = hashed_password
        request.session['resend_count'] = 0
        request.session['verify_otp_attempts'] = 0

    try:
        send_mail(
            subject="OTP Verification",
            message=f"Your OTP is {otp_code}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=True,
        )
        print("EMAIL SENT SUCCESS")
    
    except Exception as e:
        print("EMAIL ERROR:", e)
    
        # return redirect('verify_otp')

    return render(request, 'myapp/register.html')

def resend_otp_view(request):
    email = request.session.get('reg_email')
    
    if not email:
        return redirect('register')
        
    resend_count = request.session.get('resend_count', 0)
    
    if resend_count >= 3:
        return render(request, 'myapp/verify_otp.html', {'error': 'Maximum resend attempts reached.', 'email': email})
        
    # Generate 6-digit OTP
    otp_code = str(random.randint(100000, 999999))
    OTP.objects.create(email=email, otp=otp_code)
    
    # DEBUG: Print OTP in console
    print("EMAIL SENDING TO:", email)
    print("OTP:", otp_code)
    
    # Update resend count
    request.session['resend_count'] = resend_count + 1
    
    # Send OTP via email
    send_mail(
        subject="OTP Verification",
        message=f"Your OTP is {otp_code}",
        from_email=settings.EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
    
    return render(request, 'myapp/verify_otp.html', {'success': 'A new OTP has been sent.', 'email': email})

def verify_otp_view(request):
    email = request.session.get('reg_email')
    password = request.session.get('reg_password')
    first_name = request.session.get('reg_first_name', '')
    last_name = request.session.get('reg_last_name', '')

    if not email or not password:
        return redirect('register')

    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()

        if latest_otp:
            time_diff = timezone.now() - latest_otp.created_at
            if time_diff.total_seconds() > 60:
                return render(request, 'myapp/verify_otp.html', {'error': 'OTP expired. Please request a new one.', 'email': email})

            if latest_otp.otp == entered_otp:
                ip_address = get_client_ip(request)
                risk_level = calculate_risk_score(email, ip_address)

                CustomUser.objects.create(
                    email=email,
                    first_name=first_name,
                    last_name=last_name,
                    password=password,
                    is_verified=True,
                    created_ip=ip_address,
                    risk_level=risk_level
                )

                request.session.pop('reg_first_name', None)
                request.session.pop('reg_last_name', None)
                request.session.pop('reg_email', None)
                request.session.pop('reg_password', None)
                request.session.pop('resend_count', None)
                request.session.pop('verify_otp_attempts', None)

                return redirect('login')
            else:
                attempts = request.session.get('verify_otp_attempts', 0) + 1
                request.session['verify_otp_attempts'] = attempts

                if attempts >= 3:
                    ActivityLog.objects.create(user_email=email, action='failed registration OTP', is_suspicious=True)
                    request.session.pop('reg_first_name', None)
                    request.session.pop('reg_last_name', None)
                    request.session.pop('reg_email', None)
                    request.session.pop('reg_password', None)
                    request.session.pop('resend_count', None)
                    request.session.pop('verify_otp_attempts', None)
                    return redirect('register')

                return render(request, 'myapp/verify_otp.html', {'error': f'Invalid OTP. Attempts left: {3 - attempts}', 'email': email})
        else:
            return render(request, 'myapp/verify_otp.html', {'error': 'No OTP found. Please register again.', 'email': email})

    return render(request, 'myapp/verify_otp.html', {'email': email})

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        hashed_password = hash_password(password)
        ip_address = get_client_ip(request)
        
        # Check if account is frozen
        user = CustomUser.objects.filter(email=email).first()
        if user and user.blocked_until and timezone.now() < user.blocked_until:
            return render(request, 'myapp/login.html', {'error': 'Account temporarily frozen due to suspicious activity. Try again after 48 hours.'})
        
        # Unblock if 48 hours passed
        if user and user.blocked_until and timezone.now() >= user.blocked_until:
            user.is_blocked = False
            user.blocked_until = None
            user.save()
            
        # Check suspicious login criteria BEFORE evaluating password
        five_mins_ago = timezone.now() - timedelta(minutes=5)
        
        # 1. More than 3 failed attempts
        recent_failures = LoginLog.objects.filter(
            email=email, 
            success=False, 
            login_time__gte=five_mins_ago
        ).count()
        
        # 2. Multiple successful logins within short time
        recent_successes = LoginLog.objects.filter(
            email=email,
            success=True,
            login_time__gte=five_mins_ago
        ).count()
        
        is_suspicious = recent_failures >= 3 or recent_successes >= 3
        
        if user and user.password == hashed_password:
            if not user.is_verified:
                return render(request, 'myapp/login.html', {'error': 'Please verify your email first'})
                
            LoginLog.objects.create(email=email, ip_address=ip_address, success=True, is_suspicious=is_suspicious)
            
            # Log Activity
            ActivityLog.objects.create(user_email=email, action='login', is_suspicious=is_suspicious)
            
            request.session['user_id'] = user.id
            return redirect('dashboard')
        else:
            LoginLog.objects.create(email=email, ip_address=ip_address, success=False, is_suspicious=is_suspicious)
            return render(request, 'myapp/login.html', {'error': 'Invalid credentials'})
            
    return render(request, 'myapp/login.html')

def logout_view(request):
    if request.method == "POST":
        logout(request)
        return redirect('login')

    return redirect('dashboard')


def dashboard_view(request):
    user_id = request.session.get('user_id')
    if not user_id:
        return redirect('login')
        
    user = CustomUser.objects.filter(id=user_id).first()
    if not user:
        return redirect('login')
        
    # Check for rapid dashboard reloads (spam/bot detection)
    one_min_ago = timezone.now() - timedelta(minutes=1)
    recent_requests = ActivityLog.objects.filter(
        user_email=user.email,
        action='dashboard access',
        timestamp__gte=one_min_ago
    ).count()
    
    is_suspicious_activity = recent_requests >= 3
    ActivityLog.objects.create(user_email=user.email, action='dashboard access', is_suspicious=is_suspicious_activity)
    
    # Fetch data for admin dashboard UI
    all_users = CustomUser.objects.all().order_by('-created_at')
    login_logs = LoginLog.objects.all().order_by('-login_time')[:50]
    activity_logs = ActivityLog.objects.all().order_by('-timestamp')[:50]
    
    # Enrich login logs with user names
    login_logs_with_names = []
    for log in login_logs:
        user_obj = CustomUser.objects.filter(email=log.email).first()
        if user_obj:
            log.user_name = f"{user_obj.first_name} {user_obj.last_name}".strip() or user_obj.email
        else:
            log.user_name = log.email
        login_logs_with_names.append(log)
    
    # Enrich activity logs with user names
    activity_logs_with_names = []
    for log in activity_logs:
        user_obj = CustomUser.objects.filter(email=log.user_email).first()
        if user_obj:
            log.user_name = f"{user_obj.first_name} {user_obj.last_name}".strip() or user_obj.email
        else:
            log.user_name = log.user_email
        activity_logs_with_names.append(log)
    
    total_users = all_users.count()
    total_login_attempts = LoginLog.objects.count()
    total_suspicious_logins = LoginLog.objects.filter(is_suspicious=True).count()
    total_activities = ActivityLog.objects.count()
    total_suspicious_activities = ActivityLog.objects.filter(is_suspicious=True).count()
    
    # Alert System Logic
    alerts = []
    if CustomUser.objects.filter(risk_level='High Risk').exists():
        alerts.append("High risk user detected")
    if total_suspicious_logins > 0:
        alerts.append("Multiple suspicious logins detected")
    if total_suspicious_activities > 0:
        alerts.append("Spam activity detected")

    context = {
        'user': user,
        'user_full_name': f"{user.first_name} {user.last_name}".strip() or user.email,
        'all_users': all_users,
        'login_logs': login_logs_with_names,
        'activity_logs': activity_logs_with_names,
        'total_users': total_users,
        'total_login_attempts': total_login_attempts,
        'total_suspicious_logins': total_suspicious_logins,
        'total_activities': total_activities,
        'total_suspicious_activities': total_suspicious_activities,
        'alerts': alerts,
    }
        
    return render(request, 'myapp/dashboard.html', context)



def suspicious_activity_view(request):
    return redirect('dashboard')


def login_attempts_view(request):
    return redirect('dashboard')


def risk_analysis_view(request):
    return redirect('dashboard')


def alerts_view(request):
    return redirect('dashboard')


def users_view(request):
    return redirect('dashboard')


def reports_view(request):
    return redirect('dashboard')


def forgot_password_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        
        user = CustomUser.objects.filter(email=email).first()
        if not user:
            # Don't reveal if user exists or not, but don't send OTP either
            return render(request, 'myapp/forgot_password.html', {'error': 'If this email exists, an OTP will be sent.'})
            
        if user.blocked_until and timezone.now() < user.blocked_until:
             return render(request, 'myapp/forgot_password.html', {'error': 'Account temporarily frozen due to suspicious activity. Try again after 48 hours.'})
             
        # Generate 6-digit OTP
        otp_code = str(random.randint(100000, 999999))
        OTP.objects.create(email=email, otp=otp_code)
        
        # DEBUG: Print OTP in console
        print("FORGOT PASSWORD OTP SENDING TO:", email)
        print("OTP:", otp_code)
        
        request.session['reset_email'] = email
        request.session['reset_flow'] = True
        request.session['reset_otp_attempts'] = 0
        
        send_mail(
            subject="Password Reset OTP",
            message=f"Your password reset OTP is {otp_code}",
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[email],
            fail_silently=False,
        )
        
        return redirect('verify_reset_otp')
        
    # Auto-fill email if passed in query param, though not strictly required
    email_autofill = request.GET.get('email', '')
    return render(request, 'myapp/forgot_password.html', {'email': email_autofill})

def verify_reset_otp_view(request):
    email = request.session.get('reset_email')
    if not email or not request.session.get('reset_flow'):
        return redirect('login')
        
    if request.method == 'POST':
        entered_otp = request.POST.get('otp')
        latest_otp = OTP.objects.filter(email=email).order_by('-created_at').first()
        
        if latest_otp:
            time_diff = timezone.now() - latest_otp.created_at
            if time_diff.total_seconds() > 60:
                return render(request, 'myapp/verify_otp.html', {'error': 'OTP expired. Please request a new one.', 'email': email})
                
            if latest_otp.otp == entered_otp:
                request.session['reset_otp_verified'] = True
                return redirect('reset_password')
            else:
                attempts = request.session.get('reset_otp_attempts', 0) + 1
                request.session['reset_otp_attempts'] = attempts
                
                if attempts >= 3:
                    # Freeze account
                    user = CustomUser.objects.filter(email=email).first()
                    if user:
                        user.is_blocked = True
                        user.blocked_until = timezone.now() + timedelta(hours=48)
                        user.risk_level = 'High Risk'
                        user.save()
                        
                        ActivityLog.objects.create(user_email=email, action='failed password reset', is_suspicious=True)
                        
                        # Send security email
                        send_mail(
                            subject="SECURITY ALERT: Account Temporarily Frozen",
                            message=f"Dear User,\n\nWe detected suspicious activity on your account. There were multiple invalid OTP attempts during a password reset request.\n\nFor your security, your account has been frozen for 48 hours. Login has been disabled temporarily.\n\nIf you did not request this, please contact support.\n\nRegards,\nSecurity Team",
                            from_email=settings.EMAIL_HOST_USER,
                            recipient_list=[email],
                            fail_silently=False,
                        )
                        
                    # Clear session
                    request.session.pop('reset_email', None)
                    request.session.pop('reset_flow', None)
                    request.session.pop('reset_otp_attempts', None)
                    
                    return render(request, 'myapp/login.html', {'error': 'Account frozen for 48 hours due to multiple failed OTP attempts.'})
                    
                return render(request, 'myapp/verify_otp.html', {'error': f'Invalid OTP. Attempts left: {3 - attempts}', 'email': email})
        else:
            return render(request, 'myapp/verify_otp.html', {'error': 'No OTP found.', 'email': email})
            
    # Need to render a page similar to verify_otp but post goes to verify_reset_otp
    # Reusing verify_otp.html works because action URL can be overridden in the template or if not, it uses current URL
    return render(request, 'myapp/verify_otp.html', {'email': email})

def reset_password_view(request):
    email = request.session.get('reset_email')
    if not email or not request.session.get('reset_otp_verified'):
        return redirect('login')
        
    if request.method == 'POST':
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        
        if password != confirm_password:
             return render(request, 'myapp/reset_password.html', {'error': 'Passwords do not match.'})
             
        user = CustomUser.objects.filter(email=email).first()
        if user:
            user.password = hash_password(password)
            user.save()
            ActivityLog.objects.create(user_email=email, action='password reset successful', is_suspicious=False)
            
        request.session.pop('reset_email', None)
        request.session.pop('reset_flow', None)
        request.session.pop('reset_otp_verified', None)
        request.session.pop('reset_otp_attempts', None)
        
        return render(request, 'myapp/login.html', {'error': 'Password reset successful. Please login.'}) # Using error block for success message in login as hack
        
    return render(request, 'myapp/reset_password.html')
