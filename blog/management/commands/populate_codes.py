# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 18:36:09 2025

@author: Abbas Mahdavi
"""

#blog/management/commands/populate_codes.py
from django.core.management.base import BaseCommand
from blog.models import Post, Album
from random import randint

class Command(BaseCommand):
    help = "Populate missing 6-digit unique codes for Post and Album models"

    def handle(self, *args, **options):
        self.populate_model(Post)
        self.populate_model(Album)

    def generate_unique_code(self, model):
        """Generates a unique 6-digit code not used in the given model."""
        while True:
            code = randint(100000, 999999)
            if not model.objects.filter(code=code).exists():
                return code

    def populate_model(self, model):
        items = model.objects.filter(code__isnull=True)
        count = 0
        for item in items:
            item.code = self.generate_unique_code(model)
            item.save()
            count += 1
        if count:
            self.stdout.write(self.style.SUCCESS(f"{count} {model.__name__} objects updated."))
        else:
            self.stdout.write(self.style.WARNING(f"No missing codes found in {model.__name__}."))
