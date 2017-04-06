import json
import re
import logging

import requests
from django.db import models
from django.db.models.signals import post_save
import logging

class Node(models.Model):
    """
    Represents a local or remote server upon which remote authors and posts reside
    """
    name = models.CharField(max_length=512)
    host = models.CharField(max_length=512, unique=True)
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
        url = self.service_url + "author/" + str(uuid)
        return requests.get(url, auth=(self.username, self.password)).json()

    def get_author_friends(self, uuid):
        url = self.service_url + "author/" + str(uuid) + "/friends"
        return requests.get(url, auth=(self.username, self.password)).json()

    def get_author_posts(self):
        url = self.service_url + "author/posts/"
        response = requests.get(url, auth=(self.username, self.password)).json()
        if all(keys in response for keys in ('query', 'count', 'size', 'posts')):
            return response
        else:
            logging.warn(
                "%s did not conform to the expected response format! Returning an empty list of posts!"
                % url)
            return []

    def get_public_posts(self):
        url = self.service_url + "posts/"
        response = requests.get(url, auth=(self.username, self.password)).json()
        # Note: uncomment out following line to test with current "Coolbears" node if you want to test remote post results
        return response
        """
        if all(keys in response for keys in ('query', 'count', 'size', 'posts')):
            return response
        else:
            logging.warn(
                "%s did not conform to the expected response format! Returning an empty list of posts!"
                % url)
            return []
        """


    def create_or_update_remote_author(self, uuid):
        json = self.get_author(uuid).json()
        from social.app.models.author import Author
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


# TODO This post_save hook is untested!
def init_friends(sender, **kwargs):
    node = kwargs["instance"]
    if node.local is False:
        from social.app.models.author import Author
        authors = Author.objects.filter(node=node)
        for author in authors:
            for uri in node.get_author_friends(author.id).authors:
                uri = Author.get_id_from_uri(uri)
                # Simplifying assumption that there isn't a uri collision
                new_author_profile_json = node.get_author(uri)
                new_author = Author.objects.update_or_create(
                    id=uri,
                    displayName=new_author_profile_json['displayName'],
                    url=new_author_profile_json['url'],
                    node=node)

                new_author_friends_json = new_author.new_author_profile.friends
                for new_author_friend_json in new_author_friends_json:
                    # id, host, displayName, and url are available
                    new_author_friend_node = Node.objects.get_or_create(host=new_author_friends_json['host'])
                    new_author.friends.update_or_create(
                        id=uri,
                        displayName=new_author_profile_json['displayName'],
                        url=new_author_profile_json['url'],
                        node=new_author_friend_node)


post_save.connect(init_friends, sender=Node)
