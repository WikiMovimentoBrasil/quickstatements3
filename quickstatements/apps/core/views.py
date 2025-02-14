from django.http import Http404
from rest_framework import generics, mixins
from rest_framework.authentication import TokenAuthentication
from rest_framework.permissions import IsAuthenticated

from quickstatements.apps.core.models import Batch, BatchCommand

from .paginators import CustomBatchCommandPagination, CustomPagination
from .serializers import (
    BatchCommandDetailSerializer,
    BatchCommandListSerializer,
    BatchDetailSerializer,
    BatchListSerializer,
)


class BatchListView(generics.GenericAPIView, mixins.ListModelMixin):
    """
    Available batches listing
    """

    pagination_class = CustomPagination
    serializer_class = BatchListSerializer

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        queryset = Batch.objects.all().order_by("-created")
        user = self.request.query_params.get("username")
        if user is not None:
            queryset = queryset.filter(user=user)
        status = self.request.query_params.get("status")
        if status is not None:
            queryset = queryset.filter(status=status)
        return queryset

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BatchDetailView(generics.GenericAPIView, mixins.RetrieveModelMixin):
    """
    Batch detail
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = Batch.objects.all()
    serializer_class = BatchDetailSerializer

    def get_object(self):
        from django.db.models import Count, Q

        try:
            error_commands = Count(
                "batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_ERROR)
            )
            initial_commands = Count(
                "batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_INITIAL)
            )
            running_commands = Count(
                "batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_RUNNING)
            )
            done_commands = Count(
                "batchcommand", filter=Q(batchcommand__status=BatchCommand.STATUS_DONE)
            )
            batch = (
                Batch.objects.annotate(error_commands=error_commands)
                .annotate(initial_commands=initial_commands)
                .annotate(running_commands=running_commands)
                .annotate(done_commands=done_commands)
                .annotate(total_commands=Count("batchcommand"))
                .get(pk=self.kwargs["pk"])
            )
            return batch
        except Batch.DoesNotExist:
            raise Http404

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class BatchCommandListView(generics.GenericAPIView, mixins.ListModelMixin):
    """
    Batch commands listing. Uses pagination.
    """

    authentication_classes = [
        TokenAuthentication,
    ]
    permission_classes = [IsAuthenticated]

    pagination_class = CustomBatchCommandPagination
    serializer_class = BatchCommandListSerializer

    def get_queryset(self):
        return (
            BatchCommand.objects.select_related("batch")
            .filter(batch__pk=self.kwargs["batchpk"])
            .order_by("index")
        )

    def get(self, request, *args, **kwargs):
        try:
            batch = Batch.objects.get(pk=kwargs["batchpk"])
            request.batch = batch
        except Batch.DoesNotExist:
            raise Http404
        return self.list(request, *args, **kwargs)


class BatchCommandDetailView(generics.GenericAPIView, mixins.RetrieveModelMixin):
    """
    Batch command detail
    """

    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    queryset = BatchCommand.objects.select_related("batch").all()
    serializer_class = BatchCommandDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
