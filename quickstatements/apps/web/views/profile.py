from django.shortcuts import render
from rest_framework.authtoken.models import Token

from quickstatements.apps.core.client import Client
from quickstatements.apps.core.exceptions import NoToken, ServerError, UnauthorizedToken

from ..languages import LANGUAGE_CHOICES
from ..models import Preferences
from .auth import logout_per_token_expired


def profile(request):
    data = {}
    if request.user.is_authenticated:
        user = request.user

        # Wikimedia API
        is_autoconfirmed = False
        token_failed = False
        try:
            client = Client.from_user(user)
            is_autoconfirmed = client.get_is_autoconfirmed()
        except UnauthorizedToken:
            return logout_per_token_expired(request)
        except (NoToken, ServerError):
            token_failed = True

        data["is_autoconfirmed"] = is_autoconfirmed
        data["token_failed"] = token_failed

        # TOKEN
        token, created = Token.objects.get_or_create(user=user)

        # POSTing
        if request.method == "POST":
            action = request.POST["action"]
            if action == "update_language":
                prefs, _ = Preferences.objects.get_or_create(user=user)
                prefs.language = request.POST["language"]
                prefs.save()
                from django.utils import translation

                translation.activate(prefs.language)
                request.LANGUAGE_CODE = translation.get_language()
            elif action == "update_token":
                if token:
                    token.delete()
                token = Token.objects.create(user=user)

        data["token"] = token.key

        data["language"] = Preferences.objects.get_language(user, "en")
        data["language_choices"] = LANGUAGE_CHOICES

    return render(request, "profile.html", data)
