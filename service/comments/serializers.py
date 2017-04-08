from rest_framework import serializers
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404

from service.authors.serializers import UnknownAuthorSerializer
from social.app.models.comment import Comment
from social.app.models.post import Post
from social.app.models.post import Author
from social.app.models.node import Node


# For viewing comments at API endpoint
class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = UnknownAuthorSerializer()
    contentType = serializers.CharField(default="text/markdown")

    class Meta:
        model = Comment
        fields = ("id", "author", "comment", "published", "contentType")


# For posting comment to API endpoint /service/posts/<post_id>/comments/
class CreateCommentSerializer(serializers.Serializer):
    query = serializers.CharField(default="addComment")
    post = serializers.URLField()
    comment = CommentSerializer()


    # TODO: make sure you check that that post is a local post!
    def validate_post(self, value):
        """
        We do not allow anonymous comments -- all comments must be submitted by known remote nodes
        Must ensure that remote author has permission to comment on that post.
        """
        # value looks like: http://127.0.0.1:8000/posts/563aeed8-37f5-4aa9-bf7c-6e012429c4a3/
        full_url_post_id = value
        post_id = Post.get_id_from_uri(full_url_post_id)
        post = get_object_or_404(Post, pk=post_id)
        post_author = get_object_or_404(Author, pk=post.author_id)

        # Get this from the request
        full_url_remote_author_id = self.initial_data["comment"]["author"]["url"]
        remote_author_id = Author.get_id_from_uri(full_url_remote_author_id)

        remote_node_host = self.initial_data["comment"]["author"]["host"]
        host = Node.get_host_from_uri(remote_node_host)
        remote_node = get_object_or_404(Node, host=host)
        anonymous_node = remote_node is None or not remote_node.is_authenticated

        if not anonymous_node and not remote_node.share_posts:
            # We're specifically blocking this node, so prevent them from commenting on this post
            raise ValidationError('You do not have permission to comment on that post')

        if anonymous_node or not remote_node.share_images:
            # We do not allow anonymous comments
            raise ValidationError('You do not have permission to comment on that post')

        else: # We trust this node, so allow them to comment on this post IF the remote author has permission to view
            # that post.
            queryset = Post.objects.filter(id=post_id)
            queryset = queryset.exclude(visibility="SERVERONLY")

            if post.visibility == "PUBLIC" and queryset:
                return value

            # Check if remote author is friends with post author
            is_friend = post_author.friends_with_remote_author(remote_author_id)
            if post.visibility == "FRIENDS" and is_friend and queryset:
                return value

            # Check if remote author is in the visibleTo list for that post
            is_visible_to = post.visible_to_remote_author(remote_author_id)
            if post.visibility == "PRIVATE" and is_visible_to and queryset:
                return value

            # TODO: Check if remote author is FOAF to post author
            is_FOAF = False
            if post.visibility == "FOAF" and is_FOAF and queryset:
                return value

            # remote author does not have permission to post a comment
            else:
                raise ValidationError('You do not have permission to comment on that post')


    def create(self, validated_data):
        comment_id = self.initial_data["comment"]["id"]

        # Assuming we have already checked that the post is local
        full_url_post_id = self.initial_data["post"]
        post_id = Post.get_id_from_uri(full_url_post_id)
        post = get_object_or_404(Post, pk=post_id)

        # May or may not be in our DB, so use create/update
        full_url_author_id = self.initial_data["comment"]["author"]["url"]
        remote_author_id = Author.get_id_from_uri(full_url_author_id)

        # Need to add remote node as foreign key
        remote_node_host = self.initial_data["comment"]["author"]["host"]
        host = Node.get_host_from_uri(remote_node_host)
        remote_node = get_object_or_404(Node, host=host)

        remote_display_name = self.initial_data["comment"]["author"]["displayName"]
        remote_github = self.initial_data["comment"]["author"]["github"]

        # Need to add remote author to DB
        author, created = Author.objects.update_or_create(
            id=remote_author_id,
            defaults={
                'node': remote_node,
                'displayName': remote_display_name,
                'github': remote_github,
            }
        )

        remote_comment = self.initial_data["comment"]["comment"]
        published = self.initial_data["comment"]["published"]

        # Save to database and then return instance
        Comment(
            id=comment_id,
            post=post,
            author=author,
            comment=remote_comment,
            published=published,
        ).save()

        comment = get_object_or_404(Comment, pk=comment_id)
        return comment




