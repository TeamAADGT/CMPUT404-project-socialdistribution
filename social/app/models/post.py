import logging
import re
import uuid

import CommonMark
from django.db import models
from django.db.models import Q
from django.urls import reverse

from social.app.models.author import Author
from social.app.models.authorlink import AuthorLink
from social.app.models.category import Category
from social.app.models.node import Node


class Post(models.Model):
    # Code idea from Django Docs,
    # url: https://docs.djangoproject.com/en/dev/ref/models/fields/#choices
    TEXT_CONTENT_TYPES = [
        ("text/markdown", "Markdown"),
        ("text/plain", "Plain Text"),
    ]

    FILE_CONTENT_TYPES = [
        ("application/base64", "File Upload"),
    ]

    IMAGE_CONTENT_TYPES = [
        ("image/png;base64", "Image (PNG)"),
        ("image/jpeg;base64", "Image (JPEG)"),
    ]

    UPLOAD_CONTENT_TYPES = FILE_CONTENT_TYPES + IMAGE_CONTENT_TYPES
    CONTENT_TYPES = TEXT_CONTENT_TYPES + UPLOAD_CONTENT_TYPES

    VISIBILITY_OPTIONS = [
        ("PUBLIC", "Public"),
        ("FOAF", "FOAF"),
        ("FRIENDS", "Friends"),
        ("PRIVATE", "Private"),
        ("SERVERONLY", "This Server Only"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=250)
    source = models.URLField()
    origin = models.URLField()
    description = models.TextField()
    github_id = models.TextField(default="")

    content_type = models.CharField(
        max_length=20,
        choices=CONTENT_TYPES,
        default="text/plain"
    )

    content = models.TextField(default="")

    author = models.ForeignKey(
        Author,
        on_delete=models.CASCADE
    )

    categories = models.ManyToManyField(
        Category,
        blank=True
    )

    published = models.DateTimeField(auto_now_add=True)

    visibility = models.CharField(
        max_length=10,
        choices=VISIBILITY_OPTIONS,
        default="PUBLIC",
    )

    # List of Authors who can read the PRIVATE message
    # attribute only renders in /posts/add/ if visibility is set to "PRIVATE"
    visible_to_author = models.ManyToManyField(
        AuthorLink,
        related_name='visible_posts',
        blank=True,
    )

    unlisted = models.BooleanField(default=False)

    child_post = models.OneToOneField(
        to='Post',
        null=True,
        blank=True,
        related_name='parent_post',
        on_delete=models.SET_NULL
    )

    def get_absolute_url(self):
        return reverse('app:posts:detail', kwargs={'pk': self.id})

    def content_html(self):
        if self.content_type == "text/plain":
            return self.content
        if self.content_type == "text/markdown":
            parser = CommonMark.Parser()
            renderer = CommonMark.HtmlRenderer(options={'safe': True})
            return renderer.render(parser.parse(self.content))

        return ""

    def categories_list(self):
        return [cat.name for cat in self.categories.order_by('name')]

    def categories_string(self):
        names = self.categories_list()
        return " ".join(names) if names else ""

    def visible_to_uuid_list(self):
        return [str(author.id) for author in self.visible_to.all()]

    def visible_to_uris_string(self):
        authors_uuids = self.visible_to_uuid_list()
        authors_uris = list()

        for author_uuid in authors_uuids:
            author_host = Author.objects.get(pk=author_uuid).node.host
            author_service_url = Author.objects.get(pk=author_uuid).node.service_url

            protocol = ""
            if author_service_url.find("http://") >= 0:
                protocol += "http://"
            elif author_service_url.find("https://") >= 0:
                protocol += "https://"
            else:
                protocol += ""

            author_uri = reverse('app:authors:detail', kwargs={'pk': author_uuid})
            authors_uris.append(protocol + author_host + author_uri)

        return "\n".join(authors_uris) if authors_uris else ""

    def visible_to_author_uri_list(self):
        return [str(author_uri.uri) for author_uri in self.visible_to_author.all()]

    def visible_to_authors_string(self):
        authors_uris = self.visible_to_author_uri_list()
        return "\n".join(authors_uris) if authors_uris else ""

    def get_visible_to_author_uuid_list(self):
        authors_uris = self.visible_to_author_uri_list()
        authors_uuids = list()

        for author_uri in authors_uris:
            try:
                author_uuid = Author.get_id_from_uri(author_uri)
                authors_uuids.append(author_uuid)
            except Exception as e:
                logging.error(e)
                logging.error("Invalid Author Link")

        return authors_uuids

    def is_text(self):
        return self.content_type in keys(Post.TEXT_CONTENT_TYPES)

    def is_image(self):
        return self.content_type in keys(Post.IMAGE_CONTENT_TYPES)

    def is_file(self):
        return self.content_type in keys(Post.FILE_CONTENT_TYPES)

    def is_upload(self):
        return self.is_file() or self.is_image()

    def upload_url(self):
        if self.is_image():
            return "data:%s,%s" % (self.content_type, self.content)
        elif self.child_post:
            return self.child_post.upload_url()
        else:
            return ""

    def visible_to_remote_author(self, remote_author_id):
        return len(self.visible_to.filter(author_id=remote_author_id)) > 0

    @classmethod
    def get_id_from_uri(cls, uri):
        match = re.match(r'^(.+)//(.+)/posts/(?P<pk>[0-9a-z\\-]+)', uri)
        return match.group('pk')


def keys(tuple_list):
    """
    Accepts a tuple list, returns a list of each tuple's first values
    """
    return [x[0] for x in tuple_list]


def get_all_public_posts():
    return Post.objects \
        .filter(Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
        .order_by('-published')


def get_all_friend_posts(user):
    return Post.objects \
        .filter(author__id__in=user.friends.all()) \
        .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
        .order_by('-published')


def get_all_foaf_posts(author):
    friends_list = set(f.id for f in author.friends.all())
    foafs = set()

    for friend in friends_list:
        friend_obj = Author.objects.get(pk=friend)
        new_foafs = set(ff.id for ff in friend_obj.friends.all())
        foafs.update(new_foafs)
    foafs.update(friends_list)

    return Post.objects \
        .filter(Q(author__id__in=foafs)) \
        .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')


def get_all_local_private_posts():
    all_private_posts = Post.objects.filter(Q(visibility="PRIVATE")).order_by('-published')
    local_authors_uris = list()

    for post in all_private_posts:
        authors_uris = post.visible_to_author_uri_list()

        if authors_uris is not None:
            for author_uri in authors_uris:
                author_uuid = Author.get_id_from_uri(author_uri)

                if Author.objects.get(id=author_uuid) is not None:
                    local_authors_uris.append(author_uri)

    all_private_posts = all_private_posts.filter(Q(visible_to_author__uri__in=local_authors_uris))

    return all_private_posts


# This gets all remote posts from:
# /service/posts
def get_remote_node_posts():
    node_posts = list()
    for node in Node.objects.filter(local=False):
        try:
            all_public_posts_jsons = node.get_all_public_posts(size=50)
            for all_public_posts_json in all_public_posts_jsons:
                some_json = all_public_posts_json

                if len(some_json) == 0:
                    continue

            for post_json in some_json['posts']:
                author_json = post_json['author']

                # 'id' should be a URI per the spec, but we're being generous and also accepting a straight UUID
                if author_json['id'].startswith('http'):
                    remote_author_id = uuid.UUID(Author.get_id_from_uri(author_json['id']))
                else:
                    remote_author_id = uuid.UUID(author_json['id'])

                # Add remote author to DB
                author, created = Author.objects.update_or_create(
                    id=remote_author_id,
                    defaults={
                        'node': node,
                        'displayName': author_json['displayName'],
                    }
                )
                if post_json['id'].startswith('http'):
                    post_id = uuid.UUID(Post.get_id_from_uri(post_json['id']))
                else:
                    post_id = uuid.UUID(post_json['id'])

                # Add remote post to DB
                post, created = Post.objects.update_or_create(
                    id=post_id,
                    defaults={
                        'title': post_json['title'],
                        'source': post_json['source'],
                        'origin': post_json['origin'],
                        'description': post_json['description'],
                        'author': author,
                        'published': post_json['published'],
                        'content': post_json['content'],
                        'content_type': post_json['contentType'],
                        'visibility': post_json['visibility'],
                    }
                )
                node_posts.append(post)

        except Exception, e:
            logging.error(e)
            logging.warn('Skipping a post retrieved from ' + node.host)
            continue


# TODO: get posts from service/author/posts/
# This gets all remote posts from:
# /service/author/posts/
def get_all_remote_node_posts():
    node_posts = list()
    for node in Node.objects.filter(local=False):
        try:
            some_json = node.get_author_posts()
            for post_json in some_json['posts']:
                author_json = post_json['author']

                # 'id' should be a URI per the spec, but we're being generous and also accepting a straight UUID
                if 'http' in author_json['id']:
                    remote_author_id = uuid.UUID(Author.get_id_from_uri(author_json['id']))
                else:
                    remote_author_id = uuid.UUID(author_json['id'])

                # Add remote author to DB
                author, created = Author.objects.update_or_create(
                    id=remote_author_id,
                    defaults={
                        'node': node,
                        'displayName': author_json['displayName'],
                    }
                )
                if 'http' in post_json['id']:
                    post_id = uuid.UUID(Post.get_id_from_uri(post_json['id']))
                else:
                    post_id = uuid.UUID(post_json['id'])

                # Add remote post to DB
                post, created = Post.objects.update_or_create(
                    id=post_id,
                    defaults={
                        'title': post_json['title'],
                        'source': post_json['source'],
                        'origin': post_json['origin'],
                        'description': post_json['description'],
                        'author': author,
                        'published': post_json['published'],
                        'content': post_json['content'],
                        'visibility': post_json['visibility'],
                    }
                )
                node_posts.append(post)

        except Exception, e:
            logging.error(e)
            logging.warn('Skipping a post retrieved from ' + node.host)
            continue
