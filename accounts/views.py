from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm, ProfileForm
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login

# Create your views here.
def register(request):
    if request.method == "POST":
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # بعد از ثبت‌نام، کاربر لاگین می‌شود
            return redirect("home")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/register.html", {"form": form})

@login_required
def profile_view(request):
    profile = request.user.profile  # دسترسی به پروفایل کاربر
    if request.method == "POST":
        form = ProfileForm(request.POST,request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect("profile")
    else:
        form = ProfileForm(instance=profile)
    return render(request, "accounts/profile.html", {"form": form})

