from django.db.models import Q
from rest_framework import viewsets, views, generics, mixins
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer
from social.app.models.post import Post


# TODO: If ViewSet used it goes from post to default - should be fixed
# original: generics.ListAPIView
# /service/posts/
class PublicPostsList(viewsets.ReadOnlyModelViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)

    # No permission class

    def get_queryset(self):
        """
        Returns all local posts set to public visibility.
    
        Does not require authentication.

        Example response:

            {
              "count": 1,
              "posts": [
                {
                  "title": "test",
                  "source": "http://127.0.0.1:8000/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
                  "origin": "http://127.0.0.1:8000/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
                  "description": "etes",
                  "contentType": "text/markdown",
                  "content": "testg",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "bob bob",
                    "url": "http://127.0.0.1:8000/service/author/447c20fd-6fe2-4ea5-a9f7-2edabe2cc92c/",
                    "github": "https://github.com/tiegan"
                  },
                  "categories": [],
                  "comments": [],
                  "published": "2017-04-09T19:48:07.236149Z",
                  "id": "ab38123f-8290-4902-a5ce-0a4db70ce7c1",
                  "url": "http://127.0.0.1:8000/service/posts/ab38123f-8290-4902-a5ce-0a4db70ce7c1/",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false
                }
              ],
              "next": null,
              "query": "posts",
              "size": 100,
              "previous": null
            }
        """
        remote_node = self.request.user

        return get_local_posts(remote_node, public_only=True)


# Defined as a ViewSet so a custom function can be defined to get around schema weirdness -- see all_posts()
# /service/author/posts
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
        """
        All the posts on the host are returned.

        Example response:

            {
              "count": 2,
              "posts": [
                {
                  "title": "test",
                  "source": "http://127.0.0.1:8000/service/posts/19e627d8-33e7-4fc5-8701-da57db633a3b",
                  "origin": "http://127.0.0.1:8000/service/posts/19e627d8-33e7-4fc5-8701-da57db633a3b",
                  "description": "test",
                  "contentType": "text/markdown",
                  "content": "test",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "bob bob",
                    "url": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                    "github": ""
                  },
                  "categories": [],
                  "comments": [
                    {
                      "id": "4312dbf4-a0b1-472b-8ceb-82ca96d6eefc",
                      "author": {
                        "id": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                        "host": "http://127.0.0.1:8000/service/",
                        "displayName": "bob bob",
                        "url": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                        "github": ""
                      },
                      "comment": "test",
                      "published": "2017-04-10T21:02:53.960530Z",
                      "contentType": "text/markdown"
                    }
                  ],
                  "published": "2017-04-10T21:02:51.003165Z",
                  "id": "19e627d8-33e7-4fc5-8701-da57db633a3b",
                  "url": "http://127.0.0.1:8000/service/posts/19e627d8-33e7-4fc5-8701-da57db633a3b",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/19e627d8-33e7-4fc5-8701-da57db633a3b/comments",
                  "count": 1,
                  "size": 50
                },
                {
                  "title": "Hi",
                  "source": "http://127.0.0.1:8000/service/posts/c886747e-d1ce-4afc-bbeb-8a85d88ce694",
                  "origin": "http://127.0.0.1:8000/service/posts/c886747e-d1ce-4afc-bbeb-8a85d88ce694",
                  "description": "I Am",
                  "contentType": "text/plain",
                  "content": "A Post!",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "bob bob",
                    "url": "http://127.0.0.1:8000/service/author/eab83f72-d839-471f-881c-0e5d939e13c0",
                    "github": ""
                  },
                  "categories": [
                    "Wow",
                    "Fun"
                  ],
                  "comments": [],
                  "published": "2017-04-10T21:38:52.819887Z",
                  "id": "c886747e-d1ce-4afc-bbeb-8a85d88ce694",
                  "url": "http://127.0.0.1:8000/service/posts/c886747e-d1ce-4afc-bbeb-8a85d88ce694",
                  "visibility": "PRIVATE",
                  "visibleTo": [],
                  "unlisted": true,
                  "next": "http://127.0.0.1:8000/service/posts/c886747e-d1ce-4afc-bbeb-8a85d88ce694/comments",
                  "count": 0,
                  "size": 50
                }
              ],
              "next": null,
              "query": "posts",
              "size": 100,
              "previous": null
            }
        """
        # Needed to make sure this shows up in the schema -- collides with /posts/ otherwise
        return self.list(request, *args, **kwargs)


