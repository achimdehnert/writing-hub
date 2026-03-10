"""
Lektorat — Prüfungs-Framework (ADR-083)
"""
import json
import logging
import re

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.views import View
from django.views.generic import DetailView

from .models import BookProject, OutlineVersion

logger = logging.getLogger(__name__)
