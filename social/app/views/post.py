import logging
import urlparse
import uuid
from operator import attrgetter

import rest_framework
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import Http404, HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from django.views import generic
from requests import HTTPError

from rest_framework.reverse import reverse as rest_reverse
from social.app.forms.comment import CommentForm
from social.app.forms.post import PostForm
from social.app.models.author import Author
from social.app.models.comment import Comment
from social.app.models.node import Node
from social.app.models.post import Post
from social.app.models.post import (get_all_public_posts, get_all_friend_posts, get_all_foaf_posts,
                                    get_remote_node_posts, get_all_remote_node_posts, get_all_local_private_posts)


def all_posts(request):
    """
    Get /posts/
    """
    remote_posts = get_remote_node_posts()
    context = dict()
    context["user_posts"] = \
        (Post.objects
         .filter(visibility="PUBLIC")
         .filter(Q(author__node__local=False) | Q(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES]))
         .filter(unlisted=False)
         .order_by('-published'))

    return render(request, 'app/index.html', context)


def create_author_uri(author):
    author_host = author.node.host
    author_service_url = author.node.service_url
    protocol = urlparse.urlparse(author_service_url).scheme + "://"

    author_path = reverse('app:authors:detail', kwargs={'pk': author.id})
    author_uri = protocol + author_host + author_path

    return author_uri


def my_stream_posts(request):
    """
    Get /
    """
    context = dict()

    # User views "My Feed"
    if request.user.is_authenticated():
        user = request.user

        author = Author.objects.get(user=request.user.id)

        author_uri = create_author_uri(author)

        # Case V: Get other node posts
        # TODO: need to filter these based on remote author's relationship to current user.
        try:
            get_all_remote_node_posts()
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
        private_local_posts = get_all_local_private_posts() \
            .filter(Q(visible_to_author__uri=author_uri)) \
            .filter(author__id__in=author.followed_authors.all())

        posts = ((public_and_following_posts |
                  friend_posts |
                  foaf_posts |
                  private_local_posts)
                 .filter(Q(author__node__local=False) | Q(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES]))
                 .filter(unlisted=False)
                 .distinct())

        context["user_posts"] = sorted(posts, key=attrgetter('published'), reverse=True)

        return render(request, 'app/index.html', context)

    # Not authenticated
    else:
        success_url = reverse('app:posts:index')
        return HttpResponseRedirect(success_url)


class PostDetailView(generic.DetailView):
    def __init__(self, **kwargs):
        super(PostDetailView, self).__init__(**kwargs)

        # Used to cache the Comments fetched in get_object, for use in get_context_data
        self.comments = []
        # The Comments count returned from the remote Post call, used to determine whether we need past the first page
        self.count = 0

    model = Post
    queryset = Post.objects.filter(
        Q(author__node__local=False) | Q(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES]))

    template_name = 'posts/detail.html'

    def get_object(self, queryset=None):
        try:
            post = super(PostDetailView, self).get_object(queryset)
        except Http404:
            post = None

        post_id = self.kwargs["pk"]

        try:
            post_id = uuid.UUID(post_id)
        except:
            logging.warn(
                "Could not convert the given post_id to a UUID! Continuing with using the given post_id " + post_id)

        fetched_new_post = False

        if post is None:
            # No Author found -- so let's go ask our remote Nodes if they've got it
            for node in Node.objects.filter(local=False):
                try:
                    (post, self.comments, self.count) = node.create_or_update_remote_post(post_id)
                except Exception as e:
                    # Something's wrong with this node, so let's skip it
                    logging.error(e)
                    logging.error("There was a problem requesting a post from {}. Skipping this node..."
                                  .format(node.host))
                    continue

                if post is not None:
                    # Found it!
                    fetched_new_post = True
                    break

        if post is None:
            # If we got here, no one has it
            raise Http404()

        post_node = post.author.node
        if not post_node.local and not fetched_new_post:
            try:
                # Let's go get the latest version if we didn't already fetch it above
                updated_post_tuple = post_node.create_or_update_remote_post(post_id)
            except HTTPError:
                # Remote server failed in a way that wasn't a 404, so let's just display our cached version
                # with no comments
                self.comments = []
                self.count = 0
                return post

            if not updated_post_tuple or not updated_post_tuple[0]:
                # Well, looks like they deleted this author. Awkward.
                post.delete()
                raise Http404()
            else:
                (post, self.comments, self.count) = updated_post_tuple

        current_author = None

        if self.request.user.is_authenticated:
            current_author = self.request.user.profile

        if current_author:
            if current_author == post.author or post.visibility == "PUBLIC":
                can_view_post = True
            elif post.visibility == "FRIENDS" or post.visibility == "SERVERONLY":
                can_view_post = current_author.friends_with(post.author)
            elif post.visibility == "PRIVATE":
                uri = rest_reverse("service:author-detail", kwargs={'pk': current_author.id}, request=self.request)
                can_view_post = post.is_visible_to_author(uri)
            elif post.visibility == "FOAF":
                can_view_post = current_author.friends_with(post.author)
                if not can_view_post:
                    for friend in post.author.friends.all():
                        can_view_post = friend.friends_with(current_author)
                        if can_view_post:
                            break
            else:
                raise Exception("Invalid Post visibility type found.")
        else:
            can_view_post = post.visibility == "PUBLIC"

        if not can_view_post:
            raise Http404()

        return post

    def get_context_data(self, **kwargs):
        context = super(PostDetailView, self).get_context_data(**kwargs)

        post = self.object

        # Don't do anything if Post wasn't found
        if post:
            if post.author.node.local:
                context["comments"] = post.comments.all()
            else:
                if self.count > len(self.comments):
                    # We need to fetch all of the Post's Comments, including the ones past the first page we got
                    comments_json = post.author.node.get_post_comments(post.id)
                else:
                    # This means the initial Post response contained all of the comments
                    comments_json = self.comments

                all_comments = []
                for comment_json in comments_json:
                    # For compatibility with our existing views, we're instantiating models that won't get saved
                    # to the database, and displaying those
                    author = Author(
                        displayName=comment_json["author"]["displayName"]
                    )
                    comment_json["author"] = author
                    comment = Comment(
                        author=author,
                        comment=comment_json["comment"],
                        published=comment_json["published"],
                        id=comment_json["id"]
                    )
                    all_comments.append(comment)

                context["comments"] = all_comments

        return context


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
    return render(request, "posts/post_form2.html", context)


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

    if post.child_post:
        upload_content_type = post.child_post.content_type
    else:
        upload_content_type = ""

    form = PostForm(request.POST or None, request.FILES or None,
                    instance=post,
                    initial={
                        'upload_content_type': upload_content_type,
                        'categories': post.categories_string(),
                        'visible_to_author': post.visible_to_authors_string(),
                    })

    if form.is_valid():
        instance = form.save(request=request)
        messages.success(request, "You just updated your post.")
        return HttpResponseRedirect(instance.get_absolute_url())
    context = {
        "form": form,
    }
    return render(request, "posts/post_form2.html", context)


# Based on code by Django Girls,
# url: https://djangogirls.gitbooks.io/django-girls-tutorial-extensions/homework_create_more_models/
def add_comment_to_post(request, pk):
    current_author = request.user.profile
    # Even if it's a remote Post, we have it in our DB at this point
    post = get_object_or_404(Post, pk=pk)

    if request.method == "POST":
        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.author = current_author
            comment.post = post

            if post.author.node.local:
                comment.save()
            else:
                post.save_remote_comment(request, comment)

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
