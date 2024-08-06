import requests

from datetime import datetime

from django.shortcuts import render
from django.shortcuts import redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods


from api.client import Client
from core.models import Batch


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

        client = Client.from_token(token)

        # Verify submitted token by checking `username` in the response
        try:
            username = client.get_username()
        except ValueError as e:
            data = {"error": e}
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
