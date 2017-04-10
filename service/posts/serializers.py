from rest_framework import serializers

from service.authors.serializers import SimpleAuthorSerializer
from service.comments.serializers import CommentSerializer
from social.app.models.post import Post


class PostSerializer(serializers.HyperlinkedModelSerializer):
    # Not required by the spec, but makes testing a little easier
    url = serializers.HyperlinkedIdentityField(
        view_name="service:post-detail",
        source='id'
    )
    author = SimpleAuthorSerializer()
    comments = CommentSerializer(many=True)

    contentType = serializers.CharField(source="content_type", read_only=True)

    visibleTo = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        source="visible_to",
        view_name="service:author-detail",
        lookup_field="pk"
    )

    categories = serializers.ListField(
        source="categories_list",
        read_only=True
    )

    class Meta:
        model = Post
        fields = ("title", "source", "origin", "description", "contentType", "content", "author",
                  "categories", "comments", "published", "id", "url", "visibility", "visibleTo",
                  "unlisted")
