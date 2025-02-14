from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("quickstatements.apps.api.urls")),
    path("", include("quickstatements.apps.web.urls")),
]
