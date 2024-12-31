from datetime import datetime

from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.utils.translation import gettext as _

from core.client import Client
from core.models import BatchCommand
from core.parsers.base import ParserException
from core.parsers.v1 import V1CommandParser
from core.parsers.csv import CSVCommandParser
from core.exceptions import NoToken
from core.exceptions import UnauthorizedToken
from core.exceptions import ServerError

from django.core import serializers

from web.models import Preferences

from .auth import logout_per_token_expired


PAGE_SIZE = 30


@require_http_methods(
    [
        "GET",
    ]
)
def preview_batch(request):
    """
    Base call for a batch. Returns the main page, that will load 2 fragments: commands and summary
    Used for ajax calls
    """
    preview_batch = request.session.get("preview_batch")
    if preview_batch:
        total_count = 0
        initial_count = 0
        error_count = 0
        batch = list(serializers.deserialize("json", preview_batch))[0]
        preview_batch_commands = request.session.get("preview_commands", "[]")
        batch_commands = list(serializers.deserialize("json", preview_batch_commands))
        for bc in batch_commands:
            total_count += 1
            if bc.object.status == BatchCommand.STATUS_ERROR:
                error_count += 1
            else:
                initial_count += 1

        is_autoconfirmed = None
        try:
            client = Client.from_user(request.user)
            is_autoconfirmed = client.get_is_autoconfirmed()
        except UnauthorizedToken:
            return logout_per_token_expired(request)
        except (NoToken, ServerError):
            is_autoconfirmed = False

        return render(
            request,
            "preview_batch.html",
            {
                "batch": batch.object,
                "current_owner": True,
                "is_autoconfirmed": is_autoconfirmed,
                "total_count": total_count,
                "initial_count": initial_count,
                "error_count": error_count,
            },
        )
    else:
        return redirect(reverse("new_batch"))


@require_http_methods(
    [
        "GET",
    ]
)
def preview_batch_commands(request):
    """
    RETURNS fragment page with PAGINATED COMMANDs FOR A GIVEN BATCH ID
    Used for ajax calls
    """
    preview_batch_commands = request.session.get("preview_commands")
    if preview_batch_commands:
        batch_commands = list(serializers.deserialize("json", preview_batch_commands))

        try:
            page = int(request.GET.get("page", 1))
        except (TypeError, ValueError):
            page = 1

        only_errors = int(request.GET.get("show_errors", 0)) == 1
        if only_errors:
            batch_commands = [
                bc for bc in batch_commands if bc.object.status == BatchCommand.STATUS_ERROR
            ]

        paginator = Paginator(batch_commands, PAGE_SIZE)
        page = paginator.page(page)
        page.object_list = [
            d.object for d in page.object_list
        ]

        if request.user.is_authenticated:
            client = Client.from_user(request.user)
            language = Preferences.objects.get_language(request.user, "en")
            for command in page.object_list:
                command.display_label = command.get_label(client, language)


    base_url = reverse("preview_batch_commands")
    return render(request, "batch_commands.html", {"page": page, "only_errors": only_errors, "base_url": base_url})


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

            if "block_on_errors" in request.POST:
                batch.block_on_errors = True

            serialized_batch = serializers.serialize("json", [batch])
            serialized_commands = serializers.serialize("json", batch.get_preview_commands())

            request.session["preview_batch"] = serialized_batch
            request.session["preview_commands"] = serialized_commands

            return redirect(reverse("preview_batch"))
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
        except UnauthorizedToken:
            return logout_per_token_expired(request)
        except (NoToken, ServerError):
            is_autoconfirmed = False

        return render(
            request,
            "new_batch.html",
            {
                "batch_type": preferred_batch_type,
                "is_autoconfirmed": is_autoconfirmed,
            },
        )


@require_http_methods(["POST"])
def batch_allow_start(request):
    """
    Saves and allow a batch that is in the preview state to start running.
    """
    is_autoconfirmed = False
    try:
        client = Client.from_user(request.user)
        is_autoconfirmed = client.get_is_autoconfirmed()
    except UnauthorizedToken:
        return logout_per_token_expired(request)
    except (NoToken, ServerError):
        is_autoconfirmed = False

    if not is_autoconfirmed:
        return render(
            request,
            "new_batch.html",
            {
                "is_autoconfirmed": is_autoconfirmed,
                "error": _("User is not autoconfirmed. Only autoconfirmed users can run batches."),
            },
        )

    try:
        preview_batch = request.session.get("preview_batch")
        if preview_batch:

            batch = list(serializers.deserialize("json", preview_batch))[0].object

            preview_batch_commands = request.session.get("preview_commands", "[]")
            for batch_command in serializers.deserialize("json", preview_batch_commands):
                batch.add_preview_command(batch_command.object)
            batch.save_batch_and_preview_commands()

            del request.session["preview_batch"]
            del request.session["preview_commands"]

            return redirect(reverse("batch", args=[batch.pk]))
        else:
            return redirect(reverse("new_batch"))

    except Exception as e:
        return render(request, "batch_not_found.html", status=404)
