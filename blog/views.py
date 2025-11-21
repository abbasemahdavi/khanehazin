# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 18:36:09 2025

Full blog views (post_list + AJAX filter + AJAX album images + CRUD helpers)
@author: Abbas Mahdavi
"""
# -*- coding: utf-8 -*-

# blog/views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, Http404
from django.core.paginator import Paginator
from django.urls import reverse
from django.contrib.auth.decorators import login_required
from django.utils.html import strip_tags
from django.db.models import Q

# مدل‌ها را امن وارد می‌کنیم
try:
    from .models import Post, Album, Category, AlbumImage
except Exception:
    Post = None
    Album = None
    Category = None
    AlbumImage = None


def _safe_image_url(obj, field_names=('featured_image', 'image', 'cover_image', 'featured')):
    if not obj:
        return None
    for f in field_names:
        if hasattr(obj, f):
            val = getattr(obj, f)
            if not val:
                continue
            try:
                return val.url
            except Exception:
                if isinstance(val, str) and val:
                    return val
                continue
    if hasattr(obj, 'image_url'):
        try:
            return getattr(obj, 'image_url')
        except Exception:
            return None
    return None


def _get_post_url(post):
    if not post:
        return '#'
    if hasattr(post, 'get_absolute_url'):
        try:
            return post.get_absolute_url()
        except Exception:
            pass
    code = getattr(post, 'code', None)
    slug = getattr(post, 'slug', None)
    try:
        if code and slug:
            return reverse('blog:object_by_code_with_slug', args=[code, slug])
    except Exception:
        pass
    try:
        if code:
            return reverse('blog:object_by_code', args=[code])
    except Exception:
        pass
    return '#'


def _get_common_context():
    common = {}
    try:
        from .models import SiteSetting, FooterLink, FooterIcon, Menu, Ad, Category, Post, Album
    except Exception:
        SiteSetting = FooterLink = FooterIcon = Menu = Ad = Category = Post = Album = None

    site_settings = None
    try:
        if SiteSetting is not None:
            site_settings = SiteSetting.objects.first()
    except Exception:
        site_settings = None

    try:
        if FooterLink is not None:
            footer_links = FooterLink.objects.filter(show=True, site=site_settings).order_by('order') if site_settings else FooterLink.objects.filter(show=True).order_by('order')
        else:
            footer_links = []
    except Exception:
        footer_links = []

    try:
        if FooterIcon is not None:
            footer_icons = FooterIcon.objects.filter(show=True, site=site_settings).order_by('order') if site_settings else FooterIcon.objects.filter(show=True).order_by('order')
        else:
            footer_icons = []
    except Exception:
        footer_icons = []

    main_menu = None
    try:
        if Menu is not None:
            main_menu = Menu.objects.filter(enabled=True, slug='main').prefetch_related('items__children').first()
    except Exception:
        main_menu = None

    categories_list = []
    try:
        if Category is not None:
            cats_qs = Category.objects.all().order_by('name')
            for c in cats_qs:
                try:
                    post_count = Post.objects.filter(categories__id=c.id).count() if Post is not None else 0
                except Exception:
                    post_count = 0
                try:
                    album_count = Album.objects.filter(categories__id=c.id).count() if Album is not None else 0
                except Exception:
                    album_count = 0
                categories_list.append({
                    'id': getattr(c, 'id', None),
                    'name': getattr(c, 'name', str(c)),
                    'slug': getattr(c, 'slug', '') or '',
                    'count': post_count + album_count,
                })
    except Exception:
        categories_list = []

    ads_list = []
    try:
        if Ad is not None:
            ads_qs = Ad.objects.filter(is_active=True).order_by('-created_at')[:10]
            for a in ads_qs:
                try:
                    img = a.image.url
                except Exception:
                    img = ''
                ads_list.append({
                    'name': getattr(a, 'name', getattr(a, 'title', str(a))),
                    'image': img,
                    'html': getattr(a, 'external_code', '') or getattr(a, 'html', '') or '',
                })
    except Exception:
        ads_list = []

    common.update({
        'categories': categories_list,
        'ads': ads_list,
        'main_menu': main_menu,
        'footer_links': footer_links,
        'footer_icons': footer_icons,
        'site_settings': site_settings,
    })
    return common


# ---------- helper for short summary ----------
def _short_summary_from_obj(obj, length=200, preserve_words=True):
    if not obj:
        return ''
    # اگر summary پر است، ناملموس (HTML) را بازگردان
    if hasattr(obj, 'summary') and getattr(obj, 'summary'):
        return getattr(obj, 'summary') or ''
    # در غیر این صورت از short_description استفاده کن
    if hasattr(obj, 'short_description') and getattr(obj, 'short_description'):
        text = getattr(obj, 'short_description') or ''
        # short_description معمولاً متن ساده است؛ درصورت تمایل truncate کن:
        return (text if len(text) <= length else text[:length].rsplit(' ',1)[0] + "…")
    # fallback: پاک کردن تگ‌های HTML از content و truncate
    content = getattr(obj, 'content', '') or ''
    plain = strip_tags(content).strip()
    if len(plain) <= length:
        return plain
    truncated = plain[:length].rstrip()
    if not preserve_words:
        return truncated + "…"
    last_space = truncated.rfind(' ')
    if last_space > max(0, int(length * 0.4)):
        truncated = truncated[:last_space]
    return truncated.rstrip() + "…"

# ---------------------------
# Views
# ---------------------------
def post_list(request, slug=None):
    """
    صفحهٔ اصلی — album_tabs شامل فقط دسته‌هایی که آلبوم دارند.
    featured_post و other_posts شامل 'short_summary' هستند.
    + combined_items: ترکیب پست‌ها و آلبوم‌ها پشت سر هم براساس created_at
    """
    featured_post = None
    other_posts_qs = []

    selected_category = None
    if slug and Category is not None:
        try:
            selected_category = Category.objects.get(slug=slug)
        except Exception:
            selected_category = None

    try:
        if Post is not None:
            # انتخاب featured (در صورتی که فیلد featured داشته باشی)
            if hasattr(Post, 'featured'):
                featured_post = Post.objects.filter(featured=True).order_by('-created_at').first()
            if not featured_post:
                featured_post = Post.objects.order_by('-created_at').first()

            if featured_post:
                other_posts_qs = Post.objects.exclude(pk=featured_post.pk).order_by('-created_at')[:7]
            else:
                other_posts_qs = Post.objects.order_by('-created_at')[:7]

            if selected_category:
                try:
                    other_posts_qs = other_posts_qs.filter(categories=selected_category)
                except Exception:
                    other_posts_qs = [p for p in other_posts_qs if selected_category in getattr(p, 'categories', [])]
    except Exception:
        featured_post = None
        other_posts_qs = []

    # آماده‌سازی dictها برای قالب (امن)
    other_posts = []
    try:
        for p in other_posts_qs:
            try:
                cats = [c.slug for c in p.categories.all()] if hasattr(p, 'categories') else []
            except Exception:
                cats = []
            other_posts.append({
                'id': getattr(p, 'id', None),
                'title': getattr(p, 'title', str(p)),
                'created_at': getattr(p, 'created_at', None),
                'get_absolute_url': _get_post_url(p),
                'categories': cats,
                'short_summary': _short_summary_from_obj(p, 200),
            })
    except Exception:
        other_posts = []

    featured_post_dict = None
    if featured_post:
        featured_post_dict = {
            'id': getattr(featured_post, 'id', None),
            'title': getattr(featured_post, 'title', str(featured_post)),
            'created_at': getattr(featured_post, 'created_at', None),
            'content': getattr(featured_post, 'content', '')[:400],
            'summary': featured_post.summary or strip_tags(featured_post.content)[:200],
            'image_url': _safe_image_url(featured_post),
            'get_absolute_url': _get_post_url(featured_post),
        }

    # album_tabs: فقط دسته‌هایی که آلبوم دارند (خالی‌ها حذف می‌شوند)
    album_tabs = []
    try:
        if Category is not None and Album is not None:
            cats = Category.objects.all().order_by('name')
            for cat in cats:
                try:
                    if hasattr(cat, 'albums'):
                        cat_albums_qs = cat.albums.all().order_by('-created_at')[:12]
                    else:
                        cat_albums_qs = Album.objects.filter(categories__id=cat.id).order_by('-created_at')[:12]
                except Exception:
                    cat_albums_qs = []
                if cat_albums_qs and cat_albums_qs.exists():
                    albums_list = []
                    for a in cat_albums_qs:
                        cover = _safe_image_url(a, field_names=('cover_image', 'featured_image', 'image'))
                        albums_list.append({
                            'id': getattr(a, 'id', None),
                            'title': getattr(a, 'title', str(a)),
                            'cover_url': cover or '',
                            'code': getattr(a, 'code', getattr(a, 'pk', '')),
                            'album_url': reverse('blog:category_albums', args=[getattr(cat, 'slug', '')]) if getattr(cat, 'slug', '') else '#',
                        })
                    album_tabs.append({
                        'name': getattr(cat, 'name', str(cat)),
                        'slug': getattr(cat, 'slug', '') or '',
                        'albums': albums_list,
                    })
    except Exception:
        album_tabs = []

    # categories list for sidebar
    categories_list = []
    try:
        if Category is not None:
            cats = Category.objects.all().order_by('name')
            for c in cats:
                try:
                    post_count = Post.objects.filter(categories__id=c.id).count() if Post is not None else 0
                except Exception:
                    post_count = 0
                try:
                    album_count = Album.objects.filter(categories__id=c.id).count() if Album is not None else 0
                except Exception:
                    album_count = 0
                categories_list.append({
                    'id': getattr(c, 'id', None),
                    'name': getattr(c, 'name', str(c)),
                    'slug': getattr(c, 'slug', '') or '',
                    'count': post_count + album_count,
                })
    except Exception:
        categories_list = []

    # ترکیب پست‌ها و آلبوم‌ها پشت سر هم (براساس created_at)
    combined_items = []
    try:
        posts_all = Post.objects.all().only('id', 'title', 'created_at', 'slug', 'code').order_by('-created_at') if Post is not None else []
    except Exception:
        posts_all = []
    try:
        albums_all = Album.objects.all().only('id', 'title', 'created_at', 'slug', 'code').order_by('-created_at') if Album is not None else []
    except Exception:
        albums_all = []

    for p in posts_all:
        combined_items.append({
            'kind': 'post',
            'title': getattr(p, 'title', str(p)),
            'created_at': getattr(p, 'created_at', None),
            'url': _get_post_url(p),
        })
    for a in albums_all:
        # تلاش برای سازگاری با get_absolute_url اگر تعریف شده باشد
        try:
            album_url = a.get_absolute_url()
        except Exception:
            album_url = reverse('blog:album_detail', args=[getattr(a, 'slug', '')]) if getattr(a, 'slug', '') else '#'
        combined_items.append({
            'kind': 'album',
            'title': getattr(a, 'title', str(a)),
            'created_at': getattr(a, 'created_at', None),
            'url': album_url,
        })

    combined_items = sorted(combined_items, key=lambda x: (x['created_at'] or 0), reverse=True)

    context = {
        'featured_post': featured_post_dict,
        'other_posts': other_posts,
        'album_tabs': album_tabs,
        'categories': categories_list,
        'combined_items': combined_items,  # لیست ترکیبی برای قالب
    }
    context.update(_get_common_context())
    return render(request, 'blog/post_list.html', context)



def ajax_album_images(request, album_id):
    if Album is None or AlbumImage is None:
        raise Http404("Album support not available.")
    album = get_object_or_404(Album, pk=album_id)
    images = []
    try:
        imgs_qs = AlbumImage.objects.filter(album=album).order_by('order', 'id')[:50]
        for im in imgs_qs:
            try:
                url = im.image.url
            except Exception:
                url = ''
            if url:
                images.append({'url': url, 'caption': getattr(im, 'caption', '') or ''})
    except Exception:
        images = []

    category_slug = ''
    try:
        if hasattr(album, 'categories') and album.categories.exists():
            category_slug = album.categories.first().slug or ''
    except Exception:
        category_slug = ''

    data = {
        'title': getattr(album, 'title', str(album)),
        'description': getattr(album, 'order_instructions', '') or '',
        'category_slug': category_slug,
        'images': images,
    }
    return JsonResponse(data)

def post_detail(request, code, slug):
    if Post is None:
        raise Http404("Posts not enabled.")

    post = get_object_or_404(Post, code=code)

    # اگر slug اشتباه بود، ریدایرکت کن به آدرس درست
    if slug != post.slug:
        return redirect('blog:object_by_code_with_slug', code=post.code, slug=post.slug)

    post_dict = {
        'obj': post,
        'short_summary': _short_summary_from_obj(post, 200),
    }

    # ساخت combined_items برای سایدبار
    combined_items = []
    try:
        posts_all = Post.objects.all().order_by('-created_at')[:20]
        for p in posts_all:
            combined_items.append({
                'kind': 'post',
                'title': p.title,
                'created_at': p.created_at,
                'url': _get_post_url(p),
            })
    except:
        pass
    try:
        albums_all = Album.objects.all().order_by('-created_at')[:20]
        for a in albums_all:
            try:
                album_url = a.get_absolute_url()
            except:
                album_url = reverse('blog:album_detail', args=[a.slug]) if a.slug else '#'
            combined_items.append({
                'kind': 'album',
                'title': a.title,
                'created_at': a.created_at,
                'url': album_url,
            })
    except:
        pass
    combined_items = sorted(combined_items, key=lambda x: x['created_at'] or 0, reverse=True)

    context = {
        'post': post,
        'post_meta': post_dict,
        'combined_items': combined_items,
    }
    context.update(_get_common_context())
    return render(request, 'blog/post_detail.html', context)

def post_detail_by_code(request, code):
    if Post is None:
        raise Http404("Posts not enabled.")
    post = get_object_or_404(Post, code=code)
    post_dict = {'obj': post, 'short_summary': _short_summary_from_obj(post, 200)}
    context = {'post': post, 'post_meta': post_dict}
    context.update(_get_common_context())
    return render(request, 'blog/post_detail.html', context)

def post_detail_by_id(request, pk):
    post = get_object_or_404(Post, pk=pk)
    # هدایت به مسیر مبتنی بر code + slug
    return redirect('blog:object_by_code_with_slug', code=post.code, slug=post.slug)

def search(request):
    q = request.GET.get('q', '').strip()
    scope = request.GET.get('scope', 'all')
    posts = Post.objects.none() if Post is not None else []
    albums = Album.objects.none() if Album is not None else []

    if q:
        try:
            post_qs = Post.objects.filter(
                Q(title__icontains=q) |
                Q(content__icontains=q) |
                Q(short_description__icontains=q)
            )
            if scope != 'all':
                post_qs = post_qs.filter(categories__slug=scope)
            posts = post_qs.order_by('-created_at')[:200]
        except Exception:
            posts = Post.objects.none()

        try:
            album_qs = Album.objects.filter(
                Q(title__icontains=q) |
                Q(order_instructions__icontains=q)
            )
            if scope != 'all':
                album_qs = album_qs.filter(categories__slug=scope)
            albums = album_qs.order_by('-created_at')[:200]
        except Exception:
            albums = Album.objects.none()

    # آماده‌سازی پست‌ها برای قالب
    post_list = []
    for p in posts:
        post_list.append({
            'id': p.id,
            'title': p.title,
            'created_at': p.created_at,
            'get_absolute_url': _get_post_url(p),
            'short_description': _short_summary_from_obj(p, 200),
            'cover': _safe_image_url(p),
        })

    # آماده‌سازی آلبوم‌ها برای قالب
    album_list = []
    for a in albums:
        try:
            album_url = a.get_absolute_url()
        except Exception:
            album_url = reverse('blog:album_detail', args=[a.slug]) if a.slug else '#'
        album_list.append({
            'id': a.id,
            'title': a.title,
            'order_instructions': getattr(a, 'order_instructions', ''),
            'cover_image': _safe_image_url(a),
            'url': album_url,
        })

    # ساخت combined_items برای سایدبار
    combined_items = []
    for p in posts[:20]:
        combined_items.append({
            'kind': 'post',
            'title': p.title,
            'created_at': p.created_at,
            'url': _get_post_url(p),
        })
    for a in albums[:20]:
        combined_items.append({
            'kind': 'album',
            'title': a.title,
            'created_at': a.created_at,
            'url': reverse('blog:album_detail', args=[a.slug]) if a.slug else '#',
        })
    combined_items = sorted(combined_items, key=lambda x: (x['created_at'] or 0), reverse=True)

    context = {
        'q': q,
        'scope': scope,
        'posts': post_list,
        'albums': album_list,
        'combined_items': combined_items,
    }
    context.update(_get_common_context())
    return render(request, 'blog/search_results.html', context)



def album_detail(request, slug):
    if Album is None:
        raise Http404("Albums not enabled.")
    album = get_object_or_404(Album, slug=slug)
    context = {'album': album}
    context.update(_get_common_context())
    return render(request, 'blog/album_detail.html', context)

@login_required
def user_dashboard(request):
    # بدون توجه به نویسنده، همه را ترکیب کن (طبق خواسته‌ت)
    posts_qs = Post.objects.all().order_by('-created_at') if Post is not None else []
    albums_qs = Album.objects.all().order_by('-created_at') if Album is not None else []

    combined_items = []
    for p in posts_qs:
        combined_items.append({'kind': 'post', 'title': p.title, 'created_at': p.created_at, 'url': p.get_absolute_url()})
    for a in albums_qs:
        combined_items.append({'kind': 'album', 'title': a.title, 'created_at': a.created_at, 'url': a.get_absolute_url()})

    combined_items = sorted(combined_items, key=lambda x: (x['created_at'] or 0), reverse=True)

    context = {'combined_items': combined_items}
    context.update(_get_common_context())
    return render(request, 'blog/user_dashboard.html', context)

def post_edit(request, pk):
    if Post is None:
        raise Http404("Posts not enabled.")
    post = get_object_or_404(Post, pk=pk)
    context = {'post': post}
    context.update(_get_common_context())
    return render(request, 'blog/post_edit.html', context)

def post_delete(request, pk):
    if Post is None:
        raise Http404("Posts not enabled.")
    post = get_object_or_404(Post, pk=pk)
    post.delete()
    return redirect('blog:post_list')

# ---------------------------
# Category / Ajax
# ---------------------------
def category_albums(request, slug):
    category = get_object_or_404(Category, slug=slug)

    posts_qs = category.posts.all().order_by('-created_at') if hasattr(category, 'posts') else Post.objects.none()
    albums_qs = category.albums.all().order_by('-created_at') if hasattr(category, 'albums') else Album.objects.none()

    # پست ویژه (اولین پست)
    featured_post = posts_qs.first() if posts_qs.exists() else None

    # لیست پست‌ها (همه به جز پست ویژه)
    other_posts_qs_full = posts_qs[1:] if posts_qs.count() > 1 else posts_qs.none()

    posts_list = [{
        'id': p.id,
        'title': p.title,
        'created_at': p.created_at,
        'get_absolute_url': _get_post_url(p),
        'categories': [c.slug for c in p.categories.all()] if hasattr(p, 'categories') else [],
        'short_summary': _short_summary_from_obj(p, 200),
    } for p in other_posts_qs_full]

    albums_list = [{
        'id': a.id,
        'title': a.title,
        'cover_url': _safe_image_url(a) or '',
        'code': getattr(a, 'code', a.pk),
    } for a in albums_qs]

    # تب آلبوم‌های همین دسته (در صورتی که آلبومی وجود داشته باشد)
    album_tabs = []
    try:
        cat_albums = list(albums_qs[:20])
        if cat_albums:
            album_tabs = [{
                'name': getattr(category, 'name', str(category)),
                'slug': getattr(category, 'slug', '') or '',
                'albums': [{
                    'id': a.id,
                    'title': a.title,
                    'cover_url': _safe_image_url(a) or '',
                    'code': getattr(a, 'code', getattr(a, 'pk', '')),
                    'album_url': reverse('blog:category_albums', args=[getattr(category, 'slug', '')]) if getattr(category, 'slug', '') else '#',
                } for a in cat_albums]
            }]
    except Exception:
        album_tabs = []

    # combined_items برای سایدبار (اختیاری)
    combined_items = []
    for p in posts_qs[:20]:
        combined_items.append({'kind': 'post', 'title': p.title, 'created_at': p.created_at, 'url': _get_post_url(p)})
    for a in albums_qs[:20]:
        try:
            url = a.get_absolute_url()
        except Exception:
            url = reverse('blog:album_detail', args=[getattr(a, 'slug', '')]) if getattr(a, 'slug', '') else '#'
        combined_items.append({'kind': 'album', 'title': a.title, 'created_at': a.created_at, 'url': url})
    combined_items = sorted(combined_items, key=lambda x: x['created_at'] or 0, reverse=True)

    context = {
        'category': category,
        'featured_post': {
            'id': getattr(featured_post, 'id', None),
            'title': getattr(featured_post, 'title', '') if featured_post else '',
            'created_at': getattr(featured_post, 'created_at', None) if featured_post else None,
            'content': getattr(featured_post, 'content', '')[:400] if featured_post else '',
            'summary': getattr(featured_post, 'summary', '') or strip_tags(getattr(featured_post, 'content', ''))[:200] if featured_post else '',
            'image_url': _safe_image_url(featured_post) if featured_post else '',
            'get_absolute_url': _get_post_url(featured_post) if featured_post else '#',
        } if featured_post else None,
        'posts': posts_list,
        'albums': albums_list,
        'album_tabs': album_tabs,
        'combined_items': combined_items,
        'category_slug': getattr(category, 'slug', ''),
    }
    context.update(_get_common_context())

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        html = render(request, 'blog/partials/category_content.html', context).content.decode('utf-8')
        return JsonResponse({'html': html})

    return render(request, 'blog/category_albums.html', context)

def category_posts(request, slug):
    category = get_object_or_404(Category, slug=slug)
    posts = category.posts.order_by('-created_at')
    paginator = Paginator(posts, 10)  # ۱۰ پست در هر صفحه
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'blog/category_posts.html', {
        'category': category,
        'page_obj': page_obj,
        'featured_post': posts.first() if posts else None,
    })
