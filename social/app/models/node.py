import logging
import urllib
import urlparse
import re
import uuid

import requests
from django.db import models
from django.db.models.signals import post_save
from requests import HTTPError
from rest_framework.reverse import reverse

from social.app.models.utils import is_valid_url


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

    def _get_author(self, author_id):
        url = urlparse.urljoin(self.service_url, "author/" + str(author_id))
        return requests.get(url, auth=self.auth())

    def auth(self):
        return self.username, self.password

    def get_author(self, author_id):
        return self._get_author(author_id).json()

    def get_post(self, post_id):
        url = urlparse.urljoin(self.service_url, "posts/" + str(post_id))
        response = requests.get(url, auth=self.auth())
        response.raise_for_status()
        return verify_posts_endpoint_output(url, response.json())

    def get_post_comments(self, post_uuid):
        """
        Returns a list of dicts that represents all of the Comments fetched for a particular remote Post,
        traversing pagination if required.
        """
        base_url = urlparse.urljoin(self.service_url, "posts/%s/comments" % str(post_uuid))
        json = requests.get(base_url, auth=self.auth()).json()

        all_comments = json["comments"]

        while True:
            # Depending on how the other server interpreted the spec, a lack of a next page is rendered as either
            # the next field not existing, or the next field being set to an empty value, so we gotta check for both
            if 'next' in json and is_valid_url(json['next']):
                next_url = json["next"]
            else:
                break

            json = requests.get(next_url, auth=self.auth()).json()
            all_comments += json["comments"]

        return all_comments

    def get_author_friends(self, author_id):
        url = self.service_url + "author/" + str(author_id) + "/friends"
        return requests.get(url, auth=self.auth()).json()

    def get_author_posts(self):
        url = urlparse.urljoin(self.service_url, 'author/posts')
        response = requests.get(url, auth=self.auth())
        response.raise_for_status()
        return verify_posts_endpoint_output(url, response.json())

    @classmethod
    def get_host_from_uri(cls, uri):
        p = '(?:http.*://)?(?P<host>[^:/ ]+).?(?P<port>[0-9]*).*'
        m = re.search(p, uri)
        return m.group('host')

    '''
    Get all the public posts, traversing through the 'next' link as well, if present.
    '''
    def get_all_public_posts(self, size=50):
        posts_json = self.get_public_posts(size=size)
        all_posts_jsons = [posts_json]
        while True:
            if 'next' in posts_json and is_valid_url(posts_json['next']):
                posts_json = self.get_public_posts(next_url=posts_json['next'])
                all_posts_jsons.append(posts_json)
            else:
                break
        return all_posts_jsons

    '''
    Get all the posts from /service/posts
    Declare a URL in next OR specify the page and size for the initial request.
    If the next value is specified, given page and size values are ignored.
    '''
    def get_public_posts(self, page=1, size=50, next_url=None):
        if next_url is None:
            url = urlparse.urljoin(self.service_url, "posts")
            params = dict()
            if page is not None:
                params['page'] = page
            if size is not None:
                params['size'] = size

            if len(params) > 0:
                url += '?' + urllib.urlencode(params)
        else:
            url = next_url

        response = requests.get(url, auth=self.auth())
        response.raise_for_status()
        return verify_posts_endpoint_output(url, response.json())

    def create_or_update_remote_post(self, post_uuid):
        try:
            json = self.get_post(post_uuid)
        except HTTPError as e:
            if e.response.status_code == requests.codes.not_found:
                # Post not found
                return None
            else:
                raise

        # Even when fetching a single post, we get a "paginated" view of it
        # So, let's go find our post in here
        for post_json in json["posts"]:
            if post_json["id"] == post_uuid:
                from social.app.models.post import Post
                from social.app.models.author import Author

                # We've found it, so let's save a copy to the DB
                author_json = post_json['author']
                author_id = Author.get_id_from_uri(author_json['id'])
                author = self.create_or_update_remote_author(author_id)
                post, created = Post.objects.update_or_create(
                    id=uuid.UUID(post_json["id"]),
                    defaults={
                        'title': post_json['title'],
                        'description': post_json['description'],
                        'author': author,
                        'published': post_json['published'],
                        'content': post_json['content'],
                        'visibility': post_json['visibility'],
                    }
                )

                comments = post_json['comments']
                count = post_json["count"]
                return post, comments, count

        # If we got here, it means the server decided to just return an empty paginated view
        # instead of a 404
        return None

    def create_or_update_remote_author(self, author_id):
        response = self._get_author(author_id)

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
            auth=self.auth())


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

def verify_posts_endpoint_output(url, json):
    if all(keys in json for keys in ('query', 'count', 'size', 'posts')):
        return json
    else:
        logging.warn(
            "%s did not conform to the expected response format! Returning an empty list of posts!"
            % url)
        return {}
