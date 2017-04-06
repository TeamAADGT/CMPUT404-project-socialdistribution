import re
import uuid, logging

import CommonMark
from django.contrib.auth.models import User
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


# This gets all remote posts from:
# /service/posts
# TODO: need to query remote author to grab their friends?
# TODO: need to save post comments too?
def get_remote_node_posts():
    node_posts = list()
    for node in Node.objects.filter(local=False):
        print "NODE", node
        try:
            some_json = node.get_public_posts()
            for post_json in some_json['posts']:
                author_json = post_json['author']

                # 'id' should be a URI per the spec, but we're being generous and also accepting a straight UUID
                if 'http' in author_json['id']:
                    remote_author_id = uuid.UUID(Author.get_id_from_uri(author_json['id']))
                else:
                    remote_author_id = uuid.UUID(author_json['id'])


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
