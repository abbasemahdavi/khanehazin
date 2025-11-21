# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 17:05:06 2025

@author: Abbas Mahdavi
"""
#blog\admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.admin import UserAdmin
from accounts.models import CustomUser
from .models import (
    Post, Album, AlbumImage,
    Ad, Category,
    Menu, MenuItem,
    SiteSetting, FooterLink, FooterIcon
)
from django.utils.html import format_html
from ckeditor_uploader.widgets import CKEditorUploadingWidget
from django import forms

def get_site_name():
    try:
        site = SiteSetting.objects.first()
        return site.site_name if site and site.site_name else "سایت"
    except:
        return "سایت"

try:
    site_name = SiteSetting.objects.first().site_name
except Exception:
    site_name = "سایت"

admin.site.site_header = f"مدیریت {site_name}"
admin.site.site_title = f"مدیریت {site_name}"
admin.site.index_title = "داشبورد مدیریت"
# -------------------------------
# 1️⃣ پست‌ها
# -------------------------------
class PostAdminForm(forms.ModelForm):
    # فیلد content با ادیتور CKEditor و آپلود مستقیم تصویر
    content = forms.CharField(
        label="محتوای پست",
        widget=CKEditorUploadingWidget()
    )

    class Meta:
        model = Post
        fields = '__all__'


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    form = PostAdminForm
    prepopulated_fields = {"slug": ("title",)}  # تولید خودکار نامک از عنوان

    list_display = ("title", "author", "created_at", "updated_at")
    list_filter = ("author", "categories", "created_at")
    search_fields = ("title", "content", "slug")
    readonly_fields = ("created_at", "updated_at")

    fieldsets = (
        ("اطلاعات پایه", {
            "fields": ("title", "slug", "summary")
        }),
        ("محتوا", {
            "fields": ("content",)
        }),
        ("سایر اطلاعات", {
            "fields": ("author", "categories", "created_at", "updated_at")
        }),
    )
    ordering = ("-created_at",)

# -------------------------------
# 2️⃣ آلبوم‌ها
# -------------------------------
class AlbumAdminForm(forms.ModelForm):
    order_instructions = forms.CharField(
        label="توضیحات سفارش",
        widget=CKEditorUploadingWidget(),
        required=False
    )

    class Meta:
        model = Album
        fields = ['title', 'code', 'order_instructions', 'categories', 'cover_image']

class AlbumImageInline(admin.TabularInline):
    model = AlbumImage
    extra = 10
    max_num = 10
    fields = ("image", "caption", "order")
    ordering = ("order",)

@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    form = AlbumAdminForm
    inlines = [AlbumImageInline]

    list_display = ("title", "code", "created_at")
    search_fields = ("title", "code")

    fieldsets = (
    ("اطلاعات آلبوم", {
        "fields": ("title", "code", "categories", "cover_image")
    }),
    ("توضیحات سفارش", {
        "fields": ("order_instructions",)
    }),
)

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        album = form.instance
        if not album.cover_image and album.images.exists():
            first_image = album.images.order_by('order', 'id').first()
            if first_image:
                album.cover_image = first_image.image
                album.save(update_fields=['cover_image'])


# -------------------------------
# 3️⃣ آگهی‌ها
# -------------------------------
class CurrentlyActiveAdFilter(admin.SimpleListFilter):
    title = 'وضعیت نمایش'
    parameter_name = 'active_status'

    def lookups(self, request, model_admin):
        return [('active', 'در حال نمایش'), ('inactive', 'غیرفعال یا منقضی')]

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return [ad for ad in queryset if ad.is_currently_active()]
        elif self.value() == 'inactive':
            return [ad for ad in queryset if not ad.is_currently_active()]
        return queryset

@admin.register(Ad)
class AdAdmin(admin.ModelAdmin):
    list_display = ("name", "group", "is_active", "start_date", "end_date", "created_at")
    list_filter = ("group", "is_active", CurrentlyActiveAdFilter)
    search_fields = ("name",)

# -------------------------------
# 4️⃣ دسته‌ها
# -------------------------------
@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    search_fields = ("name",)
    prepopulated_fields = {"slug": ("name",)}  # تولید خودکار نامک از نام دسته

# -------------------------------
# 5️⃣ منوها
# -------------------------------
@admin.register(Menu)
class MenuAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "enabled")
    prepopulated_fields = {"slug": ("name",)}  # تولید خودکار نامک از نام منو

@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("menu", "title", "order", "show", "icon_preview")
    list_filter = ("menu", "show")
    search_fields = ("title", "menu__name")

    def icon_preview(self, obj):
        if obj.icon:
            return format_html('<i class="{}" style="font-size:1.2rem;"></i>', obj.icon)
        return "-"
    icon_preview.short_description = "پیش‌نمایش آیکون"

    class Media:
        css = {'all': ('https://cdn.jsdelivr.net/npm/bootstrap-icons@1.11.1/font/bootstrap-icons.css',)}
        js = ('blog/js/icon_preview.js',)

# -------------------------------
# 6️⃣ تنظیمات سایت و فوتر
# -------------------------------
class FooterLinkInline(admin.TabularInline):
    model = FooterLink
    extra = 3
    ordering = ['order']

class FooterIconInline(admin.TabularInline):
    model = FooterIcon
    extra = 3
    ordering = ['order']
    fields = ("title", "image", "url", "icon_class", "html", "order", "show")

@admin.register(SiteSetting)
class SiteSettingAdmin(admin.ModelAdmin):
    list_display = ("site_name", "copyright_text")
    fields = ("site_name", "about_text", "copyright_text")
    inlines = [FooterLinkInline, FooterIconInline]

# -------------------------------
# 7️⃣ مدیریت کاربران
# -------------------------------
class ManagerFilter(admin.SimpleListFilter):
    title = 'نوع کاربر'
    parameter_name = 'manager'

    def lookups(self, request, model_admin):
        return (('manager', 'مدیر'),)

    def queryset(self, request, queryset):
        if self.value() == 'manager':
            return queryset.filter(is_staff=True)
        return queryset

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ("username", "email", "is_staff", "is_superuser", "is_active")
    list_filter = ("is_active", "is_staff", "is_superuser", ManagerFilter)
    search_fields = ("username", "email")
    ordering = ("username",)
    fieldsets = (
        (_("اطلاعات حساب"), {"fields": ("username", "password")}),
        (_("اطلاعات شخصی"), {"fields": ("first_name", "last_name", "email")}),
        (_("دسترسی‌ها"), {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        (_("تاریخ‌ها"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (_("افزودن مدیر جدید"), {
            "classes": ("wide",),
            "fields": ("username", "email", "password1", "password2", "is_staff", "is_superuser", "is_active"),
        }),
    )
