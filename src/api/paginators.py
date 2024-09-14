

from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response


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
