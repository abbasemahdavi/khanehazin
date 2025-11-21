# -*- coding: utf-8 -*-
"""
Created on Sat Sep 27 18:36:09 2025

@author: Abbas Mahdavi
"""

#blog/forms.py
from django import forms
from .models import Post

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content']
