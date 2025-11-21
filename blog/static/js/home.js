document.addEventListener('DOMContentLoaded', function () {
    // CSRF utility (same as قبلا)
    function getCookie(name) {
        const match = document.cookie.match(new RegExp('(^| )' + name + '=([^;]+)'));
        if (match) return decodeURIComponent(match[2]);
        return null;
    }
    const csrftoken = getCookie('csrftoken');

    // دسته‌ها: پیش‌فرض همه تیک خورده‌اند (در template هم همین کار انجام شده)
    const categoryCheckboxes = Array.from(document.querySelectorAll('.category-checkbox'));
    const applyBtn = document.getElementById('apply-filters');
    const clearBtn = document.getElementById('clear-filters');

    function fetchFiltered(page=1) {
        const checked = categoryCheckboxes.filter(c => c.checked).map(c => c.value);
        const payload = {categories: checked, page: page};

        fetch('/ajax/filter-posts/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(payload)
        })
            .then(r => r.json())
            .then(data => {
                if (data.posts_html) {
                    const postsContainer = document.querySelector('#mainContent') || document.querySelector('#albums-area');
                    // اگر partialهای شما اسامی متفاوت دارد مطابق تنظیم کن
                    // اینجا ما فرض می‌کنیم posts_html و albums_html هر دو بازنویسی می‌شوند
                    if (data.albums_html) {
                        const albumsArea = document.getElementById('albums-area');
                        if (albumsArea) albumsArea.innerHTML = data.albums_html;
                        attachAlbumOpenButtons();
                    }
                    if (data.posts_html) {
                        // اگر لیست پست‌ها در #posts-area باشد آن را جایگزین کن
                        const postsArea = document.getElementById('posts-area');
                        if (postsArea) postsArea.innerHTML = data.posts_html;
                    }
                }
            })
            .catch(err => {
                console.error('filter error', err);
            });
    }

    applyBtn && applyBtn.addEventListener('click', function() { fetchFiltered(1); });
    clearBtn && clearBtn.addEventListener('click', function() {
        categoryCheckboxes.forEach(c => c.checked = true);
        fetchFiltered(1);
    });

    categoryCheckboxes.forEach(c => {
        c.addEventListener('change', function() {
            // تغییر سریع با هر تغییر چک‌باکس
            fetchFiltered(1);
        });
    });

    // ----- Modal / Album handling -----
    const albumModalEl = document.getElementById('albumModal');
    let albumModalInstance = null;
    if (albumModalEl) {
        // bootstrap modal instance created on demand
        albumModalInstance = new bootstrap.Modal(albumModalEl, {keyboard: true});
    }

    function attachAlbumOpenButtons() {
        const buttons = Array.from(document.querySelectorAll('.album-open'));
        buttons.forEach(btn => {
            btn.removeEventListener('click', albumClickHandler);
            btn.addEventListener('click', albumClickHandler);
        });
    }

    function albumClickHandler(e) {
        e.preventDefault();
        const albumId = this.dataset.albumId;
        if (!albumId) return;
        // fetch images via AJAX
        fetch(`/ajax/album-images/${albumId}/`, {
            method: 'GET',
            headers: {'X-Requested-With': 'XMLHttpRequest'}
        })
            .then(r => {
                if (!r.ok) throw new Error('Network response error');
                return r.json();
            })
            .then(data => {
                if (data.error) {
                    console.error(data.error);
                    return;
                }
                populateAlbumModal(data);
                if (albumModalInstance) albumModalInstance.show();
            })
            .catch(err => {
                console.error('album fetch error', err);
            });
    }

    function populateAlbumModal(data) {
        const inner = document.getElementById('albumCarouselInner');
        inner.innerHTML = '';
        const titleEl = document.getElementById('albumModalTitle');
        const descEl = document.getElementById('albumModalDesc');
        const moreBtn = document.getElementById('albumModalMore');

        titleEl.textContent = data.title || '';
        descEl.textContent = data.description || '';

        if (data.images && data.images.length > 0) {
            data.images.forEach((img, idx) => {
                const div = document.createElement('div');
                div.className = 'carousel-item' + (idx === 0 ? ' active' : '');
                const imgEl = document.createElement('img');
                imgEl.src = img.url;
                imgEl.alt = img.caption || data.title || '';
                imgEl.className = 'd-block w-100';
                imgEl.style.maxHeight = '60vh';
                imgEl.style.objectFit = 'contain';
                div.appendChild(imgEl);
                if (img.caption) {
                    const cap = document.createElement('div');
                    cap.className = 'carousel-caption d-none d-md-block';
                    cap.innerHTML = `<p>${img.caption}</p>`;
                    div.appendChild(cap);
                }
                inner.appendChild(div);
            });
            // reset carousel to first slide
            const carouselEl = document.getElementById('albumCarousel');
            const bsCarousel = bootstrap.Carousel.getOrCreateInstance(carouselEl, {ride:false, interval:false});
            bsCarousel.to(0);
        } else {
            // no images: show placeholder
            const div = document.createElement('div');
            div.className = 'carousel-item active';
            const imgEl = document.createElement('img');
            imgEl.src = '/static/images/placeholder-800x450.png';
            imgEl.alt = data.title || '';
            imgEl.className = 'd-block w-100';
            imgEl.style.maxHeight = '60vh';
            imgEl.style.objectFit = 'contain';
            div.appendChild(imgEl);
            inner.appendChild(div);
        }

        // set more button: go to category page if available
        if (data.category_slug) {
            moreBtn.href = `/category/${data.category_slug}/`;
            moreBtn.classList.remove('d-none');
        } else {
            moreBtn.href = '#';
            moreBtn.classList.add('d-none');
        }
    }

    // attach on load
    attachAlbumOpenButtons();

    // Attach handlers to dynamically created "more" for tabs (delegation)
    document.body.addEventListener('click', function(e) {
        const t = e.target.closest('.more-for-tab');
        if (t) {
            // more-for-tab already has href set in template (we used first_category_slug)
            // no special JS needed; but prevent default if href="#" or empty
            if (t.getAttribute('href') === '#' || !t.getAttribute('href')) {
                e.preventDefault();
            }
        }
    });
});
