from rest_framework import generics, status, filters, viewsets, mixins
from rest_framework.generics import CreateAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from social.app.models.comment import Comment
from social.app.models.post import Post
from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer, CreateCommentSerializer


class CommentsViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    authentication_classes = (NodeBasicAuthentication,)
    permission_classes = (IsAuthenticated,)

    pagination_class = CommentsPagination
    filter_backends = (filters.OrderingFilter,)
    ordering_fields = ('published', 'contentType',)
    ordering = ('-published',)

    def get_serializer_class(self):
        if self.request.method == "GET":
            return CommentSerializer
        else:
            return CreateCommentSerializer

    def get_queryset(self):
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

    def list(self, request, *args, **kwargs):
        """
        Returns a list of Comments written on the Post specified by id.
        
        ### Parameters
        * id: The id of the desired Post.
        
        ### Example Successful Response
            {
              "count": 3,
              "comments": [
                {
                  "id": "578e6948-130b-4976-bca1-7785f9ac8dd7",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Adam Ford",
                    "url": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "github": ""
                  },
                  "comment": "Test Comment 3",
                  "published": "2017-04-11T06:44:18.709000Z",
                  "contentType": "text/markdown"
                },
                {
                  "id": "9537c473-343e-41dd-a3f8-851684f3eb26",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Adam Ford",
                    "url": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "github": ""
                  },
                  "comment": "Test Comment 2",
                  "published": "2017-04-11T06:44:13.358000Z",
                  "contentType": "text/markdown"
                },
                {
                  "id": "67f65533-4fbc-44d5-8582-a0f6f35947cf",
                  "author": {
                    "id": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "host": "http://127.0.0.1:8000/service/",
                    "displayName": "Adam Ford",
                    "url": "http://127.0.0.1:8000/service/author/7cb311bf-69dd-4945-b610-937d032d6875",
                    "github": ""
                  },
                  "comment": "Test Comment 1",
                  "published": "2017-04-11T06:44:08.684000Z",
                  "contentType": "text/markdown"
                }
              ],
              "next": null,
              "query": "comments",
              "size": 100,
              "previous": null
            }
        """
        return super(CommentsViewSet, self).list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        """
        Adds a comment by an Author on your server on the Post specified by id on our server
        
        ### Parameters
        * id: The id of the desired Post.
        
        ### Expected Input
            {
                "query":"addComment", # Must be equal to "addComment". (required)
                "post":"http://whereitcamefrom.com/posts/zzzzz", # The URI of the Post. (required)
                "comment":{
                    "author":{
                        "id":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471", # The URI of the Author who wrote the comment. (required)
                        "host":"http://127.0.0.1:5454/", # The base service URL of this Author. (required)
                        "displayName":"Greg Johnson", # The displayName of this Author. (required)
                        "url":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471", # The URI of the Author who wrote the comment. (required)
                        "github":"http://github.com/gjohnson" # The GitHub profile URL of this Author. (optional)
                    },
                    "comment":"Sick Olde English", # The Markdown text of this comment. (required)
                    "contentType":"text/markdown", # The content type of this comment. Must be equal to "text/markdown". (required)
                    "published":"2015-03-09T13:07:04+00:00", # The ISO 8601 timestamp of when this comment was written. (required)
                    "id":"de305d54-75b4-431b-adb2-eb6b9e546013" # The ID of this comment. (required)
                }
            }
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save()
        return Response(CommentSerializer(comment, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)
