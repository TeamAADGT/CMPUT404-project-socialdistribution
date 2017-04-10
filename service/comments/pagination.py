from rest_framework import pagination
from rest_framework.response import Response


class CommentsPagination(pagination.PageNumberPagination):
    """
    Source: http://www.django-rest-framework.org/api-guide/pagination/
    """

    page_size_query_param = "size"

    def get_paginated_response(self, data):
        return Response({
            "query": "comments",
            "count": self.page.paginator.count,
            "size": self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "comments": data
        })
