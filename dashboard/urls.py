from django.conf.urls import url
from dashboard import views
from dashboard import views as dashboard_views

urlpatterns = [
    # /dashboard/
    url(r'^$', dashboard_views.index, name='index'),
    url(r'^authors/$', views.AuthorListView.as_view(), name='author-list'),
    url(r'^authors/(?P<pk>[0-9,a-z,\\-]+)$', views.AuthorDetailView.as_view(), name='author-detail'),
    url(r'^friendrequests/$', views.FriendRequestsListView.as_view(), name='friend-requests-list'),
]
