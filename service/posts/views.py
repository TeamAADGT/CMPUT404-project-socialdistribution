from rest_framework import viewsets, views, generics
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsList(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        queryset = Post.objects.filter(visibility="PUBLIC")

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

    @list_route(methods=['GET'], authentication_classes=(NodeBasicAuthentication,))
    def all_posts(self, request, *args, **kwargs):
        return self.list(request, *args, **kwargs)


class AuthorPostsView(generics.ListAPIView):
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

