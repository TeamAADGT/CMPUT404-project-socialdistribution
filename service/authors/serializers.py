from rest_framework import serializers

from social.app.models.author import Author


class AuthorURLSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail', read_only=True, lookup_field='pk')

    class Meta:
        model = Author
        fields = ('url',)


class SimpleAuthorSerializer(serializers.ModelSerializer):
    id = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail',
        lookup_field='pk',
        help_text='The URI of the Author. (required)'
    )
    host = serializers.CharField(
        source='node.service_url',
        help_text='The hostname of the Author. (required)'
    )
    url = serializers.HyperlinkedIdentityField(
        view_name='service:author-detail',
        lookup_field='pk',
        required=False,
        help_text='The URI of the Author. (optional)'
    )
    github = serializers.URLField(
        required=False,
        help_text="The URL of the Author's Github profile. Example: https://github.com/username (optional)"
    )

    class Meta:
        model = Author
        fields = ('id', 'host', 'displayName', 'url', 'github')


class AuthorSerializer(SimpleAuthorSerializer):
    friends = AuthorURLSerializer(many=True)
    firstName = serializers.CharField(source='user.first_name')
    lastName = serializers.CharField(source='user.last_name')
    email = serializers.CharField(source='user.email')

    class Meta:
        model = Author
        fields = ('id', 'host', 'displayName', 'url', 'friends', 'github', 'firstName', 'lastName', 'email', 'bio',)
