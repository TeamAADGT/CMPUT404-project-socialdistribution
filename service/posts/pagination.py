import urlparse

from rest_framework import pagination
from rest_framework.response import Response
from social.app.models.comment import Comment


class PostsPagination(pagination.PageNumberPagination):
    """
    Source: http://www.django-rest-framework.org/api-guide/pagination/
    """

    page_size_query_param = "size"

    def get_paginated_response(self, data):
        for post in data:
            post["next"] = urlparse.urljoin(post["source"], "comments/")
            post["count"] = Comment.objects.filter(post_id=post["id"]).count()
            post["size"] = 50

        return Response({
            "query": "posts",
            "count": self.page.paginator.count,
            "size": self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "posts": data
        })
