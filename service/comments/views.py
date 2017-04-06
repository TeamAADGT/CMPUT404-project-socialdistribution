from social.app.models.post import Post
from social.app.models.comment import Comment

from django.shortcuts import render, get_object_or_404


def post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    context = dict()
    context["all_comments"] = Comment.objects.filter(post_id=post.id)
    return render(request,'/social/app/template/post/comments.html', context)



