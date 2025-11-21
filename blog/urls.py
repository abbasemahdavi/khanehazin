# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 17:05:06 2025

@author: Abbas Mahdavi
"""

# blog/urls.py
from django.urls import path
from . import views
from .views import user_dashboard

app_name = 'blog'

urlpatterns = [
    # صفحهٔ جستجو
    path('search/', views.search, name='search'),

    # مسیرهای مرتبط با آلبوم‌ها و AJAX
    path('ajax/album-images/<int:album_id>/', views.ajax_album_images, name='ajax_album_images'),
    path('album/<str:slug>/', views.album_detail, name='album_detail'),

    # دسته‌بندی
    path('category/<str:slug>/', views.category_albums, name='category_albums'),

    # داشبورد کاربر
    path('dashboard/', user_dashboard, name='user_dashboard'),

    # مسیرهای CRUD پست‌ها
    path('post/new/', views.post_list, name='post_new'),
    path('post/<int:pk>/edit/', views.post_edit, name='post_edit'),
    path('post/<int:pk>/delete/', views.post_delete, name='post_delete'),

    # --- مسیرهای مبتنی بر code (بدون کلمه "code" در آدرس) ---
    # مهم: اینها باید پیش از مسیرهای مبتنی بر pk قرار بگیرند تا هنگام کدهای عددی تداخلی پیش نیاید
    path('post/<str:code>/<str:slug>/', views.post_detail, name='object_by_code_with_slug'),
    path('post/<str:code>/', views.post_detail_by_code, name='object_by_code'),

    # نمایش پست با slug بر اساس pk (اگر لازم داری نگه دار)
    path('post/<int:pk>/<str:slug>/', views.post_detail, name='post_detail'),

    # نمایش پست فقط با pk (ریدایرکت به مسیر کامل بر اساس code)
    path('post/<int:pk>/', views.post_detail_by_id, name='post_detail_by_id'),

    # صفحهٔ اصلی (همیشه آخر)
    path('', views.post_list, name='post_list'),
    path('ajax/category/<slug:slug>/', views.category_albums, name='ajax_category_content'),  # یا نام دلخواه
    path('category/<slug:slug>/', views.category_albums, name='category_albums'),
]
