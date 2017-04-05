from django.conf.urls import url, include
from rest_framework import routers

import service.authors.views
import service.friendrequest.views
import service.posts.views

import service.internal.authors.views

# router = routers.DefaultRouter()
# router.register(r'author', service.authors.views.AuthorViewSet, base_name="author")

# Viewset methods are mapped to URLs manually to get around issue where the API schema wouldn't show all available
# endpoints, causing problems in Swagger
author_urls = [
    url(r'^posts/$', service.posts.views.AllPostsViewSet.as_view({'get': 'all-posts'}), name='all-posts-list'),
    url(r'^(?P<pk>[0-9a-fA-F-]+)/posts/$',
        service.posts.views.AuthorPostsViewSet.as_view(),
        name='author-posts-list'),
    url(r'^(?P<pk>[0-9a-z\\-]+)/friends/$',
        service.authors.views.AuthorViewSet.as_view({'get': 'author_friends'}),
        name='author-friends-list'),
    url(r'^(?P<local_id>[0-9a-z\\-]+)/friends/(?P<other_host_name>[^/]+)/author/(?P<other_id>[0-9a-z\\-]+)/$',
        service.authors.views.AuthorViewSet.as_view({'get': 'two_authors_are_friends'}),
        name='two-author-friends-with-other'),
    url(r'^(?P<pk>[0-9a-z\\-]+)/$',
        service.authors.views.AuthorViewSet.as_view({'get': 'detail'}),
        name='author-detail'),
]

internal_urls = [

    url(r'^author/(?P<pk>[0-9a-z\\-]+)/follow/$',
        service.internal.authors.views.follow,
        name='author-follow'),
    url(r'^author/(?P<pk>[0-9a-z\\-]+)/unfollow/$',
        service.internal.authors.views.unfollow,
        name='author-unfollow'),
    url(r'^author/(?P<pk>[0-9a-z\\-]+)/friendrequest/$',
        service.internal.authors.views.friendrequest,
        name='author-friendrequest'),
]

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r'^author/', include(author_urls)),
    url(r'^internal/', include(internal_urls, namespace="internal")),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^friendrequest/', service.friendrequest.views.friendrequest, name='friend-request'),
    url(r'^posts/', service.posts.views.PublicPostsList.as_view(), name='public-posts-list'),
    url(r'^posts/(?P<pk>[0-9a-z\\-]+)/', service.posts.views.AllPostsViewSet.as_view({"get": "retrieve"}),
        name='post-detail'),
]

