// static/js/album-modal.js
document.addEventListener('DOMContentLoaded', function () {
    // مسیر AJAX از قالب (با reverse ساخته شود)
    const templateVar = window.AJAX_ALBUM_IMAGES_URL_TEMPLATE || window.AJAX_ALBUM_URL_TEMPLATE || null;

    function getAjaxUrl(albumId) {
        if (templateVar) {
            if (templateVar.indexOf('{album_id}') !== -1) {
                return templateVar.replace('{album_id}', encodeURIComponent(albumId));
            }
            if (templateVar.indexOf('/0/') !== -1) {
                return templateVar.replace('/0/', '/' + encodeURIComponent(albumId) + '/');
            }
        }
        return '/ajax/album-images/' + encodeURIComponent(albumId) + '/';
    }

    const modalEl = document.getElementById('albumModal');
    if (!modalEl || typeof window.bootstrap === 'undefined') {
        console.warn('album-modal: modal element یا bootstrap موجود نیست.');
        return;
    }

    const albumModal = new bootstrap.Modal(modalEl, { backdrop: true, keyboard: true });
    const carouselInner = modalEl.querySelector('#albumCarouselInner');
    const albumModalTitle = modalEl.querySelector('#albumModalTitle');
    const albumModalDesc = modalEl.querySelector('#albumModalDesc');
    const albumModalMore = modalEl.querySelector('#albumModalMore');
    const thumbContainer = modalEl.querySelector('#albumThumbnails');

    modalEl.addEventListener('hidden.bs.modal', function () {
        if (carouselInner) carouselInner.innerHTML = '';
        if (albumModalTitle) albumModalTitle.textContent = '';
        if (albumModalDesc) albumModalDesc.textContent = '';
        if (thumbContainer) thumbContainer.innerHTML = '';
        if (albumModalMore) {
            albumModalMore.href = '#';
            albumModalMore.classList.add('disabled');
        }
    });

    async function fetchAlbumImages(albumId) {
        const url = getAjaxUrl(albumId);
        try {
            const resp = await fetch(url, { credentials: 'same-origin' });
            if (!resp.ok) return null;
            return await resp.json();
        } catch (e) {
            console.error('album-modal: AJAX fetch error', e);
            return null;
        }
    }

    function escapeHtml(s) {
        return String(s || '').replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
    }

    function populateCarousel(data) {
        if (!carouselInner) return;
        carouselInner.innerHTML = '';
        if (thumbContainer) thumbContainer.innerHTML = '';
        if (albumModalTitle) albumModalTitle.textContent = data.title || '';
        if (albumModalDesc) albumModalDesc.textContent = data.description || 'بدون توضیح';

        const images = Array.isArray(data.images) ? data.images : [];
        if (!images.length) {
            carouselInner.innerHTML = '<div class="carousel-item active"><div class="text-center py-5 text-muted">تصویری یافت نشد.</div></div>';
            return;
        }

        images.forEach((img, idx) => {
            const div = document.createElement('div');
            div.className = 'carousel-item' + (idx === 0 ? ' active' : '');
            const safeUrl = escapeHtml(img.url || '');
            const safeCap = escapeHtml(img.caption || '');
            div.innerHTML = `
                <div class="d-flex justify-content-center align-items-center" style="height:70vh;">
                    <img src="${safeUrl}" alt="${safeCap}" style="max-height:100%; max-width:100%; object-fit:contain;">
                </div>
                ${safeCap ? `<div class="carousel-caption d-none d-md-block text-start"><p>${safeCap}</p></div>` : ''}
            `;
            carouselInner.appendChild(div);

            if (thumbContainer) {
                const thumb = document.createElement('img');
                thumb.src = safeUrl;
                thumb.alt = safeCap;
                thumb.className = 'img-thumbnail';
                thumb.style = 'width:80px; height:60px; object-fit:cover; cursor:pointer;';
                thumb.addEventListener('click', () => {
                    const carEl = modalEl.querySelector('#albumCarousel');
                    const bsCar = bootstrap.Carousel.getInstance(carEl);
                    if (bsCar) bsCar.to(idx);
                });
                thumbContainer.appendChild(thumb);
            }
        });

        const carEl = modalEl.querySelector('#albumCarousel');
        let bsCar = bootstrap.Carousel.getInstance(carEl);
        if (bsCar) {
            bsCar.to(0);
        } else {
            bsCar = new bootstrap.Carousel(carEl, { interval: false, ride: false, wrap: true });
        }
    }

    document.body.addEventListener('click', async function (e) {
        const trigger = e.target.closest('[data-album-id]');
        if (!trigger) return;
        e.preventDefault();
        const albumId = trigger.getAttribute('data-album-id');
        if (!albumId) return;

        if (carouselInner) carouselInner.innerHTML = '<div class="carousel-item active"><div class="text-center py-5 text-muted">در حال بارگذاری...</div></div>';
        if (albumModalTitle) albumModalTitle.textContent = '';
        if (albumModalDesc) albumModalDesc.textContent = '';
        if (thumbContainer) thumbContainer.innerHTML = '';
        if (albumModalMore) {
            albumModalMore.href = '#';
            albumModalMore.classList.add('disabled');
        }

        const data = await fetchAlbumImages(albumId);
        if (!data) {
            if (carouselInner) carouselInner.innerHTML = '<div class="carousel-item active"><div class="text-center py-5 text-danger">خطا در بارگذاری آلبوم</div></div>';
            albumModal.show();
            return;
        }

        populateCarousel(data);

        if (data.category_slug && albumModalMore) {
            albumModalMore.href = '/category/' + encodeURIComponent(data.category_slug) + '/';
            albumModalMore.classList.remove('disabled');
        }

        albumModal.show();
    });
});
