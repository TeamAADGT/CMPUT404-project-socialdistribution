from social.app.models.comment import Comment
from social.app.models.post import Post

from service.authentication.node_basic import NodeBasicAuthentication
from service.comments.pagination import CommentsPagination
from service.comments.serializers import CommentSerializer

from django.shortcuts import render, get_object_or_404

from rest_framework import generics, viewsets


def post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    context = dict()
    context["all_comments"] = Comment.objects.filter(post_id=post.id)
    return render(request,'/social/app/template/post/comments.html', context)

# List view
class CommentListView(generics.ListAPIView):
    pagination_class = CommentsPagination
    serializer_class = CommentSerializer
    authentication_classes = (NodeBasicAuthentication,)
    # No permission class

    def get_queryset(self):
        remote_node = self.request.user

        post = get_object_or_404(Post, pk=pk)
        queryset = Comment.objects.filter(post_id=post.id)
        return queryset

# Update view