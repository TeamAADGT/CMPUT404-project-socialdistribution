import requests
from django.db import models

from social.app.models.author import Author


class Node(models.Model):
    """
    Represents a local or remote server upon which remote authors and posts reside
    """
    name = models.CharField(max_length=512)
    host = models.CharField(max_length=512,unique=True)
    service_url = models.URLField(unique=True)
    local = models.BooleanField(default=False)

    username = models.CharField(blank=True, max_length=512)
    password = models.CharField(blank=True, max_length=512)

    requires_auth = models.BooleanField(default=True)
    share_images = models.BooleanField(default=True)
    share_posts = models.BooleanField(default=True)

    incoming_username = models.CharField(unique=True, default='social', blank=True, max_length=512)
    incoming_password = models.CharField(default='password', blank=True, max_length=512)

    def __str__(self):
        return '%s (%s; %s)' % (self.name, self.host, self.service_url)

    def get_author(self, uuid):
        url = self.service_url + "/author/" + str(uuid)
        return requests.get(url, auth=(self.username, self.password))

    def get_author_friends(self, uuid):
        url = self.service_url + "/author/" + str(uuid) + "/friends"
        return requests.get(url, auth=(self.username, self.password))

    def create_or_update_remote_author(self, uuid):
        json = self.get_author(uuid).json()
        author = Author.objects.update_or_create(
            id=Author.get_id_from_uri(json["id"]),
            displayName=json["displayName"],
            node=self
        )

        if "github" in json:
            author.github = json["github"]

        if "firstName" in json:
            author.user.first_name = json["firstName"]

        if "lastName" in json:
            author.user.last_name = json["lastName"]

        if "email" in json:
            author.user.email = json["email"]

        if "bio" in json:
            author.bio = json["bio"]

        author.save()
        return author

    def get_is_authenticated(self):
        return True

    is_authenticated = property(get_is_authenticated)
