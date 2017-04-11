from django.conf.urls import url, include

from social.app.views import post as post_views
from social.app.views import author as author_views
from social.app.views import friend as friend_views

posts_urlpatterns = [
    # /posts/
    url(r'^$', post_views.all_posts, name='index'),

    # /posts/add/
    url(r'^add/$', post_views.post_create, name='posts-add'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'^(?P<pk>[0-9a-z\\-]+)/$', post_views.PostDetailView.as_view(), name='detail'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'(?P<pk>[0-9a-z\\-]+)/edit/$', post_views.post_update, name='posts-update'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/delete/
    url(r'(?P<pk>[0-9a-z\\-]+)/delete/$', post_views.post_delete, name='posts-delete'),


    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/comment
    url(r'(?P<pk>[0-9a-z\\-]+)/comment/$', post_views.add_comment_to_post, name='add_comment_to_post'),
]

authors_urlpatterns = [
    # /authors/
    url(r'^$', author_views.AuthorListView.as_view(), name='list'),
    # /authors/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'^(?P<pk>[0-9a-z\\-]+)$', author_views.AuthorDetailView.as_view(), name='detail'),
    # /authors/aeea8619-a9c1-4792-a273-80ccb7255ea2/posts/
    url(r'^(?P<pk>[0-9a-z\\-]+)/posts/$', author_views.get_posts_by_author, name='posts-by-author'),
    url(r'^find-remote/', author_views.find_remote_author, name='find-remote')
]

urlpatterns = [
    # /
    url(r'^$', post_views.my_stream_posts, name='index'),
    url(r'^posts/', include(posts_urlpatterns, namespace='posts')),
    url(r'^author/', include(authors_urlpatterns, namespace='authors')),
    url(r'^friendrequests/$', friend_views.FriendRequestsListView.as_view(), name='friend-requests-list'),
]
