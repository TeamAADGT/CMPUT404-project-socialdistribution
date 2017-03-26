from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        if "pk" in self.kwargs:
            queryset = Post.objects.all()
        else:
            queryset = Post.objects.filter(visibility="PUBLIC")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        return queryset
