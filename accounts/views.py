from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib import messages

from .models import Profile


def register_view(request):

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirm_password")

        if password != confirm_password:
            messages.error(
                request,
                "Passwords do not match."
            )
            return redirect("register")

        if User.objects.filter(
            username=email
        ).exists():

            messages.error(
                request,
                "Email already registered."
            )
            return redirect("register")

        user = User.objects.create_user(
            username=email,
            email=email,
            password=password
        )

        Profile.objects.create(
            user=user,
            full_name=full_name
        )

        login(request, user)

        return redirect("home_views")

    return render(
        request,
        "accounts/register.html"
    )


def login_view(request):

    if request.method == "POST":

        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=email,
            password=password
        )

        if user is not None:

            login(request, user)

            return redirect("home_views")

        messages.error(
            request,
            "Invalid email or password."
        )

    return render(
        request,
        "accounts/login.html"
    )


def logout_view(request):

    logout(request)

    return redirect("login")


def profile_view(request):

    if not request.user.is_authenticated:
        return redirect("login")

    profile, created = Profile.objects.get_or_create(
        user=request.user,
        defaults={
            "full_name":
                request.user.get_full_name()
                or request.user.username
        }
    )

    if request.method == "POST":

        full_name = request.POST.get("full_name")
        photo = request.FILES.get("photo")

        profile.full_name = full_name

        if photo:
            profile.photo = photo

        profile.save()

        messages.success(
            request,
            "Profile updated successfully."
        )

        return redirect("profile")

    return render(
        request,
        "accounts/profile.html",
        {
            "profile": profile
        }
    )