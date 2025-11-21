document.addEventListener("DOMContentLoaded", function () {
    const iconInput = document.querySelector('#id_icon');
    if (!iconInput) return;

    // ایجاد پیش‌نمایش
    const preview = document.createElement('span');
    preview.style.marginLeft = '10px';
    iconInput.parentNode.appendChild(preview);

    function updatePreview() {
        const val = iconInput.value.trim();
        if (val) {
            preview.innerHTML = `<i class="${val}" style="font-size: 1.2rem;"></i>`;
        } else {
            preview.innerHTML = '';
        }
    }

    // به‌روزرسانی پیش‌نمایش وقتی input تغییر می‌کند
    iconInput.addEventListener('input', updatePreview);
    updatePreview();  // بارگذاری اولیه
});
