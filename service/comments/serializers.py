from rest_framework import serializers

from service.authors.serializers import SimpleAuthorSerializer
from service.posts.serializers import PostSerializer
from social.app.models.comment import Comment


# For viewing comments at API endpoint
class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = SimpleAuthorSerializer()
    contentType = serializers.CharField(default="text/markdown")

    class Meta:
        model = Comment
        fields = ("id", "author", "comment", "published", "contentType")


# For posting comment to API endpoint /service/posts/<post_id>/comments/
class CreateCommentSerializer(serializers.Serializer):
    query = serializers.CharField(default="addComment")
    post = PostSerializer()
    comment = CommentSerializer()

    # value is the instance of the post serializer that has the data in it
    def validate_post(self, value):
        post_id = value.validated_data["id"]
        # TODO:
        # Make sure that they have permission to comment on that post.

    def create(self, validated_data):




