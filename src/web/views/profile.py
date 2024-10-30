from datetime import datetime

from authlib.integrations.base_client.errors import MismatchingStateError
from django.shortcuts import render
from rest_framework.authtoken.models import Token

from core.client import Client
from core.exceptions import NoToken
from core.exceptions import UnauthorizedToken
from core.exceptions import ServerError

from web.oauth import oauth
from web.utils import user_from_access_token
from web.utils import user_from_full_token
from web.utils import clear_tokens
from web.models import Preferences
from web.languages import LANGUAGE_CHOICES

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
            elif action == "update_token":
                if token:
                    token.delete()
                token = Token.objects.create(user=user)

        data["token"] = token.key

        data["language"] = Preferences.objects.get_language(user, "en")
        data["language_choices"] = LANGUAGE_CHOICES

    return render(request, "profile.html", data)
