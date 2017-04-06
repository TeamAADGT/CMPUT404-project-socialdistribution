import base64
import feedparser
from itertools import chain
from operator import attrgetter
from background_task import background

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


def indexHome(request):
    # Currently displaying / page
    if request.user.is_authenticated():
        user = request.user
        author = Author.objects.get(user=request.user.id)
        context = dict()

        # NOTE: this does the same thing as the function indexHome in app/view.py
        # Return posts that are NOT by current user (=author) and:

        # case 1: posts.visibility=public and following                --> can view
        # case 1': posts.visibility=public  and not following          --> can't view
        # case 2': posts.visibility=friends and not friends            --> can't view
        public_and_following_posts = Post.objects \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case 2: posts.visibility=friends and friends and friends on this server --> can view
        friend_posts = Post.objects \
            .filter(author__id__in=author.friends.all()) \
            .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case 3: posts.visibility=foaf and friend/foaf                --> can view
        # case 3': posts.visibility=foaf and not either friend/foaf    --> can view
        context3 = dict()
        friends = set(f.id for f in author.friends.all())
        print ("friends", friends)
        foafs = set()

        # Get all the foafs
        for friend in friends:
            friend_obj = Author.objects.get(pk=friend)
            # print ("friend obj", friend_obj)
            new_foafs = set(ff.id for ff in friend_obj.friends.all())
            # print ("new foafs", new_foafs)
            foafs.update(new_foafs)

        foafs.update(friends)
        # print("foafs", foafs)

        foaf_posts = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(Q(author__id__in=foafs)) \
            .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')

        # TODO: need to be able to filter posts by current user's relationship to posts author
        # case 4: posts.visibility=private                             --> can't see

        # Get node posts
        # Avoid a possible ConnectionError
        try:
            node_posts = get_remote_node_posts()
        except Exception:
            node_posts = list()

        all_posts = list(
            chain(
                public_and_following_posts,
                friend_posts,
                foaf_posts,
                node_posts
            )
        )

        context["user_posts"] = sorted(all_posts, key=attrgetter('published'))

        return render(request, 'app/index.html', context)
    else:
        # Return all posts on present on the site
        context = dict()
        context['all_posts'] = Post.objects.all().order_by('-published')
        return render(request, 'app/landing.html', context)


def view_posts(request):
    if request.user.is_authenticated():
        user = request.user
        author = Author.objects.get(user=request.user.id)
        context = dict()

        # NOTE: this does the same thing as the function indexHome in app/view.py
        # Return posts that are NOT by current user (=author) and:

        # case 1: posts.visibility=public and following                --> can view
        # case 1': posts.visibility=public  and not following          --> can't view
        # case 2': posts.visibility=friends and not friends            --> can't view
        public_and_following_posts = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case 2: posts.visibility=friends and friends and friends on this server --> can view
        friend_posts = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.friends.all()) \
            .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        # case 3: posts.visibility=foaf and friend/foaf                --> can view
        # case 3': posts.visibility=foaf and not either friend/foaf    --> can view
        friends = set(f.id for f in author.friends.all())
        # print ("friends", friends)
        foafs = set()

        # Get all the foafs
        for friend in friends:
            friend_obj = Author.objects.get(pk=friend)
            # print ("friend obj", friend_obj)
            new_foafs = set(ff.id for ff in friend_obj.friends.all())
            # print ("new foafs", new_foafs)
            foafs.update(new_foafs)

        foafs.update(friends)
        # print("foafs", foafs)

        foaf_posts = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(Q(author__id__in=foafs)) \
            .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')

        # case 4: posts.visibility=public and

        # TODO: need to be able to filter posts by current user's relationship to posts author
        # case 5: posts.visibility=private                             --> can't see


        # Get node posts
        # Avoid a possible ConnectionError
        try:
            node_posts = get_remote_node_posts()
        except Exception:
            node_posts = list()

        all_posts = list(
            chain(
                public_and_following_posts,
                friend_posts,
                foaf_posts,
                node_posts
            )
        )

        context["user_posts"] = sorted(all_posts, key=attrgetter('published'))

        return render(request, 'app/index.html', context)
    else:
        # Return all posts on present on the site
        context = dict()
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

# Get the GitHub activity of a user
@background(schedule=60)
def get_github_activity(authorId, gitUrl):
    gitAuthor = Author.objects.get(user=authorId)

    # lazy way of checking if URL is correct right now
    if((gitUrl[:19] == "https://github.com/") and (len(gitUrl.split("/")) == 4)):
        data = feedparser.parse(gitUrl + ".atom")

        # get users post
        posts = Post.objects.filter(author__id=authorId).filter(title__contains="New GitHub Activity:")

        # Get encoding to decode the data
        encoding = data["encoding"]
        # Go over all the entries for the RSS feed, turn them into posts, save
        # them - this seems to work out okay imo
        for x in data.get("entries"):
            found = False
            gitId = x["id"].encode(encoding).split("/")

            # This is done to avoid adding duplicates
            for post in posts:
                entry = post.title.split()
                if(entry[3] == gitId[1]):
                    found = True
                    break
        
            if(found is False):
                post = Post.objects.create(author=gitAuthor)

                # want to stash activity ID somewhere to avoid duplication in later gets
                # it's in the title right now, just need to actually get it
                post.title = "New GitHub Activity: %s" %gitId[1]
                # uses given title to describe what the user did
                post.description = x["title"].encode(encoding)
                post.content_type = "text/markdown"
                # gives a link to the page
                post.content = "See [this page](%s)" %(x["link"].encode(encoding))
                # use their given published date so that way it's properly sorted
                post.published = x["published"].encode(encoding)
                post.save()

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
