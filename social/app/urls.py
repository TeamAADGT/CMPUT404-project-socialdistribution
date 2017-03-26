from django.conf.urls import url, include

from social.app.views import post as post_views
from social.app.views import author as author_views
from social.app.views import friend as friend_views

posts_urlpatterns = [
    # /posts/
    url(r'^$', post_views.view_posts, name='index'),

    # /posts/add/
    url(r'^add/$', post_views.post_create, name='posts-add'),

    # /posts/upload/
    url(r'^upload/$', post_views.post_upload, name='upload-new'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'^(?P<pk>[0-9a-z\\-]+)/$', post_views.DetailView.as_view(), name='detail'),

    # This is to update posts. Currently not set-up in the front-end
    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'(?P<pk>[0-9a-z\\-]+)/edit/$', post_views.PostUpdate.as_view(), name='posts-update'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/delete/
    url(r'(?P<pk>[0-9a-z\\-]+)/delete/$', post_views.PostDelete.as_view(), name='posts-delete'),

    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/comment
    url(r'(?P<pk>[0-9a-z\\-]+)/comment/$', post_views.add_comment_to_post, name='add_comment_to_post'),

    # view all comments on a posts
    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/comments
    url(r'(?P<pk>[0-9a-z\\-]+)/comments/$', post_views.view_post_comments, name='view-posts-comments'),

    # get post's image
    # /posts/aeea8619-a9c1-4792-a273-80ccb7255ea2/image
    url(r'(?P<pk>[0-9a-z\\-]+)/upload/$', post_views.get_upload_file, name='upload-view'),
]

authors_urlpatterns = [
    # /authors/
    url(r'^$', author_views.AuthorListView.as_view(), name='list'),
    # /authors/aeea8619-a9c1-4792-a273-80ccb7255ea2/
    url(r'^(?P<pk>[0-9a-z\\-]+)$', author_views.AuthorDetailView.as_view(), name='detail'),
    # /authors/aeea8619-a9c1-4792-a273-80ccb7255ea2/posts/
    url(r'^(?P<pk>[0-9a-z\\-]+)/posts/$', author_views.view_posts_by_author, name='posts-by-author'),
]

urlpatterns = [
    url(r'^$', post_views.indexHome, name='index'),
    url(r'^posts/', include(posts_urlpatterns, namespace='posts')),
    url(r'^authors/', include(authors_urlpatterns, namespace='authors')),
    url(r'^friendrequests/$', friend_views.FriendRequestsListView.as_view(), name='friend-requests-list'),
]
