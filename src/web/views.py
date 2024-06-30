
import requests

from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import render
from django.shortcuts import redirect
from django.views.decorators.http import require_http_methods

from core.models import Batch


@require_http_methods(["GET",])
def home(request):
    return render(request, "index.html")


@require_http_methods(["GET",])
def last_batches(request):
    last_batches = Batch.objects.all().order_by("-modified")[:20]
    return render(request, "batches.html", {"last_batches": last_batches})


@require_http_methods(["GET",])
def last_batches_by_user(request, user):
    last_batches = Batch.objects.filter(user=user).order_by("-modified")[:20]
    return render(request, "batches.html", {"last_batches": last_batches})


@require_http_methods(["GET",])
def batch(request, pk):
    try:
        batch = Batch.objects.get(pk=pk)
        return render(request, "batch.html", {"batch": batch})
    except Batch.DoesNotExist:
        return render(request, "batch_not_found.html", status=404)


def login(request):
    if request.session.get("username") is not None:
        return redirect("/auth/profile/")
    else:
        return render(request, "login.html", {})


def logout(request):
    request.session.flush()
    return redirect("/")


def login_dev(request):
    if request.method == "POST":
        # obtain dev token
        token = request.POST["access_token"]

        # TODO: move this logic into the api app
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        response = requests.get(
            "https://www.mediawiki.org/w/rest.php/oauth2/resource/profile",
            headers=headers,
        ).json()

        # Verify submitted token by checking `username` in the response
        try:
            username = response["username"]
        except KeyError:
            data = {"error": response}
            return render(request, "login_dev.html", data, status=400)

        # save access token and Wikimedia username in the user's session
        request.session["access_token"] = token
        request.session["username"] = username

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})


def profile(request):
    data = {
        "username": request.session.get("username"),
    }
    return render(request, "profile.html", data)
