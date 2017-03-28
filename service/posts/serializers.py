from rest_framework import serializers

from service.authors.serializers import SimpleAuthorSerializer
from social.app.models.post import Post


class PostSerializer(serializers.HyperlinkedModelSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name="service:post-detail",
        read_only=True,
        lookup_field="pk"
    )

    author = SimpleAuthorSerializer()

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
                  "categories", "comments", "published", "id", "visibility", "visibleTo", "unlisted")
