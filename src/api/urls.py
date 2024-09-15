
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views


urlpatterns = [
    path('batches/', views.BatchListView.as_view(), name="batch-list"),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name="batch-detail"),
    path('batches/<int:batchpk>/commands/', views.BatchCommandListView.as_view(), name="command-list"),
    path('commands/<int:pk>', views.BatchCommandDetailView.as_view(), name="command-detail"),
]

urlpatterns = format_suffix_patterns(urlpatterns)