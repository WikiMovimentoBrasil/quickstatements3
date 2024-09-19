from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

from .languages import LANGUAGE_CHOICES

class Token(models.Model):
    """
    User OAuth tokens
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=False, null=False)
    # TODO: store this encrypted?
    value = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Token for {self.user}: [redacted]"

    class Meta:
        verbose_name = _("Token")
        verbose_name_plural = _("Tokens")

class PreferencesManager(models.Manager):
    def get_language(self, user, default):
        try:
            prefs = self.get_queryset().get(user=user)
            return prefs.language if prefs.language else default
        except Preferences.DoesNotExist:
            return default

class Preferences(models.Model):
    """
    User preferences
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, blank=False, null=False)
    language = models.CharField(max_length=32, choices=LANGUAGE_CHOICES, blank=True, null=False)

    objects = PreferencesManager()

    def __str__(self):
        return f"Preferences for {self.user}"

    class Meta:
        verbose_name = _("Preferences")
        verbose_name_plural = _("Preferences")
