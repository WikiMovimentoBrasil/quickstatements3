from django.urls import path

import views

urlpatterns = [
    path("", views.home),    
    path("auth/login/", views.login, name="login"),
    path("auth/logout/", view.logout, name="logout"),
    path("auth/login/dev/", views.login_dev, name="login_dev"),
    path("auth/profile/", views.profile, name="profile"),

    path("batches", views.last_batches),
    path("batches/<str:user>", views.last_batches_by_user),
    path("batch/<int:pk>", views.batch),
]
