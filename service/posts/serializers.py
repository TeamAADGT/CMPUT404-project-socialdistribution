from rest_framework import serializers

from social.app.models.post import Post


class PostSerializer(serializers.HyperlinkedModelSerializer):
    contentType = serializers.CharField(source="content_type", read_only=True)

    visibleTo = serializers.HyperlinkedRelatedField(
        many=True,
        read_only=True,
        source="visible_to",
        view_name="author-detail"
    )

    categories = serializers.ListField(
        source="categories_list",
        read_only=True
    )

    class Meta:
        model = Post
        read_only_fields = ("title", "source", "origin", "description", "contentType", "content", "author",
                            "categories", "comments", "published", "id", "visibility", "visibleTo", "unlisted")
