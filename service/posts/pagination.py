import urlparse

from rest_framework import pagination
from rest_framework.response import Response
from rest_framework.reverse import reverse

from social.app.models.comment import Comment


class PostsPagination(pagination.PageNumberPagination):
    """
    Source: http://www.django-rest-framework.org/api-guide/pagination/
    """

    page_size_query_param = "size"

    def get_paginated_response(self, data):
        # The Comment page size when nested in a Post, as per spec
        comment_page_size = 5

        for post in data:
            comments_count = len(post["comments"])

            if comments_count > comment_page_size:
                # Only show the first page of Comments
                post["comments"] = post["comments"][:comment_page_size]

            # Always give the link to the first page of Comments, as per spec
            post["next"] = reverse('service:post-comments-list', kwargs={'pk': post["id"]}, request=self.request)
            post["count"] = comments_count
            post["size"] = comment_page_size

        return Response({
            "query": "posts",
            "count": self.page.paginator.count,
            "size": self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "posts": data
        })
