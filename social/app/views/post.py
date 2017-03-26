import base64
import uuid

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.db.models import Q, F
from django.http import Http404, HttpResponseRedirect, HttpResponse, HttpResponseForbidden
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import generic
from django.views.generic import UpdateView, DeleteView

from social.app.forms.comment import CommentForm
from social.app.forms.post import TextPostForm, FilePostForm
from social.app.models.author import Author
from social.app.models.category import Category
from social.app.models.comment import Comment
from social.app.models.post import Post


def indexHome(request):
    # Note: Slight modification to allow for latest posts to be displayed on landing page
    if request.user.is_authenticated():
        user = request.user
        author = Author.objects.get(user=request.user.id)
        context = dict()
        context1 = dict()
        context2 = dict()
        context3 = dict()

        # Return posts that are NOT by current user (=author) and:

        # case 1: posts.visibility=public and following               --> can view
        # case 1': posts.visibility=public  and not following          --> can't view
        # case 2': posts.visibility=friends and not friends            --> can't view
        context1['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(visibility="PUBLIC").order_by('-published')

        # case 2: posts.visibility=friends and friends                 --> can view
        context2['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.friends.all()) \
            .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC")).order_by('-published')



        # TODO: need to be able to filter posts by current user's relationship to posts author
        # case 3: posts.visibility=foaf and friend/foaf                --> can view

        friends = author.friends.all()
        foafs = list()
        print(friends)

        for friend in friends:
            new_foafs = friend.friends.all()
            foafs.append(new_foafs)

        print(foafs)



        context3['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(Q(author__id__in=foafs)) \
            .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')
        # case 3': posts.visibility=foaf and not either friend/foaf    --> can view
        # case 4: posts.visibility=private                             --> can't see

        context["user_posts"] = context1["user_posts"] | context2["user_posts"] | context3["user_posts"]

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
        context1 = dict()
        context2 = dict()

        # NOTE: this does the same thing as the function indexHome in app/view.py
        # Return posts that are NOT by current user (=author) and:

        # case 1: posts.visibility=public and following               --> can view
        # case 1': posts.visibility=public  and not following          --> can't view
        # case 2': posts.visibility=friends and not friends            --> can't view
        context1['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.followed_authors.all()) \
            .filter(visibility="PUBLIC").order_by('-published')

        # case 2: posts.visibility=friends and friends and friends on this server --> can view
        context2['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(author__id__in=author.friends.all()) \
            .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
            .order_by('-published')

        #context["user_posts"] = context1["user_posts"] | context2["user_posts"]

        # TODO: need to be able to filter posts by current user's relationship to posts author
        # case 3: posts.visibility=foaf and friend/foaf                --> can view

        # TODO: need to be able to filter posts by current user's relationship to posts author
        # case 3: posts.visibility=foaf and friend/foaf                --> can view

        context3 = dict()
        friends =set(f.id for f in author.friends.all())
        print ("friends", friends)
        foafs = set()

        for friend in friends:
            friend_obj = Author.objects.get(pk=friend)
            print "friend obj", friend_obj
            new_foafs = set(ff.id for ff in friend_obj.friends.all())
            print "new foafs", new_foafs
            foafs.update(new_foafs)

        foafs.update(friends)
        print("foafs", foafs)

        context3['user_posts'] = Post.objects \
            .filter(~Q(author__id=user.profile.id)) \
            .filter(Q(author__id__in=foafs)) \
            .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')
        # case 3': posts.visibility=foaf and not either friend/foaf    --> can view
        # case 4: posts.visibility=private                             --> can't see

        context["user_posts"] = context1["user_posts"] | context2["user_posts"] | context3["user_posts"]

        # case 3': posts.visibility=foaf and not either friend/foaf    --> can view
        # case 4: posts.visibility=private                             --> can't see

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


class PostUpdate(UpdateView):
    """
    Post update
    """
    model = Post
    fields = ['post_story', 'use_markdown', 'image']
    template_name = 'posts/post_form_update.html'

    def dispatch(self, request, *args, **kwargs):
        if not author_passes_test(self.get_object(), request):
            return redirect_to_login(request.get_full_path())
        return super(PostUpdate, self).dispatch(
            request, *args, **kwargs)


class PostDelete(DeleteView):
    model = Post
    success_url = reverse_lazy('app:posts:index')

    def dispatch(self, request, *args, **kwargs):
        if not author_passes_test(self.get_object(), request):
            return redirect_to_login(request.get_full_path())
        return super(PostDelete, self).dispatch(
            request, *args, **kwargs)


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
        instance = form.save(commit=False)

        current_author = request.user.profile
        new_id = uuid.uuid4()

        instance.id = new_id
        instance.author = current_author

        url = instance.get_absolute_url()

        instance.source = url
        instance.origin = url

        instance.save()

        categories_string = form.cleaned_data["categories"]
        if categories_string:
            for name in categories_string.split(" "):
                if not instance.categories.filter(name=name).exists():
                    category = Category.objects.filter(name=name).first()

                    if category is None:
                        category = Category.objects.create(name=name)

                    instance.categories.add(category)

            instance.save()

        messages.success(request, "You just added a new post.")
        return HttpResponseRedirect(url)
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
        instance = form.save(commit=False)

        current_author = request.user.profile
        new_id = uuid.uuid4()

        instance.id = new_id
        instance.author = current_author

        url = instance.get_absolute_url()

        instance.source = url
        instance.origin = url

        file_content = request.FILES['content']
        instance.content = base64.b64encode(file_content.read())

        # Upload posts are always unlisted
        instance.unlisted = True

        instance.save()

        categories_string = form.cleaned_data["categories"]
        if categories_string:
            for name in categories_string.split(" "):
                if not instance.categories.filter(name=name).exists():
                    category = Category.objects.filter(name=name).first()

                    if category is None:
                        category = Category.objects.create(name=name)

                    instance.categories.add(category)

            instance.save()

        messages.success(request, "You just added a new post.")
        return HttpResponseRedirect(url)
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
