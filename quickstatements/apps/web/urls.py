from django.urls import path

from .views.auth import login
from .views.auth import logout
from .views.auth import login_dev
from .views.auth import oauth_redirect
from .views.auth import oauth_callback
from .views.batch import batch
from .views.batch import batch_commands
from .views.batch import batch_stop
from .views.batch import batch_restart
from .views.batch import batch_report
from .views.batch import batch_summary
from .views.batches import home
from .views.batches import last_batches
from .views.batches import last_batches_by_user
from .views.new_batch import batch_allow_start
from .views.new_batch import new_batch
from .views.new_batch import preview_batch
from .views.new_batch import preview_batch_commands
from .views.profile import profile


urlpatterns = [
    path("", home, name="home"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("auth/login/dev/", login_dev, name="login_dev"),
    path("auth/profile/", profile, name="profile"),
    path("auth/redirect/", oauth_redirect, name="oauth_redirect"),
    path("auth/callback/", oauth_callback, name="oauth_callback"),
    path("batches/", last_batches, name="last_batches"),
    path("batches/<str:user>/", last_batches_by_user, name="last_batches_by_user"),
    path("batch/<int:pk>/", batch, name="batch"),
    path("batch/preview/", batch, name="batch_preview"),
    path("batch/<int:pk>/stop/", batch_stop, name="batch_stop"),
    path("batch/<int:pk>/restart/", batch_restart, name="batch_restart"),
    path("batch/<int:pk>/report/", batch_report, name="batch_report"),
    path("batch/<int:pk>/summary/", batch_summary, name="batch_summary"),
    path("batch/<int:pk>/commands/", batch_commands, name="batch_commands"),
    path("batch/new/", new_batch, name="new_batch"),
    path("batch/new/preview/", preview_batch, name="preview_batch"),
    path("batch/new/preview/commands/", preview_batch_commands, name="preview_batch_commands"),
    path("batch/new/preview/allow_start/", batch_allow_start, name="batch_allow_start"),
]
