from django.db import models
from django.contrib.auth.models import User
from django.utils.translation import gettext as _

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
