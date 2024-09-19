from django.contrib import admin

from core.models import Batch
from core.models import BatchCommand


@admin.register(Batch)
class BatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'status', 'created', 'modified']
    search_field = ['name', 'user']
    list_filter = ['status', 'created', 'modified']


@admin.register(BatchCommand)
class BatchCommandAdmin(admin.ModelAdmin):
    list_select_related = ["batch",]
    list_display = ['batch', 'index', 'status', 'created', 'modified']
    list_filter = ['status', 'created', 'modified']
    search_field = ['batch__name', 'batch__user']
    raw_id_field = ['batch']
