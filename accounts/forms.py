# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 15:57:10 2025

@author: Abbas Mahdavi
"""

from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from .models import CustomUser
from .models import Profile

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'phone_number', 'address')

class CustomAuthenticationForm(AuthenticationForm):
    pass

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "address", "bio", "avatar"]

