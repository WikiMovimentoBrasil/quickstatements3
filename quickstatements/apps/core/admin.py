from django.contrib import admin

from .models import Batch, BatchCommand


@admin.register(BatchCommand)
class BatchCommandAdmin(admin.ModelAdmin):
    list_select_related = ["batch"]
    list_display = ["batch", "index", "operation", "status", "error", "created", "modified"]
    list_filter = ["operation", "status", "error", "created", "modified"]
    search_field = ["batch__name", "batch__user"]
    raw_id_fields = ["batch"]


class BatchCommandInline(admin.TabularInline):
    model = BatchCommand
    show_change_link = True
    ordering = ["batch", "index"]
    fields = [
        "operation",
        "status",
        "error",
        "json",
    ]


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ["name", "user", "status", "created", "modified"]
    search_field = ["name", "user"]
    list_filter = ["status", "created", "modified"]
    inlines = [BatchCommandInline]
