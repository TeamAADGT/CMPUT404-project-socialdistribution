from rest_framework import serializers

from service.authors.serializers import SimpleAuthorSerializer, UnknownAuthorSerializer
from social.app.models.post import Post


class PostSerializer(serializers.HyperlinkedModelSerializer):
    # Not required by the spec, but makes testing a little easier
    url = serializers.HyperlinkedIdentityField(
        view_name="service:post-detail",
        source='id'
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
                  "categories", "comments", "published", "id", "url", "visibility", "visibleTo", "unlisted")


class FOAFCheckPostSerializer(serializers.Serializer):
    query = serializers.CharField(
        help_text='The requested query to be performed. Must be equal to "getPost".'
    )
    postid = serializers.UUIDField()
    url = serializers.URLField(
        help_text='The URI of the requested Post. Example: http://service/posts/{POST_ID} (required)'
    )
    author = UnknownAuthorSerializer()
    friends = serializers.ListField(
        child=serializers.URLField(),
        required=True,
        allow_empty=True
    )
