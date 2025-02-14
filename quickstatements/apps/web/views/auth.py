from authlib.integrations.base_client.errors import MismatchingStateError
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.shortcuts import redirect, render
from django.urls import reverse

from quickstatements.apps.core.exceptions import NoToken, ServerError, UnauthorizedToken

from ..oauth import oauth
from ..utils import clear_tokens, user_from_access_token, user_from_full_token


def logout_per_token_expired(request):
    django_logout(request)
    request.session["token_expired"] = True
    return redirect(reverse("login"))


def login(request):
    if request.user.is_authenticated:
        return redirect("/auth/profile/")
    else:
        data = {
            "token_expired": request.session.get("token_expired", False),
        }
        return render(request, "login.html", data)


def logout(request):
    clear_tokens(request.user)
    django_logout(request)
    return redirect("/")


def oauth_redirect(request):
    return oauth.mediawiki.authorize_redirect(request)


def oauth_callback(request):
    data = {}
    try:
        full_token = oauth.mediawiki.authorize_access_token(request)
        user = user_from_full_token(full_token)
        django_login(request, user)
        return redirect(reverse("profile"))
    except (UnauthorizedToken, KeyError):
        data["error"] = "token"
    except ServerError:
        data["error"] = "server"
    except MismatchingStateError:
        data["error"] = "mismatched_states"
    return render(request, "login.html", data, status=401)


def login_dev(request):
    if request.method == "POST":
        # obtain dev token
        access_token = request.POST["access_token"]

        try:
            user = user_from_access_token(access_token)
            django_login(request, user)
        except (NoToken, UnauthorizedToken, ServerError) as e:
            data = {"error": e}
            return render(request, "login_dev.html", data, status=400)

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})
