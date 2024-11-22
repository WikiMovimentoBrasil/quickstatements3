from django.core.paginator import Paginator
from django.shortcuts import render
from django.views.decorators.http import require_http_methods

from core.models import Batch


PAGE_SIZE = 30


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
