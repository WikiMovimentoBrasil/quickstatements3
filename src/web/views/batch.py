from django.core.paginator import Paginator
from django.shortcuts import redirect
from django.shortcuts import render
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.http import require_GET
from django.http import HttpResponse

from core.client import Client
from core.models import Batch
from core.models import BatchCommand
from core.exceptions import NoToken
from core.exceptions import UnauthorizedToken
from core.exceptions import ServerError

from web.models import Preferences

from .auth import logout_per_token_expired


PAGE_SIZE = 30


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

@require_GET
def batch_report(request, pk):
    try:
        batch = Batch.objects.get(pk=pk)
        current_owner = request.user.is_authenticated and request.user.username == batch.user
        if current_owner and batch.is_done:
            res = HttpResponse(
                content_type="text/csv",
                headers={"Content-Disposition": f'attachment; filename="batch-{pk}-report.csv"'},
            )
            batch.write_report(res)
            return res
        else:
            return render(request, "batch_not_found.html", {"pk": pk}, status=404)
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
        except UnauthorizedToken:
            # logout but do not return 302, since this
            # is called through HMTX
            logout_per_token_expired(request)
        except (NoToken, ServerError):
            pass

    base_url = reverse("batch_commands", args=[pk])
    return render(request, "batch_commands.html", {"page": page, "batch_pk": pk, "only_errors": only_errors, "base_url": base_url})


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

        response = render(
            request,
            "batch_summary.html",
            {
                "pk": batch.pk,
                "batch": batch,
                "status": batch.get_status_display(),
                "error_count": batch.error_commands,
                "initial_count": batch.initial_commands,
                "running_count": batch.running_commands,
                "done_count": batch.done_commands,
                "total_count": batch.total_commands,
                "done_percentage": round(float(100 * batch.done_commands) / batch.total_commands, 1)
                if batch.total_commands
                else 0,
                "show_block_on_errors_notice": show_block_on_errors_notice,
            },
        )
        if batch.is_done:
            previous_status = request.GET.get("previous_status")
            if previous_status and previous_status != str(batch.STATUS_DONE):
                # Refreshing the page to load the correct buttons
                # and reload the command list if it's the first DONE
                response.headers["HX-Refresh"] = "true"
        return response
    except Batch.DoesNotExist:
        return render(request, "batch_summary.html", {}, status=404)
