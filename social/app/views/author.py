import re
from operator import attrgetter

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from django.forms import inlineformset_factory
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.views import generic
from requests import HTTPError
import urlparse
from django.urls import reverse

from social.app.forms.author import FindRemoteAuthorForm
from social.app.forms.user_profile import UserFormUpdate
from social.app.models.author import Author
from social.app.models.node import Node
from social.app.models.post import Post
from social.app.models.post import (get_all_public_posts, get_all_friend_posts, get_all_foaf_posts,
    get_all_remote_node_posts, get_all_local_private_posts)


def create_author_uri(author):
    author_host = author.node.host
    author_service_url = author.node.service_url
    protocol = urlparse.urlparse(author_service_url).scheme + "://"

    author_path = reverse('app:authors:detail', kwargs={'pk': author.id})
    author_uri = protocol + author_host + author_path

    return author_uri


def get_posts_by_author(request, pk):
    """
    Get /authors/<author_guid>/posts/
    """
    current_user = request.user
    author = Author.objects.get(id=pk)
    author_guid = str(pk)
    current_author = Author.objects.get(user=request.user.id)
    current_author_guid = str(current_author.id)
    context = dict()
    context['show_add_post_button'] = "false"

    # Current user views their own posts
    if current_user.is_authenticated() and current_author_guid == author_guid:
        context['user_posts'] = Post.objects.filter(author__id=current_user.profile.id).order_by('-published')
        context['show_add_post_button'] = "true"
        return render(request, 'app/index.html', context)

    # Current user views another author's posts
    elif current_user.is_authenticated():

        # Case V: Get other node posts
        # TODO: need to filter these based on remote author's relationship to current user.
        get_all_remote_node_posts()

        # case I: posts.visibility=public
        public_posts = get_all_public_posts()
        public_posts = public_posts.filter(author__id=author.id)

        # case II: posts.visibility=friends
        friend_posts = get_all_friend_posts(current_author) \
            .filter(author__id=author.id) \
            .filter(~Q(author__id=current_user.profile.id))

        # case III: posts.visibility=foaf
        foaf_posts = get_all_foaf_posts(current_author) \
            .filter(~Q(author__id=current_user.profile.id)) \
            .filter(author__id=author.id)

        # TODO: case IV: posts.visibility=private
        # case IV: posts.visibility=private
        author_uri = create_author_uri(author)
        private_local_posts = get_all_local_private_posts() \
            .filter(Q(visible_to_author__uri=author_uri))

        posts = ((public_posts |
                  friend_posts |
                  foaf_posts |
                  private_local_posts)
                 .filter(content_type__in=[x[0] for x in Post.TEXT_CONTENT_TYPES])
                 .distinct())

        context["user_posts"] = sorted(posts, key=attrgetter('published'), reverse=True)

        return render(request, 'app/index.html', context)

    # Not authenticated
    else:
        context['user_posts'] = Post.objects \
            .filter(author__id=author.id) \
            .filter(visibility="PUBLIC").order_by('-published')
        return render(request, 'app/index.html', context)


@login_required
def edit_user(request, pk):
    user = get_object_or_404(User, pk=pk)
    user_form = UserFormUpdate(instance=user)

    profile_inline_formset = inlineformset_factory(
        User, Author,
        fields=('displayName', 'github', 'bio'))
    formset = profile_inline_formset(instance=user)
    formset.can_delete = False

    if request.user.is_authenticated() and request.user.id == user.id:

        if request.method == "POST":
            user_form = UserFormUpdate(request.POST, request.FILES, instance=user)
            formset = profile_inline_formset(request.POST, request.FILES, instance=user)

            if user_form.is_valid():
                created_user = user_form.save(commit=False)

                formset = profile_inline_formset(request.POST, request.FILES, instance=created_user)

                if formset.is_valid():
                    created_user.save()
                    formset.save()
                    messages.success(request, 'Your profile has been updated successfully!', extra_tags='alert-success')
                    return HttpResponseRedirect('/accounts/' + str(user.id))
                else:
                    messages.error(request, 'Oops! There was a problem updating your profile!',
                                   extra_tags='alert-danger')

        return render(request, "account/account_update.html", {
            "noodle": pk,
            "noodle_form": user_form,
            "formset": formset,
        })
    else:
        raise PermissionDenied


