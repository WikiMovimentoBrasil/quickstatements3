from django.urls import path

from .views import (
    login,
    login_dev,
    profile,
)

urlpatterns = [
    path("auth/login/", login, name="login"),
    path("auth/login/dev/", login_dev, name="login_dev"),
    path("auth/profile/", profile, name="profile"),
]
