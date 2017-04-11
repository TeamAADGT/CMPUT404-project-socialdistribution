import requests
from django.db.models import Q
from rest_framework import viewsets, views, generics, mixins, status, filters
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer, FOAFCheckPostSerializer
from social.app.models.author import Author
from social.app.models.node import Node
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
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('published', 'title', 'categories', 'contentType',)
    ordering = ('-published',)

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
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('published', 'title', 'categories', 'contentType',)
    ordering = ('-published',)

    def get_queryset(self):
        remote_node = self.request.user

        return get_local_posts(remote_node)

    @list_route(methods=['GET'])
    def all_posts(self, request, *args, **kwargs):
        # Needed to make sure this shows up in the schema -- collides with /posts/ otherwise
        return self.list(request, *args, **kwargs)


class SpecificPostsViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.RetrieveModelMixin,
                           viewsets.GenericViewSet):
    pagination_class = PostsPagination
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == 'create':
            return FOAFCheckPostSerializer
        return PostSerializer

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        remote_node = self.request.user

        return get_local_posts(remote_node).filter(Q(id=post_id) | Q(parent_post__id=post_id))

    @list_route(methods=['GET'])
    def retrieve(self, request, *args, **kwargs):
        """
        Returns the local post with the specified ID, if any.
        
        If the local post has an attached image, and the current remote node has permission to view images, the post
        containing that image is also returned. In other words, this endpoint will always return 0-2 posts.
        
        ### Parameters
        * id: The ID of the Post. (required)
        
        ### Example Successful Response
            {
              "count": 2,
              "posts": [
                {
                  "title": "sadfsdafsa",
                  "source": "http://127.0.0.1:8000/service/posts/ab9105af-ba92-41c1-b722-2aaa088a323a",
                  "origin": "http://127.0.0.1:8000/service/posts/ab9105af-ba92-41c1-b722-2aaa088a323a",
                  "description": "sdfsad",
                  "contentType": "text/markdown",
                  "content": "sdfasdf",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Adam Ford",
                    "url": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "github": ""
                  },
                  "categories": [
                    "1",
                    "2",
                    "3"
                  ],
                  "comments": [],
                  "published": "2017-04-11T06:14:47.556000Z",
                  "id": "ab9105af-ba92-41c1-b722-2aaa088a323a",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/ab9105af-ba92-41c1-b722-2aaa088a323a/comments",
                  "count": 0,
                  "size": 5
                },
                {
                  "title": "Upload",
                  "source": "http://127.0.0.1:8000/service/posts/d10a7f31-10ed-4567-a93d-e3e80356b9ab",
                  "origin": "http://127.0.0.1:8000/service/posts/d10a7f31-10ed-4567-a93d-e3e80356b9ab",
                  "description": "Upload",
                  "contentType": "image/png;base64",
                  "content": "iVBORw0KGgoAAAANSUhEUgAAArIAAAGKCAYAAA...",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Adam Ford",
                    "url": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "github": ""
                  },
                  "categories": [
                    "1",
                    "2",
                    "3"
                  ],
                  "comments": [],
                  "published": "2017-04-11T06:14:48.290000Z",
                  "id": "d10a7f31-10ed-4567-a93d-e3e80356b9ab",
                  "visibility": "PUBLIC",
                  "visibleTo": [],
                  "unlisted": false,
                  "next": "http://127.0.0.1:8000/service/posts/d10a7f31-10ed-4567-a93d-e3e80356b9ab/comments",
                  "count": 0,
                  "size": 5
                }
              ],
              "next": null,
              "query": "posts",
              "size": 100,
              "previous": null
            }
        """
        return self.list(self, request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Checking whether the requesting author can see this FOAF post or not.

        Expects input in the following format:

            {
                # The requested query. Must be set to "getPost". (required)
                "query":"getPost", 
                # The UUID of the requested Post. (required)
                "postid":"{POST_ID}", 
                # The URI of the requested Post. (required)
                "url":"http://service/posts/{POST_ID}", 
                # Information about the requesting Author. (required)
                "author":{ 
                    # The URI of the requesting author. (required)
                    "id":"http://127.0.0.1:5454/service/author/de305d54-75b4-431b-adb2-eb6b9e546013", 
                    # The base service URL of the requesting Author's local node. (required)
                    "host":"http://127.0.0.1:5454/service/", 
                    # The display name of the requesting Author. (optional)
                    "displayName":"Jerry Johnson", 
                    # The URI of the requesting author. (required)
                    "url":"http://127.0.0.1:5454/service/author/de305d54-75b4-431b-adb2-eb6b9e546013", 
                    # The URI of the requesting Author's Github profile. (optional)
                    "github": "http://github.com/jjohnson" 
                },
                # The URIs of the requesting Author's friends. (required; may be empty)
                "friends":[ 
                    "http://127.0.0.1:5454/author/7deee0684811f22b384ccb5991b2ca7e78abacde",
                    "http://127.0.0.1:5454/author/11c3783f15f7ade03430303573098f0d4d20797b",
                ]
            }
        
        """
        # Source: https://github.com/encode/django-rest-framework/blob/master/rest_framework/mixins.py#L18 (2017-04-07)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        remote_node = request.user

        data = serializer.validated_data

        author_dict = data["author"]

        if remote_node.service_url != author_dict["host"]:
            return Response({"detail": "You can't request a Post for an Author that's not local to yourself."},
                            status=status.HTTP_403_FORBIDDEN)
        try:
            post = Post.objects.get(id=data["postid"], author__node__local=True)
        except Post.DoesNotExist:
            return Response({"detail": "Post not found."}, status=status.HTTP_404_NOT_FOUND)

        if post.visibility != "FOAF":
            return Response({"detail": "Post's visibility is not set to FOAF. Please retry using GET instead."},
                            status=status.HTTP_403_FORBIDDEN)

        requesting_author_id = Author.get_id_from_uri(author_dict["id"])
        try:
            if remote_node.local:
                requesting_author = Author.objects.get(id=requesting_author_id)
            else:
                requesting_author = remote_node.create_or_update_remote_author(requesting_author_id)
        except Author.DoesNotExist, requests.exceptions.RequestException:
            return Response({"detail": "Error retrieving remote Author."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return_post = False

        verified_requester_friends = []

        if post.author.friends_with(requesting_author):
            return_post = True
        elif remote_node.local:
            for friend in post.author.friends.all():
                if requesting_author.friends_with(friend):
                    return_post = True
                    break
        else:
            # Need to first verify with requesting_author's node, according to spec
            for author_uri in author_dict["friends"]:
                friends = remote_node.get_if_two_authors_are_friends(requesting_author_id, author_uri)
                if friends:
                    verified_requester_friends.append(author_uri)

            for requester_friend_uri in verified_requester_friends:

                (host, requester_friend_id) = Author.parse_uri(requester_friend_uri)

                try:
                    requester_friend_node = Node.objects.get(host=host)
                except Node.DoesNotExist:
                    # We aren't connected with this Author's node, so not much we can do with it
                    continue

                if requester_friend_node.local:
                    # Easy mode! We already know the requester and this friend are friends according to requester's node
                    # So now we just check if we agree locally

                    requester_friend = Author.objects.get(id=requester_friend_id)
                    return_post = \
                        post.author.friends_with(requester_friend) \
                        and requester_friend.friends_with(requesting_author)

                elif requester_friend_node == requesting_author.node:
                    # The requester and the friend in the middle are from the same non-local node

                    requester_friend = requester_friend_node.create_or_update_remote_author(requester_friend_id)

                    return_post = \
                        post.author.friends_with(requester_friend) \
                        and requester_friend_node.get_if_two_authors_are_friends(requester_friend.id,
                                                                                 post.author_id)
                else:
                    # The requester and the friend in the middle are from different non-local nodes
                    requester_friend = requester_friend_node.create_or_update_remote_author(requester_friend_id)

                    return_post = \
                        post.author.friends_with(requester_friend) \
                        and requester_friend_node.get_if_two_authors_are_friends(requester_friend.id, post.author_id) \
                        and requester_friend_node.get_if_two_authors_are_friends(requester_friend_id,
                                                                                 requesting_author.author_id)
                if return_post:
                    # We've got at least one FOAF connection, and that's good enough
                    break

        if return_post:
            self.action = "retrieve"
            return self.retrieve(request, *args, **kwargs)
        else:
            return Response({"detail": "The requested Author is not permitted to view this Post."},
                            status=status.HTTP_403_FORBIDDEN)


class AuthorPostsView(generics.ListAPIView):
    pagination_class = PostsPagination
    serializer_class = PostSerializer
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('published', 'title', 'categories', 'contentType',)
    ordering = ('-published',)

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
