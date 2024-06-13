from django.urls import path

from .views import (
    login,
    logout,
    login_dev,
    profile,
)

urlpatterns = [
    path("auth/login/", login, name="login"),
    path("auth/logout/", logout, name="logout"),
    path("auth/login/dev/", login_dev, name="login_dev"),
    path("auth/profile/", profile, name="profile"),
]