class AuthorListView(generic.ListView):
    model = Author
    template_name = 'app/authors_list.html'
    context_object_name = 'all_authors'

    def get_queryset(self):
        return Author.objects.all().order_by('-displayName')

    def get_context_data(self, **kwargs):
        context = super(AuthorListView, self).get_context_data(**kwargs)
        context['show_remote_find_link'] = Node.objects.filter(local=False)
        return context


class AuthorDetailView(generic.DetailView):
    model = Author

    def get_object(self, queryset=None):
        try:
            author = super(AuthorDetailView, self).get_object(queryset)
        except Http404:
            author = None

        author_id = self.kwargs["pk"]
        fetched_new_author = False

        if author is None:
            # No Author found -- so let's go ask our remote Nodes if they've got it
            for node in Node.objects.filter(local=False):
                try:
                    author = node.create_or_update_remote_author(author_id)
                except HTTPError:
                    # Something's wrong with this node, so let's skip it
                    continue

                if author is not None:
                    # Found it!
                    fetched_new_author = True
                    break

        if author is None:
            # If we got here, no one has it
            raise Http404()

        if not author.node.local and not fetched_new_author:
            try:
                # Let's go get the latest version if we didn't already fetch it above
                updated_author = author.node.create_or_update_remote_author(author_id)
            except HTTPError:
                # Remote server failed in a way that wasn't a 404, so let's just display our cached version
                return author

            if updated_author is None:
                # Well, looks like they deleted this author. Awkward.
                author.delete()
                raise Http404()
            else:
                author = updated_author

        return author

    def get_context_data(self, **kwargs):
        context = super(AuthorDetailView, self).get_context_data(**kwargs)

        if self.request.user.is_authenticated():
            logged_in_author = self.request.user.profile
            detail_author = context["object"]

            context['show_follow_button'] = logged_in_author.can_follow(detail_author)
            context['show_unfollow_button'] = logged_in_author.follows(detail_author)
            context['show_friend_request_button'] = logged_in_author.can_send_a_friend_request_to(detail_author)
            context['outgoing_friend_request_for'] = logged_in_author.has_outgoing_friend_request_for(detail_author)
            context['incoming_friend_request_from'] = logged_in_author.has_incoming_friend_request_from(detail_author)
            context['is_friends'] = logged_in_author.friends_with(detail_author)
        else:
            context['show_follow_button'] = False
            context['show_unfollow_button'] = False
            context['show_friend_request_button'] = False
            context['outgoing_friend_request_for'] = False
            context['incoming_friend_request_from'] = False
            context['is_friends'] = False

        return context


def find_remote_author(request):
    """
    Source: https://docs.djangoproject.com/en/1.10/topics/forms/#the-form-class (2017-04-09)
    """
    if request.method == "POST":
        form = FindRemoteAuthorForm(request.POST)

        if form.is_valid():
            uri = form.cleaned_data['uri']
            match = re.match(FindRemoteAuthorForm.URI_REGEX, uri)
            (host, pk) = (match.group('host'), match.group('pk'))

            author = None

            try:
                node = Node.objects.get(host=host)
                if node.local:
                    author = Author.objects.get(id=pk)
                else:
                    author = node.create_or_update_remote_author(pk)

            except Node.DoesNotExist:
                form.add_error('uri', "The remote Author's node was not found. Please contact the system "
                                      "administrator and ask them to add their Node.")
            except Author.DoesNotExist:
                form.add_error('uri', "Author not found.")
            except HTTPError:
                form.add_error('uri', "Problem connecting to the remote Node. Please try again later.")

            if form.is_valid():
                # Need to check again to see if any errors got added
                return redirect('app:authors:detail', pk=author.id)
    else:
        form = FindRemoteAuthorForm()

    return render(request, 'app/find_remote_author.html', {'form': form})
