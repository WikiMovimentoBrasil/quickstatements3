
from django.urls import path
from rest_framework.urlpatterns import format_suffix_patterns
from api import views

urlpatterns = [
    path('batches/', views.BatchListView.as_view()),
    path('batches/<int:pk>/', views.BatchDetailView.as_view(), name="batch-detail"),
    path('batches/<int:batchpk>/commands/', views.BatchCommandListView.as_view(), name="batch-commands"),
    path('commands/<int:pk>', views.BatchCommandDetailView.as_view(), name="batchcommand-detail"),
]

urlpatterns = format_suffix_patterns(urlpatterns)