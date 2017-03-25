from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer

    def get_queryset(self):
        if "pk" in self.kwargs:
            return Post.objects.all()
        else:
            return Post.objects.filter(visibility="PUBLIC")
