from rest_framework import generics

from django.shortcuts import get_object_or_404

from social.app.models.comment import Comment
from social.app.models.post import Post
from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer


# List view
class CommentListView(generics.ListAPIView):
    pagination_class = CommentsPagination
    serializer_class = CommentSerializer
    authentication_classes = (NodeBasicAuthentication,)
    # No permission class

    def get_queryset(self):
        remote_node = self.request.user

        if remote_node is not None and not remote_node.share_posts:
            # We're specifically blocking this node, so short-circuit and return nothing
            return Comment.objects.none()

        post_id = self.kwargs["pk"]
        queryset = Comment.objects.filter(post_id=post_id)
        queryset = queryset.filter(author__node__local=True)

        if remote_node is None:
            # Only send 'em public post's comments if we don't know them, or they're asking for just these
            queryset = queryset.filter(post__visibility="PUBLIC")
        else:
            # We trust this node, so send them everything
            queryset = queryset.exclude(post__visibility="SERVERONLY")

        if remote_node is None or not remote_node.share_images:
            # If a node isn't authenticated or we just decided to not do it, don't send over comments on images
            queryset = queryset.filter(post__content_type__in=[key for (key, value) in Post.TEXT_CONTENT_TYPES])

        return queryset