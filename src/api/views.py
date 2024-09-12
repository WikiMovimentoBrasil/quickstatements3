from django.contrib.auth.models import Group, User
from rest_framework import serializers

from rest_framework import mixins
from rest_framework import generics
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination

from core.models import Batch
from core.models import BatchCommand


class CustomPagination(PageNumberPagination):
    page_size = 20
    max_page_size = 20

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "filters": self.request.query_params,
                "total": self.page.paginator.count,
                "page_size": len(self.page.object_list),
                "batches": data,
            }
        )


class CustomBatchCommandPagination(PageNumberPagination):
    page_size = 100
    max_page_size = 100

    def get_paginated_response(self, data):
        return Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "total": self.page.paginator.count,
                "page_size": len(self.page.object_list),
                "commands": data,
            }
        )


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
# SERIALIZERS
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################


class BatchListSerializer(serializers.HyperlinkedModelSerializer):
    """
    Simple Serializer used for API listing and BatchCommands
    """

    status = serializers.SerializerMethodField()

    def get_status(self, obj):
        return {"code": obj.status, "display": obj.get_status_display()}

    class Meta:
        model = Batch
        fields = ["url", "pk", "user", "name", "status", "message", "created", "modified"]


class BatchDetailSerializer(serializers.HyperlinkedModelSerializer):
    """
    Full batch serializer
    """

    status = serializers.SerializerMethodField()
    commands_url = serializers.SerializerMethodField()

    def get_status(self, obj):
        return {"code": obj.status, "display": obj.get_status_display()}

    def get_commands_url(self, obj):
        return reverse_lazy("batch-commands", kwargs={"batchpk": obj.pk}, request=self.context["request"])

    class Meta:
        model = Batch
        fields = ["pk", "name", "user", "status", "commands_url", "message", "created", "modified"]


class BatchCommandListSerializer(serializers.HyperlinkedModelSerializer):
    """
    Simple BatchCommand used for simple listing
    """

    url = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_action(self, obj):
        return obj.get_action_display()

    def get_url(self, obj):
        return reverse_lazy("batchcommand-detail", kwargs={"pk": obj.pk}, request=self.context["request"])

    class Meta:
        model = BatchCommand
        fields = ["url", "pk", "index", "action", "json", "status", "created", "modified"]


class BatchCommandDetailSerializer(serializers.HyperlinkedModelSerializer):
    """
    FULL batch command serializer
    """

    batch = BatchListSerializer()
    status = serializers.SerializerMethodField()
    action = serializers.SerializerMethodField()

    def get_action(self, obj):
        return obj.get_action_display()

    def get_status(self, obj):
        return {"code": obj.status, "display": obj.get_status_display()}

    class Meta:
        model = BatchCommand
        fields = ["batch", "index", "action", "raw", "json", "response_json", "status", "created", "modified"]


#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
# VIEWS
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################
#####################################################################################


class BatchListView(mixins.ListModelMixin, generics.GenericAPIView):
    """
    Available batches listing
    """

    pagination_class = CustomPagination
    serializer_class = BatchListSerializer

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


class BatchDetailView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    """
    Batch detail
    """

    queryset = Batch.objects.all()
    serializer_class = BatchDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)


class BatchCommandListView(generics.GenericAPIView, mixins.ListModelMixin):
    pagination_class = CustomBatchCommandPagination
    serializer_class = BatchCommandListSerializer

    def get_queryset(self):
        return BatchCommand.objects.select_related("batch").filter(batch__pk=self.kwargs["batchpk"]).order_by("index")

    def get(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class BatchCommandDetailView(mixins.RetrieveModelMixin, generics.GenericAPIView):
    queryset = BatchCommand.objects.select_related("batch").all()
    serializer_class = BatchCommandDetailSerializer

    def get(self, request, *args, **kwargs):
        return self.retrieve(request, *args, **kwargs)
