# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 18:36:09 2025

@author: Abbas Mahdavi
"""

# blog/context_processors.py
from .models import SiteSetting, Menu, FooterLink, FooterIcon, Ad, Category, Post, Album
from django.utils import timezone

def site_context(request):
    """
    Context processor to provide site-wide data:
      - site_settings (single or None)
      - main_menu (Menu with slug 'main' if exists)
      - footer_links, footer_icons (for first SiteSetting or all)
      - ads_by_group (dict of active ads grouped by group)
    """
    site = SiteSetting.objects.first()  # singleton-like approach
    # main menu
    main_menu = None
    try:
        main_menu = Menu.objects.filter(enabled=True, slug='main').prefetch_related('items__children').first()
    except Exception:
        main_menu = None

    # footer links/icons (prefer those linked to site, otherwise all visible)
    footer_links = FooterLink.objects.filter(show=True, site=site).order_by('order') if site else FooterLink.objects.filter(show=True).order_by('order')
    footer_icons = FooterIcon.objects.filter(show=True, site=site).order_by('order') if site else FooterIcon.objects.filter(show=True).order_by('order')

    # ads: only active ones for each group
    now = timezone.now()
    ads_qs = Ad.objects.filter(is_active=True).order_by('-created_at')
    def active_for_group(g):
        return [a for a in ads_qs.filter(group=g) if a.is_currently_active()]

    ads_by_group = {
        'header': active_for_group('header'),
        'main': active_for_group('main'),
        'sidebar': active_for_group('sidebar'),
    }

    return {
        'site_settings': site,
        'main_menu': main_menu,
        'footer_links': footer_links,
        'footer_icons': footer_icons,
        'ads_by_group': ads_by_group,
    }
