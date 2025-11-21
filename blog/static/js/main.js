document.addEventListener("DOMContentLoaded", function () {
    // ---- نمایش مودال Bootstrap ----
    const modalTriggerButtons = document.querySelectorAll("[data-bs-toggle='modal']");
    modalTriggerButtons.forEach(btn => {
        btn.addEventListener("click", function (e) {
            const targetId = btn.getAttribute("data-bs-target");
            const modalEl = document.querySelector(targetId);
            if (modalEl) {
                const modal = new bootstrap.Modal(modalEl);
                modal.show();
            }
        });
    });

    // ---- بهبود لینک‌ها برای جلوگیری از ارور 404 ----
    document.querySelectorAll("a").forEach(link => {
        link.addEventListener("click", function (e) {
            const href = this.getAttribute("href");
            // فقط اگر لینک # نیست
            if (href && href.startsWith("#")) {
                e.preventDefault();
                const target = document.querySelector(href);
                if (target) target.scrollIntoView({ behavior: "smooth" });
            }
        });
    });

