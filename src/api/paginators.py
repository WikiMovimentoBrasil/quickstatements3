

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.reverse import reverse_lazy


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
        batch = self.request.batch # We injected batch reference in the view
        return Response(
            {
                "links": {"next": self.get_next_link(), "previous": self.get_previous_link()},
                "total": self.page.paginator.count,
                "page_size": len(self.page.object_list),
                "batch": {
                    "pk": batch.pk,
                    "url": reverse_lazy("batch-detail", kwargs={"pk": batch.pk}, request=self.request)
                },
                "commands": data,
            }
        )
