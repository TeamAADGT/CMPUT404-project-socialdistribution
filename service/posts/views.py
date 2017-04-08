from django.contrib.auth.models import AnonymousUser
from django.db.models import Q
from rest_framework import viewsets, views, generics, mixins, status
from rest_framework.decorators import list_route
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from service.authentication.node_basic import NodeBasicAuthentication
from service.posts.pagination import PostsPagination
from service.posts.serializers import PostSerializer, FOAFCheckPostSerializer
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

    @list_route(methods=['GET'], authentication_classes=(NodeBasicAuthentication,),
                permission_classes=(IsAuthenticated,))
    def all_posts(self, request, *args, **kwargs):
        # Needed to make sure this shows up in the schema -- collides with /posts/ otherwise
        return self.list(request, *args, **kwargs)


class SpecificPostsViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    list:
    Returns the local post with the specified ID, if any.

    If the local post has an attached image, and the current remote node has permission to view images, the post
    containing that image is also returned. In other words, this endpoint will always return 0-2 posts.

    create:

    """
    pagination_class = PostsPagination
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PostSerializer
        return FOAFCheckPostSerializer

    def get_queryset(self):
        post_id = self.kwargs["pk"]
        remote_node = self.request.user

        return get_local_posts(remote_node).filter(Q(id=post_id) | Q(parent_post__id=post_id))

    def create(self, request, *args, **kwargs):
        """
        Checking whether the requesting author can see this FOAF post or not.

        Expects input in the following format:

            {
                "query":"getPost",
                "postid":"{POST_ID}",
                "url":"http://service/posts/{POST_ID}",
                "author":{ # requestor
                    # UUID
                    "id":"http://127.0.0.1:5454/author/de305d54-75b4-431b-adb2-eb6b9e546013",
                    "host":"http://127.0.0.1:5454/",
                    "displayName":"Jerry Johnson",
                    # url to the authors information
                    "url":"http://127.0.0.1:5454/author/de305d54-75b4-431b-adb2-eb6b9e546013",
                    # HATEOS
                    "github": "http://github.com/jjohnson"
                },
                # friends of author
                "friends":[
                    "http://127.0.0.1:5454/author/7deee0684811f22b384ccb5991b2ca7e78abacde",
                    "http://127.0.0.1:5454/author/11c3783f15f7ade03430303573098f0d4d20797b",
                ]
            }
        
        """
        # Source: https://github.com/encode/django-rest-framework/blob/master/rest_framework/mixins.py#L18 (2017-04-07)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        headers = self.get_success_headers(serializer.data)
        response_data = {}
        return Response(response_data, status=status.HTTP_200_OK, headers=headers)


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
