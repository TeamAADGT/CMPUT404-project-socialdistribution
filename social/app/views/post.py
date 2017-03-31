import base64

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, F
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic

from social.app.forms.comment import CommentForm
from social.app.forms.post import TextPostForm, FilePostForm
from social.app.models.author import Author
from social.app.models.comment import Comment
from social.app.models.node import Node
from social.app.models.post import Post


def get_remote_node_posts():
    node_posts = list()
    for node in Node.objects.filter(local=False):
        for post_json in node.get_author_posts()['posts']:
            author_json = post_json['author']
            author = Author(
                id=Author.get_id_from_uri(author_json['id']),
                node=node,
                displayName=author_json['displayName'],
            )
            post = Post(
                id=post_json['id'],
                title=post_json['title'],
                source=post_json['source'],
                origin=post_json['origin'],
                description=post_json['description'],
                author=author,
                published=post_json['published'],
            )
            node_posts.append(post)
    return node_posts


def get_home(request):
    """
    Get /
    """
    if request.user.is_authenticated(): # Redirects user to /posts/
        user = request.user
        author = Author.objects.get(user=request.user.id)
        context = dict()
        success_url = reverse('app:posts:index')
        return HttpResponseRedirect(success_url)

    else: # Shows all public posts
        context = dict()
        context['all_posts'] = Post.objects.filter(visibility="PUBLIC").order_by('-published')
        return render(request, 'app/landing.html', context)


def get_posts(request):
    """
    Get /posts/
    """
    context = dict()

    # User views "My Feed"
    if request.user.is_authenticated():
        user = request.user
        author = Author.objects.get(user=request.user.id)

        # NOTE: this code is similar to view_posts_by_author in social/app/views/author.py
        # BUT this code *filters* on "following"

        # case I: posts.visibility=public and following
        public_and_following_posts = dict()
        public_and_following_posts["user_posts"] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case II: posts.visibility=friends
        friend_posts = dict()
        friend_posts["user_posts"] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(author__id__in=author.friends.all()) \
            .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case III: posts.visibility=foaf
        friends_list = set(f.id for f in author.friends.all())
        foafs = set()

        for friend in friends_list:
            friend_obj = Author.objects.get(pk=friend)
            new_foafs = set(ff.id for ff in friend_obj.friends.all())
            foafs.update(new_foafs)
        foafs.update(friends_list)

        # TODO: Should you have to explicitly follow a foaf to see their posts in your feed?
        # This code assumes the answer to that question is yes.
        foaf_posts = dict()
        foaf_posts["user_posts"] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(Q(author__id__in=foafs)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')

        # TODO: case IV: posts.visibility=private

        # Case V: Get other node posts
        # TODO: need to filter these based on remote author's relationship to current user.
        node_posts = dict()
        try:
            node_posts["user_posts"] = get_remote_node_posts()
            if node_posts["user_posts"] == []:
                node_posts["user_posts"] = Post.objects.none()
        except Exception: # Avoid a possible ConnectionError
            node_posts["user_posts"] = Post.objects.none()

        context["user_posts"] = public_and_following_posts["user_posts"] | \
                                friend_posts["user_posts"] | \
                                foaf_posts["user_posts"] | \
                                node_posts["user_posts"]

        return render(request, 'app/index.html', context)

    # Not authenticated
    else:
        context['user_posts'] = Post.objects.filter(visibility="PUBLIC").order_by('-published')
        return render(request, 'app/index.html', context)


class DetailView(generic.DetailView):
    """
    Detail View
    """
    model = Post
    template_name = 'posts/detail.html'


def get_upload_file(request, pk):
    post = get_object_or_404(Post, pk=pk)

    if not post.is_upload():
        # doesn't make sense to do this
        return HttpResponseForbidden()

    if post.is_image():
        content = base64.b64decode(post.content)
        content_type = post.content_type.split(';')[0]
    else:
        # is application/base64, so don't decode
        content = post.content
        content_type = post.content_type

    return HttpResponse(
        content=content,
        content_type=content_type,
    )


def view_post_comments(request, pk):
    post = get_object_or_404(Post, pk=pk)
    context = dict()
    context["all_comments"] = Comment.objects.filter(post_id=post.id)
    return render(request, 'posts/comments.html', context)


@login_required
def post_create(request):
    if not request.user.is_authenticated():
        raise Http404

    form = TextPostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        instance = form.save(request=request)
        messages.success(request, "You just added a new post.")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "posts/post_form.html", context)


@login_required
def post_upload(request):
    if not request.user.is_authenticated():
        raise Http404

    form = FilePostForm(request.POST or None, request.FILES or None)
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
    success_url = reverse('app:authors:posts-by-author', kwargs = {'pk' : request.user.profile.id, })
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

    if post.is_upload():
        form = FilePostForm(request.POST or None, request.FILES or None, instance=post)
    else:
        form = TextPostForm(request.POST or None, request.FILES or None, instance=post)

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
