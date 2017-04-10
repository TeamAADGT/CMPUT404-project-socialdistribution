import logging
import re
import urlparse

import requests
from django.db import models
from django.db.models.signals import post_save
from requests import HTTPError
from rest_framework.reverse import reverse


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

    requires_auth = models.BooleanField(default=True)  # TODO: remove this attribute
    share_images = models.BooleanField(default=True)
    share_posts = models.BooleanField(default=True)

    incoming_username = models.CharField(unique=True, default='social', blank=True, max_length=512)
    incoming_password = models.CharField(default='password', blank=True, max_length=512)

    def __str__(self):
        return '%s (%s; %s)' % (self.name, self.host, self.service_url)

    def _get_author(self, uuid):
        url = self.service_url + "author/" + str(uuid)
        return requests.get(url, auth=(self.username, self.password))

    def get_author(self, uuid):
        return self._get_author(uuid).json()

    def get_author_friends(self, uuid):
        url = self.service_url + "author/" + str(uuid) + "/friends"
        return requests.get(url, auth=(self.username, self.password)).json()

    def get_if_authors_are_friends(self, first_author_id, second_author_uri):
        from social.app.models.author import Author
        (second_author_host, second_author_id) = Author.parse_uri(second_author_uri)
        second_author_host = second_author_host.replace('http://', '', 1).replace('https://', '', 1)

        if second_author_host[-1] != "/":
            second_author_host += "/"

        url = (self.service_url
               + "author/" + str(first_author_id)
               + "/friends/" + second_author_host + str(second_author_id))

        return requests.get(url, auth=(self.username, self.password)).json()["friends"]

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

    @classmethod
    def get_host_from_uri(cls, uri):
        p = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        m = re.search(p, uri)
        return m.group('host')

    def get_public_posts(self):
        url = self.service_url + "posts/"
        response = requests.get(url, auth=(self.username, self.password)).json()
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
        response = self._get_author(uuid)

        try:
            response.raise_for_status()
        except HTTPError:
            if response.status_code == requests.codes.not_found:
                # Author not found
                return None
            else:
                raise

        json = response.json()

        from social.app.models.author import Author
        (author, created) = Author.objects.update_or_create(
            id=Author.get_id_from_uri(json["id"]),
            node=self,
            defaults={
                'displayName': json['displayName'],
                'activated': True
            }
        )

        if "github" in json:
            author.github = json["github"]

        if "firstName" in json:
            author.first_name = json["firstName"]

        if "lastName" in json:
            author.last_name = json["lastName"]

        if "email" in json:
            author.email = json["email"]

        if "bio" in json:
            author.bio = json["bio"]

        author.save()
        return author

    def get_is_authenticated(self):
        return True

    is_authenticated = property(get_is_authenticated)

    def post_friend_request(self, request, local_author, remote_author):
        if remote_author.node != self or self.local:
            raise Exception("Target's node must be the same remote node.")

        current_author_uri = reverse("service:author-detail", kwargs={'pk': local_author.id}, request=request)
        target_author_uri = urlparse.urljoin(self.service_url, 'author/' + str(remote_author.id))

        return requests.post(
            urlparse.urljoin(self.service_url, "friendrequest"),
            json={
                "query": "friendrequest",
                "author": {
                    "id": current_author_uri,
                    "host": local_author.node.service_url,
                    "displayName": local_author.displayName,
                    "url": current_author_uri,
                },
                "friend": {
                    "id": target_author_uri,
                    "host": self.service_url,
                    "displayName": remote_author.displayName,
                    "url": target_author_uri,
                }
            },
            auth=(self.username, self.password))


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
