from django.urls import path

from .views import home
from .views import login
from .views import logout
from .views import login_dev
from .views import profile
from .views import last_batches
from .views import last_batches_by_user
from .views import batch


urlpatterns = [
    path("", home, name="home"),
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("auth/login/dev/", login_dev, name="login_dev"),
    path("auth/profile/", profile, name="profile"),
    path("batches/", last_batches, name="last_batches"),
    path("batches/<str:user>/", last_batches_by_user, name="last_batches_by_user"),
    path("batch/<int:pk>/", batch, name="batch"),
]
