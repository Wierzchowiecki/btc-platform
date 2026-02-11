from datetime import date, timedelta
import json
import secrets
import string

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.utils import timezone

from .models import BtcPrice, UserProfile


def home(request):
    return render(request, "core/home.html")


def login_page(request):
    """
    Flow:
    1) Generuj OTP:
        - jeśli user nie istnieje -> tworzymy User + Profile z client_id
        - zapisujemy otp + expiry
        - DEMO: pokazujemy OTP na stronie (później email/SMS)
    2) Zaloguj OTP:
        - sprawdzamy OTP
        - logujemy usera
        - jeśli must_set_password -> przekieruj do /set-password/
        - w przeciwnym razie -> /dashboard/
    """
    context = {}

    if request.method == "GET":
        return render(request, "core/login.html", context)

    username = (request.POST.get("login") or "").strip()
    otp_input = (request.POST.get("otp") or "").strip()

    # 1) Generuj OTP
    if "generate_otp" in request.POST:
        if not username:
            context["error"] = "Najpierw wpisz login."
            return render(request, "core/login.html", context)

        user, created = User.objects.get_or_create(username=username)

        profile, prof_created = UserProfile.objects.get_or_create(
            user=user,
            defaults={
                "client_id": UserProfile.generate_client_id(),
                "must_set_password": True,
            },
        )

        # Generujemy OTP 6 cyfr
        otp = "".join(secrets.choice(string.digits) for _ in range(6))
        profile.otp_code = otp
        profile.otp_expires_at = timezone.now() + timezone.timedelta(minutes=5)
        profile.save()

        context["login_prefill"] = username
        context["otp_demo"] = otp  # DEMO (później wyślemy email/SMS)
        context["info"] = "Wygenerowano OTP. Wpisz je i kliknij Zaloguj."
        return render(request, "core/login.html", context)

    # 2) Zaloguj OTP
    if "do_login" in request.POST:
        if not username:
            context["error"] = "Wpisz login."
            return render(request, "core/login.html", context)

        if not otp_input:
            context["error"] = "Wpisz OTP."
            context["login_prefill"] = username
            return render(request, "core/login.html", context)

        try:
            user = User.objects.get(username=username)
            profile = UserProfile.objects.get(user=user)
        except (User.DoesNotExist, UserProfile.DoesNotExist):
            context["error"] = "Najpierw wygeneruj OTP."
            context["login_prefill"] = username
            return render(request, "core/login.html", context)

        if not profile.otp_is_valid(otp_input):
            context["error"] = "OTP jest niepoprawne lub wygasło. Wygeneruj nowe."
            context["login_prefill"] = username
            return render(request, "core/login.html", context)

        # OTP jednorazowe: kasujemy po użyciu
        profile.otp_code = None
        profile.otp_expires_at = None
        profile.save()

        # Logowanie bez hasła (tylko po OTP) – na start OK
        user.backend = "django.contrib.auth.backends.ModelBackend"
        login(request, user)

        if profile.must_set_password:
            return redirect("set_password")

        return redirect("dashboard")

    return render(request, "core/login.html", context)


@login_required
def set_password(request):
    """
    Po OTP użytkownik ustawia własne hasło.
    """
    profile = UserProfile.objects.get(user=request.user)

    if request.method == "GET":
        return render(
            request,
            "core/set_password.html",
            {"client_id": profile.client_id},
        )

    password1 = request.POST.get("password1") or ""
    password2 = request.POST.get("password2") or ""

    if len(password1) < 6:
        return render(
            request,
            "core/set_password.html",
            {"client_id": profile.client_id, "error": "Hasło musi mieć min. 6 znaków."},
        )

    if password1 != password2:
        return render(
            request,
            "core/set_password.html",
            {"client_id": profile.client_id, "error": "Hasła nie są takie same."},
        )

    request.user.set_password(password1)
    request.user.save()

    profile.must_set_password = False
    profile.save()

    # po zmianie hasła trzeba zalogować ponownie
    user = authenticate(username=request.user.username, password=password1)
    if user:
        login(request, user)

    return redirect("dashboard")


@login_required
def dashboard(request):
    profile = UserProfile.objects.get(user=request.user)
    return render(request, "core/dashboard.html", {"client_id": profile.client_id, "login": request.user.username})


@login_required
def bitcoin(request):
    five_years_ago = date.today() - timedelta(days=365 * 5)

    qs = (
        BtcPrice.objects
        .filter(date__gte=five_years_ago)
        .order_by("date")
    )

    dates = [x.date.isoformat() for x in qs]
    prices = [float(x.price_pln) for x in qs]

    return render(
        request,
        "core/bitcoin.html",
        {"dates_json": json.dumps(dates), "prices_json": json.dumps(prices)},
    )


@login_required
def insurance(request):
    return render(request, "core/insurance.html")


def logout_view(request):
    logout(request)
    return redirect("home")
