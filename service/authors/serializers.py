from rest_framework import serializers

from social.app.models.author import Author


class UnknownAuthorSerializer(serializers.Serializer):
    """
    Used in input cases where we don't necessarily know about a remote Author yet, so it doesn't make sense
    to use a ModelSerializer
    """
    id = serializers.URLField()
    host = serializers.URLField()
    url = serializers.URLField()
    displayName = serializers.CharField(
        required=False,
        allow_blank=True
    )
    github = serializers.URLField(
        required=False,
        allow_blank=True
    )


class AuthorURLSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')

    class Meta:
        model = Author
        fields = ('url',)


class SimpleAuthorSerializer(serializers.ModelSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')
    host = serializers.CharField(source='node.service_url')
    url = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')

    class Meta:
        model = Author
        fields = ('id', 'host', 'displayName', 'url', 'github')


class UnknownAuthorSerializer(serializers.Serializer):
    """
    Used in input cases where we don't necessarily know about a remote Author yet, so it doesn't make sense
    to use a ModelSerializer
    """
    id = serializers.URLField()
    host = serializers.URLField()
    url = serializers.URLField()
    github = serializers.URLField(
        required=False,
        allow_blank=True
    )


class AuthorSerializer(serializers.ModelSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')
    host = serializers.URLField(source='node.service_url')
    url = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')

    friends = AuthorURLSerializer(many=True, read_only=True)
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = Author
        fields = ('id', 'host', 'displayName', 'url', 'friends', 'github', 'firstName', 'lastName', 'email', 'bio',)
