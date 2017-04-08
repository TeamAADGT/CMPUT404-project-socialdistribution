from rest_framework import generics
from rest_framework.generics import CreateAPIView

from social.app.models.comment import Comment
from social.app.models.post import Post
from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer, CreateCommentSerializer


class CommentListView(generics.ListCreateAPIView):
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

    def perform_create(self, serializer):
        comment = serializer











        '''
        context = dict()
        context["query"] = "addComment"

        try:
            Comment(
                id=post_id,
                author= self.kwargs["author"],
                comment= self.kwargs["comment"],
            ).save()

            context["success"] = "true"
            context["message"] = "Comment Added"
            return context

        except: # If they don't have the visibility to comment on that post
            context["success"] = "false"
            context["message"] = "Comment not allowed"
        '''




