from rest_framework import viewsets

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)

    def get_queryset(self):
        if "pk" in self.kwargs:
            return Post.objects.all()
        else:
            return Post.objects.filter(visibility="PUBLIC")
