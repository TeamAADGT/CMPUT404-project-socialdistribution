from rest_framework import models
from rest_framework import serializers

from social.app.models.author import Author
from social.app.models.node import Node


class SimpleNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ('host', 'service_url',)


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = ('host', 'service_url', 'local', 'username', 'password',)
