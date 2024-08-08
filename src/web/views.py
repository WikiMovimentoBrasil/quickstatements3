import os

from datetime import datetime

from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.contrib.auth import login as django_login, logout as django_logout
from django.urls import reverse


from api.client import Client
from core.models import Batch
from .utils import user_from_token, clear_tokens

from authlib.integrations.django_client import OAuth

oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    access_token_url="https://www.mediawiki.org/w/rest.php/oauth2/access_token",
    authorize_url="https://www.mediawiki.org/w/rest.php/oauth2/authorize",
)

@require_http_methods(["GET",])
def home(request):
    return render(request, "index.html")


@require_http_methods(["GET",])
def last_batches(request):
    last_batches = Batch.objects.all().order_by("-modified")[:20]
    return render(request, "batches.html", {"last_batches": list(last_batches)})


@require_http_methods(["GET",])
def last_batches_by_user(request, user):
    last_batches = Batch.objects.filter(user=user).order_by("-modified")[:20]
    # we need to use `username` since `user` is always supplied by django templates
    return render(request, "batches.html", {"last_batches": list(last_batches), "username": user})


@require_http_methods(["GET",])
def batch(request, pk):
    try:
        batch = Batch.objects.get(pk=pk)
        return render(request, "batch.html", {"batch": batch})
    except Batch.DoesNotExist:
        return render(request, "batch_not_found.html", {"pk": pk}, status=404)


def new_batch(request):
    if request.user and request.user.is_authenticated:
        if request.method == "POST":
            batch_owner = request.user.username
            batch_commands = request.POST.get("commands")
            batch_name = request.POST.get("name", f"Batch  user:{batch_owner} {datetime.now().isoformat()}")
            batch_type = request.POST.get("type", "v1")
            batch = Batch.objects.create_batch(batch_name, batch_commands, batch_type, batch_owner)
            return redirect(reverse("batch", args=[batch.pk]))
        else:
            return render(request, "new_batch.html", {})
    else:
        return render(request, "new_batch_error.html", {"message": "User must be logged in", "user": request.user})


def login(request):
    if request.user.is_authenticated:
        return redirect("/auth/profile/")
    else:
        return render(request, "login.html", {})


def logout(request):
    clear_tokens(request.user)
    django_logout(request)
    return redirect("/")


def oauth_redirect(request):
    return oauth.mediawiki.authorize_redirect(request)


def oauth_callback(request):
    token = oauth.mediawiki.authorize_access_token(request)["access_token"]
    user = user_from_token(token)
    django_login(request, user)
    return redirect(reverse("profile"))


def login_dev(request):
    if request.method == "POST":
        # obtain dev token
        token = request.POST["access_token"]

        try:
            user = user_from_token(token)
            django_login(request, user)
        except ValueError as e:
            data = {"error": e}
            return render(request, "login_dev.html", data, status=400)

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})


def profile(request):
    return render(request, "profile.html")
