from django.urls import path

from .views import batch
from .views import batch_commands
from .views import batch_allow_start
from .views import batch_stop
from .views import batch_restart
from .views import batch_summary
from .views import home
from .views import last_batches
from .views import last_batches_by_user
from .views import login
from .views import logout
from .views import login_dev
from .views import new_batch
from .views import oauth_redirect
from .views import oauth_callback
from .views import profile


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
    path("batch/<int:pk>/allow_start/", batch_allow_start, name="batch_allow_start"),
    path("batch/<int:pk>/stop/", batch_stop, name="batch_stop"),
    path("batch/<int:pk>/restart/", batch_restart, name="batch_restart"),
    path("batch/<int:pk>/summary/", batch_summary, name="batch_summary"),
    path("batch/<int:pk>/commands/", batch_commands, name="batch_commands"),
    path("batch/new/", new_batch, name="new_batch"),
]