# TODO: This disappears when set to ViewSet
# /service/posts/{id}/
class SpecificPostsView(generics.ListAPIView):
    """
    Returns the local post with the specified ID, if any.
    
    If the local post has an attached image, and the current remote node has permission to view images, the post
    containing that image is also returned. In other words, this endpoint will always return 0-2 posts.

    Example Image Post Response

            {
              "count": 2,
              "posts": [
                {
                  "title": "Connor McDavid",
                  "source": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374",
                  "origin": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374",
                  "description": "MVP",
                  "contentType": "text/markdown",
                  "content": "He's the best.",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Ralph Wiggum",
                    "url": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "github": ""
                  },
                  "categories": [
                    "MVP"
                  ],
                  "comments": [],
                  "published": "2017-04-10T21:50:25.802530Z",
                  "id": "682449e4-0295-418a-864c-c1f64b2a0374",
                  "url": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374/comments",
                  "count": 0,
                  "size": 50
                },
                {
                  "title": "Upload",
                  "source": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374",
                  "origin": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374",
                  "description": "Upload",
                  "contentType": "image/png;base64",
                  "content": "(image bytes)"
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Ralph Wiggum",
                    "url": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "github": ""
                  },
                  "categories": [
                    "MVP"
                  ],
                  "comments": [],
                  "published": "2017-04-10T21:50:25.830513Z",
                  "id": "4ce5f723-6ab8-4578-add1-1999b9057294",
                  "url": "http://127.0.0.1:8000/service/posts/4ce5f723-6ab8-4578-add1-1999b9057294",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/682449e4-0295-418a-864c-c1f64b2a0374/comments",
                  "count": 0,
                  "size": 50
                }
              ],
              "next": null,
              "query": "posts",
              "size": 100,
              "previous": null
            }
    """
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        remote_node = self.request.user

        return get_local_posts(remote_node).filter(Q(id=post_id) | Q(parent_post__id=post_id))


# TODO: Fix when it's a postview
# normal: generics.ListAPIView
# /service/author/{id}/posts
class AuthorPostsView(mixins.ListModelMixin, viewsets.GenericViewSet):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        """
        Returns all posts of an author that a user is allowed to see, can require authentication.

        Example response:

            {
              "count": 1,
              "posts": [
                {
                  "title": "Hi",
                  "source": "http://127.0.0.1:8000/service/posts/78da24d0-413d-410b-a550-e559ff89c802",
                  "origin": "http://127.0.0.1:8000/service/posts/78da24d0-413d-410b-a550-e559ff89c802",
                  "description": "Hey",
                  "contentType": "text/markdown",
                  "content": "Hello Super Nintendo Chalmers!",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Ralph Wiggum",
                    "url": "http://127.0.0.1:8000/service/author/7fde403e-b245-4268-93e5-343d31d0aac7",
                    "github": ""
                  },
                  "categories": [
                    "Simpsons"
                  ],
                  "comments": [],
                  "published": "2017-04-10T21:44:17.624809Z",
                  "id": "78da24d0-413d-410b-a550-e559ff89c802",
                  "url": "http://127.0.0.1:8000/service/posts/78da24d0-413d-410b-a550-e559ff89c802",
                  "visibility": "FOAF",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/78da24d0-413d-410b-a550-e559ff89c802/comments",
                  "count": 0,
                  "size": 50
                }
              ],
              "next": null,
              "query": "posts",
              "size": 100,
              "previous": null
            }
        """
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
