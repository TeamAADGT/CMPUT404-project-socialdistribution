import base64
import logging
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic

from social.app.forms.comment import CommentForm
from social.app.forms.post import PostForm
from social.app.models.author import Author
from social.app.models.comment import Comment
from social.app.models.post import Post
from social.app.models.post import get_all_public_posts, get_all_friend_posts, get_all_foaf_posts, get_remote_node_posts, get_all_private_posts



def all_posts(request):
    """
    Get /posts/
    """
    remote_posts = get_remote_node_posts()
    context = dict()
    context["user_posts"] = \
        (Post.objects
         .filter(visibility="PUBLIC")
         .filter(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES])
         .order_by('-published'))

    return render(request, 'app/index.html', context)


def my_stream_posts(request):
    """
    Get /
    """
    context = dict()

    # User views "My Feed"
    if request.user.is_authenticated():
        user = request.user

        author = Author.objects.get(user=request.user.id)

        # Case V: Get other node posts
        # TODO: need to filter these based on remote author's relationship to current user.
        try:
            get_remote_node_posts()
        except Exception, e:
            logging.error(e)

        # case I: posts.visibility=public and following
        public_and_following_posts = get_all_public_posts() \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all())

        # case II: posts.visibility=friends
        friend_posts = get_all_friend_posts(author) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(~Q(author__id=user.profile.id))

        # case III: posts.visibility=foaf
        # TODO: Should you have to explicitly follow a foaf to see their posts in your feed?
        # This code assumes the answer to that question is yes.
        foaf_posts = get_all_foaf_posts(author) \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all())

        # case IV: posts.visibility=private
        private_posts = get_all_private_posts() \
            .filter(Q(visible_to=user.profile.id))


        posts = ((public_and_following_posts |
                  friend_posts |
                  foaf_posts |
                  private_posts)
                 .filter(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES])
                 .distinct())

        context["user_posts"] = sorted(posts, key=attrgetter('published'))

        return render(request, 'app/index.html', context)

    # Not authenticated
    else:
        success_url = reverse('app:posts:index')
        return HttpResponseRedirect(success_url)


class DetailView(generic.DetailView):
    """
    """
    model = Post
    # TODO: This needs to filter out posts the current user can't see
    # TODO: If the post being viewed is a remote post, we need to fetch the latest version of it first
    # Image posts can't be viewed directly, only as part of their parent post
    queryset = Post.objects.filter(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES])
    template_name = 'posts/detail.html'


def view_post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    context = dict()
    context["all_comments"] = Comment.objects.filter(post_id=post.id)
    return render(request, 'posts/comments.html', context)


@login_required
def post_create(request):
    if not request.user.is_authenticated():
        raise Http404

    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        instance = form.save(request=request)
        messages.success(request, "You just added a new post.")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "posts/post_form.html", context)


# Delete a particular post
@login_required
def post_delete(request, pk):
    if not request.user.is_authenticated():
        raise Http404

    post = get_object_or_404(Post, pk=pk)

    if post.author != request.user.profile:
        return HttpResponse(status=401)

    post.delete()

    # How to pass argument to reverse
    # By igor(https://stackoverflow.com/users/978434/igor)
    # On StackOverflow url: https://stackoverflow.com/questions/15703475/how-to-make-reverse-lazy-lazy-for-arguments-too
    # License: CC-BY-SA 3.0
    success_url = reverse('app:authors:posts-by-author', kwargs={'pk': request.user.profile.id, })
    # Upon success redirects user to /authors/<current_user_guid>/posts/
    return HttpResponseRedirect(success_url)


# Update a particular post
@login_required
def post_update(request, pk):
    if not request.user.is_authenticated():
        raise Http404

    post = get_object_or_404(Post, pk=pk)

    if post.author != request.user.profile:
        return HttpResponse(status=401)

    form = PostForm(request.POST or None, request.FILES or None,
                    instance=post,
                    initial={
                        'upload_content_type': post.child_post.content_type if post.child_post else "",
                        'categories': post.categories_string()
                    })

    if form.is_valid():
        instance = form.save(request=request)
        messages.success(request, "You just updated your post.")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "posts/post_form.html", context)

# Based on code by Django Girls,
# url: https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/homework_create_more_models/
def add_comment_to_post(request, pk):
    post = get_object_or_404(Post, pk=pk)
    current_author = request.user.profile
    if request.method == "POST":
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = current_author
            comment.post = post
            comment.save()
            return redirect('app:posts:detail', pk=post.pk)
    else:
        form = CommentForm()
    return render(request, 'posts/add_comment_to_post.html', {'form': form})


# Authorship test idea from http://stackoverflow.com/a/28801123/2557554
# Code from mishbah (http://stackoverflow.com/users/1682844/mishbah)
# Licensed under CC-BY-SA 3.0 ((https://creativecommons.org/licenses/by-sa/3.0/deed.en)
def author_passes_test(post, request):
    if request.user.is_authenticated():
        return post.author.user == request.user
    return False
