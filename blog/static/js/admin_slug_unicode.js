// static/blog/js/admin_slug_unicode.js
(function () {
    "use strict";

    // تولید slug که حروف یونیکد (مثل فارسی) را نگه می‌دارد.
    // نکته: از Unicode property escapes استفاده شده؛ مرورگرهای مدرن پشتیبانی می‌کنند.
    function uniSlugify(s) {
        if (!s) return "";
        // حذف فاصله‌های انتها و ابتدا
        s = s.trim();

        // تبدیل چند فاصله به یک خط تیره
        s = s.replace(/\s+/g, "-");

        // حذف کاراکترهای نامعتبر: فقط حروف (Unicode), اعداد، - و _
        // requires modern browsers (Chrome, Firefox, Edge recent)
        try {
            s = s.replace(/[^\p{L}\p{N}\-_]+/gu, "");
        } catch (e) {
            // fallback: اگر regex بالا پشتیبانی نشد، فقط ASCII نامعتبر را بردار
            s = s.replace(/[^A-Za-z0-9\u0600-\u06FF\u0750-\u077F\-_]+/g, "");
        }

        // تبدیل به نیم‌فاصله یا تبدیل حروف بزرگ به کوچک برای ثبات (برای فارسی lowercase تفاوتی ندارد)
        return s.toLowerCase();
    }

    function initAutoSlug(titleId, slugId) {
        var titleEl = document.getElementById(titleId);
        var slugEl = document.getElementById(slugId);
        if (!titleEl || !slugEl) return;

        var userEdited = false;

        // اگر کاربر دستی slug را تغییر داد، دیگر اتومات را خاموش کن
        slugEl.addEventListener("input", function () {
            userEdited = true;
        });

        // وقتی تیتر تغییر می‌کند و کاربر slug را دستی تغییر نداده، slug بروز می‌شود
        titleEl.addEventListener("input", function () {
            if (userEdited) return;
            var newSlug = uniSlugify(titleEl.value);
            slugEl.value = newSlug;
        });

        // اگر صفحه بارگذاری می‌شود و slug خالی است، یکبار مقدار بگذار
        document.addEventListener("DOMContentLoaded", function () {
            if (!slugEl.value) {
                slugEl.value = uniSlugify(titleEl.value || "");
            }
        });
    }

    // همان id های استاندارد دَجانگو ادمین:
    document.addEventListener("DOMContentLoaded", function () {
        // برای فرم‌های معمولی مدل: title -> id_title , slug -> id_slug
        initAutoSlug("id_title", "id_slug");

        // اگر مدل شما title نامش متفاوت است (مثلاً 'name') می‌توانید اینجا اضافه کنید:
        initAutoSlug("id_name", "id_slug");
    });
})();
