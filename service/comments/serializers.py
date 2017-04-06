from rest_framework import serializers

from service.authors.serializers import SimpleAuthorSerializer
from social.app.models.comment import Comment


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = SimpleAuthorSerializer()

    class Meta:
        model = Comment
        fields = ("id", "author", "comment", "published")
