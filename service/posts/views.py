from rest_framework import viewsets, views, generics
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post
from social.app.models.node import Node

# TODO: lot's of duplication here.

# /service/author/posts/
# /service/posts/
# Note: Josh said these behave the same for authenticated users
class AllPostsViewSet(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        # Only share the posts that originated on our server (local)
        local_node = Node.objects.filter(local=True).get()
        queryset = Post.objects.exclude(visibility="SERVERONLY") \
            .filter(source__icontains=local_node.host)

        if not self.request.user.is_authenticated: # Not authenticated
            queryset = queryset.filter(visibility="PUBLIC")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        return queryset


# TODO: Don't think this works. Hard to test now as service/ is broken
# service/posts/<post_giud>/
class ParticularPostViewSet(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        node = self.request.user

        if not node.share_posts:
            return Post.objects.none()

        # Only share the posts that originated on our server (local)
        local_node = Node.objects.filter(local=True).get()
        queryset = Post.objects.filter(post__id=post_id) \
            .exclude(visibility="SERVERONLY") \
            .filter(source__icontains=local_node.host)

        if not self.request.user.is_authenticated:  # Not authenticated
            queryset = queryset.filter(visibility="PUBLIC")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        print queryset
        return queryset


# service/author/<author_giud>/posts/
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

        # Only share the posts that originated on our server (local)
        local_node = Node.objects.filter(local=True).get()
        queryset = Post.objects.filter(author__id=author_id)\
            .exclude(visibility="SERVERONLY") \
            .filter(source__icontains=local_node.host)

        if not self.request.user.is_authenticated:  # Not authenticated
            queryset = queryset.filter(visibility="PUBLIC")

        if not node.share_images:
            queryset = queryset.exclude(is_image=True)

        print queryset
        return queryset


