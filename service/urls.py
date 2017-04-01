from django.conf.urls import url, include
from rest_framework import routers

import service.authors.views
import service.friendrequest.views
import service.users.views
import service.posts.views

router = routers.DefaultRouter()
router.register(r'users', service.users.views.UserViewSet)
router.register(r'author', service.authors.views.AuthorViewSet, base_name="author")

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = [
    url(r'^author/(?P<local_id>[0-9a-z\\-]+)/friends/(?P<other_host_name>[^/]+)/author/(?P<other_id>[0-9a-z\\-]+)/',
        service.authors.views.two_authors_are_friends,
        name='author-friends-with-other'),
    url(r'^author/posts/', service.posts.views.AllPostsViewSet.as_view({"get": "list"}), name='all-posts-list'),
    url(r'^', include(router.urls)),
    url(r'^auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^friendrequest/', service.friendrequest.views.friendrequest, name='friend-request'),
    url(r'^posts/', service.posts.views.PublicPostsList.as_view(), name='public-posts-list'),
    url(r'^posts/(?P<pk>[0-9a-z\\-]+)/', service.posts.views.AllPostsViewSet.as_view({"get": "retrieve"}),
        name='post-detail'),
    url(r'^author/(?P<pk>[0-9a-z\\-]+)/posts/',
        service.posts.views.AuthorPostsList.as_view(),
        name='author-posts-list'),
]
