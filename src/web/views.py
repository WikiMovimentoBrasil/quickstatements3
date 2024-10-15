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
from rest_framework.authtoken.models import Token

from core.client import Client
from core.models import Batch
from core.models import BatchCommand
from core.parsers.base import ParserException
from core.parsers.v1 import V1CommandParser
from core.parsers.csv import CSVCommandParser
from core.exceptions import NoToken
from core.exceptions import InvalidToken

from .utils import user_from_token, clear_tokens
from .models import Preferences
from .languages import LANGUAGE_CHOICES


PAGE_SIZE = 30


oauth = OAuth()
oauth.register(
    name="mediawiki",
    client_id=os.getenv("OAUTH_CLIENT_ID"),
    client_secret=os.getenv("OAUTH_CLIENT_SECRET"),
    access_token_url=f"{Client.BASE_REST_URL}/oauth2/access_token",
    authorize_url=f"{Client.BASE_REST_URL}/oauth2/authorize",
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
        is_autoconfirmed = None
        if current_owner and batch.is_preview:
            try:
                client = Client.from_user(request.user)
                is_autoconfirmed = client.get_is_autoconfirmed()
            except (NoToken, InvalidToken):
                is_autoconfirmed = False
        return render(
            request,
            "batch.html",
            {"batch": batch, "current_owner": current_owner, "is_autoconfirmed": is_autoconfirmed},
        )
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
        "POST",
    ]
)
def batch_allow_start(request, pk):
    """
    Allows a batch that is in the preview state to start running.
    """
    try:
        batch = Batch.objects.get(pk=pk)
        current_owner = request.user.is_authenticated and request.user.username == batch.user
        if current_owner:
            batch.allow_start()
        return redirect(reverse("batch", args=[batch.pk]))
    except Batch.DoesNotExist:
        return render(request, "batch_not_found.html", {"pk": pk}, status=404)


@require_http_methods(
    [
        "POST",
    ]
)
def batch_restart(request, pk):
    """
    Restart a batch that was previously stopped
    Allows a batch that is in the preview state to start running.
    """
    try:
        batch = Batch.objects.get(pk=pk)
        current_owner = request.user.is_authenticated and request.user.username == batch.user
        if current_owner:
            batch.restart()
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

    only_errors = int(request.GET.get("show_errors", 0)) == 1

    filters = {"batch__pk": pk}
    if only_errors:
        filters["status"] = BatchCommand.STATUS_ERROR

    paginator = Paginator(BatchCommand.objects.filter(**filters).order_by("index"), PAGE_SIZE)
    page = paginator.page(page)

    if request.user.is_authenticated:
        try:
            language = Preferences.objects.get_language(request.user, "en")
            client = Client.from_user(request.user)
            for command in page.object_list:
                command.display_label = command.get_label(client, language)
        except NoToken:
            pass

    return render(request, "batch_commands.html", {"page": page, "batch_pk": pk, "only_errors": only_errors})


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
        show_block_on_errors_notice = batch.is_preview_initial_or_running and batch.block_on_errors

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
                "show_block_on_errors_notice": show_block_on_errors_notice,
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
            batch.status = Batch.STATUS_PREVIEW

            if "block_on_errors" in request.POST:
                batch.block_on_errors = True

            batch.save()

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

        try:
            client = Client.from_user(request.user)
            is_autoconfirmed = client.get_is_autoconfirmed()
        except (NoToken, InvalidToken):
            is_autoconfirmed = False

        return render(
            request,
            "new_batch.html",
            {
                "batch_type": preferred_batch_type,
                "is_autoconfirmed": is_autoconfirmed,
            },
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
        except InvalidToken as e:
            data = {"error": e}
            return render(request, "login_dev.html", data, status=400)

        return redirect("/auth/profile/")
    else:
        return render(request, "login_dev.html", {})


def profile(request):
    data = {}
    if request.user.is_authenticated:
        user = request.user
        token, created = Token.objects.get_or_create(user=user)

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

        data["language"] = Preferences.objects.get_language(user, "en")
        data["language_choices"] = LANGUAGE_CHOICES
        data["token"] = token.key

        is_autoconfirmed = False
        token_failed = False

        try:
            client = Client.from_user(user)
            is_autoconfirmed = client.get_is_autoconfirmed()
        except (NoToken, InvalidToken):
            token_failed = True

        data["is_autoconfirmed"] = is_autoconfirmed
        data["token_failed"] = token_failed

    return render(request, "profile.html", data)
