import re
import uuid

import CommonMark
from django.db import models
from django.urls import reverse
from django.db.models import Q

from social.app.models.author import Author
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
    visible_to = models.ManyToManyField(
        Author,
        related_name='visible_posts',
        blank=True
    )

    unlisted = models.BooleanField(default=False)


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
        return [cat.name for cat in self.categories.all()]

    def categories_string(self):
        names = self.categories_list()
        return " ".join(names) if names else ""

    def is_text(self):
        return self.content_type in keys(Post.TEXT_CONTENT_TYPES)

    def is_image(self):
        return self.content_type in keys(Post.IMAGE_CONTENT_TYPES)

    def is_file(self):
        return self.content_type in keys(Post.FILE_CONTENT_TYPES)

    def is_upload(self):
        return self.is_file() or self.is_image()

    def upload_url(self):
        return reverse('app:posts:upload-view', kwargs={'pk': self.id})


def keys(tuple_list):
    """
    Accepts a tuple list, returns a list of each tuple's first values
    """
    return [x[0] for x in tuple_list]


def get_all_public_posts():
    public_posts = dict()
    public_posts["user_posts"] = Post.objects \
        .filter(Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
        .order_by('-published')
    return public_posts["user_posts"]


def get_all_friend_posts(user):
    friend_posts = dict()
    friend_posts["user_posts"] = Post.objects \
        .filter(author__id__in=user.friends.all()) \
        .filter(Q(visibility="FRIENDS") | Q(visibility="PUBLIC") | Q(visibility="SERVERONLY")) \
        .order_by('-published')
    return friend_posts["user_posts"]


def get_all_foaf_posts(author):
    friends_list = set(f.id for f in author.friends.all())
    foafs = set()

    for friend in friends_list:
        friend_obj = Author.objects.get(pk=friend)
        new_foafs = set(ff.id for ff in friend_obj.friends.all())
        foafs.update(new_foafs)
    foafs.update(friends_list)

    foaf_posts = dict()
    foaf_posts["user_posts"] = Post.objects \
        .filter(Q(author__id__in=foafs)) \
        .filter(Q(visibility="FOAF") | Q(visibility="PUBLIC")).order_by('-published')

    return foaf_posts["user_posts"]


def get_remote_node_posts():
    node_posts = list()
    for node in Node.objects.filter(local=False):
        for post_json in node.get_author_posts()['posts']:
            author_json = post_json['author']
            author = Author(
                id=Author.get_id_from_uri(author_json['id']),
                node=node,
                displayName=author_json['displayName'],
            )
            post = Post(
                id=post_json['id'],
                title=post_json['title'],
                source=post_json['source'],
                origin=post_json['origin'],
                description=post_json['description'],
                author=author,
                published=post_json['published'],
            )
            node_posts.append(post)

    if node_posts == []:
        node_posts = Post.objects.none()

    return node_posts