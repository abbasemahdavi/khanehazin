# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 17:05:06 2025

@author: Abbas Mahdavi
"""

# blog/models.py
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
import django_jalali.db.models as jmodels
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.text import slugify
from django.utils.html import strip_tags
from django.conf import settings
import secrets
from ckeditor.fields import RichTextField

# ========================
# Category
# ========================
class Category(models.Model):
    name = models.CharField(_('نام دسته‌بندی'), max_length=200, unique=True)
    slug = models.SlugField(_('نامک (slug)'), max_length=200, unique=True, blank=True, allow_unicode=True)
    description = models.TextField(_('توضیحات'), blank=True)
    seo_title = models.CharField(_('عنوان سئو'), max_length=200, blank=True)
    seo_description = models.CharField(_('توضیحات سئو'), max_length=300, blank=True)

    class Meta:
        verbose_name = _("دسته‌بندی")
        verbose_name_plural = _("دسته‌بندی‌ها")
        ordering = ['name']

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base = slugify(self.name or '', allow_unicode=True) or f'cat-{int(timezone.now().timestamp())}'
            slug_candidate = base
            counter = 1
            qs = Category.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base}-{counter}"
                counter += 1
            self.slug = slug_candidate
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """
        مسیر لیست آلبوم‌ها برای این دسته (page with category albums).
        """
        try:
            return reverse('blog:category_albums', args=[self.slug])
        except Exception:
            return '#'


# ========================
# Post
# ========================
class Post(models.Model):
    title = models.CharField(_('عنوان'), max_length=200)
    slug = models.SlugField(_('نامک (slug)'), max_length=220, unique=True, blank=True, allow_unicode=True)
    content = models.TextField(_('متن'))
    short_description = models.CharField(_('خلاصه'), max_length=300, blank=True)
    featured_image = models.ImageField(_('عکس شاخص'), upload_to='posts/featured/', null=True, blank=True)
    code = models.CharField(_('کد یکتا'), max_length=6, unique=True, blank=True, null=True, db_index=True)
    updated_at = models.DateTimeField(_('به‌روز رسانی'), auto_now=True)
    created_at = jmodels.jDateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('نویسنده'), on_delete=models.CASCADE, default=1)
    categories = models.ManyToManyField(Category, blank=True, related_name='posts', verbose_name=_('دسته‌ها'))
    cover = models.ImageField(upload_to='posts/covers/', blank=True, null=True)
    title = models.CharField(max_length=255)
    summary = models.TextField(blank=True, null=True)
    content = RichTextField()

    class Meta:
        verbose_name = _("پست")
        verbose_name_plural = _("پست‌ها")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    # -------- Helpers ----------
    def _generate_slug_base(self):
        return slugify(self.title or '', allow_unicode=True) or f'post-{int(timezone.now().timestamp())}'

    def _get_unique_slug(self, base_slug):
        slug_candidate = base_slug
        counter = 1
        qs = Post.objects.all()
        if self.pk:
            qs = qs.exclude(pk=self.pk)
        while qs.filter(slug=slug_candidate).exists():
            slug_candidate = f"{base_slug}-{counter}"
            counter += 1
        return slug_candidate

    def _generate_unique_code(self):
        for _ in range(10):
            n = secrets.randbelow(10**6)
            code = str(n).zfill(6)
            if not Post.objects.filter(code=code).exists():
                return code
        while True:
            n = secrets.randbelow(10**6)
            code = str(n).zfill(6)
            if not Post.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        # پاک‌سازی متن پست
        if self.content:
            self.content = self.content.replace('&zwnj;', '\u200c').replace('&nbsp;', ' ')
        if not self.code:
            self.code = self._generate_unique_code()
        if not self.slug:
            self.slug = self._get_unique_slug(self._generate_slug_base())
        super().save(*args, **kwargs)

    @property
    def body(self):
        return self.content

# ========================
# Menu & MenuItem
# ========================
class Menu(models.Model):
    name = models.CharField(_('نام منو'), max_length=100, help_text=_("مثلاً 'main' یا 'footer'"))
    slug = models.SlugField(_('نامک منو'), max_length=120, unique=True)
    enabled = models.BooleanField(_('فعال'), default=True)

    class Meta:
        verbose_name = _("منو")
        verbose_name_plural = _("منوها")

    def __str__(self):
        return self.name


class MenuItem(models.Model):
    menu = models.ForeignKey(Menu, verbose_name=_('منو'), on_delete=models.CASCADE, related_name='items')
    parent = models.ForeignKey('self', verbose_name=_('والد'), on_delete=models.CASCADE, null=True, blank=True, related_name='children')
    title = models.CharField(_('عنوان'), max_length=200)
    url = models.CharField(_('آدرس (URL)'), max_length=500, blank=True)
    named_url = models.CharField(_('نام route'), max_length=200, blank=True)
    url_params = models.CharField(_('پارامترهای مسیر'), max_length=300, blank=True)
    order = models.PositiveSmallIntegerField(_('ترتیب'), default=0)
    show = models.BooleanField(_('نمایش'), default=True)
    icon = models.CharField(max_length=100, blank=True, null=True, help_text="مثلاً: 'bi bi-star-fill' برای Bootstrap Icons")

    class Meta:
        verbose_name = _("آیتم منو")
        verbose_name_plural = _("آیتم‌های منو")
        ordering = ['order']

    def __str__(self):
        return self.title

    def get_url(self):
        """
        برگرداندن URL مناسب برای تمپلیت:
        - اگر named_url تنظیم شده باشد تلاش به reverse زدن آن با پارامترهای خطی می‌کند.
        - در غیر این صورت اگر url پر شده باشد آن را بازمی‌گرداند.
        - در نهایت "#" باز می‌گردد.
        url_params: رشته‌ای مثل "pk=1,slug=abc" یا "1,abc" (اگر position-based).
        این متد تلاش می‌کند پارامترها را به صورت ساده اعمال کند. می‌توانید منطق را گسترش دهید.
        """
        if self.named_url:
            try:
                # تلاش اول: پارامترها به صورت position-based اگر تنها مقادیر جداشده باشند
                if self.url_params:
                    parts = [p.strip() for p in self.url_params.split(',') if p.strip()]
                    # اگر همه عددی بودند، تبدیل کن
                    args = []
                    kwargs = {}
                    # تشخیص سریع: اگر شامل '=' باشد فرض kwargs
                    if any('=' in p for p in parts):
                        for p in parts:
                            if '=' in p:
                                k, v = p.split('=', 1)
                                kwargs[k.strip()] = v.strip()
                    else:
                        args = parts
                    return reverse(self.named_url, args=args, kwargs=kwargs)
                else:
                    return reverse(self.named_url)
            except Exception:
                # fallback به url فیلد
                pass
        if self.url:
            return self.url
        return '#'


# ========================
# Album & AlbumImage
# ========================
class Album(models.Model):
    title = models.CharField(_('عنوان آلبوم'), max_length=200)
    slug = models.SlugField(_('نامک (slug)'), max_length=220, unique=True, blank=True, allow_unicode=True)
    code = models.CharField(_('کد آلبوم'), max_length=6, blank=True, null=True, unique=True, db_index=True)
    cover_image = models.ImageField(_('عکس شاخص'), upload_to='albums/covers/', null=True, blank=True)
    created_at = models.DateTimeField(_('تاریخ ایجاد'), auto_now_add=True)
    categories = models.ManyToManyField('blog.Category', blank=True, related_name='albums', verbose_name=_('دسته‌ها'))
    order_instructions = models.TextField(_('توضیحات سفارش'), blank=True)
    author = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name=_('نویسنده'), on_delete=models.CASCADE, default=1)

    class Meta:
        verbose_name = _("آلبوم")
        verbose_name_plural = _("آلبوم‌ها")
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    def _generate_unique_code(self):
        for _ in range(10):
            n = secrets.randbelow(10**6)
            code = str(n).zfill(6)
            if not Album.objects.filter(code=code).exists():
                return code
        while True:
            n = secrets.randbelow(10**6)
            code = str(n).zfill(6)
            if not Album.objects.filter(code=code).exists():
                return code

    def save(self, *args, **kwargs):
        if self.order_instructions:
            self.order_instructions = self.order_instructions.replace('&zwnj;', '\u200c').replace('&nbsp;', ' ')
        if not self.slug:
            base_slug = slugify(self.title, allow_unicode=True) or f'album-{int(timezone.now().timestamp())}'
            slug_candidate = base_slug
            counter = 1
            qs = Album.objects.all()
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            while qs.filter(slug=slug_candidate).exists():
                slug_candidate = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug_candidate
        if not self.code:
            self.code = self._generate_unique_code()

        super().save(*args, **kwargs)

        # قانون: اگر cover_image خالی بود، عکس اول آلبوم را تنظیم کن
        if not self.cover_image and self.images.exists():
            first_image = self.images.order_by('order', 'id').first()
            if first_image:
                self.cover_image = first_image.image
                super().save(update_fields=['cover_image'])

    @property
    def cover_url(self):
        try:
            return self.cover_image.url if self.cover_image else ''
        except Exception:
            return ''


class AlbumImage(models.Model):
    album = models.ForeignKey(Album, verbose_name=_('آلبوم'), on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(_('تصویر'), upload_to='albums/images/')
    caption = models.CharField(_('عنوان تصویر'), max_length=250, blank=True)
    order = models.PositiveSmallIntegerField(_('ترتیب'), default=0)

    class Meta:
        verbose_name = _("تصویر آلبوم")
        verbose_name_plural = _("تصاویر آلبوم")
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.album.title} - image #{self.order}"

    @property
    def image_url(self):
        try:
            return self.image.url if self.image else ''
        except Exception:
            return ''
# ========================
# SiteSetting / Footer / Ads
# ========================
# تنظیمات سایت
class SiteSetting(models.Model):
    site_name = models.CharField(_('نام سایت'), max_length=200, default=_('خانه‌آذین'))
    about_text = models.TextField(_('متن درباره'), blank=True)
    copyright_text = models.CharField(
        _('متن کپی‌رایت'),
        max_length=200,
        default='© ۱۴۰۴ خانه‌آذین'
    )

    class Meta:
        verbose_name = _("تنظیمات سایت")
        verbose_name_plural = _("تنظیمات سایت")

    def __str__(self):
        return self.site_name or _("تنظیمات سایت")


# لینک‌های فوتر
class FooterLink(models.Model):
    site = models.ForeignKey(
        SiteSetting, verbose_name=_('سایت'),
        on_delete=models.CASCADE,
        related_name='footer_links',
        null=True, blank=True
    )
    title = models.CharField(_('عنوان لینک'), max_length=200)
    url = models.CharField(_('نشانی (URL)'), max_length=500)
    order = models.PositiveSmallIntegerField(_('ترتیب نمایش'), default=0)
    show = models.BooleanField(_('نمایش'), default=True)

    class Meta:
        verbose_name = _("لینک فوتر")
        verbose_name_plural = _("لینک‌های فوتر")
        ordering = ['order']

    def __str__(self):
        return self.title


# آیکون‌های فوتر
class FooterIcon(models.Model):
    site = models.ForeignKey(SiteSetting, verbose_name=_('سایت'), on_delete=models.CASCADE, related_name='footer_icons', null=True, blank=True)
    title = models.CharField(_('عنوان آیکون'), max_length=100)
    image = models.ImageField(_('آیکون'), upload_to='footer/icons/', blank=True, null=True)
    url = models.CharField(_('نشانی (URL)'), max_length=500, blank=True)
    icon_class = models.CharField(_('کلاس آیکون (مثل bootstrap)') , max_length=200, blank=True)
    html = models.TextField(_('HTML دلخواه'), blank=True)
    order = models.PositiveSmallIntegerField(_('ترتیب'), default=0)
    show = models.BooleanField(_('نمایش'), default=True)

    class Meta:
        verbose_name = _("آیکون فوتر")
        verbose_name_plural = _("آیکون‌های فوتر")
        ordering = ['order']

    def __str__(self):
        return self.title
    
class FooterSetting(models.Model):
    about_text = models.TextField("متن درباره", default="خانه‌آذین پلتفرمی برای معرفی محصولات و نمونه‌کارها.")
    copyright_text = models.CharField("متن کپی‌رایت", max_length=255,
                                      default="© ۱۴۰۴ خانه‌آذین :: طراح: عباس مهدوی")

    def __str__(self):
        return "تنظیمات فوتر"

# ========================
# Advertising
# ========================
class Ad(models.Model):
    GROUP_HEADER = 'header'
    GROUP_MAIN = 'main'
    GROUP_SIDEBAR = 'sidebar'
    GROUP_CHOICES = [
        (GROUP_HEADER, _('هدر (Header)')),
        (GROUP_MAIN, _('بنر اصلی / بالای فوتر (Main banner)')),
        (GROUP_SIDEBAR, _('ستون چپ (Sidebar left)')),
    ]
    name = models.CharField(_('نام آگهی'), max_length=200)
    group = models.CharField(_('گروه آگهی'), max_length=20, choices=GROUP_CHOICES, db_index=True)
    image = models.ImageField(_('عکس (اختیاری)'), upload_to='ads/images/', null=True, blank=True)
    link_url = models.CharField(_('لینک مقصد (اختیاری)'), max_length=500, blank=True)
    external_code = models.TextField(_('کد خارجی (HTML/JS، اختیاری)'), blank=True)
    is_active = models.BooleanField(_('فعال'), default=True)
    start_date = models.DateTimeField(_('شروع نمایش'), null=True, blank=True)
    end_date = models.DateTimeField(_('پایان نمایش'), null=True, blank=True)
    max_impressions = models.PositiveIntegerField(_('حداکثر نمایش (بار)'), null=True, blank=True)
    impressions_count = models.PositiveIntegerField(_('تعداد نمایش فعلی'), default=0, editable=False)
    clicks_count = models.PositiveIntegerField(_('تعداد کلیک‌ها'), default=0, editable=False)
    created_at = jmodels.jDateTimeField(_('ایجاد شده در'), auto_now_add=True)
    updated_at = jmodels.jDateTimeField(_('به‌روز شده در'), auto_now=True)

    class Meta:
        verbose_name = _("آگهی")
        verbose_name_plural = _("آگهی‌ها")
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_group_display()})"

    def is_currently_active(self):
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date and now < self.start_date:
            return False
        if self.end_date and now > self.end_date:
            return False
        if self.max_impressions and self.impressions_count >= self.max_impressions:
            return False
        return True


class AdView(models.Model):
    ad = models.ForeignKey(Ad, verbose_name=_('آگهی'), on_delete=models.CASCADE, related_name='views')
    ip_address = models.CharField(_('IP بازدیدکننده'), max_length=45, blank=True, db_index=True)
    created_at = jmodels.jDateTimeField(_('زمان بازدید'), auto_now_add=True)

    class Meta:
        verbose_name = _("بازدید آگهی")
        verbose_name_plural = _("بازدیدهای آگهی")
        ordering = ['-created_at']


class AdClick(models.Model):
    ad = models.ForeignKey(Ad, verbose_name=_('آگهی'), on_delete=models.CASCADE, related_name='clicks')
    ip_address = models.CharField(_('IP کلیک‌کننده'), max_length=45, blank=True, db_index=True)
    created_at = jmodels.jDateTimeField(_('زمان کلیک'), auto_now_add=True)

    class Meta:
        verbose_name = _("کلیک آگهی")
        verbose_name_plural = _("کلیک‌های آگهی")
        ordering = ['-created_at']

def short_summary(self, length=200, preserve_words=True):
    """
    Return a clean short summary up to `length` characters.
    - If `summary` (یا short_description) exists, use it.
    - Otherwise strip HTML from `content` and truncate.
    - If preserve_words=True، تا آخرین فاصله قبل از بریدن قطع می‌کند (نه داخل کلمه).
    """
    # اولویت: خلاصهٔ صریح (summary) سپس short_description
    text = (self.summary or self.short_description or '') if hasattr(self, 'summary') or hasattr(self, 'short_description') else ''
    if not text:
        text = strip_tags(getattr(self, 'content', '') or '')

    text = text.strip()

    if len(text) <= length:
        return text

    if not preserve_words:
        return text[:length].rstrip() + "…"

    # preserve last full word (avoid breaking mid-word)
    truncated = text[:length].rstrip()
    # اگر کاراکتر بعدی فاصله نیست سعی کن تا آخرین فاصله برگردی
    last_space = truncated.rfind(' ')
    if last_space > max(0, int(length * 0.4)):  # اگر فاصلهٔ معقولی یافت شد (اجتناب از خیلی کوتاه شدن)
        truncated = truncated[:last_space]
    return truncated.rstrip() + "…"

# property دسترسی سریع برای ۲۰۰ کاراکتر (قابل صدا زدن در تمپلیت: {{ post.short_summary }})
@property
def short_summary_200(self):
    return self.short_summary(200, preserve_words=True)