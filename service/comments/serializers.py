from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from service.authors.serializers import UnknownAuthorSerializer, SimpleAuthorSerializer
from social.app.models.comment import Comment
from social.app.models.post import Post
from social.app.models.post import Author
from social.app.models.node import Node


# For viewing comments at API endpoint
class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = SimpleAuthorSerializer()
    contentType = serializers.CharField(default="text/markdown")

    class Meta:
        model = Comment
        fields = ("id", "author", "comment", "published", "contentType")


class NewCommentSerializer(serializers.Serializer):
    author = UnknownAuthorSerializer()
    comment = serializers.CharField()
    contentType = serializers.CharField(default="text/markdown")
    published = serializers.DateTimeField()
    id = serializers.UUIDField()


# For posting comment to API endpoint /service/posts/<post_id>/comments/
class CreateCommentSerializer(serializers.Serializer):
    query = serializers.CharField(default="addComment")
    post = serializers.URLField()
    comment = NewCommentSerializer()

    # TODO: make sure you check that the post is a local post!
    def validate(self, data):
        """
        We do not allow anonymous comments -- all comments must be submitted by known remote nodes
        Must ensure that remote author has permission to comment on that post.
        """
        # value looks like: http://127.0.0.1:8000/posts/563aeed8-37f5-4aa9-bf7c-6e012429c4a3/
        post_id = Post.get_id_from_uri(data['post'])

        post = get_object_or_404(Post, pk=post_id)

        # Get this from the request

        remote_node_host = data["comment"]["author"]["host"]
        remote_node = get_object_or_404(Node, service_url=remote_node_host)
        anonymous_node = remote_node is None or not remote_node.is_authenticated

        if not anonymous_node and not remote_node.share_posts:
            # We're specifically blocking this node, so prevent them from commenting on this post
            raise ValidationError('You do not have permission to comment on that post')

        if anonymous_node or not remote_node.share_images:
            # We do not allow anonymous comments
            raise ValidationError('You do not have permission to comment on that post')

        else:  # We trust this node, so allow them to comment on this post IF the remote author has permission to view
            # that post.
            remote_author_uri = data["comment"]["author"]["url"]
            remote_author_id = Author.get_id_from_uri(remote_author_uri)
            remote_author = remote_node.create_or_update_remote_author(remote_author_id)

            queryset = Post.objects.filter(id=post_id, author__node__local=True)
            queryset = queryset.exclude(visibility="SERVERONLY")  # post must not be local only

            if post.visibility == "PUBLIC" and queryset:
                return data

            # Check if remote author is friends with post author
            if post.visibility == "FRIENDS":
                is_friend = post.author.friends_with(remote_author)
                if is_friend and queryset:
                    return data

                # Check if remote author is in the visibleTo list for that post
            if post.visibility == "PRIVATE":
                is_visible_to = post.visible_to_remote_author(remote_author_id)
                if is_visible_to and queryset:
                    return data

            if post.visibility == "FOAF":
                # TODO: Check if remote author is FOAF to post author
                is_FOAF = False
                if is_FOAF and queryset:
                    return data

            # remote author does not have permission to post a comment
            else:
                raise ValidationError('You do not have permission to comment on that post')

    def create(self, validated_data):
        comment_data = validated_data["comment"]
        comment_id = comment_data["id"]

        # We have already checked that the post is local so we know it must already be in the DB
        full_url_post_id = validated_data["post"]
        post_id = Post.get_id_from_uri(full_url_post_id)
        post = get_object_or_404(Post, pk=post_id)

        # May or may not be in our DB, so use create/update
        author_data = comment_data["author"]
        full_url_author_id = author_data["url"]
        remote_author_id = Author.get_id_from_uri(full_url_author_id)

        # Need to add remote node as foreign key
        remote_node_host = author_data["host"]
        remote_node = get_object_or_404(Node, service_url=remote_node_host)

        print author_data
        remote_display_name = author_data["displayName"]
        remote_github = author_data["github"] if "github" in author_data else ""

        # Need to add remote author to DB
        author, created = Author.objects.update_or_create(
            id=remote_author_id,
            defaults={
                'node': remote_node,
                'displayName': remote_display_name,
                'github': remote_github,
            }
        )

        remote_comment = comment_data["comment"]
        published = comment_data["published"]

        Comment(
            id=comment_id,
            post=post,
            author=author,
            comment=remote_comment,
            published=published,
        ).save()

        comment = get_object_or_404(Comment, pk=comment_id)
        return comment
