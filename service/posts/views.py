from django.db.models import Q
from rest_framework import viewsets, views, generics, mixins
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


# /service/posts/
class PublicPostsList(generics.ListAPIView):
    """
    Returns all local posts set to public visibility.
    
    Does not require authentication.

    Example response:
    <pre>
    {
      &nbsp&nbsp&nbsp"count": 1,
      &nbsp&nbsp&nbsp"posts": [
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp{
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"title": "test",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"source": "http://127.0.0.1:8000/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"origin": "http://127.0.0.1:8000/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"description": "etes",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"contentType": "text/markdown",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"content": "testg",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"author": {
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"host": "http://127.0.0.1:8000/service/",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"displayName": "bob bob",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"github": "https://github.com/tiegan"
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp},
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"categories": [],
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"comments": [],
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"published": "2017-04-09T19:48:07.236149Z",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id": "ab38123f-8290-4902-a5ce-0a4db70ce7c1",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url": "http://127.0.0.1:8000/service/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"visibility": "PUBLIC",
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"visibleTo": [],
          &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"unlisted": false
        &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp}
      &nbsp&nbsp&nbsp],
      &nbsp&nbsp&nbsp"next": null,
      &nbsp&nbsp&nbsp"query": "posts",
      &nbsp&nbsp&nbsp"size": 100,
      &nbsp&nbsp&nbsp"previous": null
    }
    </pre>
    """
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)

    # No permission class

    def get_queryset(self):
        remote_node = self.request.user

        return get_local_posts(remote_node, public_only=True)


# Defined as a ViewSet so a custom function can be defined to get around schema weirdness -- see all_posts()
# /service/author/posts
class AllPostsViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    All the posts on the host are returned.

    To see an example look at /service/posts/, only difference being that /service/author/posts
    contains all posts.
    """
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


# /service/posts/{id}/
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


# /service/author/{id}/posts
class AuthorPostsView(generics.ListAPIView):
    """
    Returns all posts of an author that a user is allowed to see, can require authentication.

    For an example of this look at /service/posts/, only differences being the author ID of
    a post will always be the same and the visibility will vary.
    """
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
