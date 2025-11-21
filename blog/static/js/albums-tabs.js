/* blog/static/js/albums-tabs.js */
document.addEventListener('DOMContentLoaded', function () {
    // تنظیمات: انتظار می‌رود AJAX_ALBUM_URL_TEMPLATE توسط template تعریف شده باشد،
    // مثلاً: const AJAX_ALBUM_URL_TEMPLATE = "/ajax/album-images/0/";
    if (typeof AJAX_ALBUM_URL_TEMPLATE === 'undefined') {
        console.warn('AJAX_ALBUM_URL_TEMPLATE is not defined - albums AJAX will not work.');
    }

    // تب‌ها
    const tabsNav = document.getElementById('albums-tabs-nav');
    const tabsContent = document.getElementById('albums-tabs-content');
    if (!tabsNav || !tabsContent) return;

    // کنترل‌های بالا
    const btnPrev = document.getElementById('tabs-prev');
    const btnPlayPause = document.getElementById('tabs-playpause');
    const btnNext = document.getElementById('tabs-next');

    let currentIndex = 0;
    let autoPlayInterval = null;
    let isPlaying = false;
    const TAB_AUTOPLAY_DELAY = 4000;

    function activateTab(index) {
        const navButtons = Array.from(tabsNav.querySelectorAll('.nav-link'));
        const panes = Array.from(tabsContent.querySelectorAll('.tab-pane'));

        navButtons.forEach((b, i) => {
            b.classList.toggle('active', i === index);
            b.setAttribute('aria-selected', i === index ? 'true' : 'false');
        });
        panes.forEach((p, i) => {
            p.classList.toggle('active', i === index);
            p.classList.toggle('show', i === index);
        });

        currentIndex = index;
    }

    function prevTab() {
        const count = tabsNav.querySelectorAll('.nav-link').length;
        activateTab((currentIndex - 1 + count) % count);
    }
    function nextTab() {
        const count = tabsNav.querySelectorAll('.nav-link').length;
        activateTab((currentIndex + 1) % count);
    }
    function togglePlayPause() {
        if (isPlaying) {
            clearInterval(autoPlayInterval);
            autoPlayInterval = null;
            isPlaying = false;
            btnPlayPause.textContent = 'پخش';
            btnPlayPause.setAttribute('aria-pressed', 'false');
        } else {
            autoPlayInterval = setInterval(nextTab, TAB_AUTOPLAY_DELAY);
            isPlaying = true;
            btnPlayPause.textContent = 'توقف';
            btnPlayPause.setAttribute('aria-pressed', 'true');
        }
    }

    // وصل کردن دکمه‌ها
    if (btnPrev) btnPrev.addEventListener('click', prevTab);
    if (btnNext) btnNext.addEventListener('click', nextTab);
    if (btnPlayPause) {
        btnPlayPause.addEventListener('click', function () {
            togglePlayPause();
        });
    }

    // وقتی روی یک nav-tab کلیک شد، آن را فعال کن
    Array.from(tabsNav.querySelectorAll('.nav-link')).forEach(btn => {
        btn.addEventListener('click', function () {
            const idx = parseInt(btn.getAttribute('data-index') || 0, 10);
            activateTab(idx);
        });
    });

    // هر تب باید یک دکمه "بیشتر" مستقل داشته باشد و لینک آن به صفحهٔ دستهٔ مربوطه برود.
    // درون هر tab-pane فرض می‌کنیم المان با کلاس .tab-more وجود دارد (اگر نبود باید template را اصلاح کنیم).

    // ---------- MODAL HANDLING ----------
    const albumModalEl = document.getElementById('albumModal');
    let bsAlbumModal = null;
    if (albumModalEl && typeof bootstrap !== 'undefined') {
        bsAlbumModal = new bootstrap.Modal(albumModalEl, { keyboard: true });
    }

    function fillAlbumModal(data) {
        // data: { title, desc, images: [{url, alt}], category_slug (optional) }
        const titleEl = document.getElementById('albumModalTitle');
        const descEl = document.getElementById('albumModalDesc');
        const inner = document.getElementById('albumCarouselInner');
        const moreBtn = document.getElementById('albumModalMore');

        if (titleEl) titleEl.textContent = data.title || '';
        if (descEl) descEl.textContent = data.desc || '';

        if (inner) {
            inner.innerHTML = '';
            if (Array.isArray(data.images) && data.images.length) {
                data.images.forEach((img, i) => {
                    const item = document.createElement('div');
                    item.className = 'carousel-item' + (i === 0 ? ' active' : '');
                    const imageEl = document.createElement('img');
                    imageEl.className = 'd-block w-100';
                    imageEl.style.maxHeight = '60vh';
                    imageEl.style.objectFit = 'contain';
                    imageEl.alt = img.alt || data.title || '';
                    imageEl.src = img.url;
                    item.appendChild(imageEl);
                    inner.appendChild(item);
                });
            } else {
                // نمایش تصویر fallback (لوگو یا placeholder)
                const item = document.createElement('div');
                item.className = 'carousel-item active';
                const p = document.createElement('div');
                p.className = 'p-4 text-center text-muted';
                p.textContent = 'تصویری برای نمایش وجود ندارد.';
                item.appendChild(p);
                inner.appendChild(item);
            }
        }

        if (moreBtn) {
            if (data.category_slug) {
                // لینک امن: only if slug not empty
                moreBtn.href = `/category/${encodeURIComponent(data.category_slug)}/`;
                moreBtn.style.display = '';
            } else {
                moreBtn.href = '#';
                moreBtn.style.display = 'none';
            }
        }

        // باز کردن مودال
        if (bsAlbumModal) bsAlbumModal.show();
    }

    // المان‌های album-open در هر کارت باید data-album-id و data-album-title و data-category-slug (optional) داشته باشند.
    function attachAlbumOpenButtons(scope) {
        const opens = (scope || document).querySelectorAll('.album-open, .open-album');
        opens.forEach(btn => {
            if (btn.__albumAttached) return;
            btn.__albumAttached = true;
            btn.addEventListener('click', function (e) {
                e.preventDefault();
                const albumId = btn.getAttribute('data-album-id') || btn.dataset.albumId;
                const title = btn.getAttribute('data-album-title') || btn.dataset.albumTitle || '';
                const desc = btn.getAttribute('data-album-desc') || btn.dataset.albumDesc || '';
                const categorySlug = btn.getAttribute('data-category-slug') || btn.dataset.categorySlug || '';

                // اگر AJAX url موجود است از آن استفاده کن
                if (typeof AJAX_ALBUM_URL_TEMPLATE !== 'undefined' && albumId) {
                    const u = AJAX_ALBUM_URL_TEMPLATE.replace(/0\/?$/, albumId + '/');
                    fetch(u, {
                        method: 'GET',
                        headers: { 'X-Requested-With': 'XMLHttpRequest' }
                    })
                        .then(resp => {
                            if (!resp.ok) throw new Error('Network error');
                            return resp.json();
                        })
                        .then(json => {
                            // انتظار: json = { images: [{url, alt}], title, desc, category_slug }
                            fillAlbumModal({
                                title: json.title || title,
                                desc: json.desc || desc,
                                images: json.images || [],
                                category_slug: json.category_slug || categorySlug
                            });
                        })
                        .catch(err => {
                            console.error(err);
                            // fallback: باز کردن مودال با تنها متن
                            fillAlbumModal({ title: title, desc: desc, images: [], category_slug: categorySlug });
                        });
                } else {
                    // fallback بدون AJAX
                    fillAlbumModal({ title: title, desc: desc, images: [], category_slug: categorySlug });
                }
            });
        });
    }

    // attach initial
    attachAlbumOpenButtons(document);

    // اگر بصورت AJAX محتوا جایگزین شود، دوباره متصل کن
    // یک لیسنر کلی برای click روی المان‌هایی که ممکن است بعدا اضافه شوند:
    document.addEventListener('click', function (e) {
        const t = e.target.closest && e.target.closest('.album-open, .open-album');
        if (t) {
            // handled by per-button listener if attached; if not, attach then trigger
            if (!t.__albumAttached) {
                attachAlbumOpenButtons(t.parentElement || document);
                t.click();
            }
        }
    });

    // در صورت بسته شدن مودال، carousel را به حالت اول برگردان
    if (albumModalEl) {
        albumModalEl.addEventListener('hidden.bs.modal', function () {
            const inner = document.getElementById('albumCarouselInner');
            if (inner) inner.innerHTML = '';
        });
    }
});
