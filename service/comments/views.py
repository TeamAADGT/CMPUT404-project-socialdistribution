from rest_framework import generics, status
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response

from social.app.models.comment import Comment
from social.app.models.post import Post
from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer, CreateCommentSerializer


# TODO: Break this into separate GET/POST, prettify it
# /service/posts/{id}/comments/ (both GET and POST)
class CommentListView(generics.ListCreateAPIView):
    """
    Will either post a comment to a post (if allowed) or get comments on a post.

    (examples below just from the given examples)

    Example of a successful GET:
    <pre>
    {        
        &nbsp&nbsp&nbsp"query": "comments",
        &nbsp&nbsp&nbsp"count": 1023,
        &nbsp&nbsp&nbsp"size": 50,
        &nbsp&nbsp&nbsp"next": null,
        &nbsp&nbsp&nbsp"previous": null,
        &nbsp&nbsp&nbsp"comments":[{
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"author":{
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"http://127.0.0.1:5454/8d919f29c12e8f97bcbbd34cc908f19ab9496989",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"host":"http://127.0.0.1:5454/",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"displayName":"Greg"
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp},
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"comment":"Sweet Trick Shot",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"contentType":"text/markdown",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"published":"2015-03-09T13:07:04+00:00",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"5471fe89-7697-4625-a06e-b3ad18577b72"
        &nbsp&nbsp&nbsp}]
    }
    </pre>

    Example of a POST:
    <pre>
    {
        &nbsp&nbsp&nbsp"query": "addComment",
        &nbsp&nbsp&nbsp"post":"http://whereitcamefrom.com/posts/zzzzz",
        &nbsp&nbsp&nbsp"comment":{
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"author":{
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"host":"http://127.0.0.1:5454/",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"displayName":"Greg Johnson",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"url":"http://127.0.0.1:5454/author/1d698d25ff008f7538453c120f581471",
                &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"github": "http://github.com/gjohnson"
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp},
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"comment":"Sick Olde English",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"contentType":"text/markdown",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"published":"2015-03-09T13:07:04+00:00",
            &nbsp&nbsp&nbsp&nbsp&nbsp&nbsp"id":"de305d54-75b4-431b-adb2-eb6b9e546013"
        &nbsp&nbsp&nbsp}
    }
    </pre>

    If the POST is allowed:
    <pre>
    {
        &nbsp&nbsp&nbsp"query": "addComment",
        &nbsp&nbsp&nbsp"success": true,
        &nbsp&nbsp&nbsp"message":"Comment Added"
    }
    </pre>

    If the POST isn't allowed:
    <pre>
    {
        &nbsp&nbsp&nbsp"query": "addComment",
        &nbsp&nbsp&nbsp"success": false,
        &nbsp&nbsp&nbsp"message":"Comment not allowed"
    }
    </pre>
    """
    authentication_classes = (NodeBasicAuthentication,)
    pagination_class = CommentsPagination

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

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        comment = serializer.save()
        return Response(CommentSerializer(comment, context={'request': request}).data,
                        status=status.HTTP_201_CREATED)







