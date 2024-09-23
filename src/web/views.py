import os

from datetime import datetime

from authlib.integrations.django_client import OAuth
from django.core.paginator import Paginator
from django.contrib.auth import login as django_login
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from core.client import Client
from core.models import Batch
from core.models import BatchCommand
from core.parsers.base import ParserException
from core.parsers.v1 import V1CommandParser
from core.parsers.csv import CSVCommandParser
from .utils import user_from_token, clear_tokens
from .models import Preferences
from .languages import LANGUAGE_CHOICES


PAGE_SIZE = 30


oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    access_token_url="https://www.mediawiki.org/w/rest.php/oauth2/access_token",
    authorize_url="https://www.mediawiki.org/w/rest.php/oauth2/authorize",
)


@require_http_methods(
    [
        "GET",
    ]
)
def home(request):
    """
    Main page for this tool
    """
    return render(request, "index.html")


@require_http_methods(
    [
        "GET",
    ]
)
def last_batches(request):
    """
    List last PAGE_SIZE batches modified
    """
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    paginator = Paginator(Batch.objects.all().order_by("-modified"), PAGE_SIZE)
    return render(request, "batches.html", {"page": paginator.page(page)})


@require_http_methods(
    [
        "GET",
    ]
)
def last_batches_by_user(request, user):
    """
    List last PAGE_SIZE batches modified created by user
    """
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1
    paginator = Paginator(Batch.objects.filter(user=user).order_by("-modified"), PAGE_SIZE)
    # we need to use `username` since `user` is always supplied by django templates
    return render(request, "batches.html", {"username": user, "page": paginator.page(page)})


@require_http_methods(
    [
        "GET",
    ]
)
def batch(request, pk):
    """
    Base call for a batch. Returns the main page, that will load 2 fragments: commands and summary
    Used for ajax calls
    """
    try:
        batch = Batch.objects.get(pk=pk)
        current_owner = request.user.is_authenticated and request.user.username == batch.user
        return render(request, "batch.html", {"batch": batch, "current_owner": current_owner})
    except Batch.DoesNotExist:
        return render(request, "batch_not_found.html", {"pk": pk}, status=404)


@require_http_methods(
    [
        "POST",
    ]
)
def batch_stop(request, pk):
    """
    Base call for a batch. Returns the main page, that will load 2 fragments: commands and summary
    Used for ajax calls
    """
    try:
        batch = Batch.objects.get(pk=pk)
        current_owner = request.user.is_authenticated and request.user.username == batch.user
        if current_owner:
            batch.stop()
        return redirect(reverse("batch", args=[batch.pk]))
    except Batch.DoesNotExist:
        return render(request, "batch_not_found.html", {"pk": pk}, status=404)


@require_http_methods(
    [
        "GET",
    ]
)
def batch_commands(request, pk):
    """
    RETURNS fragment page with PAGINATED COMMANDs FOR A GIVEN BATCH ID
    Used for ajax calls
    """
    try:
        page = int(request.GET.get("page", 1))
    except (TypeError, ValueError):
        page = 1

    paginator = Paginator(BatchCommand.objects.filter(batch__pk=pk).order_by("index"), PAGE_SIZE)
    page = paginator.page(page)

    if request.user.is_authenticated:
        try:
            language = Preferences.objects.get_language(request.user, "en")
            client = Client.from_user(request.user)
            for command in page.object_list:
                command.display_label = command.get_label(client, language)
        except:
            pass

    return render(request, "batch_commands.html", {"page": page, "batch_pk": pk})


@require_http_methods(
    [
        "GET",
    ]
)
def batch_summary(request, pk):
    """
    Return informations about the current batch. Used as fragment for the main batch page
    CURRENT STATUS
    TOTAL COMMANDS
    ERROR COMMANDS
    DONE COMMANDS
    RUNNING COMMANDS
    INITIAL COMMANDS
    """
    try:
        from django.db.models import Q, Count

        error_commands = Count("batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_ERROR))
        initial_commands = Count("batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_INITIAL))
        running_commands = Count("batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_RUNNING))
        done_commands = Count("batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_DONE))
        batch = (
            Batch.objects.annotate(error_commands=error_commands)
            .annotate(initial_commands=initial_commands)
            .annotate(running_commands=running_commands)
            .annotate(done_commands=done_commands)
            .annotate(total_commands=Count("batchcommand"))
            .get(pk=pk)
        )

        return render(
            request,
            "batch_summary.html",
            {
                "pk": batch.pk,
                "status": batch.get_status_display(),
                "error_count": batch.error_commands,
                "initial_count": batch.initial_commands,
                "running_count": batch.running_commands,
                "done_count": batch.done_commands,
                "total_count": batch.total_commands,
                "done_percentage": float(100 * batch.done_commands) / batch.total_commands
                if batch.total_commands
                else 0,
            },
        )
    except Batch.DoesNotExist:
        return render(request, "batch_summary.html", {}, status=404)


@login_required()
def new_batch(request):
    """
    Creates a new batch
    """
    if request.method == "POST":
        try:
            batch_owner = request.user.username
            batch_commands = request.POST.get("commands")
            batch_name = request.POST.get("name", f"Batch  user:{batch_owner} {datetime.now().isoformat()}")
            batch_type = request.POST.get("type", "v1")
            request.session["preferred_batch_type"] = batch_type

            batch_commands = batch_commands.strip()
            if not batch_commands:
                raise ParserException("Command string cannot be empty")

            batch_name = batch_name.strip()
            if not batch_name:
                raise ParserException("Batch name cannot be empty")

            if batch_type == "v1":
                parser = V1CommandParser()
            else:
                parser = CSVCommandParser()
            
            batch = parser.parse(batch_name, batch_owner, batch_commands)
            return redirect(reverse("batch", args=[batch.pk]))
        except ParserException as p:
            error = p.message
        except Exception as p:
            error = str(p)
        return render(
            request,
            "new_batch.html",
            {
                "error": error,
                "name": batch_name,
                "batch_type": batch_type,
                "commands": batch_commands,
            },
        )

    else:
        preferred_batch_type = request.session.get("preferred_batch_type", "v1")
        return render(
            request,
            "new_batch.html",
            {
                "batch_type": preferred_batch_type,
            }
        )


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
    data = {}
    if request.user.is_authenticated:
        data["language_choices"] = LANGUAGE_CHOICES
        user = request.user
        if request.method == "POST":
            prefs, _ = Preferences.objects.get_or_create(user=user)
            prefs.language = request.POST["language"]
            prefs.save()
        data["language"] = Preferences.objects.get_language(user, "en")
    return render(request, "profile.html", data)
