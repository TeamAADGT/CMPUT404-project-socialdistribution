from rest_framework import serializers

#from service.posts.serializers import PostSerializer
from service.authors.serializers import SimpleAuthorSerializer

from social.app.models.comment import Comment


class CommentSerializer(serializers.HyperlinkedModelSerializer):
    author = SimpleAuthorSerializer()
    #post = PostSerializer()

    class Meta:
        model = Comment
        fields = ("id", "author", "comment", "published")
