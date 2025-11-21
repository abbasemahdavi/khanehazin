# -*- coding: utf-8 -*-
"""
Created on Fri Sep 26 16:00:22 2025

@author: Abbas Mahdavi
"""

from django.urls import path
from .import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/",auth_views.LoginView.as_view(template_name="accounts/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="post_list"), name="logout"),
    path("profile/", views.profile_view, name="profile"),
]
