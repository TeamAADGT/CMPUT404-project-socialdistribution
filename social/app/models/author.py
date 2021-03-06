import urlparse
import uuid
import re

from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save

from datetime import datetime

from django.utils import timezone


from rest_framework.reverse import reverse

from social.app.models.node import Node


class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    displayName = models.CharField(max_length=512)

    ### Optional Attributes

    user = models.OneToOneField(User, related_name='user', blank=True, null=True)

    # https://github.com/join
    github = models.URLField(default='', blank=True)

    first_name = models.TextField(default='', blank=True)
    last_name = models.TextField(default='', blank=True)
    email = models.EmailField(default='', blank=True)
    bio = models.TextField(default='', blank=True)

    ### Meta Attributes
    activated = models.BooleanField(default=False)

    node = models.ForeignKey(Node, on_delete=models.CASCADE)

    followed_authors = models.ManyToManyField(
        'self',
        symmetrical=False,
        # Ensures no backwards relation is created
        # No need to for an author to see who follows them
        related_name='+',
        blank=True)

    outgoing_friend_requests = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='incoming_friend_requests',
        blank=True
    )

    friends = models.ManyToManyField('self', blank=True)

    has_github_task = models.BooleanField(default=False)

    def follows(self, author):
        return self != author and len(self.followed_authors.filter(id=author.id)) > 0

    def friends_with(self, author):
        return self != author and len(self.friends.filter(id=author.id)) > 0

    def friends_with_remote_author(self, remote_author_id):
        return len(self.friends.filter(id=remote_author_id)) > 0

    def has_outgoing_friend_request_for(self, author):
        return self != author and len(self.outgoing_friend_requests.filter(id=author.id)) > 0

    def has_incoming_friend_request_from(self, author):
        return self != author and len(self.incoming_friend_requests.filter(id=author.id)) > 0

    def can_follow(self, author):
        return not (
            self == author
            or not self.activated
            or not author.activated
            or self.follows(author)
        )

    def can_send_a_friend_request_to(self, author):
        return not (
            self == author
            or not self.activated
            or not author.activated
            or self.friends_with(author)
            or self.has_outgoing_friend_request_for(author)
            or self.has_incoming_friend_request_from(author)
        )

    def add_friend_request(self, author):
        self.outgoing_friend_requests.add(author)
        self.followed_authors.add(author)

    def accept_friend_request(self, author):
        if self.incoming_friend_requests.filter(id=author.id):
            self.incoming_friend_requests.remove(author)
            self.friends.add(author)
            self.followed_authors.add(author)
        else:
            raise Exception("Attempted to accept a friend request that does not exist.")

    def get_short_json(self, request):
        """
        Note: doesn't actually return JSON, just a Dict
        """
        node = self.node

        if node.local:
            uri = reverse("service:author-detail", kwargs={'pk': self.id}, request=request)
        else:
            uri = urlparse.urljoin(node.service_url, 'author/' + str(self.id))

        return {
            "id": uri,
            "host": node.service_url,
            "displayName": self.displayName,
            "url": uri,
        }

    def __str__(self):
        return '%s' % self.displayName

    @classmethod
    def get_id_from_uri(cls, uri):
        return cls.parse_uri(uri)[1]

    @classmethod
    def parse_uri(cls, uri):
        match = re.match(r'^(?P<host>(https?://(.+)/))author/(?P<pk>[0-9a-fA-F-]+)/?', uri)
        return match.group('host'), uuid.UUID(match.group('pk'))

    def get_uri(self):
        return Author.get_uri_from_host_and_uuid(self.node.host, self.id)

    # This method cannot have the same name as get_uri as overloading
    # attributes is not directly supported in Python
    @staticmethod
    def get_uri_from_host_and_uuid(host_url, id):
        if host_url[:-1] != '/':
            host_url += '/'

        if type(id) is not uuid.UUID:
            id = uuid.UUID(id)

        if host_url.startswith("http") is False:
            host_url = "http://" + host_url

        return host_url + 'author/' + str(id)

    required_fields = {'id', 'url', 'host', 'displayName', 'github'}


def create_profile(sender, **kwargs):
    user = kwargs["instance"]

    if user.is_staff or user.username == "api":
        return

    if kwargs["created"]:
        # Creating a new User populates a new Author, if not already set
        author = Author(user=user)
        author.node = Node.objects.get(local=True)
        author.save()
    else:
        author = user.profile

    author.first_name = user.first_name
    author.last_name = user.last_name
    author.displayName = user.first_name + ' ' + user.last_name
    author.email = user.email

    author.save()


def update_profile(sender, **kwargs):
    from social.tasks import get_github_activity
    author = kwargs["instance"]
    if author.github != "" and not author.has_github_task and author.node.local:
        time = timezone.now().replace(2018, 1, 1)
        get_github_activity(str(author.id), repeat=60, repeat_until=time)
        author.has_github_task = True
        author.save()
    elif author.github == "" and author.has_github_task:
        author.has_github_task = False
        author.save()


post_save.connect(create_profile, sender=User)
post_save.connect(update_profile, sender=Author)


def get_associated_author(user):
    if user.is_staff or user.username == "api":
        return None
    return Author.objects.get_or_create(user=user)[0]


User.profile = property(get_associated_author)
