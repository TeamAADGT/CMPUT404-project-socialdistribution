from rest_framework import generics, status, viewsets
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.decorators import detail_route

from social.app.models.comment import Comment
from social.app.models.post import Post
from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer, CreateCommentSerializer


# TODO:
# /service/posts/{id}/comments/ (both GET and POST)
class CommentListView(viewsets.ReadOnlyModelViewSet):
    authentication_classes = (NodeBasicAuthentication,)
    pagination_class = CommentsPagination

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentSerializer
        else:
            return CreateCommentSerializer

    @detail_route(methods=['GET'], authentication_classes=(NodeBasicAuthentication,))
    def get_queryset(self):
        """
        Returns all the comments on a given post

        Example of a successful GET:

            {        
                "query": "comments",
                "count": 1023,
                "size": 50,
                "next": null,
                "previous": null,
                "comments":[{
                    "author":{
                        "id":"http://127.0.0.1:5454/8d919f29c12e8f97bcbbd34cc908f19ab9496989",
                        "host":"http://127.0.0.1:5454/",
                        "displayName":"Greg"
                    },
                    "comment":"Sweet Trick Shot",
                    "contentType":"text/markdown",
                    "published":"2015-03-09T13:07:04+00:00",
                    "id":"5471fe89-7697-4625-a06e-b3ad18577b72"
                }]
            }
        """
        remote_node = self.request.user
        anonymous_node = remote_node is None or not remote_node.is_authenticated

        if not anonymous_node and not remote_node.share_posts:
            # We're specifically blocking this node, so short-circuit and return nothing
            return Comment.objects.none()

        post_id = self.kwargs["pk"]
        queryset = Comment.objects.filter(post_id=post_id)
        queryset = queryset.filter(post__author__node__local=True)

        if anonymous_node:
            # Only send 'em public post's comments if we don't know them, or they're asking for just these
            queryset = queryset.filter(post__visibility="PUBLIC")
        else:
            # We trust this node, so send them everything
            queryset = queryset.exclude(post__visibility="SERVERONLY")

        if anonymous_node or not remote_node.share_images:
            # If a node isn't authenticated or we just decided to not do it, don't send over comments on images
            queryset = queryset.filter(post__content_type__in=[key for (key, value) in Post.TEXT_CONTENT_TYPES])

        return queryset

    @detail_route(methods=['GET'], authentication_classes=(NodeBasicAuthentication,))
    def create(self, request, *args, **kwargs):
        """
        Will post a comment to the specified post if allowed to
        Example of a POST:

            {
                "query": "addComment",
                "post":"http://whereitcamefrom.com/posts/zzzzz",
                "comment":{
                    "author":{
                        "id":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
                        "host":"http://127.0.0.1:5454/",
                        "displayName":"Greg Johnson",
                        "url":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
                        "github": "http://github.com/gjohnson"
                    },
                    "comment":"Sick Olde English",
                    "contentType":"text/markdown",
                    "published":"2015-03-09T13:07:04+00:00",
                    "id":"de305d54-75b4-431b-adb2-eb6b9e546013"
                }
            }

        If the POST is allowed:

            {
                "query": "addComment",
                "success": true,
                "message":"Comment Added"
            }

        If the POST isn't allowed:

            {
                "query": "addComment",
                "success": false,
                "message":"Comment not allowed"
            }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save()
        return Response(CommentSerializer(comment, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)







