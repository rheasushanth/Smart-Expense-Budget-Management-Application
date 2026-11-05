from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.contrib import messages
from .forms import RegistrationForm
from .forms import ProfileForm
from datetime import timedelta
from django.utils import timezone
from accounts.models import User, SecurityEvent
from accounts.security import log_security_event

def register(request):
    if request.user.is_authenticated:
        return redirect("home")

    if request.method == "POST":
        form = RegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            return redirect("login")
    else:
        form = RegistrationForm()

    return render(request, "accounts/register.html", {"form": form})

def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email", "").strip()
        password = request.POST.get("password", "")
        now = timezone.now()

        user_record = User.objects.filter(email__iexact=email).first()

        # Clear a lockout that has already run its course, so the attempt
        # below is judged on the credentials alone.
        if (
            user_record
            and user_record.locked_until
            and user_record.locked_until <= now
        ):
            user_record.failed_login_attempts = 0
            user_record.locked_until = None
            user_record.failed_login_window_started_at = None
            user_record.save(update_fields=[
                "failed_login_attempts",
                "locked_until",
                "failed_login_window_started_at",
            ])

        user = authenticate(
            request,
            email=email,
            password=password,
        )

        # The lock is enforced after authentication, and the reason is given
        # only to someone who supplied the correct password. Answering a
        # wrong password with "account locked" would tell an attacker which
        # email addresses are registered (SEC-002, SRS 5.1.2).
        if (
            user is not None
            and user_record
            and user_record.locked_until
            and user_record.locked_until > now
        ):
            messages.error(
                request,
                "Account temporarily locked. Please try again later."
            )
            return render(request, "accounts/login.html")

        if user is not None:
            user.failed_login_attempts = 0
            user.locked_until = None
            user.failed_login_window_started_at = None
            user.save(update_fields=[
                "failed_login_attempts",
                "locked_until",
                "failed_login_window_started_at",
            ])

            login(request, user)
            return redirect("home")

        # Record failed login for an identifiable account.
        if user_record:
            window_start = user_record.failed_login_window_started_at

            if (
                window_start is None
                or now - window_start >= timedelta(minutes=10)
            ):
                user_record.failed_login_attempts = 0
                user_record.failed_login_window_started_at = now

            user_record.failed_login_attempts += 1

            log_security_event(
                SecurityEvent.EventType.FAILED_LOGIN,
                "Failed login attempt.",
                request=request,
                user=user_record,
                email=email,
            )

            if user_record.failed_login_attempts >= 5:
                user_record.locked_until = now + timedelta(minutes=10)

                log_security_event(
                    SecurityEvent.EventType.ACCOUNT_LOCKED,
                    "Account locked after five failed login attempts.",
                    request=request,
                    user=user_record,
                    email=email,
                )

            user_record.save(update_fields=[
                "failed_login_attempts",
                "failed_login_window_started_at",
                "locked_until",
            ])

        else:
            # Also log attempts using unknown email addresses.
            log_security_event(
                SecurityEvent.EventType.FAILED_LOGIN,
                "Failed login attempt for an unknown email address.",
                request=request,
                email=email,
            )

        messages.error(request, "Invalid email or password.")

    return render(request, "accounts/login.html")

@login_required
def profile_view(request):
    if request.method == "POST":
        form = ProfileForm(request.POST, instance=request.user)

        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect("profile")
    else:
        form = ProfileForm(instance=request.user)

    return render(
        request,
        "accounts/profile.html",
        {"form": form},
    )


@login_required
def logout_view(request):
    if request.method == "POST":
        logout(request)
        messages.success(request, "You have logged out successfully.")
        return redirect("login")

    return redirect("profile")