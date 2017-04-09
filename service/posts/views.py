from django.db.models import Q
from rest_framework import viewsets, views, generics, mixins
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


class PublicPostsList(generics.ListAPIView):
    """
    Returns all local posts set to public visibility.
    
    Does not require authentication.
    
    For all posts, see /service/author/posts/.
    """
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)

    # No permission class

    def get_queryset(self):
        remote_node = self.request.user

        return get_local_posts(remote_node, public_only=True)


# Defined as a ViewSet so a custom function can be defined to get around schema weirdness -- see all_posts()
class AllPostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        remote_node = self.request.user

        return get_local_posts(remote_node)

    @list_route(methods=['GET'], authentication_classes=(NodeBasicAuthentication,), permission_classes=(IsAuthenticated,))
    def all_posts(self, request, *args, **kwargs):
        # Needed to make sure this shows up in the schema -- collides with /posts/ otherwise
        return self.list(request, *args, **kwargs)


class SpecificPostsView(generics.ListAPIView):
    """
    Returns the local post with the specified ID, if any.
    
    If the local post has an attached image, and the current remote node has permission to view images, the post
    containing that image is also returned. In other words, this endpoint will always return 0-2 posts.
    """
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        remote_node = self.request.user

        return get_local_posts(remote_node).filter(Q(id=post_id) | Q(parent_post__id=post_id))


class AuthorPostsView(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        author_id = self.kwargs["pk"]
        remote_node = self.request.user

        return get_local_posts(remote_node).filter(author__id=author_id)


def get_local_posts(remote_node, public_only=False):
    anonymous_node = remote_node is None or not remote_node.is_authenticated

    if not anonymous_node and not remote_node.share_posts:
        # We're specifically blocking this node, so short-circuit and return nothing
        return Post.objects.none()

    queryset = Post.objects.filter(author__node__local=True)

    if anonymous_node or public_only:
        # Only send 'em public posts if we don't know them, or they're asking for just these
        queryset = queryset.filter(visibility="PUBLIC")
    else:
        # We trust this node, so send them everything
        queryset = queryset.exclude(visibility="SERVERONLY")

    if anonymous_node or not remote_node.share_images:
        # If a node isn't authenticated or we just decided to not do it, don't send over images
        queryset = queryset.filter(content_type__in=[key for (key, value) in Post.TEXT_CONTENT_TYPES])

    return queryset
