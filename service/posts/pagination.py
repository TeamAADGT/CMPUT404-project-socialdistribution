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
            # Some groups end source in "/" some do not, we handle both cases.
            if post["source"][-1] == "/":
                post["next"] = post["source"] + "comments/"
            else:
                post["next"] = post["source"] + "/comments/"
            post["count"] = len(Comment.objects.filter(post_id=post["id"]))
            post["size"] = 50

        return Response({
            "query": "posts",
            "count": self.page.paginator.count,
            "size": self.page_size,
            "next": self.get_next_link(),
            "previous": self.get_previous_link(),
            "posts": data
        })
