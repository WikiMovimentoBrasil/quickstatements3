from django.contrib import admin

from .models import Token
from .models import Preferences


@admin.register(Token)
class TokenAdmin(admin.ModelAdmin):
    list_display = ["user", "expires_at"]
    list_filter = ["expires_at"]
    search_field = ["user"]
    raw_id_fields = ["user"]


@admin.register(Preferences)
class PreferencesAdmin(admin.ModelAdmin):
    list_display = ["user", "language"]
    list_filter = ["language"]
    search_field = ["user"]
    raw_id_fields = ["user"]
