from rest_framework import viewsets, views, generics
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post
from social.app.models.node import Node

class PublicPostsList(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        # Only share public posts that originated on our server (local)
        local_node = Node.objects.filter(local=True).get()
        queryset = Post.objects.filter(visibility="PUBLIC").filter(source__icontains=local_node.host)

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        return queryset


class AllPostsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        queryset = Post.objects.exclude(visibility="SERVERONLY")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        return queryset


class AuthorPostsList(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        author_id = self.kwargs["pk"]
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        queryset = Post.objects.filter(author__id=author_id)
        queryset = queryset.exclude(visibility="SERVERONLY")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        return queryset
