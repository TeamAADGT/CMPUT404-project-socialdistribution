from django.conf.urls import url, include

import service.authors.views
import service.friendrequest.views
import service.posts.views
import service.comments.views

import service.internal.authors.views

# ViewSet methods are mapped to URLs manually to get around issue where the API schema wouldn't show all available
# endpoints, causing problems in Swagger
author_urls = [
    url(r'^(?P<pk>[0-9a-fA-F-\\-]+)/?$',
        service.authors.views.AuthorViewSet.as_view({'get': 'retrieve'}),
        name='author-detail'),
    url(r'^posts/?$', service.posts.views.AllPostsViewSet.as_view({'get': 'all_posts'}), name='all-posts-list'),
    url(r'^(?P<pk>[0-9a-fA-F-]+)/posts/?$',
        service.posts.views.AuthorPostsView.as_view(),
        name='author-posts-list'),
    url(r'^(?P<pk>[0-9a-fA-F-]+)/friends/?$',
        service.authors.views.AuthorViewSet.as_view({
            'get': 'author_friends',
            'post': 'author_friends_search'
        }),
        name='author-friends-list'),
    url(r'^(?P<local_id>[0-9a-fA-F-]+)/friends/(?P<other_host_name>[^/]+)/author/(?P<other_id>[0-9a-fA-F-]+)/?$',
        service.authors.views.AuthorViewSet.as_view({'get': 'two_authors_are_friends'}),
        name='two-authors-are-friends'),
]

internal_urls = [
    url(r'^author/(?P<pk>[0-9a-fA-F-]+)/follow/?$',
        service.internal.authors.views.follow,
        name='author-follow'),
    url(r'^author/(?P<pk>[0-9a-fA-F-]+)/unfollow/?$',
        service.internal.authors.views.unfollow,
        name='author-unfollow'),
    url(r'^author/(?P<pk>[0-9a-fA-F-]+)/friendrequest/?$',
        service.internal.authors.views.friendrequest,
        name='author-friendrequest'),
]

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
service_urls = [
    url(r'^author/', include(author_urls)),
    url(r'^internal/', include(internal_urls, namespace="internal")),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^friendrequest/?$', service.friendrequest.views.FriendRequestViewSet.as_view({'post': 'friendrequest'}),
        name='friend-request'),
    url(r'^posts/(?P<pk>[0-9a-fA-F-]+)/comments/?$', service.comments.views.CommentListView.as_view(),
        name='comment-detail'),
    url(r'^posts/?$', service.posts.views.PublicPostsList.as_view(), name='public-posts-list'),
    url(r'^posts/(?P<pk>[0-9a-fA-F-]+)/?$', service.posts.views.SpecificPostsView.as_view(),
        name='post-detail'),
]

urlpatterns = [
    url(r'^service/', include(service_urls)),
]
