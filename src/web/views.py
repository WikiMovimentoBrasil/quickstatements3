
from django.http import HttpResponse
from django.http import HttpResponseNotFound
from django.shortcuts import render
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